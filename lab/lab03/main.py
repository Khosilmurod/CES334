from gpiozero import LED
import time

led = LED(4)
print("Starting LED blink program on GPIO4 (physical pin 7)")

try:
    while True:
        print("LED ON")
        led.on()
        time.sleep(1)
        print("LED OFF")
        led.off()
        time.sleep(1)
except KeyboardInterrupt:
    print("Program stopped by user")
    led.close()