"""Pyglet interface that sends keypresses to the Pico."""

from cv2 import COLOR_BGR2RGB, VideoCapture, cvtColor
from PIL import Image as PILImage
from pyglet.app import run
from pyglet.clock import schedule_interval
from pyglet.image import ImageData
from pyglet.media.exceptions import MediaException
from pyglet.resource import image, media
from pyglet.text import Label, Weight
from pyglet.window import Window, key
from serial import Serial
from zxing import BarCodeReader

GAME_NAMES = ["Reaction Test", "Tornado", "Pixel Chase"]

window = Window(fullscreen=True)
title = Label(
    "Neopixel Games",
    font_name="Mona Sans",
    font_size=48,
    weight=Weight.BOLD,
    x=window.width // 2,
    y=window.height - 320,
    anchor_x="center",
    anchor_y="center",
)
game_label = Label(
    "Game -1: india delta kilo",
    font_name="Mona Sans",
    font_size=36,
    x=window.width // 2,
    y=window.height // 2 - 100,
    anchor_x="center",
    anchor_y="center",
)
instructions_label = Label(
    "Scan a floppy disk to choose a game",
    font_name="Mona Sans",
    font_size=24,
    x=window.width // 2,
    y=200,
    anchor_x="center",
    anchor_y="center",
)
logo = image("riicc-ondark.svg")
logo.anchor_x = logo.width // 2
logo.anchor_y = logo.height // 2
beep = media("beep.wav", streaming=False)

serial = Serial("/dev/ttyACM1", timeout=1)
zxing_reader = BarCodeReader()
state = {"game_id": -1, "image_pyglet": None}


@window.event
def on_key_press(symbol: int, modifiers: int) -> None:
    """Handle key presses."""
    if symbol in (key.W, key.A, key.S, key.D, key.F, key.G):
        command = "press\n"
    elif symbol in (key._0, key._1, key._2):
        command = f"game {symbol - key._0}\n"
        try:
            beep.play()
        except MediaException:
            pass
    else:
        return
    print(command)
    serial.write(command.encode("utf-8"))


@window.event
def on_draw() -> None:
    """Draw the window."""
    window.clear()
    title.draw()
    logo.blit(window.width // 2, window.height - 150)
    if state["image_pyglet"] is not None and state["game_id"] == -1:
        state["image_pyglet"].blit(window.width // 2, window.height // 2 - 100)
    if state["game_id"] != -1:
        game_label.draw()
    instructions_label.draw()


def scan_aztec(dt: float) -> None:
    """Update the camera feed."""
    print(dt)
    if state["game_id"] != -1:
        return
    ret, image_cv = VideoCapture(0).read()
    image_rgb = cvtColor(image_cv, COLOR_BGR2RGB)
    height, width, _ = image_rgb.shape
    state["image_pyglet"] = ImageData(width, height, "RGB", image_rgb.tobytes(), pitch=width * -3)
    state["image_pyglet"].anchor_x = width // 2
    state["image_pyglet"].anchor_y = height // 2
    pil_image = PILImage.fromarray(image_rgb)
    scanned = zxing_reader.decode(pil_image)
    print(scanned)
    if not scanned.parsed:
        return
    if not scanned.parsed.startswith("RIICC Neopixel Game"):
        return
    game_id = int(scanned.parsed[-1])
    if game_id < 0 or game_id > 2:
        print("Invalid game ID")
        return
    print("STARTING GAME", scanned.parsed)
    state["game_id"] = int(scanned.parsed[-1])
    game_label.text = f"Game {game_id}: {GAME_NAMES[game_id]}"
    instructions_label.text = "Press the button to start"
    command = f"game {game_id}\n"
    serial.write(command.encode("utf-8"))
    try:
        beep.play()
    except MediaException:
        pass


if __name__ == "__main__":
    print(f"Connected to: {serial.name}")
    schedule_interval(scan_aztec, 0.5)
    run()
