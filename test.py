import serial

# Open serial connection
serial_port = '/dev/tty.usbserial-XXXX'  # Replace with your actual port
ser = serial.Serial(serial_port, baudrate=115200, timeout=1)

# Function to move the servo to a specific position
def move_servo(servo_id, position):
    # Break down the position into low and high bytes
    position_low = position & 0xFF
    position_high = (position >> 8) & 0xFF
    
    # Create the command packet
    command = bytearray([0xFF, 0xFF, servo_id, 0x07, 0x03, 0x1E, position_low, position_high])
    
    # Calculate the checksum (inverted sum of the relevant bytes)
    checksum = ~(servo_id + 0x07 + 0x03 + 0x1E + position_low + position_high) & 0xFF
    command.append(checksum)
    
    # Send the command to the servo
    ser.write(command)
    print(f"Sent command: {command}")

# Move servo with ID 1 to position 512 (90 degrees)
move_servo(1, 512)

# Close the serial connection
ser.close()
