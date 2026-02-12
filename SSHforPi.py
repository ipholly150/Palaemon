import serial
import sys
import tty
import termios
import threading
import time

# --- CONFIG ---
ESP32_PORT = '/dev/ttyUSB0' # or /dev/ttyACM0
BAUD = 115200
current_pwm = 1500
step_size = 25
running = True

# Setup Serial to ESP32
try:
    ser = serial.Serial(ESP32_PORT, BAUD, timeout=1)
    print(f"Connected to ESP32 on {ESP32_PORT}")
except:
    print("ESP32 not found.")
    sys.exit()

def getch():
    """Reads a single character from the terminal without needing 'Enter'."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def heartbeat():
    global running
    while running:
        ser.write(f"{current_pwm}\n".encode())
        time.sleep(0.03) # 30Hz

# Start Heartbeat
threading.Thread(target=heartbeat, daemon=True).start()

print("CONTROLS (via SSH): W = Up, S = Down, Space = STOP, Q = Quit")

try:
    while True:
        char = getch().lower()
        if char == 'w':
            current_pwm = min(2000, current_pwm + step_size)
            print(f"\rPWM: {current_pwm} (UP)   ", end="")
        elif char == 's':
            current_pwm = max(1000, current_pwm - step_size)
            print(f"\rPWM: {current_pwm} (DOWN) ", end="")
        elif char == ' ':
            current_pwm = 1500
            print(f"\r!!! STOP !!!          ", end="")
        elif char == 'q':
            running = False
            break
finally:
    ser.write(b"1500\n")
    ser.close()
    print("\nSafe Shutdown.")
