# codec2-sdk

Pinned, repeatable local build wrapper for [drowe67/codec2](https://github.com/drowe67/codec2).
It exists so applications such as SerialTerminal can load a known Codec2 build instead of
implicitly depending on the distribution's `libcodec2` package.

## Current upstream

`upstream.lock.json` pins Codec2 to commit:

```text
310777b1c6f1af0bc7c72f5b32f80f6fd9136962
```

The upstream CMake project reports Codec2 version `1.2.0` at that commit. The commit is
newer than the 1.2.0 release tag; the full SHA, not the version string alone, is the SDK
identity.

## Requirements

Linux build requirements are intentionally small:

```bash
sudo apt install git build-essential cmake python3
```

No system Codec2 package is required. LPCNet is disabled for this SDK profile.

## Build

From the repository root:

```bash
./scripts/build
```

The script:

1. creates `upstream/codec2` if needed and fetches exactly the locked commit;
2. verifies the upstream checkout has the expected origin and SHA;
3. performs an out-of-source CMake `Release` build with `BUILD_SHARED_LIBS=ON`;
4. installs headers and the shared library entirely below this repository;
5. packages relocatable `c2enc`/`c2dec` wrappers plus their binaries and the upstream license;
6. writes a build manifest;
7. runs both a direct Python `ctypes` encode/decode test and a `.c2` file round trip.

On Linux x86-64 the resulting tree is:

```text
dist/linux-x86_64/
├── bin/
│   ├── c2enc
│   └── c2dec
├── include/
│   └── codec2/
├── libexec/
│   ├── c2enc.bin
│   └── c2dec.bin
├── lib/
│   ├── libcodec2.so -> ...
│   └── libcodec2.so.1.2
├── licenses/
│   └── codec2-COPYING
└── manifest.json
```

`dist/bin/c2enc` and `dist/bin/c2dec` set the library search path relative to their own
location before entering the matching `libexec/*.bin`, so the SDK tree can be moved without
retaining a CMake build-tree RPATH dependency.

`build/`, `dist/`, and `upstream/` are local/generated and are intentionally not committed.
The repository therefore remains small while every build remains tied to a reviewable SHA.
The build intentionally targets only `codec2`, `c2enc`, and `c2dec` instead of compiling the
full set of FreeDV/modem command-line utilities.

Set `JOBS=N` to override build parallelism:

```bash
JOBS=4 ./scripts/build
```

## Fetch only

```bash
./scripts/fetch-upstream
```

The fetch command refuses to discard local modifications in `upstream/codec2` and refuses
an unexpected upstream remote. Updating Codec2 is therefore an explicit edit of
`upstream.lock.json`, followed by a clean build and tests.

## Smoke test an existing build

```bash
./scripts/smoke-test
```

The direct-library smoke test uses only Python's standard `ctypes`; no Python Codec2 package
or binding is required. For mode 3200 it verifies the expected public API geometry:
160 samples/frame, 64 bits/frame, and 8 encoded bytes/frame, then performs encode/decode.

The file smoke test creates a one-second 8 kHz S16_LE tone, encodes it to a standard `.c2`
file, verifies the `C0 DE C2` file magic, and decodes it again.

## Intended SerialTerminal integration

SerialTerminal should load the SDK shared library by explicit path, for example:

```text
../codec2-sdk/dist/linux-x86_64/lib/libcodec2.so
```

The application should not silently fall back to an arbitrary system `libcodec2.so` when a
portable/reproducible build is required. A future SerialTerminal option/environment variable
can override the SDK path without changing this repository.

For store-and-forward voice messages the preferred file representation is a normal Codec2
`.c2` file. Codec2 already defines a compact file header containing magic, version, mode and
flags, so the first prototype does not need a custom container.

## CI

GitHub Actions runs the same `./scripts/build` path on Ubuntu 24.04, including the direct
`ctypes` test and `.c2` file round trip, and uploads `dist/linux-x86_64/` as a workflow
artifact. CI does not use Ubuntu's Codec2 package.

## Clean

```bash
./scripts/clean
```

This removes `build/` and `dist/` but intentionally retains the verified upstream checkout.

## Licensing

Codec2 is upstream software and carries its own licensing terms. The build copies the exact
upstream `COPYING` file into `dist/.../licenses/codec2-COPYING`. This repository does not
vendor or modify Codec2 source code.
