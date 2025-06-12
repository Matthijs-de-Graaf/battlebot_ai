import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import os
import numpy as np
import cv2
import hailo
import asyncio
from hailo_apps_infra.hailo_rpi_common import (
    get_caps_from_pad,
    get_numpy_from_buffer,
    app_callback_class,
)
from hailo_apps_infra.detection_pipeline import GStreamerDetectionApp
from encoder import CANEncoder

class BattleBotCallback(app_callback_class):
    def __init__(self, canbus: CANEncoder):
        super().__init__()
        self.min_bbox_area = 5000
        self.frame_width = 1280
        self.frame_height = 720
        self.box_width = 150  # Kleinere box (ongeveer 6 cm breed op 13 cm afstand)
        self.box_height = 300  # Kleinere box (ongeveer 15 cm hoog op 13 cm afstand)
        self.use_frame = True
        self.canbus = canbus
        self.base_speed = 1500
        self.max_turn_adjustment = 100
        self.gripper_open = 1000
        self.gripper_closed = 2000
        self.last_bottle_center = None  # Voor het bijhouden van de laatst bekende positie
        self.close_distance_threshold = 100000  # Threshold voor bounding box grootte (in pixels)
        self.frames_without_detection = 0  # Teller voor frames zonder detectie
        self.max_frames_without_detection = 10  # Max aantal frames voordat we stoppen

    def process_detection(self, pad, info, extra):
        buffer = info.get_buffer()
        if buffer is None:
            print("No buffer available")
            return Gst.PadProbeReturn.OK

        format, width, height = get_caps_from_pad(pad)
        if format is None or width is None or height is None:
            print(f"Invalid caps: format={format}, width={width}, height={height}")
            return Gst.PadProbeReturn.OK

        # Center de detectiebox
        box_x1 = (self.frame_width - self.box_width) // 2
        box_y1 = (self.frame_height - self.box_height) // 2
        box_x2 = box_x1 + self.box_width
        box_y2 = box_y1 + self.box_height

        left_speed = self.base_speed
        right_speed = self.base_speed
        gripper = self.gripper_open

        roi = hailo.get_roi_from_buffer(buffer)
        detections = roi.get_objects_typed(hailo.HAILO_DETECTION)
        bottle_detected = False

        for detection in detections:
            label = detection.get_label()
            bbox = detection.get_bbox()
            confidence = detection.get_confidence()

            if label == "bottle" and confidence > 0.5:
                x_min = int(bbox.xmin() * width)
                y_min = int(bbox.ymin() * height)
                x_max = int(bbox.xmax() * width)
                y_max = int(bbox.ymax() * height)
                bottle_center = ((x_min + x_max) // 2, (y_min + y_max) // 2)
                bottle_area = (x_max - x_min) * (y_max - y_min)

                if bottle_area < self.min_bbox_area:
                    continue

                bottle_detected = True
                self.last_bottle_center = bottle_center  # Update laatst bekende positie
                self.frames_without_detection = 0  # Reset teller

                # Controleer of de fles dichtbij is (grote bounding box)
                if bottle_area > self.close_distance_threshold:
                    left_speed = 0  # Stop de bot
                    right_speed = 0
                    gripper = self.gripper_closed
                    print(f"Bottle zeer dichtbij, Confidence: {confidence:.2f}, Area: {bottle_area}, Gripper sluiten")
                elif (box_x1 <= bottle_center[0] <= box_x2 and
                      box_y1 <= bottle_center[1] <= box_y2):
                    left_speed = self.base_speed
                    right_speed = self.base_speed
                    print(f"Bottle gecentreerd in box, Confidence: {confidence:.2f}, Center: {bottle_center}")
                else:
                    center_x = self.frame_width // 2
                    deviation = bottle_center[0] - center_x
                    adjustment = int((deviation / center_x) * self.max_turn_adjustment)
                    left_speed = self.base_speed + adjustment + 150
                    right_speed = self.base_speed - adjustment + 150
                    left_speed = max(1000, min(2000, left_speed))
                    right_speed = max(1000, min(2000, right_speed))
                    print(f"Bottle gedetecteerd, Confidence: {confidence:.2f}, Center: {bottle_center}, Area: {bottle_area}, "
                          f"Left: {left_speed}, Right: {right_speed}")

        if not bottle_detected:
            self.frames_without_detection += 1
            if self.last_bottle_center and self.frames_without_detection <= self.max_frames_without_detection:
                # Gebruik laatst bekende positie om te sturen
                center_x = self.frame_width // 2
                deviation = self.last_bottle_center[0] - center_x
                adjustment = int((deviation / center_x) * self.max_turn_adjustment)
                left_speed = self.base_speed + adjustment + 150
                right_speed = self.base_speed - adjustment + 150
                left_speed = max(1000, min(2000, left_speed))
                right_speed = max(1000, min(2000, right_speed))
                gripper = self.gripper_open
                self.canbus.sendSteering((left_speed, right_speed, gripper))
                print(f"Geen fles gedetecteerd, gebruik laatst bekende positie: {self.last_bottle_center}, "
                      f"Left: {left_speed}, Right: {right_speed}")
            else:
                # Geen recente detectie, zoekmodus
                left_speed = self.base_speed + 175
                right_speed = self.base_speed - 165
                gripper = self.gripper_closed
                self.canbus.sendSteering((left_speed, right_speed, gripper))
                print("Geen fles gedetecteerd, zoeken")

        self.canbus.sendHeartbeat()

        return Gst.PadProbeReturn.OK

async def main():
    canbus = CANEncoder().callMCP2515Instance()
    if canbus.mcp2515 is None:
        print("Failed to initialize CAN bus, exiting")
        return

    Gst.init([])

    user_data = BattleBotCallback(canbus)
    app = GStreamerDetectionApp(user_data.process_detection, user_data)
    loop = GLib.MainLoop()
    try:
        app.run()
        loop.run()
    except KeyboardInterrupt:
        print("Shutting down...")
        canbus.mcp2515.closeMcp2515()
        loop.quit()
    except Exception as e:
        print(f"Error in main loop: {e}")
        canbus.mcp2515.closeMcp2515()
        loop.quit()

if __name__ == "__main__":
    asyncio.run(main())