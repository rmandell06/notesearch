import pytest

from app.services.embedding import EmbeddingService


@pytest.fixture(scope="module")
def service() -> EmbeddingService:
    s = EmbeddingService()
    s._ensure_loaded()  # warm the model+tokenizer once for the module
    return s


def test_returns_one_vector_per_text(service: EmbeddingService) -> None:
    vectors = service.embed(["hello world", "the cat sat on the mat"])
    assert len(vectors) == 2
    assert all(len(v) == 128 for v in vectors)


def test_empty_input_returns_empty(service: EmbeddingService) -> None:
    assert service.embed([]) == []


def test_empty_string_still_yields_a_vector(service: EmbeddingService) -> None:
    vectors = service.embed(["", "hello"])
    assert len(vectors) == 2
    assert len(vectors[0]) == 128
    assert len(vectors[1]) == 128


def test_different_inputs_produce_different_vectors(service: EmbeddingService) -> None:
    a, b = service.embed(["the cat sat on the mat", "completely unrelated text"])
    assert a != b
