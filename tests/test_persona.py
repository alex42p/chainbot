import io
import random
import pytest
import persona


def test_load_persona_samples_from_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(persona, "DATASET_PATH", str(tmp_path / "missing_persona.txt"))

    samples = persona.load_persona_samples_from_file()

    assert samples == []


def test_load_persona_samples_from_file_parses_comments_and_blank_lines(tmp_path, monkeypatch):
    dataset_path = tmp_path / "dataset.txt"
    dataset_path.write_text("hello\n# comment\n\nworld\n", encoding="utf-8")
    monkeypatch.setattr(persona, "DATASET_PATH", str(dataset_path))

    samples = persona.load_persona_samples_from_file()

    assert samples == ["hello", "world"]


def test_load_persona_samples_from_s3_falls_back_to_file(monkeypatch):
    monkeypatch.setattr(persona, "S3_BUCKET", "")
    monkeypatch.setattr(persona, "DATASET_PATH", "missing.txt")
    sentinel = ["fallback"]
    monkeypatch.setattr(persona, "load_persona_samples_from_file", lambda: sentinel)

    samples = persona.load_persona_samples_from_s3()

    assert samples is sentinel


class FakeS3Client:
    def get_object(self, Bucket, Key):
        return {"Body": io.BytesIO(b"hello\n#ignored\nworld\n")}


def test_load_persona_samples_from_s3_parses_lines(monkeypatch):
    monkeypatch.setattr(persona, "S3_BUCKET", "fake-bucket")
    monkeypatch.setattr(persona, "S3_KEY", "fake-key")
    monkeypatch.setattr(persona.boto3, "client", lambda *args, **kwargs: FakeS3Client())

    samples = persona.load_persona_samples_from_s3()

    assert samples == ["hello", "world"]


def test_sample_persona_samples_returns_all_when_under_max():
    samples = ["one", "two"]

    subset = persona.sample_persona_samples(samples, max_samples=10)

    assert subset == samples
    assert subset is not samples


def test_sample_persona_samples_uses_random_sample_for_large_sets(monkeypatch):
    samples = ["one", "two", "three", "four", "five"]
    monkeypatch.setattr(persona.random, "sample", lambda seq, k: seq[:k])

    subset = persona.sample_persona_samples(samples, max_samples=3)

    assert subset == ["one", "two", "three"]
