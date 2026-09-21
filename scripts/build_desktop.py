"""Build a self-contained app into a NEW directory; never clean or replace previous builds."""

import argparse
import hashlib
import json
import platform
import plistlib
import shutil
import subprocess
import sys
import tempfile
from importlib import metadata
from pathlib import Path

from PIL import Image, ImageDraw

from batchlens import __version__

ROOT = Path(__file__).resolve().parents[1]


def stage_macos_bundle(bundle):
    """Copy a new build to local scratch before signing; preserve the source build.

    Finder/sync services can immediately reattach forbidden signing metadata in
    Documents. Sign and assemble the DMG outside that directory instead of racing
    those services. This scratch folder is retained, never recursively deleted.
    """
    scratch = Path(tempfile.mkdtemp(prefix="batchlens-sign-"))
    app = scratch / bundle.name
    subprocess.run(["ditto", "--norsrc", "--noextattr", str(bundle), str(app)], check=True)
    return app


def icon_file(out):
    image = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((40, 40, 984, 984), radius=220, fill="#173330")
    draw.rounded_rectangle((235, 210, 345, 790), radius=54, fill="#fafbf7")
    draw.ellipse((255, 405, 675, 805), fill="#fafbf7")
    draw.ellipse((365, 515, 565, 695), fill="#173330")
    draw.rounded_rectangle((710, 210, 820, 790), radius=54, fill="#a4d8ad")
    destination = out / ("BatchLens.icns" if sys.platform == "darwin" else "BatchLens.ico")
    image.save(destination)
    return destination


def notices(out):
    folder = out / "third-party-licenses"
    folder.mkdir()
    records = []
    for distribution in metadata.distributions():
        name = distribution.metadata["Name"]
        records.append(f"{name} {distribution.version}")
        for file in distribution.files or []:
            if file.name.lower().startswith(
                ("license", "licence", "copying", "notice")
            ) and file.suffix.lower() in {"", ".txt", ".md", ".rst"}:
                source = Path(distribution.locate_file(file))
                if not source.is_file():
                    continue
                target = folder / name / str(file).replace("..", "_")
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
    (folder / "PACKAGES.txt").write_text(
        "Build environment packages:\n" + "\n".join(sorted(records))
    )
    shutil.copyfile(ROOT / "LICENSE", folder / "BATCHLENS-LICENSE.txt")
    return folder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--gui-smoke", action="store_true")
    args = parser.parse_args()
    if sys.platform not in {"darwin", "win32"}:
        parser.error("Build desktop installers natively on macOS or Windows")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    icon = icon_file(out)
    legal = notices(out)
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        "BatchLens Bio",
        "--windowed",
        "--onedir",
        "--distpath",
        str(out / "frozen"),
        "--workpath",
        str(out / "work"),
        "--specpath",
        str(out),
        "--icon",
        str(icon),
        "--collect-data",
        "batchlens",
        "--collect-data",
        "webview",
        "--add-data",
        f"{legal}:third-party-licenses",
    ]
    for name in ["batchlens-bio", "numpy", "pandas", "pydantic", "PyYAML", "Jinja2", "pywebview"]:
        command += ["--copy-metadata", name]
    for name in ["pytest", "IPython", "matplotlib", "scipy", "PyQt5", "PyQt6", "PySide6"]:
        command += ["--exclude-module", name]
    if sys.platform == "darwin":
        command += ["--osx-bundle-identifier", "io.github.guatou904.batchlens-bio"]
    command.append(str(ROOT / "packaging/desktop_entry.py"))
    subprocess.run(command, cwd=ROOT, check=True)
    if sys.platform == "darwin":
        app = stage_macos_bundle(out / "frozen/BatchLens Bio.app")
        executable = app / "Contents/MacOS/BatchLens Bio"
        plist = app / "Contents/Info.plist"
        info = plistlib.loads(plist.read_bytes())
        info.update(CFBundleShortVersionString=__version__, CFBundleVersion=__version__)
        plist.write_bytes(plistlib.dumps(info))
        subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(app)], check=True)
        subprocess.run(["codesign", "--verify", "--deep", "--strict", str(app)], check=True)
    else:
        executable = out / "frozen/BatchLens Bio/BatchLens Bio.exe"
    smoke = out / "desktop-smoke.json"
    subprocess.run(
        [str(executable), "--smoke-test", str(smoke), "--out", str(out / "smoke-audits")],
        cwd=out,
        check=True,
        timeout=300,
    )
    assert json.loads(smoke.read_text())["frozen"] is True
    if args.gui_smoke:
        gui_smoke = out / "desktop-gui-smoke.json"
        subprocess.run(
            [
                str(executable),
                "--smoke-gui",
                str(gui_smoke),
                "--out",
                str(out / "gui-smoke-audits"),
            ],
            cwd=out,
            check=True,
            timeout=120,
        )
        assert json.loads(gui_smoke.read_text())["javascript_audit"] == "passed"
    if sys.platform == "darwin":
        stage = app.parent / "dmg-content"
        stage.mkdir()
        (stage / "Applications").symlink_to("/Applications")
        subprocess.run(["ditto", str(app), str(stage / app.name)], check=True)
        (stage / "READ ME.txt").write_text(
            "Drag BatchLens Bio into Applications, then open it.\n"
            "No Python installation is needed. Reports are saved to ~/BatchLens Audits.\n"
            "This alpha build is ad-hoc signed, not Apple-notarized. See docs/desktop.md "
            "in the project repository for platform verification and distribution status.\n"
        )
        dmg = out / f"BatchLens-Bio-{__version__}-macOS-{platform.machine()}.dmg"
        subprocess.run(
            [
                "hdiutil",
                "create",
                "-volname",
                "BatchLens Bio",
                "-srcfolder",
                str(stage),
                "-format",
                "UDZO",
                str(dmg),
            ],
            check=True,
        )
        subprocess.run(["hdiutil", "verify", str(dmg)], check=True)
        (out / "SHA256SUMS").write_text(
            f"{hashlib.sha256(dmg.read_bytes()).hexdigest()}  {dmg.name}\n"
        )
    print(f"Desktop build and frozen smoke check passed: {out}")


if __name__ == "__main__":
    main()
