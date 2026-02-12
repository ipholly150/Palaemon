import serial
import time
import threading

# --- CONFIG ON PI ---
# Run 'ls /dev/tty*' on the Pi to confirm if this is USB0 or ACM0
ESP32_PORT = '/dev/ttyUSB0' 
BT_PORT = '/dev/rfcomm0' # This is the virtual Bluetooth serial port
BAUD = 115200

# Setup ESP32 Serial
try:
    ser_esp = serial.Serial(ESP32_PORT, BAUD, timeout=1)
    print(f"Success: Connected to ESP32 at {ESP32_PORT}")
except:
    print("Error: Could not find ESP32. Try /dev/ttyACM0?")
    exit()

print("Waiting for Bluetooth connection... (Run 'sudo rfcomm watch hci0' in another terminal)")

# Main loop to bridge Bluetooth to ESP32
while True:
    try:
        with serial.Serial(BT_PORT, BAUD, timeout=1) as ser_bt:
            print("Laptop Connected!")
            while True:
                if ser_bt.in_waiting > 0:
                    data = ser_bt.read().decode('utf-8').lower()
                    print(f"Received from Laptop: {data}")
                    
                    # Forward the command to the ESP32
                    # (You can add your PWM logic here later)
                    ser_esp.write(data.encode('utf-8'))
    except Exception as e:
        time.sleep(1) # Wait for Bluetooth to be ready
