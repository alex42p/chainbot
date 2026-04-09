import asyncio
import importlib
import sys
import boto3
from botocore.exceptions import ClientError


def import_llm(monkeypatch):
    class FakeBedrockClient:
        def __init__(self, *args, **kwargs):
            pass

    fake_client = FakeBedrockClient()
    monkeypatch.setattr(boto3, "client", lambda *args, **kwargs: fake_client)
    if "llm" in sys.modules:
        del sys.modules["llm"]
    import llm
    llm.bedrock = fake_client
    return llm


def test_build_system_prompt_includes_persona_samples(monkeypatch):
    llm = import_llm(monkeypatch)

    prompt = llm._build_system_prompt(["hello", "world"])

    assert "REAL MESSAGES FROM CHAINMAN" in prompt
    assert "- hello" in prompt
    assert "- world" in prompt


def test_generate_response_returns_trimmed_text(monkeypatch):
    llm = import_llm(monkeypatch)

    def fake_converse(**kwargs):
        return {"output": {"message": {"content": [{"text": " hi there "}]}}}

    llm.bedrock.converse = fake_converse

    response = asyncio.run(llm.generate_response(
        user_message="hello",
        persona_samples=["sample"],
        author_name="Alice",
        history=[{"role": "user", "content": "previous"}],
    ))

    assert response == "hi there"


def test_generate_response_handles_client_error(monkeypatch):
    llm = import_llm(monkeypatch)

    def fake_converse(**kwargs):
        raise ClientError({"Error": {"Message": "boom"}}, "Converse")

    llm.bedrock.converse = fake_converse

    response = asyncio.run(llm.generate_response(
        user_message="hello",
        persona_samples=["sample"],
        author_name="Alice",
        history=None,
    ))

    assert "sksksksksks" in response


def test_generate_response_handles_generic_exception(monkeypatch):
    llm = import_llm(monkeypatch)

    def fake_converse(**kwargs):
        raise RuntimeError("unexpected")

    llm.bedrock.converse = fake_converse

    response = asyncio.run(llm.generate_response(
        user_message="hello",
        persona_samples=["sample"],
        author_name="Alice",
        history=None,
    ))

    assert "whoops" in response
