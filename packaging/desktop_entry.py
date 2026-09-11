"""PyInstaller entry; launch a GUI without opening a terminal."""

from batchlens.desktop import main

if __name__ == "__main__":
    raise SystemExit(main())
