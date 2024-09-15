import socket
import argparse
import os


def get_args():
    parser = argparse.ArgumentParser(
        description="<command description>",
        usage="upload [-h] [-v | -q] [-H ADDR] [-p PORT] [-s FILEPATH] [-n FILENAME]"
    )
    parser.add_argument('-v', '--verbose', action='store_true', help="increase output verbosity")
    parser.add_argument('-q', '--quiet', action='store_true', help="decrease output verbosity")
    parser.add_argument('-H', '--host', type=str, required=True, help="server IP address")
    parser.add_argument('-p', '--port', type=int, required=True, help="server port")
    parser.add_argument('-s', '--src', type=str, required=True, help="source file path")
    parser.add_argument('-n', '--name', type=str, required=True, help="file name")
    return parser.parse_args()


def get_file(src: str):
    try:
        if os.path.isfile(src):
            with open(src, 'r') as file:
                data = file.read
        else:
             print(f"Invalid source: {src}")
    except Exception as e:
        print(f"Error: {e}")                


def main():
    args = get_args()
    get_file(args.src)


if __name__ == "__main__":
      main()