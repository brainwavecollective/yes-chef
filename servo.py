import serial
import time

# Initialize UART serial communication with the control board
ser = serial.Serial('/dev/serial0', 115200, timeout=1)

# Send a command to move a servo
def move_servo(servo_id, angle):
    command = bytearray([servo_id, angle])
    ser.write(command)
    time.sleep(0.1)

# Example: Move servo 1 to 90 degrees
move_servo(1, 90)