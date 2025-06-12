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
from hcsr04 import HCSR04

class BattleBotCallback(app_callback_class):
    def __init__(self, canbus: CANEncoder, sensor: HCSR04):
        super().__init__()
        self.min_bbox_area = 5000
        self.square_size = 400
        self.canbus = canbus
        self.sensor = sensor
        self.base_speed = 1500
        self.dynamic_pwm_value = 500
        self.max_turn_adjustment = 100  
        self.gripper_open = 1000  
        self.gripper_closed = 2000
        self.threshold = 50
        self.video_width = 1280
        self.video_height = 720
        # self.bottle_distance = 11.5
        self.bottle_detected = False

    def difference_wheels_pwm(self, steering_data):
        left_wheel = steering_data[0]
        right_wheel = steering_data[1]
        gripper = steering_data[2]

        min_waarde_wiel = min(left_wheel, right_wheel)
        max_waarde_wiel = max(left_wheel, right_wheel)

        difference_values = int((max_waarde_wiel % min_waarde_wiel) / 2)
        print(steering_data)

        if difference_values > 50:

            left_wheel = int(1500 + (left_wheel - 1500) * 1.0)
            right_wheel = int(1500 + (right_wheel - 1500) * 1.0)
            gripper = gripper

            if left_wheel < (right_wheel - 5):
                left_wheel = int(1500 + (left_wheel - 1500) * 0.5 - 5)
            elif left_wheel > (right_wheel + 5):
                right_wheel = int(1500 + (right_wheel - 1500) * 0.5 - 60)

            return self.canbus.sendSteering((left_wheel, right_wheel, gripper))
        else:
            if left_wheel > right_wheel:
                left_wheel -= difference_values
                right_wheel += difference_values
            elif left_wheel < right_wheel:
                left_wheel += difference_values
                right_wheel -= difference_values

            return self.canbus.sendSteering((left_wheel, right_wheel, gripper))

    def process_detection(self, pad, info, extra):
        buffer = info.get_buffer()
        if buffer is None:
            print("No buffer available")
            return Gst.PadProbeReturn.OK

        format, width, height = get_caps_from_pad(pad)
        if format is None or width is None or height is None:
            print(f"Invalid caps: format={format}, width={width}, height={height}")
            return Gst.PadProbeReturn.OK

        square_x1 = (self.video_width - self.square_size) // 2
        square_y1 = (self.video_height - self.square_size) // 2
        square_x2 = square_x1 + self.square_size
        square_y2 = square_y1 + self.square_size

        # print(square_x1, square_y1, square_x2, square_y2)

        left_speed = self.base_speed
        right_speed = self.base_speed
        gripper = self.gripper_open

        roi = hailo.get_roi_from_buffer(buffer)
        detections = roi.get_objects_typed(hailo.HAILO_DETECTION)

        # Afstand tot de fles
        distance = self.sensor.get_distance()
        truncated_distance = float(f"{distance:.1f}"[:5])
        # print(truncated_distance)

        #
        # ############3
        #
        
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
                self.bottle_detected = True
                
                # print(x_min, y_min, x_max, y_max)

                if bottle_area < self.min_bbox_area:
                    continue

                if (square_x1 <= bottle_center[0] <= square_x2 and
                    square_y1 <= bottle_center[1] <= square_y2):
                    left_speed = self.base_speed + self.dynamic_pwm_value
                    right_speed = self.base_speed + self.dynamic_pwm_value

                    steering_data = (int(left_speed), int(right_speed), int(gripper))
                    self.difference_wheels_pwm(steering_data)
                    # self.canbus.sendHeartbeat()
                    print(f"Bottle centered, Confidence: {confidence:.2f}, Center: {bottle_center}, Area: {bottle_area}, "
                          f"Left: {left_speed}, Right: {right_speed}")
                
                else:
                    center_x = self.video_width // 2
                    deviation = bottle_center[0] - center_x
                    adjustment = int((deviation / center_x) * self.max_turn_adjustment)
                    
                    left_speed = self.base_speed + adjustment + self.dynamic_pwm_value
                    right_speed = self.base_speed - adjustment + self.dynamic_pwm_value

                    left_speed = max(1000, min(2000, left_speed))
                    right_speed = max(1000, min(2000, right_speed))
                    gripper = self.gripper_open

                    steering_data = (int(left_speed), int(right_speed), int(gripper))
                    self.difference_wheels_pwm(steering_data)
                    # self.canbus.sendHeartbeat()
                    print(f"Bottle detected, Confidence: {confidence:.2f}, Center: {bottle_center}, Area: {bottle_area}, "
                          f"Left: {left_speed}, Right: {right_speed}")

            elif self.bottle_detected:
            #     self.bottle_detected = False
                if truncated_distance > float(11) and truncated_distance < float(12):
                    left_speed = self.base_speed  
                    right_speed = self.base_speed 
                    gripper = self.gripper_closed
                    print(f"{truncated_distance}")
                elif truncated_distance > float(12):
                    left_speed = self.base_speed  + self.dynamic_pwm_value
                    right_speed = self.base_speed + self.dynamic_pwm_value

                    gripper = self.gripper_open

                    steering_data = (int(left_speed), int(right_speed), int(gripper))
                    self.difference_wheels_pwm(steering_data)
                    print(f"boven de twaalef: {truncated_distance, steering_data}")
            else:
                self.bottle_detected = False
                gripper = self.gripper_closed
                steering_data = (int(left_speed), int(right_speed), int(gripper))
                self.difference_wheels_pwm(steering_data)

        return Gst.PadProbeReturn.OK

async def main():
    canbus = CANEncoder().callMCP2515Instance()
    if canbus.mcp2515 is None:
        print("Failed to initialize CAN bus, exiting")
        return

    sensor = HCSR04()
    sensor.setup_sensors()

    Gst.init([])

    user_data = BattleBotCallback(canbus, sensor)
    app = GStreamerDetectionApp(user_data.process_detection, user_data)
    loop = GLib.MainLoop()

    try:
        app.run()
        loop.run()
    except KeyboardInterrupt:
        print("Shutting down...")
        canbus.mcp2515.closeMcp2515()
        sensor.gpio_stop()
        loop.quit()
    except Exception as e:
        print(f"Error in main loop: {e}")
        canbus.mcp2515.closeMcp2515()
        sensor.gpio_stop()
        loop.quit()

if __name__ == "__main__":
    asyncio.run(main())