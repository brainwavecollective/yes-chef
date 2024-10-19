import serial
import time
import struct

class ArmControl:
    def __init__(self):
        self.position = "neutral"
        try:
            self.ser = serial.Serial('/dev/serial0', 115200, timeout=1)
            print("Serial connection established successfully.")
        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")
            self.ser = None

    def move_servo(self, servo_id, angle):
        if self.ser is None:
            return "Serial connection not available"
        
        # ST series servo command format
        header = 0x55
        cmd = 0x03  # Write servo position command
        params = struct.pack('<BHBH', servo_id, angle, 0, 1000)  # time = 1000ms
        length = len(params) + 2
        checksum = (sum(params) + cmd + length) & 0xFF
        command = struct.pack('<3B', header, header, length) + bytes([cmd]) + params + bytes([checksum])
        
        self.ser.write(command)
        time.sleep(0.1)
        return f"Command sent to move servo {servo_id} to angle {angle}"

    def move(self, direction):
        valid_directions = {"up": (1, 90), "down": (1, 0), "left": (2, 0), "right": (2, 180)}
        if direction.lower() in valid_directions:
            self.position = direction.lower()
            servo_id, angle = valid_directions[direction.lower()]
            result = self.move_servo(servo_id, angle)
            return f"Arm moved to {self.position} position. {result}"
        else:
            return "Invalid direction"

    def get_status(self):
        return f"Current arm position: {self.position}"

    def close(self):
        if self.ser:
            self.ser.close()
            print("Serial connection closed.")

    def read_feedback(self):
        if self.ser is None:
            return "Serial connection not available"
        
        # ST series servo read position command
        header = 0x55
        cmd = 0x15  # Read servo position command
        servo_id = 1  # Assuming we're reading from servo 1
        params = struct.pack('<B', servo_id)
        length = len(params) + 2
        checksum = (sum(params) + cmd + length) & 0xFF
        command = struct.pack('<3B', header, header, length) + bytes([cmd]) + params + bytes([checksum])
        
        self.ser.write(command)
        time.sleep(0.1)
        
        if self.ser.in_waiting:
            response = self.ser.read(self.ser.in_waiting)
            if len(response) >= 8 and response[0] == 0x55 and response[1] == 0x55:
                position = struct.unpack('<H', response[5:7])[0]
                return f"Servo position: {position}"
            else:
                return f"Received unexpected response: {response.hex()}"
        return "No feedback received"

    def send_raw_command(self, command):
        if self.ser is None:
            return "Serial connection not available"
        self.ser.write(command)
        time.sleep(0.1)
        return f"Raw command sent: {command.hex()}"

if __name__ == "__main__":
    print("Starting ArmControl diagnostic tests...")
    arm = ArmControl()

    if arm.ser is None:
        print("Failed to establish serial connection. Exiting test.")
    else:
        print("\nTest 1: Moving servo 1 to various positions")
        for angle in [0, 45, 90, 135, 180]:
            print(f"Moving to {angle} degrees...")
            result = arm.move_servo(1, angle)
            print(result)
            time.sleep(1)
            feedback = arm.read_feedback()
            print(f"Feedback: {feedback}")
            time.sleep(1)

        print("\nTest 2: Testing different move commands")
        for direction in ["up", "down", "left", "right"]:
            print(f"Moving {direction}...")
            result = arm.move(direction)
            print(result)
            time.sleep(1)
            feedback = arm.read_feedback()
            print(f"Feedback: {feedback}")
            time.sleep(1)

        print("\nTest 3: Sending raw commands")
        # Example raw command to move servo 1 to position 512 (middle)
        raw_command = bytes([0x55, 0x55, 0x08, 0x03, 0x01, 0x00, 0x02, 0x00, 0x00, 0x0E])
        print(arm.send_raw_command(raw_command))
        time.sleep(1)
        feedback = arm.read_feedback()
        print(f"Feedback after raw command: {feedback}")

        print("\nTest 4: Rapid movement test")
        for _ in range(5):
            arm.move_servo(1, 0)
            time.sleep(0.5)
            arm.move_servo(1, 180)
            time.sleep(0.5)

        print("\nTest 5: Continuous feedback reading")
        print("Reading feedback for 5 seconds...")
        start_time = time.time()
        while time.time() - start_time < 5:
            feedback = arm.read_feedback()
            print(f"Continuous feedback: {feedback}")
            time.sleep(0.5)

        print("\nTest completed. Closing connection...")
        arm.close()

    print("Diagnostic tests finished.")
