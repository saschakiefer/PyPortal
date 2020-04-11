import re
import time

import adafruit_esp32spi.adafruit_esp32spi_socket as socket
import adafruit_logging as logging
import adafruit_requests as requests
import adafruit_touchscreen
import board
import busio
import displayio
import usb_hid
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_pyportal import PyPortal
from digitalio import DigitalInOut
from adafruit_button import Button
from adafruit_bitmap_font import bitmap_font

esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
esp32_gpio0 = DigitalInOut(board.ESP_GPIO0)

screen_width = 480
screen_height = 320

# Set up logging
logger = logging.getLogger("dashboard")
logger.setLevel(logging.INFO)  # change as desired

logger.info("My Multi Dasboard")

# Initialize WIFI Microncontroller
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(
    spi, esp32_cs, esp32_ready, esp32_reset, esp32_gpio0
)

# Screen Setup
pyportal = PyPortal(esp=esp, external_spi=spi, debug=True)
display = board.DISPLAY
display.rotation = 0
display.auto_brightness = True

pyportal.set_background("/images/fractal_loading.bmp")

# Initialize Touchscreen
touch_screen = adafruit_touchscreen.Touchscreen(
    board.TOUCH_XL,
    board.TOUCH_XR,
    board.TOUCH_YD,
    board.TOUCH_YU,
    calibration=((6272, 60207), (7692, 56691)),
    size=(screen_width, screen_height),
)

# Initiallize the Keyboard
try:
    # Initialize with the available USB devices. The constructur pics the
    # correct one from the list
    keyboard = Keyboard(usb_hid.devices)
    keyboard_active = True
    logger.info("Keyboard activated")
except OSError:
    keyboard_active = False
    logger.warning("No keyboard found")

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    logger.error("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# Connect to AP
logger.info("Connecting to AP...")
while not esp.is_connected:
    try:
        esp.connect_AP(secrets["ssid"], secrets["password"])
    except RuntimeError as e:
        logger.warning("could not connect to AP, retrying: ", e)
        continue

logger.info("Connected to: " + str(esp.ssid, "utf-8"))

# Init the requests object
requests.set_socket(socket, esp)

# Sound effects
soundBeep = "/sounds/beep.wav"

# Display Groups + Background Image
main_group = displayio.Group(max_size=15)

image_file = open("/images/fractal.bmp", "rb")
image = displayio.OnDiskBitmap(image_file)
try:
    image_sprite = displayio.TileGrid(image, pixel_shader=displayio.ColorConverter())
except TypeError:
    image_sprite = displayio.TileGrid(
        image, pixel_shader=displayio.ColorConverter(), position=(0, 0)
    )
main_group.append(image_sprite)

# Set the font and preload letters
font = bitmap_font.load_font("/fonts/Helvetica-Bold-16.bdf")
font.load_glyphs(b"abcdefghjiklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890- ()")

# Buttons
BUTTON_HEIGHT = int(screen_height / 4.5)
BUTTON_WIDTH = int(screen_width / 2)
BUTTON_Y = int(screen_height - BUTTON_HEIGHT)

buttons = []

button_action_1 = Button(
    x=0,
    y=BUTTON_Y,
    width=BUTTON_WIDTH,
    height=BUTTON_HEIGHT,
    label="Developer Scene",
    label_font=font,
    label_color=0xFF7E00,
    fill_color=0x5C5B5C,
    outline_color=0x767676,
    selected_fill=0x1A1A1A,
    selected_outline=0x2E2E2E,
    selected_label=0x525252,
)

buttons.append(button_action_1)

button_action_2 = Button(
    x=0 + BUTTON_WIDTH,
    y=BUTTON_Y,
    width=BUTTON_WIDTH,
    height=BUTTON_HEIGHT,
    label="Office Scene",
    label_font=font,
    label_color=0xFF7E00,
    fill_color=0x5C5B5C,
    outline_color=0x767676,
    selected_fill=0x1A1A1A,
    selected_outline=0x2E2E2E,
    selected_label=0x525252,
)

buttons.append(button_action_2)

[main_group.append(button.group) for button in buttons]


class Fritbox_Status:
    """Encapsulate the FritBox status calls via the upnp protocol
    TODO: make the class independent of gloabl variables (secret, logger) and
    extract it to an own module
    """

    def __init__(self):
        self.fritz_url_base = f"http://{secrets['access_point_ip']}:{secrets['access_point_port']}/igdupnp/control/"
        self.ritz_sap_action_base = "urn:schemas-upnp-org:service:"

        self.fritz_soap_connection = '<?xml version="1.0" encoding="utf-8"?><s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><u:GetStatusInfo xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1"></u:GetStatusInfo></s:Body></s:Envelope>'

        self.fritz_soap_link_status = '<?xml version="1.0" encoding="utf-8"?><s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><u:GetCommonLinkProperties xmlns:u="urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1"></u:GetCommonLinkProperties></s:Body></s:Envelope>'

        self.fritz_headers = {
            "charset": "utf-8",
            "content-type": "text/xml",
            "soapaction": None,
        }

    def get_dsl_status(self):
        return {
            "connected": self.is_connected(),
            "linked": self.is_linked(),
        }

    def is_connected(self):
        status = self.do_call(
            url_suffix="WANIPConn1",
            soapaction="urn:schemas-upnp-org:service:WANIPConnection:1#GetStatusInfo",
            body=self.fritz_soap_connection,
        )

        return status == "Connected"

    def is_linked(self):
        status = self.do_call(
            url_suffix="WANCommonIFC1",
            soapaction="urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1#GetCommonLinkProperties",
            body=self.fritz_soap_link_status,
        )

        return status == "Up"

    def do_call(self, url_suffix=None, soapaction=None, body=None):
        logger.debug("Get: " + url_suffix)

        url = f"{self.fritz_url_base}{url_suffix}"

        headers = self.fritz_headers.copy()
        headers["soapaction"] = soapaction

        try:
            response = requests.post(url, data=body, headers=headers, timeout=2)
        except RuntimeError as error:
            logger.warning(str(error))
            return "Unknown"  # We just ignore this and wait for the next request

        if url_suffix == "WANIPConn1":
            regex = r"<NewConnectionStatus>(.*)<\/NewConnectionStatus>"
        else:
            regex = r"<NewPhysicalLinkStatus>(.*)<\/NewPhysicalLinkStatus>"

        matches = re.search(regex, response.text)
        status = matches.groups()[0]

        logger.debug("Received state: " + status)

        return status


fritz_status = Fritbox_Status()

# We collect 3 points to simulate a "long press" of the button
point_list = []

# initialize the dsl check
current_period = 0  # ensure, that it immidiately starts
last_dsl_check = time.monotonic()

board.DISPLAY.show(main_group)

logger.info("Waiting for input")
while True:
    if last_dsl_check + current_period < time.monotonic():
        """ Only check the dsl every 30 seconds. Therefore there is an
        own counter parallel to the endless loop that watches for keyboard
        input. The check time is decreased to two seconds as soon as
        dsl is gone and increased back to 30 seconds when it's back
        """
        dsl_status = fritz_status.get_dsl_status()

        logger.info(
            "Is linked: "
            + str(dsl_status["linked"])
            + " -=- Is Connected: "
            + str(dsl_status["connected"])
        )

        if dsl_status["connected"]:
            current_period = 15
        else:
            current_period = 2

        last_dsl_check = time.monotonic()
    if keyboard_active:
        point = touch_screen.touch_point

        if point:
            # append each touch connection to a list
            # I had an issue with the first touch detected not being accurate
            point_list.append(point)

            # after three trouch detections have occured.
            if len(point_list) == 3:
                # discard the first touch detection and average the other
                # two get the x,y of the touch
                x = (point_list[1][0] + point_list[2][0]) / 2
                y = (point_list[1][1] + point_list[2][1]) / 2
                logger.info("(" + str(x) + "/" + str(y) + ") pressed")

                pyportal.play_file(soundBeep)

                for i, button in enumerate(buttons):
                    if button.contains((x, y, 65000)):
                        logger.info(f"Button {button} pressed")

                        if i == 0:
                            logger.info("Developer Scene Selected")

                            keyboard.send(
                                Keycode.COMMAND,
                                Keycode.CONTROL,
                                Keycode.OPTION,
                                Keycode.SHIFT,
                                Keycode.ONE,
                            )
                        elif i == 1:
                            logger.info("Office Scene Selected")

                            keyboard.send(
                                Keycode.COMMAND,
                                Keycode.CONTROL,
                                Keycode.OPTION,
                                Keycode.SHIFT,
                                Keycode.TWO,
                            )

                # clear list for next detection
                point_list = []

                # sleep to avoid pressing two buttons on accident
                time.sleep(0.2)
