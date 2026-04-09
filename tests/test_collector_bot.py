import asyncio
import importlib
import os
import sys

import pytest


def import_collector_bot(monkeypatch, dataset_path):
    monkeypatch.setenv("DISCORD_SCRAPER_TOKEN", "dummy-token")
    monkeypatch.setenv("DISCORD_CHANNEL_ID", "123")
    monkeypatch.setenv("DATASET_PATH", str(dataset_path))
    if "data.collector_bot" in sys.modules:
        del sys.modules["data.collector_bot"]
    return importlib.import_module("data.collector_bot")


def test_check_channels_returns_single_and_multiple_ids(monkeypatch, tmp_path):
    dataset_path = tmp_path / "dataset.txt"
    collector_bot = import_collector_bot(monkeypatch, dataset_path)

    collector_bot.DISCORD_CHANNEL_ID = "123, 456, not-a-number"
    collector_bot.TESTING = False

    channel_ids = collector_bot.check_channels()

    assert channel_ids == [123, 456]


def test_collect_messages_raises_when_user_id_missing(monkeypatch, tmp_path):
    dataset_path = tmp_path / "dataset.txt"
    collector_bot = import_collector_bot(monkeypatch, dataset_path)
    monkeypatch.setenv("USER_ID", "")

    with pytest.raises(ValueError):
        asyncio.run(collector_bot.collect_messages())


def test_collect_messages_filters_history(monkeypatch, tmp_path):
    dataset_path = tmp_path / "dataset.txt"
    collector_bot = import_collector_bot(monkeypatch, dataset_path)
    monkeypatch.setenv("USER_ID", "42")
    collector_bot.TESTING = False
    collector_bot.check_channels = lambda: [123]

    class FakeMessage:
        def __init__(self, author_id, content):
            self.author = type("Author", (), {"id": author_id})
            self.content = content

    class FakeChannel:
        def __init__(self):
            self.guild = "guild-name"
            self.name = "channel-name"

        async def history(self, limit=None, oldest_first=None, after=None):
            yield FakeMessage(42, "hello world")
            yield FakeMessage(42, "http://link")
            yield FakeMessage(99, "hello world")
            yield FakeMessage(42, "@mention")
            yield FakeMessage(42, "hey")

    async def fake_fetch_channel(cid):
        return FakeChannel()

    monkeypatch.setattr(collector_bot.client, "fetch_channel", fake_fetch_channel)
    monkeypatch.setattr(collector_bot.discord.abc, "Messageable", object, raising=False)

    results = asyncio.run(collector_bot.collect_messages())

    assert results == ["hello world"]
