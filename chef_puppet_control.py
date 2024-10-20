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
        self.mouth_open_position = 1800
        self.mouth_closed_position = 1200

        self.motors_bus = FeetechMotorsBus(
            port=self.port,
            motors={self.motor_name: (self.motor_index, self.motor_model)},
        )

        self.closed_position = self.mouth_closed_position
        self.open_positions = [self.mouth_open_position]  # Various open positions

        # Easily adjustable parameters for mouth movement
        self.silence_threshold = 0.1
        self.vowel_threshold = 0.35
        self.segment_duration = 0.02  # 20ms segments
        self.mouth_update_delay = 0.02  # 10ms delay between mouth updates
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
                self._set_mouth_state(0.0)  # Closed position (1100)
                time.sleep(self.mouth_update_delay)
            elif segment_amplitude > self.vowel_threshold:
                self._set_mouth_state(1.0)  # Fully open position (2200)
                time.sleep(self.mouth_update_delay * 5)
            else:
                openness = (segment_amplitude - self.silence_threshold) / (self.vowel_threshold - self.silence_threshold)
                self._set_mouth_state(openness)
                time.sleep(self.mouth_update_delay)
            
            print(f"Segment {i+1}/{num_segments}, Amplitude: {segment_amplitude:.4f}, Mouth openness: {self._get_mouth_state():.2f}")

        # Ensure the mouth is closed after processing all segments
        self._set_mouth_state(0.0)  # Closed position (1100)

    def _set_mouth_state(self, openness):
        """Set the mouth state with a value between 0.0 (closed) and 1.0 (open)."""
        openness = max(0.0, min(1.0, openness))  # Ensure openness is between 0.0 and 1.0
        position = int(self.mouth_closed_position + (self.mouth_open_position - self.mouth_closed_position) * openness)
        position = max(self.mouth_closed_position, min(self.mouth_open_position, position))
        try:
            self.motors_bus.write("Goal_Position", position)
            self.current_mouth_state = openness
        except Exception as e:
            print(f"Error setting mouth state: {e}")

    def _get_mouth_state(self):
        """Get the current mouth state as a value between 0.0 (closed) and 1.0 (open)."""
        return self.current_mouth_state

    def stop_mouth_movement(self):
        self._set_mouth_state(0.2)  # Ensure the mouth is closed

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

    def load_and_set_state(self, name, movement_duration=0.4):
        """
        Load a named state from the YAML file and set servo positions with a smooth ramp.
        """
        all_positions = self.load_positions()
        if name not in all_positions:
            print(f"No state named '{name}' found in positions.yaml")
            return

        target_positions = all_positions[name]
        current_positions = {}
        temp_buses = {}

        # Connect to all servos and get their current positions
        for servo_name, (servo_index, servo_model) in self.all_servos.items():
            if servo_name not in target_positions:
                continue

            try:
                temp_bus = FeetechMotorsBus(
                    port=self.port,
                    motors={servo_name: (servo_index, servo_model)},
                )
                temp_bus.connect()
                temp_bus.set_bus_baudrate(self.baudrate)
                
                current_position = temp_bus.read("Present_Position")
                if isinstance(current_position, np.ndarray):
                    current_position = int(current_position.item())
                current_positions[servo_name] = current_position
                temp_buses[servo_name] = temp_bus

            except Exception as e:
                print(f"Error connecting to {servo_name}: {str(e)}")

        # Calculate position changes
        position_changes = {
            servo: target_positions[servo] - current_positions[servo]
            for servo in current_positions
        }

        # Perform smooth ramp movement
        steps = 100  # Number of steps for the ramp
        step_duration = movement_duration / steps

        for step in range(1, steps + 1):
            for servo_name, change in position_changes.items():
                new_position = int(current_positions[servo_name] + (change * step / steps))
                try:
                    temp_buses[servo_name].write("Goal_Position", new_position)
                except Exception as e:
                    print(f"Error setting position for {servo_name}: {str(e)}")
            
            time.sleep(step_duration)

        # Disconnect all temporary buses
        for temp_bus in temp_buses.values():
            temp_bus.disconnect()

        print(f"Finished setting positions for state '{name}' with smooth ramp")

    def cleanup(self):
        puppet.load_and_set_state("default_position")
        self.motors_bus.disconnect()
        print("ChefPuppetControl cleanup completed")

    def move_servo(self, motor_id, position=None, increment=None, movement_duration=0.4):
        """
        Move a specific servo to a given position or by a given increment.
        
        :param motor_id: The ID of the motor to move
        :param position: The target position (if provided)
        :param increment: The increment to move by (if position is not provided)
        :param movement_duration: Duration of the movement in seconds
        """
        servo_name = next((name for name, (index, _) in self.all_servos.items() if index == motor_id), None)
        
        if not servo_name:
            print(f"No servo found with Motor ID: {motor_id}")
            return

        try:
            temp_bus = FeetechMotorsBus(
                port=self.port,
                motors={servo_name: self.all_servos[servo_name]},
            )
            temp_bus.connect()
            temp_bus.set_bus_baudrate(self.baudrate)
            
            current_position = temp_bus.read("Present_Position")
            if isinstance(current_position, np.ndarray):
                current_position = int(current_position.item())

            if position is not None:
                clamped_position = max(1000, min(3000, position))
            elif increment is not None:
                clamped_position = max(1000, min(3000, current_position + increment))
            else:
                print("No position or increment specified")
                temp_bus.disconnect()
                return

            print(f"Moving {servo_name} (Motor ID: {motor_id}) from {current_position} to position {clamped_position}")
            
            # Perform smooth incremental movement
            steps = 20
            step_duration = movement_duration / steps
            position_change = clamped_position - current_position

            for step in range(1, steps + 1):
                intermediate_position = int(current_position + (position_change * step / steps))
                temp_bus.write("Goal_Position", intermediate_position)
                time.sleep(step_duration)

            time.sleep(0.1)  # Short pause at the end of movement
            
            temp_bus.disconnect()
            print(f"Finished moving {servo_name}")
        except Exception as e:
            print(f"Error moving {servo_name}: {str(e)}")

if __name__ == "__main__":
    puppet = ChefPuppetControl()
    import argparse

    parser = argparse.ArgumentParser(description="Control Chef Puppet")
    parser.add_argument("--motor_id", type=int, help="Motor ID to move")
    parser.add_argument("--position", type=int, help="Position to move the motor to")
    parser.add_argument("--increment", type=int, help="Increment to move the motor by")
    parser.add_argument("--state", type=str, help="State to load and set")
    args = parser.parse_args()

    if args.motor_id is not None:
        puppet.move_servo(args.motor_id, position=args.position, increment=args.increment)
    elif args.state is not None:
        puppet.load_and_set_state(args.state)
    else:
        print("No specific motor movement or state requested. Continuing with default behavior...")

    # print("Testing mouth movement...")
    # for _ in range(3):
    #     puppet._set_mouth_state(1)  # Open
    #     time.sleep(0.2)
    #     puppet._set_mouth_state(0)  # Close
    #     time.sleep(0.1)

    # print("Recording servo states...")
    # puppet.record_state("default_position", connect_delay=0.5)  # You can adjust the delay as needed

    # Load and set a state
    print("Loading and setting saved state...")
    
    # puppet.load_and_set_state("default_position")
    # time.sleep(5)
    # puppet._set_mouth_state(0.4)
    # time.sleep(0.3)
    # puppet._set_mouth_state(0.8)
    # time.sleep(0.3)
    # puppet._set_mouth_state(0.4)
    # time.sleep(0.3)
    # puppet._set_mouth_state(0.2)
    # puppet.load_and_set_state("default_position", movement_duration=0.4)

    puppet.cleanup()
