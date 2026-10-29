from io import BytesIO
from pathlib import Path
import tempfile
import unittest
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from g24lab.plot_io import save_png, write_verified_png


class CompleteFigureOutput(unittest.TestCase):
    def test_large_png_can_be_fully_decoded(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "method.png"
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.imshow(np.random.default_rng(24).random((600, 800)))
            try:
                save_png(fig, path, dpi=150)
            finally:
                plt.close(fig)
            self.assertGreater(path.stat().st_size, 3 * 65536)
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                image.load()
            self.assertEqual([p.name for p in Path(folder).iterdir()], ["method.png"])

    def test_truncated_png_is_rejected_and_previous_file_survives(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "method.png"
            buffer = BytesIO()
            Image.fromarray(np.random.default_rng(25).integers(0, 256, (400, 600, 3), dtype=np.uint8)).save(buffer, format="PNG")
            original = buffer.getvalue()
            write_verified_png(original, path)
            with self.assertRaises((OSError, SyntaxError)):
                write_verified_png(original[:len(original) // 2], path)
            self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
