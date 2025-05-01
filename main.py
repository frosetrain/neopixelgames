from time import sleep

from serial import Serial


def main():
    with Serial("/dev/ttyACM1", timeout=1) as ser:
        print(f"Connected to: {ser.name}")
        while True:
            input("Press Enter")
            ser.write(b"press\n")


if __name__ == "__main__":
    main()
