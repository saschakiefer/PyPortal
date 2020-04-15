from adafruit_bitmap_font import bitmap_font
from adafruit_button import Button


class ButtonController:
    BUTTON_PADDING = 8

    def __init__(self, screen_width=480, screen_height=320):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.button_width = int(screen_width / 3)
        self.button_height = int(screen_height / 4.5)

        self.button_y = (
            screen_height - self.button_height + ButtonController.BUTTON_PADDING
        )

        self.font = bitmap_font.load_font("/fonts/Helvetica-Bold-16.bdf")
        self.font.load_glyphs(
            b"abcdefghjiklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890- ()"
        )

        # Initialize Buttons
        self.buttons = []
        self.buttons.append(self._create_button("Developer\n   Scene"))
        self.buttons.append(self._create_button("Web Developer\n       Scene"))
        self.buttons.append(self._create_button("Office\nScene"))

    def _create_button(self, label):
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
        return self.buttons
