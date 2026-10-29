"""Validate complete PNG bytes before atomically publishing a figure."""
from __future__ import annotations
from io import BytesIO
import os
from pathlib import Path
import tempfile
from PIL import Image


def _validate_png(payload: bytes) -> None:
    with Image.open(BytesIO(payload)) as image:
        if image.format != "PNG":
            raise ValueError("Expected a PNG figure")
        image.verify()
    with Image.open(BytesIO(payload)) as image:
        image.load()


def write_verified_png(payload: bytes, path: Path) -> None:
    """Reject incomplete images without replacing an existing complete output."""
    _validate_png(payload)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent,
                                         prefix=".figure-", suffix=".png", delete=False) as stream:
            temporary = Path(stream.name)
            if stream.write(payload) != len(payload):
                raise OSError("Incomplete PNG write")
            stream.flush()
            os.fsync(stream.fileno())
        written = temporary.read_bytes()
        if written != payload:
            raise OSError("PNG readback differs from the rendered bytes")
        _validate_png(written)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def save_png(figure, path: Path, **kwargs) -> None:
    buffer = BytesIO()
    figure.savefig(buffer, format="png", **kwargs)
    write_verified_png(buffer.getvalue(), Path(path))
