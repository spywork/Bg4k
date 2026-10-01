"""Native executable smoke test, run on every supported build runner."""
import hashlib
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import urllib.request
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
machine = "arm64" if platform.machine().lower() in ("arm64", "aarch64") else "x86_64"
system = {"win32": "Windows", "darwin": "macOS", "linux": "Linux"}[sys.platform]
package = ROOT / "release" / f"BG4K_{system}_{machine}"
binary = package / ("BG4K.exe" if sys.platform == "win32" else "BG4K")
if sys.platform == "darwin":
    binary = package / "BG4K.app" / "Contents" / "MacOS" / "BG4K"
options = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
with tempfile.TemporaryDirectory(prefix="bg4k smoke ") as temp:
    folder = Path(temp)
    original = folder / "foto prova è.jpg"
    urllib.request.urlretrieve("https://raw.githubusercontent.com/danielgatis/rembg/main/examples/girl-1.jpg", original)
    checksum = hashlib.sha256(original.read_bytes()).hexdigest()
    with Image.open(original) as image:
        rotated = folder / "orientamento.jpg"
        exif = Image.Exif()
        exif[274] = 6
        image.save(rotated, exif=exif)
    assert subprocess.run([str(binary)], cwd=folder, timeout=90, **options).returncode == 0
    result = subprocess.run([str(binary), str(folder / "missing.jpg"), str(original), str(rotated)],
                            cwd=folder, timeout=240, **options)
    assert result.returncode == 1, result.returncode
    for source in (original, rotated):
        with Image.open(source) as opened:
            width, height = ImageOps.exif_transpose(opened).size
        with Image.open(package / f"{source.stem}_bg4k.png") as output:
            assert output.size == (round(width * 3840 / max(width, height)),
                                   round(height * 3840 / max(width, height)))
            assert output.mode == "RGBA"
            low, high = output.getchannel("A").getextrema()
            assert low == 0 and high >= 250
        (package / f"{source.stem}_bg4k.png").unlink()
    assert hashlib.sha256(original.read_bytes()).hexdigest() == checksum
    log = package / "BG4K_errori.log"
    assert "missing.jpg" in log.read_text(encoding="utf-8")
    log.unlink()
    if sys.platform == "linux":
        import os
        env = dict(os.environ, XDG_DATA_HOME=str(folder / "local data"))
        assert subprocess.run([str(binary), "--install-launcher"], env=env, timeout=90).returncode == 0
        desktop = folder / "local data" / "applications" / "bg4k.desktop"
        assert desktop.is_file() and "Terminal=false" in desktop.read_text()
        subprocess.run(["desktop-file-validate", str(desktop)], check=True)
print(f"Smoke test superato: {system} {machine}")
