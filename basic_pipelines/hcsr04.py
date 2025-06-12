import lgpio
import time

class HCSR04:
    def __init__(self):
        self.forward_trigger = 16
        self.forward_echo = 20
        self.gpio = lgpio.gpiochip_open(0)
        self.timeout = 0.02  # 20ms timeout (adjust as needed)
        

    def setup_sensors(self):    
        lgpio.gpio_claim_output(self.gpio, self.forward_trigger)
        lgpio.gpio_claim_input(self.gpio, self.forward_echo)
        lgpio.gpio_write(self.gpio, self.forward_trigger, 0)  # Ensure trigger is low initially
        time.sleep(0.1)  # Small delay to stabilize

    def measure_distance(self, trigger, echo):
        # Send 10us trigger pulse
        lgpio.gpio_write(self.gpio, trigger, 1)
        time.sleep(0.00001)  # 10 microseconds
        lgpio.gpio_write(self.gpio, trigger, 0)

        # Wait for echo to go high (start of pulse) with timeout
        start_wait = time.time()
        while lgpio.gpio_read(self.gpio, echo) == 0:
            if time.time() - start_wait > self.timeout:
                return -1  # Timeout, no echo start detected

        start_time = time.time()

        # Wait for echo to go low (end of pulse) with timeout
        while lgpio.gpio_read(self.gpio, echo) == 1:
            if time.time() - start_time > self.timeout:
                return -1  # Timeout, no echo end detected

        end_time = time.time()

        # Calculate distance (speed of sound = 343 m/s, so 17150 cm/s)
        distance = (end_time - start_time) * 17150
        return distance if distance < 400 else -1  # Filter out unrealistic distances (>4m)

    def get_distance(self):
        """Get a single distance measurement."""
        return self.measure_distance(self.forward_trigger, self.forward_echo)
    def gpio_stop(self):
        lgpio.gpio_write(self.gpio, self.forward_trigger, 0)  # Ensure trigger is low
        lgpio.gpio_free(self.gpio, self.forward_trigger)
        lgpio.gpio_free(self.gpio, self.forward_echo)
        lgpio.gpiochip_close(self.gpio)

    def run(self):
        self.setup_sensors()
        try:
            while True:
                distance = self.get_distance()
                if distance >= 0:
                    print(f"Sensor: {distance:.2f} cm")
                    
                else:
                    print("Sensor: Measurement failed")
                time.sleep(0.06)  # 60ms delay to allow sensor to settle (HC-SR04 needs ~50ms)
        except KeyboardInterrupt:
            print("The script has been interrupted")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.gpio_stop()

if __name__ == "__main__":
    try:
        sensor = HCSR04()
        sensor.run()
    except KeyboardInterrupt:
        print("Interrupted")
    except Exception as e:
        print(f"Main error: {e}")