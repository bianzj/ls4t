"""Real EVO window exercising the current regional SLSTR component solver."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

try:
    from osgeo import gdal
except ImportError:
    gdal = None

SCRIPT = Path(__file__).parent / "examples/slstr_evo_sample.py"


@unittest.skipUnless(gdal is not None, "GDAL is required for the SLSTR example")
class SlstrEvoSampleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("slstr_evo_sample", SCRIPT)
        cls.example = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.example)

    def test_real_evo_window_runs_current_component_method(self):
        manifest, arrays = self.example.load_sample()
        self.assertFalse(manifest["synthetic"])
        self.assertEqual(manifest["site"], "EVO")
        self.assertEqual(arrays["lat"].shape, (10, 10))

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "day"
            summary = self.example.run_sample(output)
            self.assertEqual(summary["method"], self.example.retrieval.METHOD)
            self.assertEqual(summary["status"], "written")
            self.assertGreater(summary["valid_pixels"], 0)
            self.assertLess(summary["nadir_mapping_max_distance_km"], 2)
            self.assertIsNotNone(summary["station_anchor_component_K"]["vegetation"])

            products = {}
            for name in self.example.retrieval.PRODUCTS:
                dataset = gdal.Open(str(output / name))
                self.assertEqual((dataset.RasterYSize, dataset.RasterXSize), (10, 10))
                products[name] = dataset.ReadAsArray()
                dataset = None
            valid = products["vegetation.tif"] > 0
            self.assertEqual(int(valid.sum()), summary["valid_pixels"])
            self.assertTrue(np.all(products["sunlit_soil.tif"][valid] + 1e-4 >=
                                   products["shaded_soil.tif"][valid]))
            saved = json.loads((output / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(saved, summary)

    def test_night_gate_marks_same_window_no_valid(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "night"
            summary = self.example.run_sample(output, force_night=True)
            self.assertEqual(summary["status"], "no_valid")
            self.assertEqual(summary["valid_pixels"], 0)
            self.assertFalse(list(output.glob("*.tif")))
