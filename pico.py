"""Code to run on Orpheus Pico."""

from math import floor
from random import choice, randint, random, uniform
from time import monotonic, sleep

import board
import neopixel
import usb_cdc
from adafruit_itertools import cycle
from adafruit_led_animation import color
from adafruit_led_animation.animation.chase import Chase
from adafruit_led_animation.animation.comet import Comet
from adafruit_led_animation.animation.pulse import Pulse
from adafruit_led_animation.animation.rainbowcomet import RainbowComet
from adafruit_led_animation.animation.rainbowsparkle import RainbowSparkle
from adafruit_led_animation.animation.SparklePulse import SparklePulse
from adafruit_led_animation.sequence import AnimationSequence
from rainbowio import colorwheel

console = usb_cdc.data
num_pixels = 32
pixels = neopixel.NeoPixel(board.GP0, num_pixels, brightness=0.1, auto_write=False)


def read_console(timeout: int | None) -> str | None:
    """Read a line from the console, with a timeout."""
    console.timeout = timeout
    readline = console.readline().decode("utf-8").strip()
    if readline:
        print("Received:", readline)
        return readline


def sleep_with_interrupt(seconds: int) -> bool:
    """Sleep for a specified time, but return when a press is received."""
    start = monotonic()
    while monotonic() - start < seconds:
        readline = read_console(0)
        if not readline:
            continue
        print("Received:", readline)
        if readline != "press":
            continue
        return True
    return False


def rainbow_cycle(wait: float, segments: int):
    """Cycle through the rainbow."""
    for j in range(255):
        for i in range(num_pixels):
            rc_index = (i * 256 // (num_pixels // segments)) + j
            pixels[i] = colorwheel(rc_index & 255)
        pixels.show()
        sleep(wait)


def swoosh(swoosh_color: tuple[int, int, int]) -> None:
    """Show an error pattern."""
    for i in range(num_pixels):
        pixels[i] = swoosh_color
        pixels.show()
        sleep(1 / 32)
    for i in range(num_pixels):
        pixels[i] = color.BLACK
        pixels.show()
        sleep(1 / 32)
    pixels.fill(color.BLACK)
    pixels.show()


def show_score(score: int, swoosh_color: tuple[int, int, int]) -> None:
    """Show a score."""
    score = min(score, num_pixels - 1)
    for i in range(score):
        pixels[i] = swoosh_color
        pixels.show()
        sleep(1 / 30)
    sleep(2)
    for i in range(score, 0, -1):
        pixels[i] = color.BLACK
        pixels.show()
        sleep(1 / 30)
    pixels.fill(color.BLACK)
    pixels.show()


def reaction_test():
    """Run the reaction test."""
    print("Press enter to start")
    read_console(None)
    print("Starting")
    for i in range(18, 13, -1):
        pixels[i] = color.RED
        pixels.show()
        result = sleep_with_interrupt(1)
        if result:
            print("Jump start!")
            swoosh(color.RED)
            return
    result = sleep_with_interrupt(uniform(0.2, 3))
    if result:
        print("Jump start!")
        swoosh(color.RED)
        return
    pixels.fill(color.BLACK)
    pixels.show()
    start_time = monotonic()
    result = read_console(5)
    if result:
        end_time = monotonic()
        reaction_time = end_time - start_time
        print(f"Your reaction time is: {round(reaction_time * 1000)} ms")
        show_score(round(reaction_time * 100), color.ORANGE)
    else:
        print("You took too long to press!")
        swoosh(color.RED)


def tornado_level(speed: float, target_colors: list[tuple[int, int, int]]) -> bool:
    """Press the button when the cursor hits the target."""
    target = randint(3, num_pixels - 3)
    pixels[target] = target_colors[0]
    pixels[target - 1] = target_colors[1]
    pixels[target + 1] = target_colors[1]
    pixels[target + 2] = target_colors[2]
    pixels[target - 2] = target_colors[2]
    pixels.show()

    cursor = 0

    while True:
        pixels[cursor - 1] = color.BLACK
        pixels[target] = target_colors[0]
        pixels[target - 1] = target_colors[1]
        pixels[target + 1] = target_colors[1]
        pixels[target + 2] = target_colors[2]
        pixels[target - 2] = target_colors[2]
        pixels[cursor] = color.WHITE
        pixels.show()
        result = sleep_with_interrupt(speed)
        if result:
            break
        cursor += 1
        cursor %= num_pixels
    print(cursor, target)
    diff = abs(cursor - target)
    sleep(1)
    if diff == 0:
        print("Perfect!")
        swoosh(target_colors[0])
    elif diff == 1:
        print("Close!")
        swoosh(target_colors[1])
    elif diff == 2:
        print("Not bad!")
        swoosh(target_colors[2])
    else:
        print("Too slow!")
        swoosh(color.RED)
    return True if diff <= 2 else False


def tornado_game():
    """Play tornado at increasing speeds until the game is over."""
    level_color_sequence = [
        [color.GREEN, color.TEAL, color.BLUE],
        [color.BLUE, color.PURPLE, color.PINK],
        [color.YELLOW, color.ORANGE, color.RED],
    ]
    level_colors = cycle(level_color_sequence)
    print("Press enter to start")
    read_console(None)
    print("Starting")
    level = 1
    for level_color in level_colors:
        result = tornado_level(1 / (level * 5), level_color)
        if not result:
            break
        level += 1

    # Pulse 3 times
    for _ in range(3):
        for i in range(0, 255, 2):
            pixels.fill((0, i, 0))
            pixels.show()
        for i in range(255, 0, -2):
            pixels.fill((0, i, 0))
            pixels.show()

    # Show final level
    show_score(level, color.ORANGE)


def pixel_chase():
    """Pac-Man but on a ring."""
    print("Press enter to start")
    read_console(None)
    print("Starting")
    bad_guy = 16.0
    bad_guy_velocity = 0.0
    cookie = 24
    player = 0
    level = 1
    direction = True

    while True:
        pixels.fill(color.BLACK)
        pixels[cookie] = color.YELLOW
        pixels[player] = color.CYAN
        pixels[floor(bad_guy)] = color.RED
        pixels.show()

        if player == floor(bad_guy):
            break
        if player == cookie:
            level += 1
            cookie = randint(0, num_pixels - 1)

        player += (1 if direction else -1) * 1
        player %= num_pixels
        bad_guy += bad_guy_velocity
        bad_guy %= num_pixels
        bad_guy_velocity += (random() - 0.5) / 3
        bad_guy_velocity = max(-0.5, bad_guy_velocity)
        bad_guy_velocity = min(0.5, bad_guy_velocity)

        result = sleep_with_interrupt(1 / (level + 5))
        if result:
            direction = not direction

    # Game over
    swoosh(color.RED)
    show_score(level, color.ORANGE)


chase = Chase(pixels, speed=0.05, color=choice(color.RAINBOW), size=3, spacing=5)
comet = Comet(pixels, speed=0.05, color=choice(color.RAINBOW), tail_length=16, ring=True)
pulse = Pulse(pixels, speed=0.05, color=choice(color.RAINBOW), period=1)
rainbow_comet = RainbowComet(pixels, speed=0.05, tail_length=16, ring=True)
rainbow_sparkle = RainbowSparkle(pixels, speed=0.05, num_sparkles=3)
sparkle_pulse = SparklePulse(pixels, speed=0.05, period=3, color=choice(color.RAINBOW))

animations = AnimationSequence(
    chase,
    comet,
    pulse,
    rainbow_comet,
    rainbow_sparkle,
    sparkle_pulse,
    advance_interval=10,
    auto_clear=True,
    random_order=True,
)


if __name__ == "__main__":
    pixels.fill(color.BLACK)
    pixels.show()

    while True:
        animations.animate()

        # Check if a game was chosen
        read = read_console(0)
        if not read:
            continue

        # Start a game
        pixels.fill(color.BLACK)
        pixels.show()
        read_split = read.split(" ")
        if read_split[0] != "game":
            continue
        if read_split[1] == "0":
            reaction_test()
        elif read_split[1] == "1":
            tornado_game()
        elif read_split[1] == "2":
            pixel_chase()

        # Game ended
        console.write("end\n")
        sleep(1)
