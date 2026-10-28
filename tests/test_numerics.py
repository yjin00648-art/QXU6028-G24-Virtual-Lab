from pathlib import Path
import hashlib
import json
import unittest
import numpy as np
from g24lab import l1, l2, l3
from tests.negative_controls import synthetic_pairs

ROOT = Path(__file__).resolve().parents[1]


class NumericalGates(unittest.TestCase):
    def test_input_manifests(self):
        for prefix in ("", "blind_"):
            files = {f.name: f for stage in ("L1", "L2", "L3") for f in (ROOT / f"{prefix}{stage}" / "data").iterdir() if f.is_file()}
            for item in json.loads(files["manifest.json"].read_text())["files"]:
                self.assertEqual(files[item["name"]].stat().st_size, item["bytes"])
                self.assertEqual(hashlib.sha256(files[item["name"]].read_bytes()).hexdigest(), item["sha256"])

    def test_l1_reference_ratios(self):
        params = json.loads((ROOT / "L1" / "data" / "L1_params.json").read_text())
        for ef, expected in ((0, 1.0), (0.073, 2.0), (0.1, 2.6), (0.2, 5.1)):
            self.assertAlmostEqual(l1.correction_factor(ef, params["T"], params["c"]), expected, delta=0.06)

    def test_signed_separate_normalisation(self):
        xy = l2.core.normalise_pairs(np.array([-10., 5.]), np.array([2., 4.]))
        np.testing.assert_allclose(xy, [[-1, 0.5], [0.5, 1]])

    def test_joint_nearest_ef(self):
        rms, indices = l2.nearest(np.array([[0.9, 0.9]]), np.array([0., 1.]), np.array([1., 0.]))
        self.assertGreater(rms, 0.8)
        self.assertIn(indices[0], (0, 1))

    def test_selection_threshold_and_minimum_gap(self):
        self.assertFalse(l2.select_hard_gap(2., 0.85, 1.))
        self.assertTrue(l2.select_hard_gap(2., 0.849, 1.))
        self.assertFalse(l2.select_hard_gap(0.5, 0.1, 1.))

    def test_cone_can_be_selected(self):
        data = synthetic_pairs(0.)
        means = l2.core.prepare_means(data)
        xy = l2.core.normalise_pairs(means.R_H_mean.to_numpy(), means.R_xx_mean.to_numpy())
        fitted = l2.fit_central(xy, 300.)
        self.assertEqual(fitted["model"], "cone")
        self.assertEqual(fitted["selected_gap"], 0.)
        self.assertLess(fitted["selected_residual"], 1e-12)

    def test_global_gap_not_dataset_specific(self):
        data = synthetic_pairs(6.)
        means = l2.core.prepare_means(data)
        xy = l2.core.normalise_pairs(means.R_H_mean.to_numpy(), means.R_xx_mean.to_numpy())
        fitted = l2.fit_central(xy, 300.)
        self.assertEqual(fitted["model"], "hard_gap")
        self.assertAlmostEqual(fitted["selected_gap"], 6., places=4)

    def test_course_grid(self):
        _, gaps, *_ = l2.library(300., "course")
        self.assertEqual(len(gaps), 31)
        np.testing.assert_allclose(np.diff(gaps), 0.25)

    def test_zero_mean_projection_and_gradient(self):
        gradient = l3.gradient_matrix(10)
        projector = l3.zero_mean_projector(100)
        self.assertEqual(gradient.shape, (180, 100))
        np.testing.assert_allclose(gradient @ np.ones(100), 0., atol=1e-12)
        np.testing.assert_allclose(projector @ np.ones(100), 0., atol=1e-12)
        np.testing.assert_allclose(projector @ projector, projector, atol=1e-12)

    def test_l3_original_dimensions_and_null_mode(self):
        for prefix in ("", "blind_"):
            matrix = np.load(ROOT / f"{prefix}L3" / "data" / "L3_A.npy")
            scans = np.loadtxt(ROOT / f"{prefix}L3" / "data" / "L3_d.csv", delimiter=",")
            self.assertEqual(matrix.shape, (128, 100))
            self.assertEqual(scans.shape, (3, 128))
            self.assertLess(np.max(np.abs(matrix.sum(axis=1))), 1e-11)


if __name__ == "__main__":
    unittest.main(verbosity=2)
