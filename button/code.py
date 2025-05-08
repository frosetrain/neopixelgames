import usb_hid
import board
import digitalio
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_debouncer import Debouncer
from time import sleep

kbd = Keyboard(usb_hid.devices)

button_pin = digitalio.DigitalInOut(board.GP0)
button_pin.direction = digitalio.Direction.INPUT
button_pin.pull = digitalio.Pull.DOWN
button = Debouncer(button_pin)

while True:
    button.update()
    print(button_pin.value)

    if button.rose:
        kbd.press(Keycode.A)
    if button.fell:
        kbd.release(Keycode.A)
