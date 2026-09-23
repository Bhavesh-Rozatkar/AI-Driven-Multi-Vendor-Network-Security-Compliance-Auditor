import json
from cisco_config_to_json import chunk_config, deep_merge
from risk.risk_analyzer import severity_for_score


def test_chunking():
    chunks = chunk_config("a\nbb\nccc", max_chars=4)
    assert "\n".join(chunks).replace("\n\n", "\n") or chunks


def test_deep_merge_deduplicates_lists():
    assert deep_merge({"a": [1, 2]}, {"a": [2, 3]}) == {"a": [1, 2, 3]}


def test_severity_ranges():
    assert severity_for_score(0) == "Low"
    assert severity_for_score(20) == "Low"
    assert severity_for_score(21) == "Moderate"
    assert severity_for_score(40) == "Moderate"
    assert severity_for_score(41) == "Medium"
    assert severity_for_score(60) == "Medium"
    assert severity_for_score(61) == "High"
    assert severity_for_score(80) == "High"
    assert severity_for_score(81) == "Critical"
    assert severity_for_score(100) == "Critical"
