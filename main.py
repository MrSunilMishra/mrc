import network
import socket
from machine import Pin, PWM, UART, Timer
import time
import sys

# ------------------------------
# ====== PIN CONFIG ============
# ------------------------------
# Motor direction pins
LEFT_FWD  = Pin(25, Pin.OUT)
LEFT_BKD  = Pin(26, Pin.OUT)
RIGHT_FWD = Pin(27, Pin.OUT)
RIGHT_BKD = Pin(14, Pin.OUT)

# PWM enable pins for speed control
PWM_LEFT_PIN  = 12   # ENA
PWM_RIGHT_PIN = 13   # ENB

pwm_left  = PWM(Pin(PWM_LEFT_PIN), freq=1000)
pwm_right = PWM(Pin(PWM_RIGHT_PIN), freq=1000)

# default speed percent
current_speed_percent = 50

def set_pwm_from_percent(pct):
    # pct: 0..100
    if pct < 0: pct = 0
    if pct > 100: pct = 100
    duty = int((pct / 100.0) * 1023)  # ESP32 PWM duty range 0..1023
    pwm_left.duty(duty)
    pwm_right.duty(duty)

set_pwm_from_percent(current_speed_percent)

# RF receiver input pin (data line)
RF_PIN = Pin(4, Pin.IN)

# Eye sensor (eye-closed detection) input
EYE_PIN = Pin(34, Pin.IN) # 1=open/OK, 0=closed

# Buzzer and light
BUZZER = Pin(32, Pin.OUT)
HEADLIGHT = Pin(33, Pin.OUT)

# Bluetooth UART (HC-05) - using UART(2) on ESP32
# HC-05 TX -> ESP32 RX (GPIO16)
# HC-05 RX -> ESP32 TX (GPIO17)
uart = UART(2, baudrate=9600, rx=16, tx=17, timeout=10)

# ------------------------------
# ====== WIFI AP & Web UI ======
# ------------------------------
ap = network.WLAN(network.AP_IF)
ap.config(essid="SmartCar_AP", password="12345678")
ap.active(True)
print("AP active, config:", ap.ifconfig())
print("Open http://192.168.4.1 to control.")

html = """<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/html">
<head>
<title>ESP32 Smart Car</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { text-align: center; font-family: Arial, sans-serif; background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); color: #fff; margin-top: 20px; }
h2 { background: #111; color: #00ffcc; padding: 10px; border-radius: 10px; display: inline-block; }
form { margin-top: 20px; }
button { width: 90px; height: 40px; margin: 6px; font-size: 16px; border: none; border-radius: 8px; cursor: pointer; color: white; background: #333; transition: background 0.3s, transform 0.1s; }
button:hover { background: #00ccff; transform: scale(1.05); }
button:active { background: #0077aa; transform: scale(0.95); }
.speed-buttons button { width: 45px; height: 35px; margin: 4px; font-size: 14px; }
.footer { margin-top: 20px; font-size: 13px; color: #aaa; }
</style>
</head>
<body>
  <h2>🚗 Subhadip & Sunil Smart Car</h2>
  <form>
    <div>
      <button name="cmd" value="F">Forward</button>
      <button name="cmd" value="B">Backward</button><br>
      <button name="cmd" value="L">Left</button>
      <button name="cmd" value="R">Right</button><br>
      <button name="cmd" value="G">F+L</button>
      <button name="cmd" value="I">F+R</button>
      <button name="cmd" value="H">B+L</button>
      <button name="cmd" value="J">B+R</button><br>
      <button name="cmd" value="S">Stop</button><br>
      <button name="cmd" value="V">Horn</button>
      <button name="cmd" value="LIGHT">Light</button><br>
    </div>
    <div class="speed-buttons">
     <p>Speed:</p>
      <button name="cmd" value="0">0</button>
      <button name="cmd" value="1">10</button>
      <button name="cmd" value="2">20</button>
      <button name="cmd" value="3">30</button>
      <button name="cmd" value="4">40</button>
      <button name="cmd" value="5">50</button>
      <button name="cmd" value="6">60</button>
      <button name="cmd" value="7">70</button>
      <button name="cmd" value="8">80</button>
      <button name="cmd" value="9">90</button>
      <button name="cmd" value="q">100</button>
   </div><br>
    <button name="cmd" value="D" style="background:#ff3333;">Stop All</button>
  </form>
  <div class="footer">© Subhadip & Sunil | ESP32 Smart Car Project</div>
</body>
</html>
"""

# ------------------------------
# ====== TIMERS & STATE ========
# ------------------------------
last_rf_time = time.time()
last_eye_time = time.time()
auto_stop_time = 3  # seconds
current_state = "STOP"

# ------------------------------
# ====== UTILITY FUNCTIONS =====
# ------------------------------
def stop_all_motors():
    LEFT_FWD.off(); LEFT_BKD.off()
    RIGHT_FWD.off(); RIGHT_BKD.off()
    global current_state
    current_state = "STOP"

def forward():
    LEFT_FWD.on(); LEFT_BKD.off()
    RIGHT_FWD.on(); RIGHT_BKD.off()
    global current_state
    current_state = "FORWARD"

def backward():
    LEFT_FWD.off(); LEFT_BKD.on()
    RIGHT_FWD.off(); RIGHT_BKD.on()
    global current_state
    current_state = "BACKWARD"

def left_turn():
    LEFT_FWD.off(); LEFT_BKD.on()
    RIGHT_FWD.on(); RIGHT_BKD.off()
    global current_state
    current_state = "LEFT"

def right_turn():
    LEFT_FWD.on(); LEFT_BKD.off()
    RIGHT_FWD.off(); RIGHT_BKD.on()
    global current_state
    current_state = "RIGHT"

def forward_left():
    LEFT_FWD.on(); LEFT_BKD.off()
    RIGHT_FWD.on(); RIGHT_BKD.off()
    global current_state
    current_state = "FORWARD_LEFT"

def forward_right():
    LEFT_FWD.on(); LEFT_BKD.off()
    RIGHT_FWD.on(); RIGHT_BKD.off()
    global current_state
    current_state = "FORWARD_RIGHT"

def back_left():
    LEFT_FWD.off(); LEFT_BKD.on()
    RIGHT_FWD.off(); RIGHT_BKD.on()
    global current_state
    current_state = "BACK_LEFT"

def back_right():
    LEFT_FWD.off(); LEFT_BKD.on()
    RIGHT_FWD.off(); RIGHT_BKD.on()
    global current_state
    current_state = "BACK_RIGHT"

def horn_beep():
    BUZZER.on()
    time.sleep(0.2)
    BUZZER.off()

def toggle_light():
    HEADLIGHT.value(not HEADLIGHT.value())

def emergency_stop_all():
    stop_all_motors()
    set_pwm_from_percent(0)
    print("EMERGENCY STOP: All stopped and PWM zeroed")

def map_speed_char_to_percent(ch):
    if ch == 'q': return 100
    if ch.isdigit(): return int(ch) * 10
    return None

def handle_command(cmd):
    global current_speed_percent
    cmd = cmd.strip()
    if not cmd: return
    if cmd == 'F': forward()
    elif cmd == 'B': backward()
    elif cmd == 'L': left_turn()
    elif cmd == 'R': right_turn()
    elif cmd == 'G': forward_left()
    elif cmd == 'I': forward_right()
    elif cmd == 'H': back_left()
    elif cmd == 'J': back_right()
    elif cmd == 'S': stop_all_motors()
    elif cmd == 'V': horn_beep()
    elif cmd == 'v': BUZZER.off()
    elif cmd == 'LIGHT': toggle_light()
    elif cmd == 'D': emergency_stop_all()
    else:
        pct = map_speed_char_to_percent(cmd)
        if pct is not None:
            current_speed_percent = pct
            set_pwm_from_percent(current_speed_percent)
            print("Speed set to", current_speed_percent, "%")
        else:
            print("Unknown command:", cmd)
    print("State:", current_state, "Speed:", current_speed_percent)

# ------------------------------
# ====== SAFETY CHECK TIMER ====
# ------------------------------
def safety_timer_callback(t):
    global last_rf_time, last_eye_time
    now = time.time()
    try:
        if RF_PIN.value() == 1: last_rf_time = now
    except: pass
    
    try:
        if EYE_PIN.value() == 1: last_eye_time = now
    except: pass

    if now - last_rf_time > auto_stop_time:
        stop_all_motors()
        BUZZER.on(); print("RF signal lost"); time.sleep(0.2); BUZZER.off()
        last_rf_time = now

    if now - last_eye_time > auto_stop_time:
        stop_all_motors()
        BUZZER.on(); print("Eye sensor closed"); time.sleep(0.2); BUZZER.off()
        last_eye_time = now

safety_timer = Timer(-1)
safety_timer.init(period=500, mode=Timer.PERIODIC, callback=safety_timer_callback)

# ------------------------------
# ====== WEB SERVER & MAIN LOOP
# ------------------------------
def start_web_server_nonblocking():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 80))
    s.listen(1)
    s.settimeout(0.1) # Non-blocking timeout
    print("Non-blocking web server ready")
    return s

web_sock = start_web_server_nonblocking()

print("Main loop starting...")
try:
    while True:
        # 1. Bluetooth Check
        if uart.any():
            try:
                data = uart.read(1)
                if data:
                    ch = data.decode('utf-8').strip()
                    if ch: handle_command(ch)
            except Exception as e:
                print("UART error:", e)

        # 2. Web Server Check
        try:
            conn, addr = web_sock.accept()
            request = conn.recv(1024)
            if request:
                req_str = str(request)
                if "cmd=" in req_str:
                    try:
                        cmd = req_str.split("cmd=")[1].split(" ")[0]
                        cmd = cmd.split("+")[0] # clean URL encoding
                        handle_command(cmd)
                    except: pass
            conn.send("HTTP/1.1 200 OK\nContent-Type: text/html\nConnection: close\n\n")
            conn.sendall(html)
            conn.close()
        except OSError:
            pass # No connection, continue loop

        # 3. Sensor Instant Check
        if RF_PIN.value() == 1: last_rf_time = time.time()
        if EYE_PIN.value() == 1: last_eye_time = time.time()
        
        time.sleep(0.01)

except KeyboardInterrupt:
    stop_all_motors()
    pwm_left.deinit()
    pwm_right.deinit()
    web_sock.close()
    sys.exit()