"""Release count validation follows the selected manifest, including future releases."""
import copy
import unittest
from agent_workflow.installer import validate_release_counts


class ManifestCountTests(unittest.TestCase):
    def setUp(self):
        self.release = {"version": "9.2.0", "bundle": {"version": "9.2.0"},
                        "skills": [{"source": {"kind": "new"}}],
                        "counts": {"new": 1, "total": 1}}

    def test_selected_release_count_is_dynamic(self):
        validate_release_counts(self.release)
        self.release["skills"].append({"source": {"kind": "reuse"}})
        self.release["counts"] = {"new": 1, "reuse": 1, "total": 2}
        validate_release_counts(self.release)

    def test_incorrect_count_and_version_are_rejected(self):
        for key, value in [("total", 74), ("new", True), ("new", -1)]:
            candidate = copy.deepcopy(self.release)
            candidate["counts"][key] = value
            with self.assertRaises(ValueError):
                validate_release_counts(candidate)
        self.release["bundle"]["version"] = "9.1.0"
        with self.assertRaises(ValueError):
            validate_release_counts(self.release)

    def test_mismatched_versions_fail_without_count_metadata(self):
        self.release.pop("counts")
        self.release["bundle"]["version"] = "9.1.0"
        with self.assertRaises(ValueError):
            validate_release_counts(self.release)
