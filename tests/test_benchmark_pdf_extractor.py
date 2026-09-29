import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from pypdf import PdfReader
from backend.compliance.pdf_extractor import extract_cis_controls_from_pdf

PDF = Path(__file__).resolve().parents[2] / "input" / "CIS_pfSense_Firewall_Benchmark_v1.1.0.pdf"

def test_cis_pfsense_benchmark_extracts_all_33_recommendations():
    if not PDF.exists():
        pytest.skip("Reference CIS PDF is not bundled; upload it through the application to test this fixture.")
    controls, _ = extract_cis_controls_from_pdf(PdfReader(str(PDF)))
    assert len(controls) == 33
    assert controls[0]["rule_id"] == "1.1"
    assert controls[-1]["rule_id"] == "6.1"
    assert all(c["assessment_status"] == "MANUAL" for c in controls)
    assert controls[0]["title"] == "Ensure SSH warning banner is configured"
    assert "Audit:" not in controls[0]["title"]
    assert controls[0]["source_pages"]

def test_cis_parser_does_not_merge_section_headings_with_controls():
    if not PDF.exists():
        pytest.skip("Reference CIS PDF is not bundled; upload it through the application to test this fixture.")
    controls, _ = extract_cis_controls_from_pdf(PdfReader(str(PDF)))
    ids = [c["rule_id"] for c in controls]
    assert "4.1" not in ids
    assert "5.1" not in ids
    assert "5.5" not in ids
    assert "4.1.1" in ids and "5.1.1" in ids and "5.5.1" in ids
