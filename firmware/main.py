import machine
import time
import urequests
import json
import config
from pn532 import PN532_I2C

# Hardware Setup
relay = machine.Pin(4, machine.Pin.OUT)
buzzer = machine.Pin(5, machine.Pin.OUT)

# I2C Setup
try:
    i2c = machine.I2C(0, sda=machine.Pin(21), scl=machine.Pin(22))
    nfc = PN532_I2C(i2c)
    print("NFC Initialized")
except Exception as e:
    print("NFC Error:", e)
    nfc = None

# Offline queue file
QUEUE_FILE = "queue.txt"

def grant_access():
    print("Access Granted")
    buzzer.on()
    time.sleep(0.2)
    buzzer.off()
    relay.on()       # Unlock
    time.sleep(5)    # Keep open for 5 seconds
    relay.off()      # Lock

def deny_access():
    print("Access Denied")
    for _ in range(3):
        buzzer.on()
        time.sleep(0.1)
        buzzer.off()
        time.sleep(0.1)

def save_to_queue(uid, valid, timestamp):
    entry = {"uid": uid, "status": valid, "timestamp": timestamp}
    with open(QUEUE_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print("Saved to offline queue")

def process_queue():
    try:
        # Read all lines
        lines = []
        try:
            with open(QUEUE_FILE, "r") as f:
                lines = f.readlines()
        except OSError:
            # No file
            return

        if not lines:
            return

        print(f"Processing {len(lines)} offline logs...")
        
        remaining_lines = []
        for line in lines:
            if not line.strip(): continue
            try:
                entry = json.loads(line)
                if sync_to_cloud(entry["uid"], entry["status"]):
                    print("Synced old log")
                else:
                    remaining_lines.append(line)
            except:
                pass # Corrupt line
        
        # Rewrite remaining
        with open(QUEUE_FILE, "w") as f:
            for line in remaining_lines:
                f.write(line)
                
    except Exception as e:
        print("Queue Process Error:", e)

def sync_to_cloud(uid, valid):
    url = f"{config.SUPABASE_URL}/rest/v1/attendance_logs"
    headers = {
        "apikey": config.SUPABASE_KEY,
        "Authorization": f"Bearer {config.SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    data = {
        "student_uid": uid,
        "status": valid
        # timestamp defaults to now() on server, or can be passed if queue is old.
        # Ideally, we pass the timestamp from the record if it exists
    }
    
    try:
        r = urequests.post(url, headers=headers, json=data)
        if r.status_code in [200, 201]:
            r.close()
            return True
        r.close()
    except Exception as e:
        print("Sync Error:", e)
    
    return False

# Main Loop
last_sync_check = 0

print("System Ready...")
while True:
    if nfc:
        uid = nfc.read_passive_target(timeout=500)
    else:
        uid = None
        time.sleep(1)

    if uid:
        uid_str = '0x' + ''.join(['{:02x}'.format(i) for i in uid])
        print(f"Card Detected: {uid_str}")
        
        valid = False
        if uid_str in config.AUTHORIZED_UIDS:
            valid = True
            grant_access()
        else:
            deny_access()
            
        # Try sync immediately
        if not sync_to_cloud(uid_str, valid):
            # Save to queue if fail
            # Note: RTC time might be unset if no NTP, so timestamp is relative or generic
            save_to_queue(uid_str, valid, time.time())

    # Background Tasks (every 60s)
    now = time.time()
    if now - last_sync_check > 60:
        process_queue()
        last_sync_check = now
    
    # Small delay to prevent loop hogging
    if not uid:
        time.sleep(0.1)
