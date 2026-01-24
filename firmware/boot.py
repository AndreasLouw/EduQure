import network
import time
import config

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print('Connecting to network...')
        wlan.connect(config.WIFI_SSID, config.WIFI_PASS)
        
        start_time = time.time()
        while not wlan.isconnected():
            time.sleep(1)
            if time.time() - start_time > 15: # Timeout after 15s
                print("Wifi connect timeout")
                return False
                
    print('Network config:', wlan.ifconfig())
    return True

connect_wifi()
