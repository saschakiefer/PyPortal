import time

from adafruit_bitmap_font import bitmap_font
from adafruit_button import Button
from adafruit_hid.keycode import Keycode


class ButtonController:
    BUTTON_PADDING = 8

    def __init__(self, keyboard, screen_width=480, screen_height=320, debug=False):
        """Constructor

        Arguments:
            keyboard {adafruit_hid.keyboard.Keyboard} -- Keyboard instance

        Keyword Arguments:
            screen_width {int} -- Display width (default: {480})
            screen_height {int} -- Display hight (default: {320})
            debug {bool} -- Show debug information (default: {False})
        """
        self._debug_mode = debug
        self.keyboard = keyboard

        # Do some pixel math
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.button_width = int(screen_width / 3)
        self.button_height = int(screen_height / 4.5)

        self.button_y = (
            screen_height - self.button_height + ButtonController.BUTTON_PADDING
        )

        # Initialize font
        self.font = bitmap_font.load_font("/fonts/Helvetica-Bold-16.bdf")
        self.font.load_glyphs(
            b"abcdefghjiklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890- ()"
        )
        self.log("Button Font Initialized")

        self.buttons = []

        # Initialize Buttons with a Bitton Object and the related
        # keyboard shortcut to be sent to the host
        self.buttons.append(
            (
                self._create_button("Developer\n   Scene"),
                (
                    Keycode.COMMAND,
                    Keycode.CONTROL,
                    Keycode.OPTION,
                    Keycode.SHIFT,
                    Keycode.FOUR,
                ),
            )
        )

        self.buttons.append(
            (
                self._create_button("Web Developer\n       Scene"),
                (
                    Keycode.COMMAND,
                    Keycode.CONTROL,
                    Keycode.OPTION,
                    Keycode.SHIFT,
                    Keycode.ONE,
                ),
            )
        )

        self.buttons.append(
            (
                self._create_button("Office\nScene"),
                (
                    Keycode.COMMAND,
                    Keycode.CONTROL,
                    Keycode.OPTION,
                    Keycode.SHIFT,
                    Keycode.TWO,
                ),
            )
        )

        self.log("Buttons created")

    def log(self, text):
        """Simple logger

        Arguments:
            text {string} -- Display text
        """
        if self._debug_mode:
            print(text)

    def _create_button(self, label):
        """Create a button instance with automatic calculation of the
        correct position and the button size.

        Arguments:
            label {string} -- Button label (can contain \n)

        Returns:
            adafruit_button.Button -- Button instance
        """
        button_x = (
            len(self.buttons) * self.button_width + ButtonController.BUTTON_PADDING
        )

        return Button(
            x=button_x,
            y=self.button_y,
            width=self.button_width - 2 * ButtonController.BUTTON_PADDING,
            height=self.button_height - 2 * ButtonController.BUTTON_PADDING,
            label=label,
            label_font=self.font,
            label_color=0xD7C6E0,
            fill_color=0x601D83,
            selected_fill=0xD7C6E0,
            selected_label=0x601D83,
            style=Button.ROUNDRECT,
        )

    def get_buttons(self):
        """Generate a list of the Button objects

        Returns:
            list -- list with button objects
        """
        button_list = []
        [button_list.append(button[0]) for button in self.buttons]

        return button_list

    def check_and_send_shortcut_to_host(self, x, y):
        """Check if any button contains the coordinates that where touched.
        If so send the keyboard shortcut belonging to the button (see
        constructor) to the host.

        Arguments:
            x {int} -- x-coordinate of the touch
            y {int} -- y-coordinate of the touch
        """
        for button in self.buttons:
            if button[0].contains((x, y, 65000)):
                self.log(f"Button {button} pressed")

                button[0].selected = True

                self.keyboard.send(*button[1])

                # sleep to avoid pressing two buttons on accident
                time.sleep(0.2)

                # change the button state again
                button[0].selected = False

                break
