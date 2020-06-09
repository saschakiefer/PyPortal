import displayio
import gc


class StatusIconController:
    def __init__(self, debug=False):
        """Constructor

        Keyword Arguments:
            debug {bool} -- Show debug output (default: {False})
        """
        self._debug_mode = debug

        self.icons = {
            "dsl_status": {
                "icon_path_active": "/images/linked.bmp",
                "icon_path_inactive": "/images/unlinked.bmp",
                "x": 5,
                "y": 5,
                "scale": 1,
                "is_active": False,
                "object": None,
            },
            "wifi_status": {
                "icon_path_active": "/images/wifi_on.bmp",
                "icon_path_inactive": "/images/wifi_off.bmp",
                "x": 52,
                "y": 5,
                "scale": 1,
                "is_active": False,
                "object": None,
            },
            "keyboard_status": {
                "icon_path_active": "/images/keyboard_on.bmp",
                "icon_path_inactive": "/images/keyboard_off.bmp",
                "x": 99,
                "y": 5,
                "scale": 1,
                "is_active": False,
                "object": None,
            },
        }

        self.log("Creating Status Icon Objects")
        self._create_group_for_icon(self.icons["dsl_status"])
        self._create_group_for_icon(self.icons["wifi_status"])
        self._create_group_for_icon(self.icons["keyboard_status"])

    def log(self, text):
        """Simple logger

        Arguments:
            text {string} -- Display text
        """
        if self._debug_mode:
            print(text)

    def get_icons(self):
        """Return a list of group objects containing the icon image
        for the main display group

        Returns:
            list -- list with group objects
        """
        return [icon[1]["object"] for icon in self.icons.items()]

    def set_dsl_status(self, active=False):
        """Set the status of the DSL link icon

        Keyword Arguments:
            active {bool} -- True=active, False=inactive (default: {False})
        """
        self.log("Setting DSL status to " + str(active))
        self._set_status(self.icons["dsl_status"], active)

    def set_wifi_status(self, active=False):
        """Set the status of the WIFI icon

        Keyword Arguments:
            active {bool} -- True=active, False=inactive (default: {False})
        """
        self.log("Setting wifi status to " + str(active))
        self._set_status(self.icons["wifi_status"], active)

    def set_keyboard_status(self, active=False):
        """Set the status of the keyboard icon

        Keyword Arguments:
            active {bool} -- True=active, False=inactive (default: {False})
        """
        self.log("Setting keyboard status to " + str(active))
        self._set_status(self.icons["keyboard_status"], active)

    def _set_status(self, icon, active):
        """Generic method to set the status of an icon object. The status
        is only changed (i.e. the status image is loaded), when the actual
        status is differnet than the one to be set

        Arguments:
            icon {dict} -- icon object from the icon dictionary
            active {[type]} -- True=active, False=inactive
        """
        if icon["is_active"] == active:
            self.log("Icon Status did not change. Nothing to do.")
            return  # nothing to do

        if active:
            self._set_image(icon["object"], icon["icon_path_active"])
        else:
            self._set_image(icon["object"], icon["icon_path_inactive"])

        icon["is_active"] = active
        self.log(f"is_active status changed to {active}")

    def _create_group_for_icon(self, icon):
        """Create a display group object from an icon dictionary object
        Chnages are done inplace to the "object" atrribute.

        Arguments:
            icon {dict} -- icon object from the icon dictionary
        """
        group = displayio.Group(max_size=1)
        group.x = icon["x"]
        group.y = icon["y"]
        group.scale = icon["scale"]

        self._set_image(group, icon["icon_path_inactive"])

        icon["object"] = group

    def _set_image(self, group, filename):
        """Generic method to chnage the icon based on the image loaded
        from the filename.

        Arguments:
            group {group} -- display group object to be modified
            filename {str} -- file path+name
        """
        if group:
            group.pop()

        if not filename:
            return  # we're done, no icon desired

        image_file = open(filename, "rb")
        image = displayio.OnDiskBitmap(image_file)
        self.log(filename + " loaded")

        try:
            image_sprite = displayio.TileGrid(
                image, pixel_shader=displayio.ColorConverter()
            )
        except TypeError:
            image_sprite = displayio.TileGrid(
                image, pixel_shader=displayio.ColorConverter(), position=(0, 0)
            )

        group.append(image_sprite)
