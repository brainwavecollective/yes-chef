# yes-chef



## Raspberry Pi / Servo Control Board Integration 

The board communicates with the Raspberry Pi using the UART interface, leveraging the Raspberry Pi’s GPIO pins for serial communication. 

### Raspberry Pi Configuration

#### Enable UART 
UART can be enabled by configuring the Pi’s /boot/config.txt file or using the raspi-config tool: `sudo raspi-config`  
Navigate to Interfacing Options → Serial → Enable UART.

#### Install SO-ARM100 Library 
```
git clone https://github.com/TheRobotStudio/SO-ARM100
cd SO-ARM100
make install
```

### Raspberry Pi Control Code 
Once UART is enabled and libraries installed, you can write code to control the servos via UART.
Python Code Example (using UART): You can use the pyserial library to send commands to the control board via UART:
In this example:
`/dev/serial0` is the UART device on the Raspberry Pi.
The move_servo function sends a command to a specified servo (by ID) to move it to a certain angle.
Note: The exact command format (byte sequence) depends on the protocol defined by the control board for serial bus servos.
```
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
```

### Receiving UART Feedback (Optional)
The Wonrabai board supports receiving feedback from servos (such as angle, voltage, load, etc.). You can read data from the UART port using ser.read() to get this feedback and process it in your code, enabling more complex interactions (e.g., closed-loop control).  



