#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ML01 LED Controller for Raspberry Pico 2W with TPIC6B595 + Web Interface
16 LEDs controller with 3 modes: OFF, ON1 (all on), ON2 (chase effect)
Created for MicroPython with microdot web server
Use with microdot.py and index_v08.html
2025.11.08 VERSION 01.10 - Modification of def play_hourly_animation
2025.11.08 VERSION 01.09 - Adds pico temperature display
2025.11.08 VERSION 01.08 - Animation added to the start of the chase function and every hour + Fix bug with restart function
2025.11.02 VERSION 01.07 - Simplified code + Fixed logs display with pagination + Removed memory stats from HTML
2025.10.31 VERSION 01.06 - Fix memory allocation error
2025.10.30 VERSION 01.05 - Manual restart (Button 2 long press + API) replace autofunction + Chunked HTML loading + Add purge memory
2025.10.26 VERSION 01.04 - Modification of chase mode for a display synchronized with minutes of NTP server
2025.10.25 VERSION 01.03 - Inserting logs.html directly into index.html + correction of the start date + Add memory status
2025.10.21 VERSION 01.02 - Buttons inactive without WiFi Fix + Add NTP synchronization + Replace UPDATE button with LOGS button + Create logs page + Weekly automatic restart + Change LONG_PRESS_TIME + Freeing up memory to avoid logs saturation
2025.10.05 VERSION 01.01 - WiFi Reconnection Fix
2025.07.19 VERSION 01.00 - Initial version
"""

import machine
import time
import utime
from machine import Pin
import gc
import network
import json
import _thread
from microdot import Microdot, Response
import ubinascii

# =============================================================================
# CONFIGURATION
# =============================================================================

# WiFi
WIFI_SSID = "wifi5g841"
WIFI_PASSWORD = "TimeconnectGB179"
WIFI_CHECK_INTERVAL = 600
WIFI_RECONNECT_ATTEMPTS = 2
WIFI_RECONNECT_DELAY = 20

# NTP
NTP_TIMEZONE_OFFSET = 1  # UTC+1

# Server
WEB_PORT = 80
DEVICE_NAME = "ML01-LED-Controller"

# GPIO
SER_DATA_PIN = 7
REGISTER_CLOCK_PIN = 8
SHIFT_CLOCK_PIN = 9
BUTTON1_PIN = 4
BUTTON2_PIN = 5

# Timing
CHASE_SPEED = 3.75  # Minutes per LED (60/16)
CHASE_ANIMATION_SPEED = 0.05  # LED animation speed in seconds
CHASE_BLINK_SPEED = 1  # Blink speed for hourly animation finale in seconds
DEBOUNCE_TIME = 50
LONG_PRESS_TIME = 1500

# Authentication
AUTH_ENABLED = True
AUTH_USERNAME = "admin"
AUTH_PASSWORD = "gregTest"
AUTH_TOKEN = None

# Security
IP_WHITELIST_ENABLED = True
ALLOWED_IPS = [
    "192.168.0.10", "192.168.0.14", "192.168.0.40",
    "192.168.0.72", "192.168.0.73", "192.168.0.122"
]
RATE_LIMIT_ENABLED = True
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 30

# LED notifications
LED_NOTIFICATION_ENABLED = True
NEW_CONNECTION_BLINK_DURATION = 10

# Memory management
MEMORY_CHECK_INTERVAL = 1800  # 30 minutes
MEMORY_WARNING_THRESHOLD = 100000  # 100KB
MAX_LOG_ENTRIES = 1000

# =============================================================================
# GLOBALS
# =============================================================================

# Modes
MODE_OFF = 0
MODE_ON1 = 1
MODE_ON2 = 2

# State
current_mode = MODE_ON1
running = True
chase_position = 0
chase_first_update = False
last_hour_animation = -1  # Track last hour for animation trigger
web_server_running = False
restart_requested = False  # Flag for restart request
restart_request_time = 0   # Time when restart was requested

# Stats
program_start_time = time.time()
mode_on1_start_time = time.time()
total_on1_hours = 0.0

# Monitoring
last_wifi_check = 0
last_memory_check = 0
wifi_reconnecting = False

# Hardware
ser_data = None
reg_clock = None
shift_clock = None
button1 = None
button2 = None
onboard_led = None
temp_sensor = None  # Temperature sensor ADC
wlan = None
app = Microdot()

# Tracking
connected_ips = set()
led_blink_end_time = 0
request_counts = {}

# Logs
log_entries = []

# =============================================================================
# LOGGING
# =============================================================================

def add_log(message, log_type="INFO"):
    """Add log entry"""
    global log_entries
    timestamp = format_datetime(time.time())
    log_entries.append({
        "timestamp": timestamp,
        "type": log_type,
        "message": message
    })
    
    if len(log_entries) > MAX_LOG_ENTRIES:
        log_entries = log_entries[-MAX_LOG_ENTRIES:]
        gc.collect()
    
    if len(log_entries) % 50 == 0:
        gc.collect()
    
    print(f"[{log_type}] {message}")

# =============================================================================
# MEMORY MANAGEMENT
# =============================================================================

def check_memory():
    """Check and log memory status"""
    global last_memory_check
    
    current_time = time.time()
    if current_time - last_memory_check < MEMORY_CHECK_INTERVAL:
        return
    
    last_memory_check = current_time
    gc.collect()
    free = gc.mem_free()
    
    print(f"[MEMORY] Periodic check - Free: {free} bytes ({len(log_entries)} logs)")
    
    if free < MEMORY_WARNING_THRESHOLD:
        print(f"[MEMORY] WARNING: Low memory! Cleaning up...")
        add_log(f"Low memory: {free} bytes - reducing logs", "SYSTEM")
        log_entries[:] = log_entries[-500:]
        gc.collect()
        print(f"[MEMORY] After cleanup: {gc.mem_free()} bytes")

# =============================================================================
# WIFI
# =============================================================================

def connect_wifi():
    """Connect to WiFi"""
    global wlan, onboard_led
    
    print("Connecting to WiFi...")
    
    if wlan is None:
        wlan = network.WLAN(network.STA_IF)
    
    wlan.active(True)
    
    if LED_NOTIFICATION_ENABLED and onboard_led is None:
        onboard_led = Pin("LED", Pin.OUT)
        onboard_led.value(0)
    
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        timeout = 200
        
        while not wlan.isconnected() and timeout > 0:
            if timeout % 20 == 0:
                print(".", end="")
            time.sleep_ms(100)
            timeout -= 1
        
        print()
        
        if wlan.isconnected():
            ip_info = wlan.ifconfig()
            add_log(f"WiFi connected - IP: {ip_info[0]}", "WIFI")
            print(f"IP: {ip_info[0]}")
            
            if LED_NOTIFICATION_ENABLED and onboard_led:
                onboard_led.value(1)
            
            sync_time_ntp()
            return True
        else:
            if not wifi_reconnecting:
                add_log("WiFi connection failed", "ERROR")
            if LED_NOTIFICATION_ENABLED and onboard_led:
                onboard_led.value(0)
            return False
    else:
        if LED_NOTIFICATION_ENABLED and onboard_led:
            onboard_led.value(1)
        sync_time_ntp()
        return True

def check_wifi_connection():
    """Monitor WiFi and reconnect if needed"""
    global wlan, wifi_reconnecting, last_wifi_check
    
    current_time = time.time()
    
    if current_time - last_wifi_check < WIFI_CHECK_INTERVAL:
        return
    
    last_wifi_check = current_time
    
    if wifi_reconnecting:
        return
    
    if wlan is None or not wlan.isconnected():
        add_log("WiFi lost! Reconnecting...", "WIFI")
        print("\n⚠️  WiFi lost! Reconnecting...")
        wifi_reconnecting = True
        
        if LED_NOTIFICATION_ENABLED and onboard_led:
            onboard_led.value(0)
        
        gc.collect()
        
        for attempt in range(WIFI_RECONNECT_ATTEMPTS):
            print(f"Attempt {attempt + 1}/{WIFI_RECONNECT_ATTEMPTS}...")
            
            if connect_wifi():
                add_log("WiFi reconnected!", "WIFI")
                print("✓ Reconnected!")
                wifi_reconnecting = False
                return
            
            if attempt < WIFI_RECONNECT_ATTEMPTS - 1:
                time.sleep(WIFI_RECONNECT_DELAY)
        
        add_log("WiFi reconnection failed", "ERROR")
        print("✗ Reconnection failed")
        wifi_reconnecting = False

def sync_time_ntp():
    """Sync time with NTP"""
    try:
        import ntptime
        add_log("Syncing time with NTP...", "SYSTEM")
        ntptime.settime()
        
        utc_time = time.time()
        local_time = utc_time + (NTP_TIMEZONE_OFFSET * 3600)
        tm = time.localtime(local_time)
        machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))
        
        add_log(f"Time synced: {format_datetime(time.time())}", "SYSTEM")
        print(f"✓ Time synced (UTC+{NTP_TIMEZONE_OFFSET})")
        return True
    except Exception as e:
        add_log(f"NTP sync failed: {str(e)}", "ERROR")
        return False

# =============================================================================
# HARDWARE
# =============================================================================

def init_gpio():
    """Initialize GPIO"""
    global ser_data, reg_clock, shift_clock, button1, button2, temp_sensor
    
    print("Initializing GPIO...")
    ser_data = Pin(SER_DATA_PIN, Pin.OUT)
    reg_clock = Pin(REGISTER_CLOCK_PIN, Pin.OUT)
    shift_clock = Pin(SHIFT_CLOCK_PIN, Pin.OUT)
    button1 = Pin(BUTTON1_PIN, Pin.IN, Pin.PULL_UP)
    button2 = Pin(BUTTON2_PIN, Pin.IN, Pin.PULL_UP)
    temp_sensor = machine.ADC(4)
    
    ser_data.value(0)
    reg_clock.value(0)
    shift_clock.value(0)
    print("GPIO initialized")

def read_pico_temperature():
    """Read Pico internal temperature in Celsius"""
    try:
        if temp_sensor is None:
            return None
        
        # Read ADC value
        adc_value = temp_sensor.read_u16()
        
        # Convert to voltage (3.3V reference)
        voltage = adc_value * 3.3 / 65535
        
        # Convert to temperature (formula from Pico datasheet)
        # T = 27 - (ADC_voltage - 0.706)/0.001721
        temperature = 27 - (voltage - 0.706) / 0.001721
        
        return round(temperature, 1)
    except Exception as e:
        print(f"[ERROR] Temperature read failed: {e}")
        return None

def cleanup_gpio():
    """Cleanup GPIO"""
    shift_out_16bit(0x00, 0x00)
    if ser_data:
        ser_data.init(Pin.IN)
    if reg_clock:
        reg_clock.init(Pin.IN)
    if shift_clock:
        shift_clock.init(Pin.IN)
    if onboard_led:
        onboard_led.value(0)
    print("GPIO cleaned")

def shift_out_16bit(data_low, data_high):
    """Send 16-bit data to shift registers"""
    for i in range(7, -1, -1):
        ser_data.value((data_high >> i) & 1)
        shift_clock.value(1)
        utime.sleep_us(1)
        shift_clock.value(0)
        utime.sleep_us(1)
    
    for i in range(7, -1, -1):
        ser_data.value((data_low >> i) & 1)
        shift_clock.value(1)
        utime.sleep_us(1)
        shift_clock.value(0)
        utime.sleep_us(1)
    
    reg_clock.value(1)
    utime.sleep_us(1)
    reg_clock.value(0)

# =============================================================================
# LED CONTROL
# =============================================================================

def set_mode_off():
    """Turn off all LEDs"""
    shift_out_16bit(0x00, 0x00)

def set_mode_on1():
    """Turn on all LEDs"""
    shift_out_16bit(0xFF, 0xFF)

def play_chase_animation(target_led):
    """
    Play LED chase animation sequence
    - Full cycle: LED 1 to 16
    - Partial cycle: LED 1 to target_led
    target_led: final LED position (0-15)
    """
    print(f"[CHASE] Starting animation to LED {target_led + 1}")
    
    # Cycle 1: Full animation LED 1 to 16
    for i in range(16):
        if i < 8:
            data_low = 1 << i
            data_high = 0x00
        else:
            data_low = 0x00
            data_high = 1 << (i - 8)
        shift_out_16bit(data_low, data_high)
        time.sleep(CHASE_ANIMATION_SPEED)
    
    # Cycle 2: Partial animation LED 1 to target_led
    for i in range(target_led + 1):
        if i < 8:
            data_low = 1 << i
            data_high = 0x00
        else:
            data_low = 0x00
            data_high = 1 << (i - 8)
        shift_out_16bit(data_low, data_high)
        time.sleep(CHASE_ANIMATION_SPEED)
    
    print(f"[CHASE] Animation complete, LED {target_led + 1} active")

def play_hourly_animation():
    """
    Play full LED chase animation at XX:00:00
    3 full cycles (LED 1 to 16), then 3 rapid blinks of all LEDs, stops at LED 1
    """
    print("[CHASE] Hourly animation triggered - 3 cycles + blinks")
    
    # 3 full cycles: LED 1 to 16
    for cycle in range(3):
        print(f"[CHASE] Cycle {cycle + 1}/3")
        for i in range(16):
            if i < 8:
                data_low = 1 << i
                data_high = 0x00
            else:
                data_low = 0x00
                data_high = 1 << (i - 8)
            shift_out_16bit(data_low, data_high)
            time.sleep(CHASE_ANIMATION_SPEED)
    
    # 3 rapid blinks of all LEDs
    print("[CHASE] Final blinks (3x)")
    for blink in range(3):
        # All LEDs ON
        shift_out_16bit(0xFF, 0xFF)
        time.sleep(CHASE_BLINK_SPEED)
        # All LEDs OFF
        shift_out_16bit(0x00, 0x00)
        time.sleep(CHASE_BLINK_SPEED)
    
    # Final position: LED 1 (position 0)
    shift_out_16bit(0x01, 0x00)
    print("[CHASE] Hourly animation complete, LED 1 active")

def update_chase_mode():
    """Update chase effect with animations"""
    global chase_position, chase_first_update, last_hour_animation
    
    # Get current time info
    current_time = time.time()
    tm = time.localtime(current_time)
    current_hour = tm[3]
    current_minute = tm[4]
    current_second = tm[5]
    
    # Check for hourly animation (at XX:00:00)
    if current_minute == 0 and current_second == 0 and last_hour_animation != current_hour:
        last_hour_animation = current_hour
        play_hourly_animation()
        chase_position = 0  # LED 1 position
        return
    
    # Get LED position based on current time
    led_position = get_current_led_from_time()
    
    # Check if it's the first update (mode just started)
    if chase_first_update:
        chase_first_update = False
        play_chase_animation(led_position)
        chase_position = led_position
        return
    
    # Normal update: only change if position changed
    if led_position != chase_position:
        chase_position = led_position
        
        if chase_position < 8:
            data_low = 1 << chase_position
            data_high = 0x00
        else:
            data_low = 0x00
            data_high = 1 << (chase_position - 8)
        
        shift_out_16bit(data_low, data_high)

def get_current_led_from_time():
    """Calculate LED position from time"""
    current_time = time.time()
    tm = time.localtime(current_time)
    minutes = tm[4]
    seconds = tm[5]
    fractional = current_time - int(current_time)
    
    total_minutes = minutes + (seconds / 60.0) + (fractional / 60.0)
    led_position = int(total_minutes / CHASE_SPEED)
    
    if led_position >= 16:
        led_position = 0
    
    return led_position

def manage_onboard_led():
    """Manage onboard LED"""
    global led_blink_end_time
    
    if not LED_NOTIFICATION_ENABLED or not onboard_led:
        return
    
    current_time = time.time()
    
    if current_time < led_blink_end_time:
        blink_state = int(current_time * 5) % 2
        onboard_led.value(blink_state)
    else:
        if wlan and wlan.isconnected():
            onboard_led.value(1)
        else:
            onboard_led.value(0)

def trigger_new_connection():
    """Trigger LED notification"""
    global led_blink_end_time
    if LED_NOTIFICATION_ENABLED:
        led_blink_end_time = time.time() + NEW_CONNECTION_BLINK_DURATION

# =============================================================================
# BUTTONS
# =============================================================================

def check_button_press(button):
    """Check button press type"""
    if not button.value():
        press_start = time.ticks_ms()
        while not button.value():
            if time.ticks_diff(time.ticks_ms(), press_start) > LONG_PRESS_TIME:
                return "long"
            time.sleep_ms(10)
        time.sleep_ms(DEBOUNCE_TIME)
        return "short"
    return None

def handle_button1():
    """Handle button 1 - mode switching/exit"""
    global running
    press = check_button_press(button1)
    if press == "long":
        print("\nButton 1 long press - shutting down...")
        running = False
    elif press == "short":
        change_mode_next()

def handle_button2():
    """Handle button 2 - manual restart"""
    press = check_button_press(button2)
    if press == "long":
        print("\nButton 2 long press - restarting...")
        perform_restart()

def change_mode_next():
    """Cycle to next mode"""
    global current_mode, mode_on1_start_time, total_on1_hours, chase_position, chase_first_update, last_hour_animation
    
    old_mode = current_mode
    
    if current_mode == MODE_ON1:
        current_mode = MODE_ON2
        if mode_on1_start_time:
            total_on1_hours += (time.time() - mode_on1_start_time) / 3600
            mode_on1_start_time = None
    elif current_mode == MODE_ON2:
        current_mode = MODE_OFF
    else:
        current_mode = MODE_ON1
        mode_on1_start_time = time.time()
    
    if current_mode == MODE_ON2:
        chase_position = get_current_led_from_time()
        chase_first_update = True
        last_hour_animation = -1  # Reset hourly animation tracker
    
    add_log(f"Mode: {get_mode_name(old_mode)} -> {get_mode_name(current_mode)}", "MODE")

def set_mode(mode):
    """Set specific mode (API)"""
    global current_mode, mode_on1_start_time, total_on1_hours, chase_position, chase_first_update, last_hour_animation
    
    if mode not in [MODE_OFF, MODE_ON1, MODE_ON2]:
        return False
    
    old_mode = current_mode
    
    if current_mode == MODE_ON1 and mode != MODE_ON1:
        if mode_on1_start_time:
            total_on1_hours += (time.time() - mode_on1_start_time) / 3600
            mode_on1_start_time = None
    
    if mode == MODE_ON1 and current_mode != MODE_ON1:
        mode_on1_start_time = time.time()
    
    current_mode = mode
    
    if mode == MODE_ON2:
        chase_position = get_current_led_from_time()
        chase_first_update = True
        last_hour_animation = -1  # Reset hourly animation tracker
    
    add_log(f"Mode: {get_mode_name(old_mode)} -> {get_mode_name(current_mode)}", "MODE")
    return True

def get_mode_name(mode):
    """Get mode name"""
    if mode == MODE_OFF:
        return "OFF"
    elif mode == MODE_ON1:
        return "ON"
    elif mode == MODE_ON2:
        return "CHASE"
    return "Unknown"

def perform_restart():
    """Restart system"""
    add_log("Manual restart initiated", "SYSTEM")
    print("\n" + "="*50)
    print("RESTARTING...")
    print("="*50)
    time.sleep(2)
    machine.reset()

# =============================================================================
# STATISTICS
# =============================================================================

def calculate_on1_hours():
    """Calculate total ON1 hours"""
    hours = total_on1_hours
    if mode_on1_start_time:
        hours += (time.time() - mode_on1_start_time) / 3600
    return hours

def format_duration(hours):
    """Format duration"""
    total_seconds = int(hours * 3600)
    days = total_seconds // 86400
    remaining = total_seconds % 86400
    hours_part = remaining // 3600
    minutes = (remaining % 3600) // 60
    
    if days > 0:
        return f"{days}d {hours_part}h {minutes}m"
    elif hours_part > 0:
        return f"{hours_part}h {minutes}m"
    return f"{minutes}m"

def format_datetime(timestamp):
    """Format timestamp"""
    tm = time.localtime(timestamp)
    return "{:02d}/{:02d}/{:04d} - {:02d}:{:02d}:{:02d}".format(
        tm[2], tm[1], tm[0], tm[3], tm[4], tm[5]
    )

def get_system_stats():
    """Get system statistics"""
    on1_hours = calculate_on1_hours()
    uptime = (time.time() - program_start_time) / 3600
    pico_temp = read_pico_temperature()
    
    # Determine temperature status
    temp_status = "Normal"
    if pico_temp is not None:
        if pico_temp > 70:
            temp_status = "Critical"
        elif pico_temp > 60:
            temp_status = "High"
        elif pico_temp > 50:
            temp_status = "Warm"
            
    # Format temperature string
    temp_str = "{}°C".format(pico_temp) if pico_temp is not None else "N/A"
   
    return {
        "device_name": DEVICE_NAME,
        "current_mode": get_mode_name(current_mode),
        "program_start": format_datetime(program_start_time),
        "uptime": format_duration(uptime),
        "total_on1_time": format_duration(on1_hours),
        "last_update": format_datetime(time.time()),
        "chase_position": chase_position if current_mode == MODE_ON2 else "N/A",
        "total_leds": 16,
        "wifi_status": "Connected" if (wlan and wlan.isconnected()) else "Disconnected",
        "pico_temperature": temp_str,
        "temp_status": temp_status
    }

def get_network_info():
    """Get network info"""
    if wlan and wlan.isconnected():
        ip_info = wlan.ifconfig()
        return {
            "connected": True,
            "ssid": WIFI_SSID,
            "ip": ip_info[0],
            "subnet": ip_info[1],
            "gateway": ip_info[2],
            "dns": ip_info[3]
        }
    return {
        "connected": False,
        "ssid": WIFI_SSID,
        "ip": "Not connected"
    }

# =============================================================================
# SECURITY
# =============================================================================

def generate_auth_token():
    """Generate auth token"""
    global AUTH_TOKEN
    if AUTH_ENABLED:
        auth_string = f"{AUTH_USERNAME}:{AUTH_PASSWORD}"
        AUTH_TOKEN = ubinascii.b2a_base64(auth_string.encode()).decode().strip()

def check_auth(request):
    """Check authentication"""
    if not AUTH_ENABLED:
        return True
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Basic '):
        return auth_header[6:] == AUTH_TOKEN
    return False

def get_client_ip(request):
    """Get client IP"""
    return getattr(request, 'client_addr', ['unknown', 0])[0]

def check_ip_allowed(client_ip):
    """Check IP whitelist"""
    if not IP_WHITELIST_ENABLED:
        return True
    return client_ip in ALLOWED_IPS

def check_rate_limit(client_ip):
    """Check rate limit"""
    if not RATE_LIMIT_ENABLED:
        return True
    
    current_time = time.time()
    
    # Cleanup old entries
    expired = [ip for ip in request_counts 
               if current_time - request_counts[ip]['last_reset'] > RATE_LIMIT_WINDOW]
    for ip in expired:
        del request_counts[ip]
    
    if client_ip not in request_counts:
        request_counts[client_ip] = {'count': 0, 'last_reset': current_time}
    elif current_time - request_counts[client_ip]['last_reset'] > RATE_LIMIT_WINDOW:
        request_counts[client_ip] = {'count': 0, 'last_reset': current_time}
    
    request_counts[client_ip]['count'] += 1
    return request_counts[client_ip]['count'] <= RATE_LIMIT_MAX_REQUESTS

def security_check(request):
    """Main security check"""
    client_ip = get_client_ip(request)
    
    if not check_ip_allowed(client_ip):
        return Response("Access denied", status_code=403)
    
    if not check_rate_limit(client_ip):
        return Response("Too many requests", status_code=429)
    
    if AUTH_ENABLED and request.path.startswith('/api/') and not check_auth(request):
        response = Response("Authentication required", status_code=401)
        response.headers['WWW-Authenticate'] = 'Basic realm="ML01"'
        return response
    
    return None

def add_security_headers(response):
    """Add security headers"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Cache-Control'] = 'no-cache'
    return response

# =============================================================================
# WEB ROUTES
# =============================================================================

@app.route('/')
def index(request):
    """Main page with streaming"""
    gc.collect()
    free_mem = gc.mem_free()
    print(f"[MEMORY] Loading index.html - Free: {free_mem} bytes")
    
    client_ip = get_client_ip(request)
    
    if client_ip not in connected_ips:
        connected_ips.add(client_ip)
        trigger_new_connection()
        add_log(f"New connection: {client_ip}", "SECURITY")
    
    if not check_ip_allowed(client_ip):
        return Response("Access denied", status_code=403)
    
    if not check_rate_limit(client_ip):
        return Response("Too many requests", status_code=429)
    
    def html_generator():
        try:
            with open('index.html', 'r') as f:
                while True:
                    chunk = f.read(2048)
                    if not chunk:
                        break
                    yield chunk
        except Exception as e:
            print(f"[ERROR] Streaming failed: {e}")
            yield "Error loading page"
    
    try:
        response = Response(html_generator())
        response.headers['Content-Type'] = 'text/html'
        return add_security_headers(response)
    except Exception as e:
        print(f"[ERROR] Response failed: {e}")
        return Response("Server error", status_code=500)

@app.route('/api/mode', methods=['POST'])
def api_set_mode(request):
    """API: Set mode"""
    sec = security_check(request)
    if sec:
        return sec
    
    try:
        client_ip = get_client_ip(request)
        add_log(f"Mode change by {client_ip}", "SECURITY")
        
        data = request.json
        if not data:
            raise ValueError("Invalid JSON")
        
        mode = data.get('mode')
        if set_mode(mode):
            response = Response(json.dumps({'success': True, 'mode': get_mode_name(mode)}))
        else:
            response = Response(json.dumps({'success': False, 'error': 'Invalid mode'}), status_code=400)
        
        response.headers['Content-Type'] = 'application/json'
        return add_security_headers(response)
    except Exception as e:
        response = Response(json.dumps({'success': False, 'error': str(e)}), status_code=500)
        response.headers['Content-Type'] = 'application/json'
        return add_security_headers(response)

@app.route('/api/stats')
def api_get_stats(request):
    """API: Get stats (without memory info)"""
    sec = security_check(request)
    if sec:
        return sec
    
    try:
        response_data = {
            'stats': get_system_stats(),
            'network': get_network_info(),
            'client_ip': get_client_ip(request)
        }
        response = Response(json.dumps(response_data))
    except Exception as e:
        response = Response(json.dumps({'error': str(e)}), status_code=500)
    
    response.headers['Content-Type'] = 'application/json'
    return add_security_headers(response)

@app.route('/api/logs')
def api_get_logs(request):
    """API: Get logs with pagination"""
    sec = security_check(request)
    if sec:
        return sec
    
    try:
        # Get pagination parameters from query string
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 100))
        
        # Validate parameters
        if page < 1:
            page = 1
        if limit < 1 or limit > 500:  # Max 500 logs per page
            limit = 100
        
        total_logs = len(log_entries)
        total_pages = (total_logs + limit - 1) // limit  # Ceiling division
        
        # Calculate slice indices
        # Page 1 shows MOST RECENT logs (end of list)
        # Page 2 shows older logs, etc.
        end_index = total_logs - ((page - 1) * limit)
        start_index = max(0, end_index - limit)
        
        # Get logs slice (reversed to show newest first on page 1)
        logs_subset = log_entries[start_index:end_index]
        logs_subset.reverse()  # Newest first
        
        response_data = {
            'logs': logs_subset,
            'pagination': {
                'page': page,
                'limit': limit,
                'total_logs': total_logs,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1,
                'showing_from': start_index + 1,
                'showing_to': end_index
            }
        }
        response = Response(json.dumps(response_data))
    except Exception as e:
        response = Response(json.dumps({'error': str(e)}), status_code=500)
    
    response.headers['Content-Type'] = 'application/json'
    return add_security_headers(response)

@app.route('/api/logs/clear', methods=['POST'])
def api_clear_logs(request):
    """API: Clear logs"""
    sec = security_check(request)
    if sec:
        return sec
    
    try:
        global log_entries
        client_ip = get_client_ip(request)
        log_count = len(log_entries)
        log_entries = []
        gc.collect()
        
        add_log(f"Logs cleared by {client_ip} ({log_count} entries)", "SYSTEM")
        
        response = Response(json.dumps({
            'success': True,
            'cleared_count': log_count
        }))
    except Exception as e:
        response = Response(json.dumps({'success': False, 'error': str(e)}), status_code=500)
    
    response.headers['Content-Type'] = 'application/json'
    return add_security_headers(response)

@app.route('/api/restart', methods=['POST'])
def api_restart(request):
    """API: Manual restart - sets flag for main loop to handle"""
    sec = security_check(request)
    if sec:
        return sec
    
    try:
        global restart_requested, restart_request_time
        
        client_ip = get_client_ip(request)
        add_log(f"Restart requested by {client_ip} via API", "SYSTEM")
        print(f"[SYSTEM] Restart requested by {client_ip}")
        
        # Set restart flag instead of creating new thread
        restart_requested = True
        restart_request_time = time.time()
        
        # Send immediate response
        response_data = {'success': True, 'message': 'Restart command received'}
        response = Response(json.dumps(response_data))
        response.headers['Content-Type'] = 'application/json'
        return add_security_headers(response)
        
    except Exception as e:
        print(f"[ERROR] Restart API error: {e}")
        add_log(f"Restart API error: {str(e)}", "ERROR")
        response_data = {'success': False, 'error': str(e)}
        response = Response(json.dumps(response_data), status_code=500)
        response.headers['Content-Type'] = 'application/json'
        return add_security_headers(response)

# =============================================================================
# MAIN
# =============================================================================

def display_instructions():
    """Display instructions"""
    print("\n" + "="*70)
    print("ML01 LED CONTROLLER - PICO 2W")
    print("="*70)
    print("\nMODES:")
    print("• OFF: All LEDs off")
    print("• ON: All LEDs on")
    print("• CHASE: Sequential LED movement")
    print("\nCONTROLS:")
    print("• Button 1 short: Switch mode")
    print("• Button 1 long: Shutdown")
    print("• Button 2 long: Manual restart")
    print("• Web: http://[IP_ADDRESS]")
    print("\nLED NOTIFICATIONS:")
    print("• Solid: WiFi connected")
    print("• OFF: WiFi disconnected")
    print("• Fast blink: New connection")
    print("-"*70 + "\n")

def web_server_thread():
    """Web server thread"""
    global web_server_running, onboard_led
    
    print("[WEB] Thread started")
    time.sleep(3)
    
    gc.collect()
    free_mem = gc.mem_free()
    print(f"[WEB] Free memory: {free_mem} bytes")
    
    if not wlan or not wlan.isconnected():
        print("[WEB] ERROR: WiFi not connected!")
        add_log("Web server aborted: no WiFi", "ERROR")
        return
    
    try:
        print(f"[WEB] Starting on port {WEB_PORT}...")
        print(f"[WEB] http://{wlan.ifconfig()[0]}:{WEB_PORT}")
        
        web_server_running = True
        
        if onboard_led:
            for _ in range(3):
                onboard_led.value(0)
                time.sleep(0.2)
                onboard_led.value(1)
                time.sleep(0.2)
        
        app.run(host='0.0.0.0', port=WEB_PORT, debug=False)
        
    except OSError as e:
        if e.args[0] == 98:
            print(f"[WEB] ERROR: Port {WEB_PORT} in use!")
            add_log(f"Port {WEB_PORT} in use", "ERROR")
        else:
            print(f"[WEB] OSError: {e}")
            add_log(f"Web server error: {str(e)}", "ERROR")
    except Exception as e:
        print(f"[WEB] Exception: {e}")
        add_log(f"Web server error: {str(e)}", "ERROR")
    finally:
        web_server_running = False
        print("[WEB] Server stopped")

def main_loop():
    """Main loop"""
    global running, restart_requested, chase_first_update, last_hour_animation
    
    last_chase_time = time.ticks_ms()
    print("Starting with mode ON1\n")
    
    # Initialize chase mode properly if starting in CHASE mode
    if current_mode == MODE_ON2:
        chase_first_update = True
        last_hour_animation = -1
    
    while running:
        try:
            current_time = time.ticks_ms()
            
            # Check if restart was requested via API
            if restart_requested:
                restart_requested = False  # Reset flag before restart
                print("[SYSTEM] Restart flag detected, rebooting in 2 seconds...")
                time.sleep(2)  # Give time for HTTP response to be sent
                perform_restart()
                # Note: perform_restart() calls machine.reset() so code never reaches here
            
            check_wifi_connection()
            check_memory()
            
            if current_mode == MODE_OFF:
                set_mode_off()
            elif current_mode == MODE_ON1:
                set_mode_on1()
            elif current_mode == MODE_ON2:
                # Check every 100ms for smooth synchronization
                # Except during animations (handled inside update_chase_mode)
                if time.ticks_diff(current_time, last_chase_time) >= 100:
                    update_chase_mode()
                    last_chase_time = current_time
            
            manage_onboard_led()
            handle_button1()
            handle_button2()
            
            time.sleep(0.01)
            
        except KeyboardInterrupt:
            add_log("Ctrl+C pressed", "SYSTEM")
            print("\nKeyboard interrupt...")
            running = False
            break
        except Exception as e:
            add_log(f"Loop error: {str(e)}", "ERROR")
            print(f"Loop error: {e}")
            time.sleep(0.1)

def main():
    """Main entry point"""
    global running, program_start_time, mode_on1_start_time
    
    try:
        display_instructions()
        
        print("Initializing security...")
        if AUTH_ENABLED:
            generate_auth_token()
            add_log(f"Auth enabled (user: {AUTH_USERNAME})", "SYSTEM")
            print(f"✓ Auth: {AUTH_USERNAME}")
        if IP_WHITELIST_ENABLED:
            print(f"✓ IP filter: {len(ALLOWED_IPS)} allowed")
        if RATE_LIMIT_ENABLED:
            print(f"✓ Rate limit: {RATE_LIMIT_MAX_REQUESTS}/{RATE_LIMIT_WINDOW}s")
        
        init_gpio()
        add_log("ML01 Controller started", "SYSTEM")
        
        if not connect_wifi():
            add_log("WiFi failed at startup", "ERROR")
            print("WARNING: No WiFi. Buttons still work.")
        else:
            program_start_time = time.time()
            mode_on1_start_time = time.time()
            add_log("Start time updated after NTP", "SYSTEM")
            
            try:
                print("Starting web server thread...")
                time.sleep(1)
                _thread.start_new_thread(web_server_thread, ())
                time.sleep(5)
                
                if web_server_running:
                    add_log(f"Web server on http://{wlan.ifconfig()[0]}", "SYSTEM")
                    print(f"✓ Web: http://{wlan.ifconfig()[0]}")
                    if AUTH_ENABLED:
                        print(f"  Login: {AUTH_USERNAME} / {AUTH_PASSWORD}")
                else:
                    print("⚠ Web server starting...")
            except Exception as e:
                add_log(f"Web server failed: {str(e)}", "ERROR")
                print(f"✗ Web server failed: {e}")
        
        set_mode_on1()
        main_loop()
        
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        cleanup_gpio()
        print("\n" + "="*42)
        print("FINAL STATISTICS")
        print(f"Started: {format_datetime(program_start_time)}")
        print(f"Total ON time: {format_duration(calculate_on1_hours())}")
        print("="*42)
        print("Program terminated\n")

if __name__ == "__main__":
    main()
