from __future__ import annotations

import asyncio
import json

from whats_eat.app.postprocessing import (
    attach_output_postprocessor,
    dedupe_supervisor_output,
)


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


class _StubApp:
    """Minimal compiled-graph stand-in exposing invocation methods."""

    _progress_chunk = {"type": "progress", "status": "working"}

    def _make_output(self) -> dict:
        payload = {
            "cards": [
                {"place_id": "abc", "name": "Thai Delight", "why": ["close by"]},
                {"place_id": "abc", "name": "Thai Delight", "why": ["close by", "popular"]},
            ],
            "rationale": "Duplicates on purpose.",
        }
        return {"messages": [FakeMessage(json.dumps(payload))]}

    def invoke(self, *args, **kwargs):  # noqa: ANN001 - signature matches runtime expectations
        return self._make_output()

    async def ainvoke(self, *args, **kwargs):  # noqa: ANN001
        await asyncio.sleep(0)
        return self._make_output()

    def batch(self, *args, **kwargs):  # noqa: ANN001
        return [self._make_output(), self._make_output()]

    async def abatch(self, *args, **kwargs):  # noqa: ANN001
        await asyncio.sleep(0)
        return [self._make_output()]

    def stream(self, *args, **kwargs):  # noqa: ANN001
        yield self._make_output()
        yield dict(self._progress_chunk)

    async def astream(self, *args, **kwargs):  # noqa: ANN001
        yield self._make_output()
        yield dict(self._progress_chunk)

    def stream_events(self, *args, **kwargs):  # noqa: ANN001
        yield self._make_output()

    async def astream_events(self, *args, **kwargs):  # noqa: ANN001
        yield self._make_output()


def test_attach_output_postprocessor_wraps_sync_methods() -> None:
    app = _StubApp()
    attach_output_postprocessor(app, dedupe_supervisor_output)

    result = app.invoke({})
    assert len(_extract_cards(result)) == 1

    batch_results = app.batch([{}, {}])
    assert all(len(_extract_cards(item)) == 1 for item in batch_results)

    stream_chunks = list(app.stream({}))
    assert len(stream_chunks) == 2
    assert len(_extract_cards(stream_chunks[0])) == 1
    assert stream_chunks[1] == _StubApp._progress_chunk

    event_chunks = list(app.stream_events({}))
    assert len(event_chunks) == 1
    assert len(_extract_cards(event_chunks[0])) == 1


def _collect_async(iterator):
    async def _consume() -> list:
        return [item async for item in iterator]

    return asyncio.run(_consume())


def test_attach_output_postprocessor_wraps_async_methods() -> None:
    app = _StubApp()
    attach_output_postprocessor(app, dedupe_supervisor_output)

    result = asyncio.run(app.ainvoke({}))
    assert len(_extract_cards(result)) == 1

    batch_results = asyncio.run(app.abatch([{}, {}]))
    assert all(len(_extract_cards(item)) == 1 for item in batch_results)

    stream_chunks = _collect_async(app.astream({}))
    assert len(stream_chunks) == 2
    assert len(_extract_cards(stream_chunks[0])) == 1
    assert stream_chunks[1] == _StubApp._progress_chunk

    event_chunks = _collect_async(app.astream_events({}))
    assert len(event_chunks) == 1
    assert len(_extract_cards(event_chunks[0])) == 1

