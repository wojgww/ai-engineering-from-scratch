"""Finite process emitting real stdout/stderr and optionally reading stdin.

See README.md: inspect /proc/PID/fd and redirect a live process using GDB.
Writes through os.write to avoid confusing Python buffering with fd changes.
Source: https://man7.org/linux/man-pages/man2/dup2.2.html.
"""

import argparse
import math
import os
import select
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticks", type=int, default=300)
    parser.add_argument("--interval", type=float, default=1)
    parser.add_argument("--read-input", action="store_true")
    args = parser.parse_args()
    if args.ticks < 1 or not math.isfinite(args.interval) or args.interval < 0:
        parser.error("ticks >= 1 and finite interval >= 0 required")
    for tick in range(1, args.ticks + 1):
        os.write(1, f"pid={os.getpid()} stdout tick={tick}\n".encode())
        os.write(2, f"pid={os.getpid()} stderr tick={tick}\n".encode())
        if args.read_input and select.select([0], [], [], 0)[0]:
            chunk = os.read(0, 64)
            if chunk:
                os.write(1, b"stdin: " + repr(chunk).encode() + b"\n")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
