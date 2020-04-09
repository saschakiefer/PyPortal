# PyPortal CheatSheet

[Adafruit CircuitPython API Reference — Adafruit CircuitPython 0.0.0 documentation](https://circuitpython.readthedocs.io/en/latest/docs/index.html)

## Minmial Modules

Use the `requirements_min.txt` file as a basis for new Projects. These are the ones, that usually are needed. Copy the file to your project directory and rename it to `requirements.txt`. You can use `circup` to install/remove packages. `circup freeze -r`creates/overrites the `requirements.txt`with the currently installed libraries on the device.

## Secrets

```Python
# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise
```

## Access the Internet

Without using the `adafruit_pyportal` library.

### Initialize the WLAN Microcontroller

Initialize the WLAN microcontroller ESP32 using the [Serial Peripheral Interface (SPPI)](https://de.wikipedia.org/wiki/Serial_Peripheral_Interface):

```Python
import board
import busio
from digitalio import DigitalInOut
from adafruit_esp32spi import adafruit_esp32spi

esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
```

### Connect to the Access Point

```Python
print("Connecting to AP...")
while not esp.is_connected:
    try:
        esp.connect_AP(secrets["ssid"], secrets["password"])
    except RuntimeError as e:
        print("could not connect to AP, retrying: ", e)
        continue
print("Connected to", str(esp.ssid, "utf-8"), "\tRSSI:", esp.rssi)
print("My IP address is", esp.pretty_ip(esp.ip_address))
print(
    "IP lookup adafruit.com: %s" % esp.pretty_ip(esp.get_host_by_name("adafruit.com"))
)
```

### Initialize the Requests Object and Fire a Request

Tells our requests library the type of socket we're using (socket type varies by connectivity type - we'll be using the adafruit_esp32spi_socket for this example). We'll also set the interface to an esp object. This is a little bit of a hack, but it lets us use requests like CPython does.

```Python
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
import adafruit_requests as requests

requests.set_socket(socket, esp)

r = requests.get(TEXT_URL)
print(r.text) # or print(r.json())
r.close(
```

The requests API docs can be found [here](https://adafruit-circuitpython-requests.readthedocs.io/en/latest/api.html)

## Logging

```Python
import adafruit_logging as logging

# Set up logging
logger = logging.getLogger("logger")
logger.setLevel(logging.INFO)  # change as desired
```

## Create User Interfaces
[Overview | Making a PyPortal User Interface with DisplayIO | Adafruit Learning System](https://learn.adafruit.com/making-a-pyportal-user-interface-displayio/overview)

## Simulate a Keyboard

```python
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
import usb_hid

keyboard_active = False

#Initiallize the Keyboard
try:
    # Initialize with the available USB devices. The constructur pics the
    # correct one from the list
    kbd = Keyboard(usb_hid.devices)
    keyboard_active = True
except OSError:
    keyboard_active = False

if keyboard_active:
    kbd.send(Keycode.COMMAND, Keycode.CONTROL, Keycode.OPTION, Keycode.SHIFT, Keycode.ONE)
```

Documentation: [Introduction — Adafruit HID Library 1.0 documentation](https://circuitpython.readthedocs.io/projects/hid/en/latest/)
