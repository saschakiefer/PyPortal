import gc
import re
import time

import adafruit_esp32spi.adafruit_esp32spi_socket as socket
import adafruit_logging as logging
import adafruit_requests as requests
import adafruit_touchscreen
import board
import busio
import displayio
import supervisor
import usb_hid
from adafruit_bitmap_font import bitmap_font
from adafruit_button import Button
from adafruit_display_text.label import Label
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_pyportal import PyPortal
from digitalio import DigitalInOut

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
pyportal = PyPortal(
    esp=esp,
    external_spi=spi,
    url="https://www.adafruit.com/api/quotes.php",
    json_path=([0, "text"], [0, "author"]),
)
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

# This will handel switching Images and Icons
def set_image(group, filename):
    """Set the image file for a given goup for display.
    This is most useful for Icons or image slideshows.
        :param group: The chosen group
        :param filename: The filename of the chosen image
    """
    if group:
        group.pop()

    if not filename:
        return  # we're done, no icon desired

    image_file = open(filename, "rb")
    image = displayio.OnDiskBitmap(image_file)
    try:
        image_sprite = displayio.TileGrid(
            image, pixel_shader=displayio.ColorConverter()
        )
    except TypeError:
        image_sprite = displayio.TileGrid(
            image, pixel_shader=displayio.ColorConverter(), position=(0, 0)
        )
    group.append(image_sprite)


# Display Groups + Background Image
main_group = displayio.Group(max_size=15)
set_image(main_group, "/images/fractal.bmp")

# Set the font and preload letters
font = bitmap_font.load_font("/fonts/Helvetica-Bold-16.bdf")
font.load_glyphs(b"abcdefghjiklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890- ()")

# Buttons
BUTTON_HEIGHT = int(screen_height / 4.5)
BUTTON_WIDTH = int(screen_width / 3)
BUTTON_Y = int(screen_height - BUTTON_HEIGHT)
BUTTON_PADDING = 8

buttons = []

button_action_1 = Button(
    x=0 + BUTTON_PADDING,
    y=BUTTON_Y + BUTTON_PADDING,
    width=BUTTON_WIDTH - 2 * BUTTON_PADDING,
    height=BUTTON_HEIGHT - 2 * BUTTON_PADDING,
    label="Developer\n   Scene",
    label_font=font,
    label_color=0xD7C6E0,
    fill_color=0x601D83,
    selected_fill=0xD7C6E0,
    selected_label=0x601D83,
    style=Button.ROUNDRECT,
)

buttons.append(button_action_1)

button_action_2 = Button(
    x=0 + BUTTON_WIDTH + BUTTON_PADDING,
    y=BUTTON_Y + BUTTON_PADDING,
    width=BUTTON_WIDTH - 2 * BUTTON_PADDING,
    height=BUTTON_HEIGHT - 2 * BUTTON_PADDING,
    label="Web Developer\n       Scene",
    label_font=font,
    label_color=0xD7C6E0,
    fill_color=0x601D83,
    selected_fill=0xD7C6E0,
    selected_label=0x601D83,
    style=Button.ROUNDRECT,
)

buttons.append(button_action_2)

button_action_3 = Button(
    x=0 + BUTTON_WIDTH + BUTTON_WIDTH + BUTTON_PADDING,
    y=BUTTON_Y + BUTTON_PADDING,
    width=BUTTON_WIDTH - 2 * BUTTON_PADDING,
    height=BUTTON_HEIGHT - 2 * BUTTON_PADDING,
    label="Office\nScene",
    label_font=font,
    label_color=0xD7C6E0,
    fill_color=0x601D83,
    selected_fill=0xD7C6E0,
    selected_label=0x601D83,
    style=Button.ROUNDRECT,
)

buttons.append(button_action_3)

[main_group.append(button.group) for button in buttons]

# Initialize the status Icons
linked_group = displayio.Group(max_size=1)
linked_group.x = 5
linked_group.y = 5
linked_group.scale = 1
set_image(linked_group, "/images/unlinked.bmp")

main_group.append(linked_group)

wifi_group = displayio.Group(max_size=1)
wifi_group.x = 52
wifi_group.y = 5
wifi_group.scale = 1
set_image(wifi_group, "/images/wifi_on.bmp")

main_group.append(wifi_group)

keyboard_group = displayio.Group(max_size=1)
keyboard_group.x = 99
keyboard_group.y = 5
keyboard_group.scale = 1

if keyboard_active:
    set_image(keyboard_group, "/images/keyboard_on.bmp")
else:
    set_image(keyboard_group, "/images/keyboard_off.bmp")


main_group.append(keyboard_group)

# Quote Label
quote_font = bitmap_font.load_font("/fonts/Arial-ItalicMT-23.bdf")
quote_font.load_glyphs(
    b"abcdefghjiklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890- ()"
)
quote_font_hight = Label(font, text="M", color=0x03AD31, max_glyphs=10)

quote_label = Label(quote_font, text="Loading Quote...", color=0xFED73F, max_glyphs=500)
quote_label.x = 10
quote_label.y = 120
main_group.append(quote_label)


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
        gc.collect()
        logger.debug("Get: " + url_suffix)

        url = f"{self.fritz_url_base}{url_suffix}"

        headers = self.fritz_headers.copy()
        headers["soapaction"] = soapaction

        try:
            gc.collect()
            response = requests.post(url, data=body, headers=headers, timeout=2)
            gc.collect()
        except MemoryError:
            supervisor.reload()
        except:
            logger.warning("Couldn't get DSL status, will try again later.")
            return "Unknown"  # We just ignore this and wait for the next request

        if url_suffix == "WANIPConn1":
            regex = r"<NewConnectionStatus>(.*)<\/NewConnectionStatus>"
        else:
            regex = r"<NewPhysicalLinkStatus>(.*)<\/NewPhysicalLinkStatus>"

        matches = re.search(regex, response.text)
        status = matches.groups()[0]

        logger.debug("Received state: " + status)

        response = None
        regex = None
        matches = None
        gc.collect()

        return status


fritz_status = Fritbox_Status()

# We collect 3 points to simulate a "long press" of the button
point_list = []

# initialize the dsl check
current_period = 0  # ensure, that it immidiately starts
last_dsl_check = time.monotonic()

last_quote_check = time.monotonic() - 3601

board.DISPLAY.show(main_group)

logger.info("Waiting for input")
while True:
    # CHeck status
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
            set_image(linked_group, "/images/linked.bmp")
            current_period = 15
        else:
            set_image(linked_group, "/images/unlinked.bmp")
            current_period = 2

        last_dsl_check = time.monotonic()

    # Load new quote
    if last_quote_check + 3600 < time.monotonic():
        try:
            quote_json = pyportal.fetch()
            quote_text = '"' + quote_json[0] + '" - ' + quote_json[1]
            quote = pyportal.wrap_nicely(quote_text, 40)

            # Only show quotes with 4 lines ore less
            if len(quote) <= 4:
                new_quote = ""
                test = ""
                for w in quote:
                    new_quote += "\n" + w
                    test += "M\n"
                quote_font_hight.text = test  # Odd things happen without this
                glyph_box = quote_font_hight.bounding_box
                quote_label.text = ""  # Odd things happen without this
                quote_label.text = new_quote

        except MemoryError:
            supervisor.reload()
        except:
            logger.warning("Couldn't get quote, try again later.")
        finally:
            quote_json = None
            quote = None
            quote_text = None
            gc.collect()

        last_quote_check = time.monotonic()

    # Check keyboard trigger
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
                        button.selected = True

                        if i == 0:
                            logger.info("Developer Scene Selected")

                            keyboard.send(
                                Keycode.COMMAND,
                                Keycode.CONTROL,
                                Keycode.OPTION,
                                Keycode.SHIFT,
                                Keycode.FOUR,
                            )

                            break

                        elif i == 1:
                            logger.info("Web Developer Scene Selected")

                            keyboard.send(
                                Keycode.COMMAND,
                                Keycode.CONTROL,
                                Keycode.OPTION,
                                Keycode.SHIFT,
                                Keycode.ONE,
                            )

                            break
                        elif i == 2:
                            logger.info("Office Scene Selected")

                            keyboard.send(
                                Keycode.COMMAND,
                                Keycode.CONTROL,
                                Keycode.OPTION,
                                Keycode.SHIFT,
                                Keycode.TWO,
                            )

                            break

                # clear list for next detection
                point_list = []

                # sleep to avoid pressing two buttons on accident
                time.sleep(0.2)

                # change the button state again
                button.selected = False
