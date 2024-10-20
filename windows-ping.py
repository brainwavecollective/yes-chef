import serial
import time
import struct

def debug_print(message):
    print(f"[DEBUG] {time.strftime('%H:%M:%S')} - {message}")

def calculate_checksum(data):
    return 255 - (sum(data) % 256)

def send_command(ser, cmd):
    ser.write(cmd)
    debug_print(f"Sent: {cmd.hex()}")
    time.sleep(0.1)
    if ser.in_waiting:
        response = ser.read(ser.in_waiting)
        debug_print(f"Received: {response.hex()}")
        return response
    debug_print("No response")
    return None

def test_ping(ser):
    cmd = bytes([0x55, 0x55, 0xFE, 0x02, 0x01, 0x00])
    return send_command(ser, cmd)

def test_read_voltage(ser):
    cmd = bytes([0x55, 0x55, 0xFE, 0x02, 0x0F, 0xF3])
    return send_command(ser, cmd)

def test_read_servo_position(ser, servo_id):
    cmd = bytes([0x55, 0x55, servo_id, 0x03, 0x1C, 0x00])
    cmd += bytes([calculate_checksum(cmd[2:])])
    return send_command(ser, cmd)

def test_move_servo(ser, servo_id, position, time_ms):
    cmd = struct.pack('<BBBBBHHB', 0x55, 0x55, servo_id, 0x07, 0x01, position, time_ms, 0)
    cmd = cmd[:-1] + bytes([calculate_checksum(cmd[2:-1])])
    return send_command(ser, cmd)

def test_connection(port, baud_rate, timeout=0.5):
    debug_print(f"Testing connection on {port} at {baud_rate} baud")
    try:
        with serial.Serial(port, baudrate=baud_rate, timeout=timeout) as ser:
            debug_print("Port opened successfully")

            # Test general ping
            debug_print("Testing ping...")
            test_ping(ser)

            # Test voltage reading
            debug_print("Testing voltage reading...")
            test_read_voltage(ser)

            # Test reading position for servos 0-5
            for servo_id in range(6):
                debug_print(f"Testing read position for servo {servo_id}...")
                test_read_servo_position(ser, servo_id)

            # Test moving servo 1
            debug_print("Testing move command for servo 1...")
            test_move_servo(ser, 1, 500, 1000)  # Move to middle position
            time.sleep(1)
            test_read_servo_position(ser, 1)

        debug_print("Connection test completed")
    except serial.SerialException as e:
        debug_print(f"Error: {e}")

def main():
    port = 'COM6'  # Change this to your actual port
    baud_rates = [9600, 19200, 38400, 57600, 115200]

    for baud_rate in baud_rates:
        test_connection(port, baud_rate)
        time.sleep(1)

    debug_print("All tests completed")

if __name__ == "__main__":
    main() 