import gc
import re
from secrets import secrets

import adafruit_esp32spi.adafruit_esp32spi_socket as socket
import adafruit_requests as requests
import supervisor


class FritzboxStatus:
    """ Encapsulate the FritBox status calls via the upnp protocol"""

    # -------------------- Static Values for the SOAP Messages ---------
    fritz_url_base = f"http://{secrets['access_point_ip']}:{secrets['access_point_port']}/igdupnp/control/"
    fritz_soap_action_base = "urn:schemas-upnp-org:service:"

    fritz_soap_connection = (
        '<?xml version="1.0" encoding="utf-8"?><s:Envelope s:encodingStyle='
        '"http://schemas.xmlsoap.org/soap/encoding/"xmlns:s='
        '"http://schemas.xmlsoap.org/soap/envelope/"><s:Body><u:GetStatusInfo '
        'xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1">'
        "</u:GetStatusInfo></s:Body></s:Envelope>"
    )

    fritz_soap_link_status = (
        '<?xml version="1.0" encoding="utf-8"?><s:Envelope s:encodingStyle='
        '"http://schemas.xmlsoap.org/soap/encoding/"xmlns:s='
        '"http://schemas.xmlsoap.org/soap/envelope/"><s:Body>'
        "<u:GetCommonLinkProperties "
        'xmlns:u="urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1">'
        "</u:GetCommonLinkProperties></s:Body></s:Envelope>"
    )

    fritz_headers = {
        "charset": "utf-8",
        "content-type": "text/xml",
        "soapaction": None,
    }

    def __init__(self, pyportal, debug=False):
        self._debug_mode = debug
        self._pyportal = pyportal

        # Initialize requests object with esp, provided to the pyportal
        requests.set_socket(socket, pyportal._esp)

    def log(self, text):
        """Simple logger

        Parameters:
        text -- text to log
        """
        if self._debug_mode:
            print(text)

    def get_dsl_status(self):
        """Build the DSL status as a dictionary with 2 elements:
        linked: link status
        connected: connection status
        Values are either True or False
        """
        return {
            "linked": self.is_linked(),
            "connected": self.is_connected(),
        }

    def is_connected(self):
        """Check if the FritzBox is connected to the internet.
        Returns True or False
        """
        status = self._do_call(
            url_suffix="WANIPConn1",
            soapaction=FritzboxStatus.fritz_soap_action_base
            + "WANIPConnection:1#GetStatusInfo",
            body=FritzboxStatus.fritz_soap_connection,
        )

        return status == "Connected"

    def is_linked(self):
        """Check if the FritzBox is linked with the service provider.
        Returns True or False
        """
        status = self._do_call(
            url_suffix="WANCommonIFC1",
            soapaction=FritzboxStatus.fritz_soap_action_base
            + "WANCommonInterfaceConfig:1#GetCommonLinkProperties",
            body=FritzboxStatus.fritz_soap_link_status,
        )

        return status == "Up"

    def _do_call(self, url_suffix=None, soapaction=None, body=None):
        """Main method performaing the SOAP action. Returns the raw status
        text.

        Parameters:
        url_suffix -- command suffix for the url
        soapaction -- SOAP header fields
        body -- SOAP body
        """
        gc.collect()

        url = f"{FritzboxStatus.fritz_url_base}{url_suffix}"
        headers = FritzboxStatus.fritz_headers.copy()
        headers["soapaction"] = soapaction

        try:
            gc.collect()
            response = requests.post(url, data=body, headers=headers, timeout=2)
            gc.collect()
        except MemoryError:
            supervisor.reload()
        except:
            self.log("Couldn't get DSL status, will try again later.")
            return "Unknown"  # We just ignore this and wait for the next request

        # Finde the raw status based on the respective XML Tags
        if url_suffix == "WANIPConn1":
            regex = r"<NewConnectionStatus>(.*)<\/NewConnectionStatus>"
        else:
            regex = r"<NewPhysicalLinkStatus>(.*)<\/NewPhysicalLinkStatus>"

        matches = re.search(regex, response.text)
        status = matches.groups()[0]

        self.log(f"Received DSL state for {url_suffix}: {status}")

        # Clean Up
        response = None
        regex = None
        matches = None
        gc.collect()

        return status
