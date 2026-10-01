"""Build native offline BG4K packages. Run on the target OS with Python 3.12."""
from __future__ import annotations
import hashlib
from importlib.metadata import distributions
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent
MODEL_URL = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/isnet-general-use.onnx"
MODEL_SHA256 = "60920e99c45464f2ba57bee2ad08c919a52bbf852739e96947fbb4358c0d964a"

def download_model() -> Path:
    folder = ROOT / "models"
    folder.mkdir(exist_ok=True)
    model = folder / "isnet-general-use.onnx"
    if not model.exists() or hashlib.sha256(model.read_bytes()).hexdigest() != MODEL_SHA256:
        temporary = model.with_suffix(".download")
        urllib.request.urlretrieve(MODEL_URL, temporary)
        if hashlib.sha256(temporary.read_bytes()).hexdigest() != MODEL_SHA256:
            temporary.unlink(missing_ok=True)
            raise RuntimeError("Il modello scaricato non corrisponde alla checksum prevista.")
        temporary.replace(model)
    return model

def collect_licenses(destination: Path) -> None:
    parts = [(ROOT / "LICENZE.txt").read_text(encoding="utf-8"),
             "\n\n=== Dipendenze effettive di questa compilazione ===\n"]
    for dist in sorted(distributions(), key=lambda d: d.metadata["Name"].lower()):
        parts.append(f"\n{dist.metadata['Name']} {dist.version}\n")
        for entry in dist.files or []:
            name = str(entry).lower()
            if (("dist-info" in name and ("license" in name or "notice" in name))
                    or name.endswith("onnxruntime/license") or name.endswith("onnxruntime/thirdpartynotices.txt")):
                path = Path(dist.locate_file(entry))
                if path.is_file() and path.suffix.lower() not in (".py", ".pyc"):
                    parts.append(f"\n{entry}\n" + path.read_text(encoding="utf-8", errors="replace"))
    destination.write_text("".join(parts), encoding="utf-8")

def build() -> Path:
    model = download_model()
    release = ROOT / "release"
    release.mkdir(exist_ok=True)
    command = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
               "--name", "BG4K", "--add-data", f"{model}{os.pathsep}.",
               "--collect-binaries", "onnxruntime", "--collect-data", "onnxruntime"]
    if sys.platform == "darwin":
        command += ["--onedir", "--windowed", "--argv-emulation",
                    "--osx-bundle-identifier", "com.spywork.bg4k"]
    else:
        command += ["--onefile"]
        if sys.platform == "win32":
            command += ["--windowed"]
    command += [str(ROOT / "BG4K.py")]
    subprocess.run(command, cwd=ROOT, check=True)
    machine = __import__("platform").machine().lower()
    architecture = "arm64" if machine in ("arm64", "aarch64") else "x86_64"
    if sys.platform == "darwin":
        source = ROOT / "dist" / "BG4K.app"
        plist = source / "Contents" / "Info.plist"
        info = plistlib.loads(plist.read_bytes())
        info.update({"LSUIElement": True,
                     "CFBundleDocumentTypes": [{"CFBundleTypeName": "Image",
                                                "CFBundleTypeRole": "Viewer",
                                                "LSHandlerRank": "Alternate",
                                                "LSItemContentTypes": ["public.image"]}]})
        plist.write_bytes(plistlib.dumps(info))
        subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(source)], check=True)
        name = f"BG4K_macOS_{architecture}"
    elif sys.platform == "win32":
        source = ROOT / "dist" / "BG4K.exe"
        name = "BG4K_Windows_x86_64"
    elif sys.platform == "linux":
        source = ROOT / "dist" / "BG4K"
        name = f"BG4K_Linux_{architecture}"
    else:
        raise RuntimeError(f"Sistema non supportato: {sys.platform}")
    package = release / name
    package.mkdir(exist_ok=True)
    destination = package / source.name
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
    else:
        shutil.copy2(source, destination)
    for filename in ("README.md", "LEGGIMI.txt", "LICENSE", "BG4K.py", "build.py", "requirements-build.txt"):
        shutil.copy2(ROOT / filename, package / filename)
    collect_licenses(package / "LICENZE.txt")
    if sys.platform == "linux":
        installer = package / "Installa_collegamento.sh"
        installer.write_text('#!/bin/sh\nset -eu\ncd -- "$(dirname -- "$0")"\nexec ./BG4K --install-launcher\n', encoding="utf-8")
        installer.chmod(0o755)
        archive = release / f"{name}.tar.gz"
        with tarfile.open(archive, "w:gz") as output:
            output.add(package, arcname=package.name)
    elif sys.platform == "darwin":
        archive = release / f"{name}.zip"
        subprocess.run(["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent",
                        str(package), str(archive)], check=True)
    else:
        archive = release / f"{name}.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
            for path in package.rglob("*"):
                if path.is_file():
                    output.write(path, path.relative_to(release))
    print(f"Pacchetto creato: {archive}")
    return archive

if __name__ == "__main__":
    build()
