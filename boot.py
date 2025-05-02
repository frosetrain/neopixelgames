"""Initialize the Pico."""

import usb_cdc

usb_cdc.enable(console=True, data=True)
