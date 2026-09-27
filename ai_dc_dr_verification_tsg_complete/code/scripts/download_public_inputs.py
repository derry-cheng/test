#!/usr/bin/env python3
"""Restore the four optional public CSV inputs and verify their locked hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCES = {
    "data/raw/burstgpt/BurstGPT_without_fails_1.csv": (
        "https://github.com/HPMLL/BurstGPT/releases/download/v2.0/"
        "BurstGPT_without_fails_1.csv"
    ),
    "data/raw/burstgpt/BurstGPT_without_fails_2.csv": (
        "https://github.com/HPMLL/BurstGPT/releases/download/v2.0/"
        "BurstGPT_without_fails_2.csv"
    ),
    "data/raw/mit_supercloud/scheduler_data.csv": (
        "https://mit-supercloud-dataset.s3.amazonaws.com/2022-hpca/"
        "scheduler_data.csv"
    ),
    "data/raw/mit_supercloud/dcgm_verified_full.csv": (
        "https://mit-supercloud-dataset.s3.amazonaws.com/2022-hpca/dcgm.csv"
    ),
}
CHUNK_BYTES = 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(CHUNK_BYTES), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(path: Path, expected_bytes: int, expected_sha256: str) -> bool:
    return (
        path.is_file()
        and path.stat().st_size == expected_bytes
        and sha256_file(path) == expected_sha256
    )


def download(url: str, destination: Path, expected_bytes: int) -> None:
    temporary = destination.with_name(destination.name + ".part")
    digest = hashlib.sha256()
    total = 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "aicdr-public-data-reproducer/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response, temporary.open(
            "wb"
        ) as output:
            while True:
                block = response.read(CHUNK_BYTES)
                if not block:
                    break
                output.write(block)
                digest.update(block)
                total += len(block)
                progress = min(100.0, 100.0 * total / expected_bytes)
                print(
                    f"\r  {destination.name}: {progress:6.2f}% "
                    f"({total:,}/{expected_bytes:,} bytes)",
                    end="",
                    flush=True,
                )
        print()
        if total != expected_bytes:
            raise ValueError(
                f"{destination}: expected {expected_bytes} bytes, received {total}"
            )
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    print(f"  SHA-256 {digest.hexdigest()}  {destination.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="verify local files without downloading missing inputs",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="project root (defaults to the repository project directory)",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    manifest_path = root / "data/processed/data_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = {source["path"]: source for source in manifest["sources"]}
    missing_sources = sorted(set(SOURCES) - set(expected))
    if missing_sources:
        raise ValueError(f"Sources missing from locked manifest: {missing_sources}")

    failures: list[str] = []
    for relative_path, url in SOURCES.items():
        record = expected[relative_path]
        destination = root / relative_path
        if verify(destination, int(record["bytes"]), record["sha256"]):
            print(f"OK  {relative_path}")
            continue
        if args.check_only:
            failures.append(relative_path)
            print(f"MISSING OR HASH MISMATCH  {relative_path}")
            continue
        print(f"Downloading {url}")
        download(url, destination, int(record["bytes"]))
        if not verify(destination, int(record["bytes"]), record["sha256"]):
            destination.unlink(missing_ok=True)
            raise ValueError(f"Locked size or SHA-256 check failed: {relative_path}")

    # The small PGLib case is tracked in Git and is checked here too.
    pglib_path = "data/raw/pglib/pglib_opf_case118_ieee.m"
    pglib = expected[pglib_path]
    if verify(root / pglib_path, int(pglib["bytes"]), pglib["sha256"]):
        print(f"OK  {pglib_path}")
    else:
        failures.append(pglib_path)
        print(f"MISSING OR HASH MISMATCH  {pglib_path}")
    if failures:
        print("Input check failed: " + ", ".join(failures), file=sys.stderr)
        return 1
    print("All five source records match the locked byte counts and SHA-256 hashes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
