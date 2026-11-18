"""Entry for make.fun's news-image-20261118 bounty.

Copies assets/entry.png to the output directory as entry.png after validating
the asset. Standard library only, no network access.
"""

import argparse
import hashlib
import os
import struct
import sys
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 1048576
MAX_DIMENSION = 1024
ASSET_NAME = "entry.png"
OUTPUT_NAME = "entry.png"


def read_ihdr(data):
    """Return (width, height) from the IHDR chunk, or raise ValueError."""
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("asset is not a PNG (bad signature)")
    if len(data) < 8 + 8 + 13:
        raise ValueError("asset is truncated")

    length = struct.unpack(">I", data[8:12])[0]
    chunk_type = data[12:16]
    if chunk_type != b"IHDR":
        raise ValueError("first PNG chunk is not IHDR")
    if length != 13:
        raise ValueError("IHDR chunk has an unexpected length")

    width, height = struct.unpack(">II", data[16:24])
    return width, height


def validate(data):
    """Validate the asset bytes; raise ValueError on any problem."""
    if len(data) > MAX_BYTES:
        raise ValueError(
            "asset is %d bytes, exceeds the %d byte limit" % (len(data), MAX_BYTES)
        )
    width, height = read_ihdr(data)
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        raise ValueError(
            "asset is %dx%d, exceeds the %dx%d limit"
            % (width, height, MAX_DIMENSION, MAX_DIMENSION)
        )
    return width, height


def output_dir():
    """Return the output directory from the environment or the default."""
    return Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")


def parse_args(argv=None):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="validate the asset and print its dimensions without writing a file",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    asset_path = Path(__file__).resolve().parent / "assets" / ASSET_NAME
    try:
        data = asset_path.read_bytes()
    except OSError as exc:
        print("error: cannot read asset %s: %s" % (asset_path, exc), file=sys.stderr)
        return 1

    try:
        width, height = validate(data)
    except ValueError as exc:
        print("error: invalid asset: %s" % exc, file=sys.stderr)
        return 1

    if args.verify_only:
        print("verified %s (%dx%d, %d bytes)" % (asset_path, width, height, len(data)))
        return 0

    out_dir = output_dir()
    out_path = out_dir / OUTPUT_NAME
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(data)
    except OSError as exc:
        print("error: cannot write %s: %s" % (out_path, exc), file=sys.stderr)
        return 1

    digest = hashlib.sha256(data).hexdigest()
    print(
        "wrote %s (%dx%d, %d bytes, sha256 %s)"
        % (out_path, width, height, len(data), digest)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
