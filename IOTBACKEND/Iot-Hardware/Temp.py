import time
import adafruit_dht
import board
import RPi.GPIO as GPIO
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from pubnub.callbacks import SubscribeCallback
import datetime
import os


GPIO.setwarnings(False)


GPIO.setmode(GPIO.BCM)


try:
    dht_device = adafruit_dht.DHT11(board.D17)
except Exception as e:
    print(f"Error initializing DHT11 sensor: {e}")
    exit(1)


ldr_pin = 18  
GPIO.setup(ldr_pin, GPIO.IN)


led_pin = 23 
GPIO.setup(led_pin, GPIO.OUT)


TEMP_THRESHOLD = 10 

MAX_RETRIES = 5 
retry_delay = 5 
successful_reads = 0


pnconfig = PNConfiguration()
pnconfig.subscribe_key = os.getenv("PUBNUB_SUBSCRIBE_KEY", "sub-c-6963e588-282e-41ec-8194-9b6710e52ad3")
pnconfig.publish_key = os.getenv("PUBNUB_PUBLISH_KEY", "pub-c-45bab202-c191-4fbe-a1d0-2628df540689")
pnconfig.secret_key = os.getenv("PUBNUB_SECRET_KEY", "sec-c-MmM5ZTI3YjEtOGU5NC00YzY4LTk0NjYtZWI0MTUyYjlkMGY0")
pnconfig.uuid = os.getenv("PUBNUB_USER_ID", "temperature-subscriber") 
pubnub = PubNub(pnconfig)

channel = "Temperature-App" 


print("Reading from DHT11 sensor and LDR (Press Ctrl+C to exit)...")

try:
    while True:
        retries = 0
        while retries < MAX_RETRIES:
            try:
              
                temperature_c = dht_device.temperature 
                humidity = dht_device.humidity 

                if temperature_c is not None and humidity is not None:
                    print(f"Temperature: {temperature_c} C  Humidity: {humidity}%")
                    successful_reads += 1
                    retries = 0  
                    break 
                else:
                    print("Failed to retrieve data from sensor")
                    retries += 1 
                    time.sleep(retry_delay)

            except RuntimeError as error:
                print(f"Runtime error reading sensor: {error.args}")
                retries += 1  
                time.sleep(retry_delay)

        if retries == MAX_RETRIES:
            print("Exceeded maximum retries. Check sensor wiring or placement.")
            break
 data = {
            "temperature": temperature_c,
            "humidity": humidity,
            "light_level": light_status,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        pubnub.publish().channel(channel).message(data).sync()
        print(f"Published data to PubNub: {data}")