from time import sleep

from serial import Serial


def main():
    with Serial("/dev/ttyACM1", timeout=1) as ser:
        print(f"Connected to: {ser.name}")
        while True:
            line = input("Press Enter").strip()
            if line == "0":
                ser.write(b"game 0\n")
            elif line == "1":
                ser.write(b"game 1\n")
            elif line == "2":
                ser.write(b"game 2\n")
            else:
                ser.write(b"press\n")


if __name__ == "__main__":
    main()
