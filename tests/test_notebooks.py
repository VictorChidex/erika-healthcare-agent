"""Offline tests of the notebook source, file handoff, and fail-closed loader."""
import ast
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
DATA_NOTEBOOK = ROOT / "notebooks" / "ERIKA_Part_1_Generate_Data.ipynb"
AGENT_NOTEBOOK = ROOT / "notebooks" / "ERIKA_Part_2_Agent_Existing_Records.ipynb"


def cells(path):
    return json.loads(path.read_text(encoding="utf-8"))["cells"]


def code_source(path, startswith):
    matches = ["".join(c["source"]) for c in cells(path)
               if c["cell_type"] == "code" and "".join(c["source"]).startswith(startswith)]
    if len(matches) != 1:
        raise AssertionError(f"Expected one cell beginning {startswith!r}; got {len(matches)}")
    return matches[0]


class NotebookTests(unittest.TestCase):
    def test_all_code_cells_parse_and_have_no_saved_outputs(self):
        for path in (DATA_NOTEBOOK, AGENT_NOTEBOOK):
            for cell in cells(path):
                if cell["cell_type"] == "code":
                    ast.parse("".join(cell["source"]))
                    self.assertEqual(cell["outputs"], [])
                    self.assertIsNone(cell["execution_count"])

    def test_agent_has_no_generator(self):
        code = "\n".join("".join(c["source"]) for c in cells(AGENT_NOTEBOOK)
                         if c["cell_type"] == "code")
        self.assertNotIn("def generate_synthetic_files", code)
        self.assertNotIn("def build_fixture", code)
        self.assertNotIn("aria_agent.invoke(", code)

    def test_generator_to_independent_reader(self):
        with TemporaryDirectory() as tmp:
            folder = Path(tmp) / "hospital_open_synthetic_data"
            generator = {}
            exec(code_source(DATA_NOTEBOOK, '"""Generate deterministic'), generator)
            exec(code_source(DATA_NOTEBOOK, '"""Open-access file tools'), generator)
            manifest = generator["generate_synthetic_files"](folder)
            self.assertEqual(manifest["generated_notes"], 47)

            reader = {}
            exec(code_source(AGENT_NOTEBOOK, '"""Open-access file tools'), reader)
            store = reader["OpenSyntheticStore"](folder)
            self.assertEqual(store.hospital_stats(), {
                "hospital_visits": 47, "unique_patients": 20,
                "admissions": 7, "discharges": 6, "currently_admitted": 1,
            })
            documents = store.list_documents()
            self.assertEqual(len(documents), 47)
            self.assertEqual(store.read_document("DOC-ENC-020-2")["patient_id"], "SYN-020")
            for document in documents:
                self.assertEqual(store.read_document(document["document_id"])["patient_id"],
                                 document["patient_id"])
            self.assertEqual(store.calculate_bmi("SYN-001")["bmi"], 22.9)

    def test_missing_folder_is_rejected_without_creation(self):
        with TemporaryDirectory() as tmp:
            reader = {}
            exec(code_source(AGENT_NOTEBOOK, '"""Open-access file tools'), reader)
            missing = Path(tmp) / "missing"
            with self.assertRaises(FileNotFoundError):
                reader["OpenSyntheticStore"](missing)
            self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
