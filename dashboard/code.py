import time
import re

import adafruit_esp32spi.adafruit_esp32spi_socket as socket
import adafruit_logging as logging
import adafruit_requests as requests
import board
import busio
from adafruit_esp32spi import adafruit_esp32spi
from digitalio import DigitalInOut

esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

# Set up logging
logger = logging.getLogger("dashboard")
logger.setLevel(logging.INFO)  # change as desired

logger.info("My Multi Dasboard")

# Initialize wlan Microncontroller
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

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


class Fritbox_Status:
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

        response = requests.post(url, data=body, headers=headers, timeout=2)

        if url_suffix == "WANIPConn1":
            regex = r"<NewConnectionStatus>(.*)<\/NewConnectionStatus>"
        else:
            regex = r"<NewPhysicalLinkStatus>(.*)<\/NewPhysicalLinkStatus>"

        matches = re.search(regex, response.text)
        status = matches.groups()[0]

        logger.debug("Received state: " + status)

        return status


fritz_status = Fritbox_Status()

while True:
    logger.info(
        "Is linked: "
        + str(fritz_status.is_linked())
        + " -=- Is Connected: "
        + str(fritz_status.is_connected())
    )
    time.sleep(30)
