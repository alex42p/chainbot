import asyncio
import importlib
import json
import os
import sys

import pytest


def import_collector_easy(monkeypatch, dataset_path):
    monkeypatch.setenv("DATASET_PATH", str(dataset_path))
    if "data.collector_easy" in sys.modules:
        del sys.modules["data.collector_easy"]
    return importlib.import_module("data.collector_easy")


def test_write_messages_from_data_missing_messages_directory(tmp_path, monkeypatch):
    dataset_path = tmp_path / "dataset.txt"
    collector_easy = import_collector_easy(monkeypatch, dataset_path)
    monkeypatch.setattr(collector_easy, "__file__", str(tmp_path / "collector_easy.py"))

    with pytest.raises(ValueError, match="Messages directory not found"):
        collector_easy.write_messages_from_data()


def test_write_messages_from_data_filters_links_and_short_messages(tmp_path, monkeypatch):
    dataset_path = tmp_path / "dataset.txt"
    collector_easy = import_collector_easy(monkeypatch, dataset_path)
    monkeypatch.setattr(collector_easy, "__file__", str(tmp_path / "collector_easy.py"))

    messages_dir = tmp_path / "Messages" / "channel1"
    messages_dir.mkdir(parents=True)
    message_file = messages_dir / "messages.json"
    payload = [
        {"Contents": "hello world"},
        {"Contents": "   "},
        {"Contents": "http://example.com"},
        {"Contents": "@mention"},
        {"Contents": "hey"},
    ]
    message_file.write_text(json.dumps(payload), encoding="utf-8")

    collector_easy.write_messages_from_data()

    written = dataset_path.read_text(encoding="utf-8").splitlines()
    assert written == ["hello world", "@mention", "hey"]
