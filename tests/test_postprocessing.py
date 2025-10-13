from __future__ import annotations

import json

from whats_eat.app.postprocessing import dedupe_supervisor_output


class FakeMessage:
    """Minimal stand-in for an AIMessage used in unit tests."""

    def __init__(self, content: str) -> None:
        self.content = content


def _extract_cards(output: dict) -> list[dict]:
    final_message = output["messages"][-1]
    payload = json.loads(final_message.content)
    return payload["cards"]


def test_dedupe_supervisor_output_merges_duplicate_cards() -> None:
    payload = {
        "cards": [
            {
                "place_id": "abc",
                "name": "Thai Delight",
                "why": ["close by"],
                "photos": [{"name": "https://example.com/photo-1.jpg"}],
            },
            {
                "place_id": "abc",
                "name": "Thai Delight",
                "address": "123 Orchard Rd",
                "why": ["great reviews", "close by"],
                "photos": [
                    {"name": "https://example.com/photo-1.jpg"},
                    {"name": "https://example.com/photo-2.jpg"},
                ],
            },
            {
                "place_id": "def",
                "name": "Spice Hub",
                "summary": "Known for fragrant curries.",
                "why": ["bold flavours"],
            },
            {
                "place_id": "def",
                "name": "Spice Hub",
                "photos": [{"name": "https://example.com/photo-3.jpg"}],
            },
        ],
        "rationale": "Recommended based on your Thai craving.",
    }

    output = {"messages": [FakeMessage(json.dumps(payload))]}

    dedupe_supervisor_output(output)

    cards = _extract_cards(output)
    assert len(cards) == 2

    first, second = cards

    assert first["place_id"] == "abc"
    # Address is merged from the duplicate entry
    assert first["address"] == "123 Orchard Rd"
    # Photos are deduplicated and merged
    assert {photo["name"] for photo in first["photos"]} == {
        "https://example.com/photo-1.jpg",
        "https://example.com/photo-2.jpg",
    }
    # Reasons keep order and uniqueness
    assert first["why"] == ["close by", "great reviews"]

    assert second["place_id"] == "def"
    assert second["summary"] == "Known for fragrant curries."
    assert second["why"] == ["bold flavours"]
    assert second["photos"] == [{"name": "https://example.com/photo-3.jpg"}]


def test_dedupe_supervisor_output_is_noop_for_unique_cards() -> None:
    payload = {
        "cards": [
            {"place_id": "abc", "name": "Thai Delight"},
            {"place_id": "def", "name": "Spice Hub"},
        ],
        "rationale": "All unique.",
    }

    json_payload = json.dumps(payload)
    message = FakeMessage(json_payload)
    output = {"messages": [message]}

    dedupe_supervisor_output(output)

    # Content remains untouched when no changes are needed
    assert output["messages"][-1].content == json_payload

