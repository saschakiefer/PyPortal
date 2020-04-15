import gc
import time
from secrets import secrets

import adafruit_esp32spi.adafruit_esp32spi_socket as socket
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
from fritz_box import FritzboxStatus
from digitalio import DigitalInOut
from button_controller import ButtonController

# -------------------- Initialize some static values -------------------
DEBUG_MODE = True

SCREEN_WIDTH = 480
SCREEN_HEIGHT = 320

esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
esp32_gpio0 = DigitalInOut(board.ESP_GPIO0)

# -------------------- Some helper functions ---------------------------
def log(text):
    if DEBUG_MODE:
        print(text)


# -------------------- Initialize the board ----------------------------
# Initialize WIFI microncontroller
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(
    spi, esp32_cs, esp32_ready, esp32_reset, esp32_gpio0
)
log("Wifi controller initialized")

# Connect to access point
log("Connecting to access point...")
while not esp.is_connected:
    try:
        esp.connect_AP(secrets["ssid"], secrets["password"])
    except RuntimeError as e:
        log("could not connect to AP, retrying: ", e)
        continue

log("Connected to: " + str(esp.ssid, "utf-8"))

# PyPortal setup
pyportal = PyPortal(
    esp=esp,
    external_spi=spi,
    url="https://www.adafruit.com/api/quotes.php",  # Only used for the quotes
    json_path=([0, "text"], [0, "author"]),
    debug=DEBUG_MODE,
)
pyportal.set_background("/images/fractal_loading.bmp")
log("Pyportal initialized")

# Display setup
display = board.DISPLAY
display.rotation = 0
display.auto_brightness = True
log("Display initialized")

# Touchscreen setup
touch_screen = adafruit_touchscreen.Touchscreen(
    board.TOUCH_XL,
    board.TOUCH_XR,
    board.TOUCH_YD,
    board.TOUCH_YU,
    calibration=((6272, 60207), (7692, 56691)),
    size=(SCREEN_WIDTH, SCREEN_HEIGHT),
)
log("Touchscreen initialized")

# Keyboard setup
try:
    # Initialize with the available USB devices. The constructur picks the
    # correct one from the list
    keyboard = Keyboard(usb_hid.devices)
    keyboard_active = True
    log("Keyboard activated")
except OSError:
    keyboard_active = False
    log("No keyboard found")


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

# # Set the font and preload letters
# font = bitmap_font.load_font("/fonts/Helvetica-Bold-16.bdf")
# font.load_glyphs(b"abcdefghjiklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890- ()")

# # Buttons
# BUTTON_HEIGHT = int(SCREEN_HEIGHT / 4.5)
# BUTTON_WIDTH = int(SCREEN_WIDTH / 3)
# BUTTON_Y = int(SCREEN_HEIGHT - BUTTON_HEIGHT)
# BUTTON_PADDING = 8

# buttons = []

# button_action_1 = Button(
#     x=0 + BUTTON_PADDING,
#     y=BUTTON_Y + BUTTON_PADDING,
#     width=BUTTON_WIDTH - 2 * BUTTON_PADDING,
#     height=BUTTON_HEIGHT - 2 * BUTTON_PADDING,
#     label="Developer\n   Scene",
#     label_font=font,
#     label_color=0xD7C6E0,
#     fill_color=0x601D83,
#     selected_fill=0xD7C6E0,
#     selected_label=0x601D83,
#     style=Button.ROUNDRECT,
# )

# buttons.append(button_action_1)

# button_action_2 = Button(
#     x=0 + BUTTON_WIDTH + BUTTON_PADDING,
#     y=BUTTON_Y + BUTTON_PADDING,
#     width=BUTTON_WIDTH - 2 * BUTTON_PADDING,
#     height=BUTTON_HEIGHT - 2 * BUTTON_PADDING,
#     label="Web Developer\n       Scene",
#     label_font=font,
#     label_color=0xD7C6E0,
#     fill_color=0x601D83,
#     selected_fill=0xD7C6E0,
#     selected_label=0x601D83,
#     style=Button.ROUNDRECT,
# )

# buttons.append(button_action_2)

# button_action_3 = Button(
#     x=0 + BUTTON_WIDTH + BUTTON_WIDTH + BUTTON_PADDING,
#     y=BUTTON_Y + BUTTON_PADDING,
#     width=BUTTON_WIDTH - 2 * BUTTON_PADDING,
#     height=BUTTON_HEIGHT - 2 * BUTTON_PADDING,
#     label="Office\nScene",
#     label_font=font,
#     label_color=0xD7C6E0,
#     fill_color=0x601D83,
#     selected_fill=0xD7C6E0,
#     selected_label=0x601D83,
#     style=Button.ROUNDRECT,
# )

# buttons.append(button_action_3)

button_controller = ButtonController(
    screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT
)
buttons = button_controller.get_buttons()
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
quote_font_hight = Label(quote_font, text="M", color=0x03AD31, max_glyphs=10)

quote_label = Label(quote_font, text="Loading Quote...", color=0xFED73F, max_glyphs=500)
quote_label.x = 10
quote_label.y = 120
main_group.append(quote_label)

# -------------------- Setup display elements --------------------------
fritz_status = FritzboxStatus(pyportal, debug=DEBUG_MODE)

# ------------- Initialize some helpers for the main loop --------------
# We collect 3 points to simulate a debounced button press. In addition
# the first touch point usually is not correct, so we discard that
point_list = []

# Initialize the dsl check timer
current_dsl_check_period = 0  # ensure, that it immidiately starts
last_dsl_check = time.monotonic()

# Initialize the quote check timer
last_quote_check = time.monotonic() - 3601

# -------------------- Start the main loop -----------------------------
board.DISPLAY.show(main_group)

log("Start event loop")

while True:
    # Check dsl status
    if last_dsl_check + current_dsl_check_period < time.monotonic():
        """ Only check the dsl every 30 seconds. The check time is decreased
        to two seconds as soon as dsl is gone and increased back to
        30 seconds when it's back
        """
        dsl_status = fritz_status.get_dsl_status()

        if dsl_status["connected"]:
            set_image(linked_group, "/images/linked.bmp")
            current_dsl_check_period = 15
        else:
            set_image(linked_group, "/images/unlinked.bmp")
            current_dsl_check_period = 2

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
            log("Couldn't get quote, try again later.")
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
                log("(" + str(x) + "/" + str(y) + ") pressed")

                pyportal.play_file(soundBeep)

                for i, button in enumerate(buttons):
                    if button.contains((x, y, 65000)):
                        log(f"Button {button} pressed")
                        button.selected = True

                        if i == 0:
                            log("Developer Scene Selected")

                            keyboard.send(
                                Keycode.COMMAND,
                                Keycode.CONTROL,
                                Keycode.OPTION,
                                Keycode.SHIFT,
                                Keycode.FOUR,
                            )

                            break

                        elif i == 1:
                            log("Web Developer Scene Selected")

                            keyboard.send(
                                Keycode.COMMAND,
                                Keycode.CONTROL,
                                Keycode.OPTION,
                                Keycode.SHIFT,
                                Keycode.ONE,
                            )

                            break
                        elif i == 2:
                            log("Office Scene Selected")

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
