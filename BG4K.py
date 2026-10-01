"""BG4K: silent, offline image cutout and 3840-pixel export for Windows."""
from __future__ import annotations

import io
import logging
import os
from pathlib import Path
import sys
import tempfile


def output_folder() -> Path:
    return Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve().parent


def record_error(folder: Path, message: str) -> None:
    try:
        handler = logging.FileHandler(folder / "BG4K_errori.log", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        logger = logging.getLogger("bg4k")
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)
        logger.error(message, exc_info=True)
        logger.removeHandler(handler)
        handler.close()
    except Exception:
        pass


def process_file(source: Path, folder: Path, session) -> Path:
    import numpy as np
    from PIL import Image, ImageCms, ImageFilter, ImageOps

    if not source.is_file():
        raise ValueError(f"Il file non esiste: {source}")
    with Image.open(source) as opened:
        opened.seek(0)
        original = ImageOps.exif_transpose(opened)
        original.load()
        rgba = original.convert("RGBA")
        profile = original.info.get("icc_profile")
        if profile:
            try:
                converted = ImageCms.profileToProfile(
                    original.convert("RGB"), ImageCms.ImageCmsProfile(io.BytesIO(profile)),
                    ImageCms.createProfile("sRGB"), outputMode="RGB",
                )
                converted.putalpha(rgba.getchannel("A"))
                rgba = converted
            except (OSError, ValueError, ImageCms.PyCMSError):
                pass

    # Flatten existing transparency only for inference; retain it in the output.
    rgb = Image.new("RGB", rgba.size, "white")
    rgb.paste(rgba, mask=rgba.getchannel("A"))
    sample = np.asarray(rgb.resize((1024, 1024), Image.Resampling.LANCZOS), dtype=np.float32)
    sample = sample / max(float(sample.max()), 1e-6) - 0.5
    tensor = np.ascontiguousarray(sample.transpose(2, 0, 1)[None])
    prediction = session.run(None, {session.get_inputs()[0].name: tensor})[0][0, 0]
    low, high = float(prediction.min()), float(prediction.max())
    if not np.isfinite(prediction).all() or high - low < 1e-8:
        raise ValueError("Il modello non ha prodotto una maschera valida.")
    prediction = np.clip((prediction - low) / (high - low), 0, 1)
    mask = Image.fromarray(np.rint(prediction * 255).astype(np.uint8))
    mask = mask.resize(rgba.size, Image.Resampling.LANCZOS)
    alpha = np.asarray(mask, dtype=np.float32) * np.asarray(rgba.getchannel("A"), dtype=np.float32) / 255
    rgba.putalpha(Image.fromarray(np.rint(alpha).astype(np.uint8)))

    width, height = rgba.size
    scale = 3840 / max(width, height)
    target = (max(1, round(width * scale)), max(1, round(height * scale)))
    result = rgba.resize(target, Image.Resampling.LANCZOS)
    # Modest edge sharpening; no invented detail or changes to the model's face.
    color = result.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.0, percent=65, threshold=3))
    color.putalpha(result.getchannel("A"))
    destination = folder / f"{source.stem}_bg4k.png"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=folder, prefix=".bg4k-", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
        color.save(temporary, format="PNG", compress_level=6,
                   icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes())
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return destination


def main() -> int:
    arguments = sys.argv[1:]
    if not arguments:
        return 0
    folder = output_folder()
    try:
        import onnxruntime as ort
        resource_folder = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent / "work"))
        options = ort.SessionOptions()
        options.log_severity_level = 3
        options.intra_op_num_threads = min(4, os.cpu_count() or 1)
        session = ort.InferenceSession(str(resource_folder / "isnet-general-use.onnx"),
                                       sess_options=options, providers=["CPUExecutionProvider"])
    except Exception:
        record_error(folder, "Impossibile avviare il modello di rimozione dello sfondo.")
        return 1
    errors = 0
    for argument in arguments:
        try:
            process_file(Path(argument), folder, session)
        except Exception:
            errors += 1
            record_error(folder, f"Errore durante l'elaborazione di {argument!r}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
