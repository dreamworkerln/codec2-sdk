#!/usr/bin/env python3
from __future__ import annotations

import ctypes
import math
import pathlib
import sys

CODEC2_MODE_3200 = 0
EXPECTED_SAMPLES_PER_FRAME = 160
EXPECTED_BITS_PER_FRAME = 64
EXPECTED_BYTES_PER_FRAME = 8


def find_library(dist: pathlib.Path) -> pathlib.Path:
    libdir = dist / "lib"
    candidates = []
    for pattern in ("libcodec2.so", "libcodec2.so.*", "libcodec2.dylib"):
        candidates.extend(libdir.glob(pattern))
    candidates = sorted({path.resolve() for path in candidates if path.is_file()})
    if not candidates:
        raise SystemExit(f"no shared Codec2 library found under {libdir}")
    for candidate in candidates:
        if candidate.name == "libcodec2.so" or candidate.name == "libcodec2.dylib":
            return candidate
    return candidates[0]


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} DIST_DIR")
    dist = pathlib.Path(sys.argv[1]).resolve()
    library_path = find_library(dist)
    lib = ctypes.CDLL(str(library_path))

    lib.codec2_create.argtypes = [ctypes.c_int]
    lib.codec2_create.restype = ctypes.c_void_p
    lib.codec2_destroy.argtypes = [ctypes.c_void_p]
    lib.codec2_destroy.restype = None
    lib.codec2_samples_per_frame.argtypes = [ctypes.c_void_p]
    lib.codec2_samples_per_frame.restype = ctypes.c_int
    lib.codec2_bits_per_frame.argtypes = [ctypes.c_void_p]
    lib.codec2_bits_per_frame.restype = ctypes.c_int
    lib.codec2_bytes_per_frame.argtypes = [ctypes.c_void_p]
    lib.codec2_bytes_per_frame.restype = ctypes.c_int
    lib.codec2_encode.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.POINTER(ctypes.c_short),
    ]
    lib.codec2_decode.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_short),
        ctypes.POINTER(ctypes.c_ubyte),
    ]

    state = lib.codec2_create(CODEC2_MODE_3200)
    if not state:
        raise SystemExit("codec2_create(CODEC2_MODE_3200) returned NULL")
    try:
        nsam = lib.codec2_samples_per_frame(state)
        nbit = lib.codec2_bits_per_frame(state)
        nbyte = lib.codec2_bytes_per_frame(state)
        expected = (
            EXPECTED_SAMPLES_PER_FRAME,
            EXPECTED_BITS_PER_FRAME,
            EXPECTED_BYTES_PER_FRAME,
        )
        actual = (nsam, nbit, nbyte)
        if actual != expected:
            raise SystemExit(f"unexpected Codec2 3200 frame geometry: {actual} != {expected}")

        Speech = ctypes.c_short * nsam
        Bits = ctypes.c_ubyte * nbyte
        total_energy = 0
        nonzero_payloads = 0
        for frame_index in range(25):
            offset = frame_index * nsam
            speech = Speech(
                *(
                    int(12000 * math.sin(2.0 * math.pi * 440.0 * (offset + i) / 8000.0))
                    for i in range(nsam)
                )
            )
            bits = Bits()
            decoded = Speech()
            lib.codec2_encode(state, bits, speech)
            if any(bits):
                nonzero_payloads += 1
            lib.codec2_decode(state, decoded, bits)
            total_energy += sum(int(sample) * int(sample) for sample in decoded)

        if nonzero_payloads == 0:
            raise SystemExit("encoder produced only zero payloads")
        if total_energy == 0:
            raise SystemExit("decoder produced only zero PCM")
    finally:
        lib.codec2_destroy(state)

    print(
        "ctypes smoke OK: "
        f"{library_path.name}, mode=3200, samples={nsam}, bits={nbit}, bytes={nbyte}"
    )


if __name__ == "__main__":
    main()
