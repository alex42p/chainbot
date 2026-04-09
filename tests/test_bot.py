import asyncio
import importlib
import sys
from types import ModuleType
from typing import Any

import persona


class DummyUser:
    def __init__(self, display_name="TestUser"):
        self.display_name = display_name


class DummyChannel:
    def __init__(self):
        self.sent = []

    def typing(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def send(self, text):
        self.sent.append(text)


class DummyMessage:
    def __init__(self, author, content, mentions=None):
        self.author = author
        self.content = content
        self.mentions = mentions or []
        self.channel = DummyChannel()


def import_bot(monkeypatch):
    monkeypatch.setattr(persona, "load_persona_samples", lambda load_type="": [])
    monkeypatch.setattr(persona, "sample_persona_samples", lambda samples: samples)
    if "bot" in sys.modules:
        del sys.modules["bot"]
    bot = importlib.import_module("bot")
    bot.chat_history.clear()
    return bot


def test_message_contains_keyword_true(monkeypatch):
    bot = import_bot(monkeypatch)

    assert bot.message_contains_keyword("I want the battle pass")


def test_message_contains_keyword_false(monkeypatch):
    bot = import_bot(monkeypatch)

    assert not bot.message_contains_keyword("good morning")


def test_on_message_ignores_non_trigger(monkeypatch):
    bot: Any = import_bot(monkeypatch)
    fake_client = type("FakeClient", (), {"user": DummyUser()})()
    monkeypatch.setattr(bot, "client", fake_client)

    message = DummyMessage(author=DummyUser(), content="hello there")
    monkeypatch.setattr(bot, "generate_response", lambda *args, **kwargs: "nope")

    asyncio.run(bot.on_message(message))

    assert message.channel.sent == []


def test_on_message_triggers_and_appends_history(monkeypatch):
    bot: Any = import_bot(monkeypatch)
    fake_client = type("FakeClient", (), {"user": DummyUser()})()
    monkeypatch.setattr(bot, "client", fake_client)
    bot.sample_persona_samples = lambda samples: ["sample"]

    async def fake_generate_response(*args, **kwargs):
        return "hi"

    bot.generate_response = fake_generate_response

    message = DummyMessage(author=DummyUser(), content="tell me about bot")

    asyncio.run(bot.on_message(message))

    assert message.channel.sent == ["hi"]
    assert bot.chat_history[-2:] == [
        {"role": "user", "content": "tell me about bot"},
        {"role": "assistant", "content": "hi"},
    ]
