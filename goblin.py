#!/usr/bin/env python3
import argparse
import sys

def up(args):
    print(f"Running 'up' command with args: {args}")

def down(args):
    print(f"Running 'down' command with args: {args}")

def install(args):
    print(f"Running 'install' command with args: {args}")
    import os
    import stat

    # Create a shell script named 'goblin'
    script_content = '#!/bin/bash\npython3 ' + os.path.abspath(__file__) + ' "$@"'
    with open('/usr/local/bin/goblin', 'w') as f:
        f.write(script_content)

    # Make the script executable
    os.chmod('/usr/local/bin/goblin', os.stat('/usr/local/bin/goblin').st_mode | stat.S_IEXEC)

    print("Installation complete. You can now use 'goblin' command.")


def main():
    parser = argparse.ArgumentParser(description="Goblin CLI")
    parser.add_argument("command", help="Command to execute (e.g., up, down)")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Additional arguments")

    args = parser.parse_args()

    command = args.command.lower()
    if command == "up":
        up(args.args)
    elif command == "down":
        down(args.args)
    elif command == "install":
        install(args.args)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()



