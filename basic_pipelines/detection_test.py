import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import os
import time
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
        self.square_center_width = 200
        self.canbus = canbus
        self.sensor = sensor
        self.base_speed = 1500
        self.dynamic_pwm_value = 280
        self.max_turn_adjustment = 75
        self.gripper_open = 2000  
        self.gripper_closed = 1000
        self.threshold = 50
        self.video_width = 1280
        self.video_height = 720
        self.bottle_detected = False
        self.history_distance = []
        self.new_result = 0

    def difference_wheels_pwm(self, steering_data):     
        left_wheel, right_wheel, gripper = steering_data

        min_waarde_wiel = min(left_wheel, right_wheel)
        max_waarde_wiel = max(left_wheel, right_wheel)

        difference_values = int((max_waarde_wiel % min_waarde_wiel) / 2)
        print(steering_data)

        if difference_values > 50:

            left_wheel = int(1500 + (left_wheel - 1500) * 1.0)
            right_wheel = int(1500 + (right_wheel - 1500) * 1.0)

            if left_wheel < (right_wheel - 5):
                left_wheel = int(1500 + (left_wheel - 1500) * 0.5 - 5)
            elif left_wheel > (right_wheel + 5):
                right_wheel = int(1500 + (right_wheel - 1500) * 0.5 - 60)

        else:
            if left_wheel > right_wheel:
                left_wheel -= difference_values
                right_wheel += difference_values
            elif left_wheel < right_wheel:
                left_wheel += difference_values
                right_wheel -= difference_values

        self.canbus.sendSteering((left_wheel, right_wheel, gripper))

    def defining_center_square(self):
        # Taking the width of the screen (1280 pixels) and then i wanted to make the square (400 pixels), this is hardcoded and can be changed
        # Left wall is 440
        # Top wall is 0
        # Right wall is 840
        # Bottom wall is 720
        center_left_wall = (self.video_width - self.square_center_width) // 2
        # center_top_wall = (self.video_height - self.square_center_width) // 2
        center_top_wall = 0
        center_right_wall = center_left_wall + self.square_center_width
        # center_bottom_wall = center_top_wall + self.square_center_width
        center_bottom_wall = self.video_height
        
        return center_left_wall, center_top_wall, center_right_wall, center_bottom_wall

    def defining_bottle_square(self, bbox, width, height):
        # Taking the pixels of the width and height of the bottle by taking the bbox (bounding box from hailo, who is making the boxes)
        # Works the same as defining_center_square, kinda
        bottle_left_wall = int(bbox.xmin() * width)
        bottle_top_wall = int(bbox.ymin() * height)
        bottle_right_wall = int(bbox.xmax() * width)
        bottle_bottom_wall = int(bbox.ymax() * height)

        bottle_center = ((bottle_left_wall + bottle_right_wall) // 2, (bottle_top_wall + bottle_bottom_wall) // 2)
        bottle_area = (bottle_right_wall - bottle_left_wall) * (bottle_right_wall - bottle_top_wall)
        bottle_width = bottle_right_wall - bottle_left_wall
        bottle_height = bottle_bottom_wall - bottle_top_wall 

        return bottle_center, bottle_area, bottle_width, bottle_height
    
    def moving_wheels_pwm(self, status_moving, status_gripper, adjustment=0):
        # Decide which PWM values based on the status
        left_speed = 1500
        right_speed = 1500

        if status_moving == "move":
            left_speed = self.base_speed + self.dynamic_pwm_value
            right_speed = self.base_speed + self.dynamic_pwm_value
        elif status_moving == "move_left":
            left_speed = self.base_speed - adjustment + self.dynamic_pwm_value
            right_speed = self.base_speed + adjustment + self.dynamic_pwm_value
            print("LEFT")
        elif status_moving == "move_right":
            left_speed = self.base_speed + adjustment + self.dynamic_pwm_value
            right_speed = self.base_speed - adjustment + self.dynamic_pwm_value
            print("RIGHT")
        elif status_moving == "move_left_slow":
            left_speed = self.base_speed - adjustment + self.dynamic_pwm_value
            right_speed = self.base_speed + adjustment + self.dynamic_pwm_value
            print("LEFT SLOW")
        elif status_moving == "move_right_slow":
            left_speed = self.base_speed + adjustment + self.dynamic_pwm_value
            right_speed = self.base_speed - adjustment + self.dynamic_pwm_value
            print("RIGHT")
        elif status_moving == "searching":
            left_speed = self.base_speed + adjustment + self.dynamic_pwm_value
            right_speed = self.base_speed - adjustment - self.dynamic_pwm_value
        elif status_moving == "slow":
            left_speed = self.base_speed - adjustment + self.dynamic_pwm_value
            right_speed = self.base_speed - adjustment + self.dynamic_pwm_value
            print("SLOW")
        elif status_moving == "stop":
            left_speed = self.base_speed
            right_speed = self.base_speed
         
        gripper = status_gripper
        
        new_left_speed = max(1000, min(2000, left_speed))
        new_right_speed = max(1000, min(2000, right_speed))  

        # print(left_speed, right_speed, gripper)
        
        # self.canbus.sendHeartbeat()
        steering_data = int(new_left_speed), int(new_right_speed), int(gripper)
        # self.difference_wheels_pwm(steering_data)
        self.canbus.sendSteering(steering_data)
        
    def adjust_wheels_pwm(self, bottle_center, slow):
        # Correct the direction of the wheels to go to the bottle
        # Center_x is middle of the screen (1280 // 2 = 640)
        # Deviation is just for knowing which side the wheels must turn (left or right)
        # Is for knowing how far the deviation is from the middle of the screen (deviation / 640) * 100 
        center_x = self.video_width // 2 # Vertical line on the x axis
        deviation = bottle_center[0] - center_x
        adjustment = abs(int((deviation / center_x) * self.max_turn_adjustment))

        if deviation < 0:
            # if adjustment < 15:
            #     adjustment = abs(adjustment) * 1
            #     self.moving_wheels_pwm("move_left", self.gripper_open, adjustment)
            #     print(f"(div<0|move_left|adjus<15) center_bottle: {bottle_center[0]}, deviation: {deviation}, adjustment: {adjustment}")
            if slow:
                adjustment -= 10
                self.moving_wheels_pwm("move_left_slow", self.gripper_open, adjustment)
                print(f"(div<0|move_left) center_bottle: {bottle_center[0]}, deviation: {deviation}, adjustment: {adjustment}")

            self.moving_wheels_pwm("move_left", self.gripper_open, adjustment)
            print(f"(div<0|move_left) center_bottle: {bottle_center[0]}, deviation: {deviation}, adjustment: {adjustment}")

        elif deviation > 0:
            # if adjustment < 15:
            #     adjustment = abs(adjustment) * 1
            #     self.moving_wheels_pwm("move_right", self.gripper_open, adjustment)
            #     print(f"(div<0|move_right|adjus<15) center_bottle: {bottle_center[0]}, deviation: {deviation}, adjustment: {adjustment}")
            if slow:
                adjustment -= 10
                self.moving_wheels_pwm("move_right_slow", self.gripper_open, (adjustment))
                print(f"(div<0|move_right) center_bottle: {bottle_center[0]}, deviation: {deviation}, adjustment: {adjustment}")

            self.moving_wheels_pwm("move_right", self.gripper_open, adjustment)
            print(f"(div<0|move_right) center_bottle: {bottle_center[0]}, deviation: {deviation}, adjustment: {adjustment}")


    def process_detection(self, pad, info, extra):
        buffer = info.get_buffer()
        if buffer is None:
            print("No buffer available")
            return Gst.PadProbeReturn.OK

        format, width, height = get_caps_from_pad(pad)
        if format is None or width is None or height is None:
            print(f"Invalid caps: format={format}, width={width}, height={height}")
            return Gst.PadProbeReturn.OK

        # All variables from the function and is added later in the if statement
        center_left_wall, center_top_wall, center_right_wall, center_bottom_wall = self.defining_center_square()
        # print(self.defining_center_square)

        # self.moving_wheels_pwm("stop", self.gripper_open)

        roi = hailo.get_roi_from_buffer(buffer)
        detections = roi.get_objects_typed(hailo.HAILO_DETECTION)

        # Afstand tot de fles
        distance = self.sensor.get_distance()
        truncated_distance = float(f"{distance:.1f}"[:5])
        
        for detection in detections:
            label = detection.get_label()
            bbox = detection.get_bbox()
            confidence = detection.get_confidence()

            # We are targeting the bottle, so remove the vase later and the same with th 30% confidence
            if label == "bottle" and confidence > 0.3 or label == "vase":
                bottle_center, bottle_area, bottle_width, bottle_height = self.defining_bottle_square(bbox, width, height)
                self.bottle_detected = True
        
                print(bottle_height)

                if bottle_area < self.min_bbox_area:
                    continue

                if (center_left_wall <= bottle_center[0] <= center_right_wall and
                    center_top_wall <= bottle_center[1] <= center_bottom_wall):
                    # If the bottle is in the middle, then the gripper needs to be set open for taking action later. 
                    # Need to change the if statement bc i think this is not neccesary
                    if bottle_height < 240:
                        self.moving_wheels_pwm("move", self.gripper_open)
                    else:
                        self.moving_wheels_pwm("slow", self.gripper_open, adjustment=10)

                    # self.adjust_wheels_pwm(bottle_center)

                    # print(f"Bottle centered, Confdidence: {confidence:.2f}, Center: {bottle_center}, Area: {bottle_area}")
                
                else:
                    if bottle_height < 240:
                        # Face the bottle
                        self.adjust_wheels_pwm(bottle_center, slow=False)
                        # print(f"Botstle detected, Confidence: {confidence:.2f}, Center: {bottle_center}, Area: {bottle_area}")
                    else:
                        self.adjust_wheels_pwm(bottle_center, slow=True)
                    # pass 

                # elif truncated_distance > float(12):
                #     self.moving_wheels_pwm("move", self.gripper_open)
                #     print(f"boven de twaalef: {truncated_distance}")
                #     time.sleep(0.1)
            elif self.bottle_detected:
                # Is going to spin to look for the bottle
                # self.bottle_detected = False
                # self.moving_wheels_pwm("searching", self.gripper_open)
                # if self.bottle_detected:
                #     # If the bottle was seen and then take action for closing the gripper
                # print("bottle_detected")
                if truncated_distance == float(-1):
                    continue

                if len(self.history_distance) < 20:
                    self.history_distance.append(truncated_distance)
                else:
                    self.history_distance.pop(0)
                 
                result = 0

                for distance_new in self.history_distance:
                    result += distance_new
                
                if len(self.history_distance) == 19:
                    self.new_result = float(f"{result / 20:.1f}"[:5])
                    

                if self.new_result > float(20):
                    print(f"probeer verder  , gripper value: {self.gripper_closed}")
                    self.moving_wheels_pwm("move", self.gripper_open)
                    print(self.new_result)

                if self.new_result <= float(12) and self.new_result > float(3):
                    print(self.new_result)
                    print(f"Attempt to close gripper: Distance: {truncated_distance}, gripper value: {self.gripper_closed}")
                    self.moving_wheels_pwm("stop", self.gripper_closed)
                    time.sleep(0.001)

            else:
                # self.moving_wheels_pwm("searching", self.gripper_open)
                print("Hij pass")
                pass

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