import json
import os
import urllib.request
from pathlib import Path
from typing import Any, List, Optional, Sequence, Union

DEFAULT_OPENAI_MODEL = "text-embedding-3-small"
DEFAULT_HF_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_OUTPUT_DIR = Path("rag") / "embeddings"

try:
    import openai
except ImportError:  # pragma: no cover
    openai = None  # type: ignore

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover
    SentenceTransformer = None  # type: ignore


class EmbedderError(Exception):
    pass


def _get_openai_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EmbedderError(
            "OPENAI_API_KEY is required for OpenAI embeddings."
        )
    return api_key


def _validate_provider(provider: str) -> str:
    provider = provider.lower()
    valid_providers = {"openai", "sentence-transformers", "huggingface", "hf"}
    if provider not in valid_providers:
        raise EmbedderError(
            f"Unsupported provider '{provider}'. Supported providers: openai, sentence-transformers, huggingface."
        )
    if provider == "hf":
        return "huggingface"
    return provider


def _get_hf_api_key() -> str:
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        raise EmbedderError(
            "HUGGINGFACE_API_KEY is required for Hugging Face embeddings."
        )
    return api_key


def _get_default_provider() -> str:
    if SentenceTransformer is not None:
        return "sentence-transformers"
    if os.getenv("HUGGINGFACE_API_KEY"):
        return "huggingface"
    if openai is not None:
        return "openai"
    raise EmbedderError(
        "No embedding backend is available. Install sentence-transformers, set HUGGINGFACE_API_KEY, or install openai."
    )


def _openai_embeddings(texts: Sequence[str], model: str) -> List[List[float]]:
    if openai is None:
        raise EmbedderError(
            "The openai package is not installed. Install it with `pip install openai`."
        )

    openai.api_key = _get_openai_api_key()
    response = openai.Embeddings.create(model=model, input=list(texts))
    return [item["embedding"] for item in response["data"]]


def _hf_embeddings(texts: Sequence[str], model: str) -> List[List[float]]:
    if SentenceTransformer is None:
        raise EmbedderError(
            "sentence-transformers is not installed. Install it with `pip install sentence-transformers`."
        )

    model_instance = SentenceTransformer(model)
    embeddings = model_instance.encode(list(texts), show_progress_bar=False)
    if hasattr(embeddings, "tolist"):
        return embeddings.tolist()  # type: ignore[attr-defined]
    return [list(vector) for vector in embeddings]


def _huggingface_embeddings(texts: Sequence[str], model: str) -> List[List[float]]:
    api_key = _get_hf_api_key()
    url = f"https://api-inference.huggingface.co/embeddings/{model}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    request_body = json.dumps({"inputs": list(texts)}).encode("utf-8")

    request = urllib.request.Request(url, data=request_body, headers=headers)
    try:
        with urllib.request.urlopen(request) as response:
            response_text = response.read().decode("utf-8")
            data = json.loads(response_text)
    except urllib.error.HTTPError as exc:
        raise EmbedderError(
            f"Hugging Face API error: {exc.code} {exc.reason}."
        )

    if isinstance(data, dict) and data.get("error"):
        raise EmbedderError(f"Hugging Face API error: {data['error']}")
    if isinstance(data, list):
        return [item["embedding"] if isinstance(item, dict) else item for item in data]
    raise EmbedderError("Unexpected response format from Hugging Face embeddings API.")


def embed_texts(
    texts: Sequence[str],
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> List[List[float]]:
    """Return embeddings for a sequence of texts."""
    provider = _validate_provider(provider or _get_default_provider())
    if provider == "openai":
        return _openai_embeddings(texts, model or DEFAULT_OPENAI_MODEL)
    if provider == "huggingface":
        return _huggingface_embeddings(texts, model or DEFAULT_HF_MODEL)
    return _hf_embeddings(texts, model or DEFAULT_HF_MODEL)


def embed_schema_chunks(
    chunks: Sequence[str],
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> List[dict[str, Any]]:
    """Return chunk metadata with embedding vectors."""
    embeddings = embed_texts(chunks, provider=provider, model=model)
    return [
        {"chunk_id": index + 1, "text": chunk, "embedding": embedding}
        for index, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]


def save_embeddings(
    chunks: Sequence[str],
    embeddings: Sequence[Sequence[float]],
    output_path: Union[str, Path],
) -> Path:
    """Write chunk texts and embeddings to a JSON file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {"chunk_id": index + 1, "text": chunk, "embedding": list(embedding)}
        for index, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]
    output_file.write_text(json.dumps({"chunks": payload}, indent=2), encoding="utf-8")
    return output_file


if __name__ == "__main__":
    try:
        from rag.chunker import create_schema_chunks
    except ImportError:
        from chunker import create_schema_chunks

    chunks = create_schema_chunks()
    try:
        embeddings = embed_texts(chunks)
    except EmbedderError as exc:
        print(f"Embedding failed: {exc}")
        print("Install sentence-transformers, set HUGGINGFACE_API_KEY, or install openai.")
        raise

    output_file = save_embeddings(chunks, embeddings, DEFAULT_OUTPUT_DIR / "schema_embeddings.json")
    print(f"Saved {len(chunks)} embeddings to {output_file}")
