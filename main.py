"""Pyglet interface that sends keypresses to the Pico."""

from datetime import datetime
from os import makedirs

from cv2 import COLOR_BGR2RGB, VideoCapture, cvtColor
from PIL import Image as PILImage
from pyglet.app import run
from pyglet.clock import schedule_interval
from pyglet.image import ImageData
from pyglet.media.exceptions import MediaException
from pyglet.resource import image, media
from pyglet.text import Label, Weight
from pyglet.window import Window, key
from pyzbar.pyzbar import ZBarSymbol, decode
from serial import Serial

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
    "",
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
state = {"game_id": -1, "image_pyglet": None}
capture = VideoCapture(0)


def start_game(game_id: int) -> None:
    """Start a game."""
    print("STARTING GAME", game_id)
    state["game_id"] = game_id
    game_label.text = f"Game {game_id}: {GAME_NAMES[game_id]}"
    instructions_label.text = "Press the button to start"
    command = f"game {game_id}\n"
    serial.write(command.encode("utf-8"))
    try:
        beep.play()
    except MediaException:
        pass


def end_game() -> None:
    """End the game."""
    print("ENDING GAME")
    state["game_id"] = -1
    game_label.text = ""
    instructions_label.text = "Scan a floppy disk to choose a game"
    read_camera(0)


@window.event
def on_key_press(symbol: int, modifiers: int) -> None:
    """Handle key presses."""
    if symbol in (key.W, key.A, key.S, key.D, key.F, key.G):
        print("button pressed")
        serial.write("press\n".encode("utf-8"))
        if state["game_id"] != -1:
            instructions_label.text = ""
    elif symbol in (key._0, key._1, key._2):
        start_game(symbol - key._0)
    elif symbol == key.M:
        end_game()
    else:
        return


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
    if serial.in_waiting > 0:
        line = serial.readline().decode("utf-8").strip()
        print(line)
        if line == "end":
            end_game()


def read_camera(dt: float) -> None:
    """Update the camera feed."""
    ret, frame = capture.read()
    if frame is None or state["game_id"] != -1:
        return

    image_rgb = cvtColor(frame, COLOR_BGR2RGB)
    height, width, _ = image_rgb.shape
    state["image_pyglet"] = ImageData(width, height, "RGB", image_rgb.tobytes(), pitch=width * -3)
    state["image_pyglet"].anchor_x = width // 2
    state["image_pyglet"].anchor_y = height // 2
    pil_image = PILImage.fromarray(image_rgb)
    scanned = decode(pil_image, symbols=[ZBarSymbol.QRCODE])
    if not scanned:
        return
    scanned_text = scanned[0].data.decode("utf-8")
    if not scanned_text.startswith("RIICC Neopixel Game"):
        return
    game_id = int(scanned_text[-1])
    if game_id < 0 or game_id > 2:
        print("Invalid game ID")
        return
    # Take a photo haha
    current_iso_dt = datetime.now().isoformat(timespec="seconds")
    makedirs("dist", exist_ok=True)
    pil_image.save(f"dist/{current_iso_dt}.png")
    start_game(game_id)


if __name__ == "__main__":
    print(f"Connected to: {serial.name}")

    schedule_interval(read_camera, 1 / 30)
    run()
