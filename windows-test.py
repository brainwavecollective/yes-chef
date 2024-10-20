import serial

# Set the correct COM port
serial_port = 'COM6'
baud_rate = 115200

# Open the serial connection
ser = serial.Serial(serial_port, baudrate=baud_rate, timeout=1)

# Function to move the servo
def move_servo(servo_id, position):
    command = bytearray([0xFF, 0xFF, servo_id, 0x07, 0x03, 0x1E, position & 0xFF, (position >> 8) & 0xFF])
    checksum = ~(servo_id + 0x07 + 0x03 + 0x1E + (position & 0xFF) + ((position >> 8) & 0xFF)) & 0xFF
    command.append(checksum)
    ser.write(command)
    print(f"Moved servo {servo_id} to position {position}")
    
    # Attempt to read feedback
    if ser.in_waiting > 0:
        feedback = ser.read(ser.in_waiting)
        print(f"Feedback received: {feedback}")


# Move servo with ID 1 to position 512 (approximately 90 degrees)
move_servo(1, 512)

# Close the serial connection
ser.close()
