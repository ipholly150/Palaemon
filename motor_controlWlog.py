import serial
import time
import csv
import threading
from pynput import keyboard

# --- CONFIGURATION ---
COM_PORT = 'COM8'
BAUD_RATE = 115200

RC_PLANE_MODE = False

if RC_PLANE_MODE:
    min_pwm = 1000
    max_pwm = 2000
    stop_pwm = 1000
    current_pwm = stop_pwm
else:
    min_pwm = 1100
    max_pwm = 1900
    stop_pwm = 1500
    current_pwm = stop_pwm

step_size = 25
LOG_PATH = "pwm_log.csv"

HEARTBEAT_HZ = 30  # send current PWM continuously at 30 Hz

# --- SETUP SERIAL CONNECTION ---
try:
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Wait for ESP32 reset/boot
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    print(f"Connected to {COM_PORT}")
except Exception as e:
    print(f"Error connecting to {COM_PORT}: {e}")
    raise SystemExit(1)

t0 = time.perf_counter()  # high-resolution monotonic clock

# Open CSV log
log_f = open(LOG_PATH, "w", newline="")
writer = csv.writer(log_f)
writer.writerow(["t_s", "pwm", "event"])  # header

# Thread safety (keyboard thread + heartbeat thread)
lock = threading.Lock()
running = True

def log_event(pwm, event):
    """Log a row with timestamp and PWM."""
    t_s = time.perf_counter() - t0
    writer.writerow([f"{t_s:.6f}", int(pwm), event])
    log_f.flush()

def clamp_pwm(pwm):
    return max(min_pwm, min(max_pwm, pwm))

def send_raw_pwm(pwm):
    """Send PWM without logging (used by heartbeat)."""
    pwm = clamp_pwm(pwm)
    ser.write(f"{pwm}\n".encode("utf-8"))
    return pwm

def send_command(pwm, event="CMD"):
    """Send PWM and log it with a timestamp (used on key events)."""
    pwm = send_raw_pwm(pwm)
    log_event(pwm, event)
    print(f"[{event}] t={time.perf_counter() - t0:.3f}s  pwm={pwm}")

def heartbeat_loop():
    """Continuously resend the current PWM so ESP32 failsafe won't trigger."""
    global running
    period = 1.0 / HEARTBEAT_HZ
    while running:
        with lock:
            pwm = current_pwm
        try:
            send_raw_pwm(pwm)
        except Exception:
            # If serial dies, exit heartbeat; main finally will attempt stop/close.
            running = False
            break
        time.sleep(period)

# Send initial stop so the log has a starting point
send_command(current_pwm, event="START_STOP")

# Start heartbeat thread
hb = threading.Thread(target=heartbeat_loop, daemon=True)
hb.start()

def on_press(key):
    global current_pwm, running

    try:
        if key == keyboard.Key.up:
            with lock:
                current_pwm = clamp_pwm(current_pwm + step_size)
                pwm = current_pwm
            send_command(pwm, event="UP")

        elif key == keyboard.Key.down:
            with lock:
                current_pwm = clamp_pwm(current_pwm - step_size)
                pwm = current_pwm
            send_command(pwm, event="DOWN")

        elif key == keyboard.Key.space:
            with lock:
                current_pwm = stop_pwm
                pwm = current_pwm
            print("!!! EMERGENCY STOP !!!")
            send_command(pwm, event="STOP")

        elif key == keyboard.Key.esc:
            print("Exiting...")
            running = False
            return False

    except Exception as e:
        print(f"Error: {e}")

print("\n--- MOTOR CONTROL READY (HEARTBEAT ENABLED) ---")
print("UP Arrow   : Speed Up")
print("DOWN Arrow : Slow Down")
print("SPACEBAR   : EMERGENCY STOP")
print("ESC        : Quit")
print(f"Logging to: {LOG_PATH}")
print(f"Heartbeat : {HEARTBEAT_HZ} Hz")

try:
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
finally:
    # Stop heartbeat
    running = False

    # Always try to stop on exit (and log it)
    try:
        with lock:
            current_pwm = stop_pwm
        send_raw_pwm(stop_pwm)
        log_event(stop_pwm, "EXIT_STOP")
    except Exception:
        pass

    try:
        ser.close()
    except Exception:
        pass

    try:
        log_f.close()
    except Exception:
        pass

    print("Serial closed. Log saved.")
