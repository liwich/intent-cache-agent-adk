from datetime import date

from intent_cache_agent.canonicalization import canonicalize_mapping


def test_canonicalize_mapping_normalizes_values() -> None:
    mapping = {
        "empty": "",
        "date": date(2024, 1, 1),
        "list": ["b", "a"],
        "nested": {"z": 1, "a": 2},
    }
    result = canonicalize_mapping(mapping)

    assert "empty" not in result
    assert result["date"] == "2024-01-01"
    assert result["list"] == ["b", "a"]
    assert list(result["nested"].keys()) == ["a", "z"]
