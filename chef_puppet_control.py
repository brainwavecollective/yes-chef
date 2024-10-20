import time
import threading
import numpy as np
import yaml
from lerobot.common.robot_devices.motors.feetech import FeetechMotorsBus

class ChefPuppetControl:
    def __init__(self):
        self.motor_name = "servo6"  # Mouth servo
        self.motor_index = 6
        self.motor_model = "sts3215"
        self.port = "/dev/ttyACM0"
        self.baudrate = 1000000

        self.motors_bus = FeetechMotorsBus(
            port=self.port,
            motors={self.motor_name: (self.motor_index, self.motor_model)},
        )

        self.closed_position = 1100
        self.open_positions = [1400, 1700, 2000]  # Various open positions

        # Easily adjustable parameters for mouth movement
        self.silence_threshold = 0.1
        self.vowel_threshold = 0.35
        self.segment_duration = 0.02  # 20ms segments
        self.mouth_update_delay = 0.01  # 10ms delay between mouth updates
        self.current_mouth_state = 0

        self.all_servos = {
            "servo1": (1, "sts3215"),
            "servo2": (2, "sts3215"),
            "servo3": (3, "sts3215"),
            "servo4": (4, "sts3215"),
            "servo5": (5, "sts3215"),
            "servo6": (6, "sts3215"),
        }

        self._connect_motors()

    def _connect_motors(self):
        try:
            print(f"Attempting to connect to {self.motor_name} on port {self.port}")
            self.motors_bus.connect()
            print(f"Connected successfully. Setting baudrate to {self.baudrate}")
            self.motors_bus.set_bus_baudrate(self.baudrate)
        except Exception as e:
            print(f"An error occurred while connecting to motors: {str(e)}")

    def move_mouth(self, audio_buffer):
        """Move mouth based on audio buffer, analyzing smaller segments within the chunk."""
        sample_rate = 44100  # Hz
        audio_data = np.frombuffer(audio_buffer, dtype=np.int16).astype(np.float32)
        audio_data /= np.max(np.abs(audio_data))  # Normalize

        segment_size = int(self.segment_duration * sample_rate)
        num_segments = 2

        for i in range(num_segments):
            start = i * segment_size
            end = start + segment_size
            segment = audio_data[start:end]
            
            segment_amplitude = np.mean(np.abs(segment))
            
            if segment_amplitude < self.silence_threshold:
                self._set_mouth_state(0)  # Closed
                time.sleep(self.mouth_update_delay)
            elif segment_amplitude > self.vowel_threshold:
                self._set_mouth_state(1)
                time.sleep(self.mouth_update_delay * 5)
            else:
                openness = (segment_amplitude - self.silence_threshold) / (self.vowel_threshold - self.silence_threshold)
                self._set_mouth_state(openness)
                time.sleep(self.mouth_update_delay)
            
            print(f"Segment {i+1}/{num_segments}, Amplitude: {segment_amplitude:.4f}, Mouth openness: {self._get_mouth_state():.2f}")

        # Ensure the mouth is closed after processing all segments
        self._set_mouth_state(0)

    def _set_mouth_state(self, openness):
        """Set the mouth state with a value between 0 (closed) and 1 (fully open)."""
        self.current_mouth_state = max(0, min(1, openness))  # Ensure openness is between 0 and 1
        position = int(self.closed_position + (self.open_positions[-1] - self.closed_position) * self.current_mouth_state)
        try:
            self.motors_bus.write("Goal_Position", position)
        except Exception as e:
            print(f"Error setting mouth state: {e}")

    def _get_mouth_state(self):
        """Get the current mouth state."""
        return self.current_mouth_state

    def stop_mouth_movement(self):
        self._set_mouth_state(0)  # Ensure the mouth is closed

    # Placeholder methods for compatibility with the previous SkeletonControl
    def start_body_movement(self):
        print("Body movement started (placeholder)")

    def stop_body_movement(self):
        print("Body movement stopped (placeholder)")

    def eyes_on(self):
        print("Eyes turned on (placeholder)")

    def eyes_off(self):
        print("Eyes turned off (placeholder)")

    def record_state(self, name, connect_delay=0.5):
        """
        Connect to all servos with a staggered delay, record their positions,
        and save to positions.yaml with the given name.
        """
        positions = {}
        
        for servo_name, (servo_index, servo_model) in self.all_servos.items():
            try:
                print(f"Connecting to {servo_name}...")
                temp_bus = FeetechMotorsBus(
                    port=self.port,
                    motors={servo_name: (servo_index, servo_model)},
                )
                temp_bus.connect()
                temp_bus.set_bus_baudrate(self.baudrate)

                time.sleep(connect_delay)

                # Read the current position and convert to a simple integer
                position = temp_bus.read("Present_Position")
                if isinstance(position, np.ndarray):
                    position = int(position.item())
                positions[servo_name] = position

                print(f"Recorded position for {servo_name}: {position}")

                temp_bus.disconnect()
                time.sleep(connect_delay)

            except Exception as e:
                print(f"Error recording state for {servo_name}: {str(e)}")

        # Load existing positions or create a new dictionary
        try:
            with open('positions.yaml', 'r') as file:
                all_positions = yaml.safe_load(file) or {}
        except FileNotFoundError:
            all_positions = {}

        # Add or update the named position
        all_positions[name] = positions

        # Save all positions to YAML file
        with open('positions.yaml', 'w') as file:
            yaml.dump(all_positions, file, default_flow_style=False)

        print(f"Servo positions for '{name}' have been recorded and saved to positions.yaml")

    def load_positions(self):
        """Load positions from the YAML file."""
        try:
            with open('positions.yaml', 'r') as file:
                return yaml.safe_load(file) or {}
        except FileNotFoundError:
            print("positions.yaml not found. No positions loaded.")
            return {}

    def load_and_set_state(self, name, connect_delay=0.5):
        """
        Load a named state from the YAML file and set servo positions accordingly.
        """
        all_positions = self.load_positions()
        if name not in all_positions:
            print(f"No state named '{name}' found in positions.yaml")
            return

        positions = all_positions[name]
        
        for servo_name, position in positions.items():
            if servo_name not in self.all_servos:
                print(f"Warning: {servo_name} not found in connected servos. Skipping.")
                continue

            servo_index, servo_model = self.all_servos[servo_name]
            try:
                print(f"Setting position for {servo_name}...")
                temp_bus = FeetechMotorsBus(
                    port=self.port,
                    motors={servo_name: (servo_index, servo_model)},
                )
                temp_bus.connect()
                temp_bus.set_bus_baudrate(self.baudrate)

                time.sleep(connect_delay)

                # Set the position
                temp_bus.write("Goal_Position", position)
                print(f"Set position for {servo_name} to {position}")

                temp_bus.disconnect()
                time.sleep(connect_delay)

            except Exception as e:
                print(f"Error setting position for {servo_name}: {str(e)}")

        print(f"Finished setting positions for state '{name}'")

    def cleanup(self):
        self.stop_mouth_movement()
        self.motors_bus.disconnect()
        print("ChefPuppetControl cleanup completed")

if __name__ == "__main__":
    puppet = ChefPuppetControl()

    # print("Testing mouth movement...")
    # for _ in range(3):
    #     puppet._set_mouth_state(1)  # Open
    #     time.sleep(0.2)
    #     puppet._set_mouth_state(0)  # Close
    #     time.sleep(0.1)

    print("Recording servo states...")
    # puppet.record_state("standing_position", connect_delay=0.5)  # You can adjust the delay as needed

    # Load and set a state
    print("Loading and setting saved state...")
    puppet.load_and_set_state("standing_position", connect_delay=0.5)

    puppet.cleanup()
