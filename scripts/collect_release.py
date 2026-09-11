"""Collect validated installers without overwriting artifacts, then hash every release file."""

import argparse
import hashlib
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--desktop", type=Path, required=True)
    parser.add_argument("--dist", type=Path, required=True)
    args = parser.parse_args()
    installers = []
    for source in sorted(args.desktop.rglob("*")):
        if source.suffix not in {".dmg", ".exe", ".json"}:
            continue
        name = f"{source.parent.name}-{source.name}" if source.suffix == ".json" else source.name
        target = args.dist / name
        if target.exists():
            raise FileExistsError(target)
        shutil.copyfile(source, target)
        if source.suffix in {".dmg", ".exe"}:
            installers.append(target)
    if len(installers) != 3:
        raise ValueError("Expected macOS arm64 + x86_64 DMGs and a Windows x64 installer")
    with (args.dist / "SHA256SUMS").open("x", encoding="utf-8") as stream:
        for path in sorted(args.dist.iterdir()):
            if path.is_file() and path.name != "SHA256SUMS":
                stream.write(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n")


if __name__ == "__main__":
    main()
