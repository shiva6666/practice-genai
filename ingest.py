"""Build index.json by chunking source files and embedding each chunk."""
import ast
import json
import os
from pathlib import Path

from google import genai
from google.genai import types


ROOT = Path.cwd().resolve()
CHUNK_TARGET = 2000
OVERLAP = 200
BATCH_SIZE = 100
MODEL = "gemini-embedding-001"
CODE_EXTENSIONS = {
    ".c", ".cc", ".cpp", ".cs", ".css", ".go", ".h", ".hpp", ".html",
    ".java", ".js", ".jsx", ".kt", ".md", ".mjs", ".php", ".py", ".rb",
    ".rs", ".scss", ".sh", ".sql", ".swift", ".ts", ".tsx", ".vue", ".yaml",
    ".yml",
}
IGNORED_DIRECTORIES = {
    ".git", ".hg", ".svn", ".venv", "venv", "__pycache__", "node_modules",
    "build", "dist", "target",
}


def embed_texts(texts):
    """Embed a batch of document chunks for later retrieval."""
    if not texts:
        return []

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit("Set GEMINI_API_KEY or GOOGLE_API_KEY before running ingest.py.")

    client = genai.Client(api_key=api_key)
    result = client.models.embed_content(
        model=MODEL,
        contents=texts,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
    )
    return [embedding.values for embedding in result.embeddings]


def iter_code_files():
    """Yield supported source and documentation files under ROOT."""
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRECTORIES for part in path.relative_to(ROOT).parts):
            continue
        if path.suffix.lower() in CODE_EXTENSIONS:
            yield path


def _make_chunk(source, text, start_line):
    text = text.strip()
    if not text:
        return None
    line_count = text.count("\n") + 1
    return {
        "source": source,
        "start_line": start_line,
        "end_line": start_line + line_count - 1,
        "text": text,
    }


def chunk_generic(source, text):
    """Split text into fixed-size character windows with a small overlap."""
    chunks = []
    position = 0

    while position < len(text):
        end = min(position + CHUNK_TARGET, len(text))
        if end < len(text):
            newline = text.rfind("\n", position, end)
            if newline > position + CHUNK_TARGET // 2:
                end = newline + 1

        chunk = _make_chunk(source, text[position:end], text.count("\n", 0, position) + 1)
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        position = max(end - OVERLAP, position + 1)

    return chunks


def chunk_python(source, text):
    """Split Python at top-level definitions, falling back when parsing fails."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return chunk_generic(source, text)

    definitions = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start_line = min(
                [node.lineno, *(decorator.lineno for decorator in node.decorator_list)]
            )
            definitions.append(start_line)

    if not definitions:
        return chunk_generic(source, text)

    lines = text.splitlines()
    boundaries = [1, *definitions, len(lines) + 1]
    chunks = []
    for index in range(len(boundaries) - 1):
        start_line = boundaries[index]
        end_line = boundaries[index + 1] - 1
        section = "\n".join(lines[start_line - 1:end_line])
        if section.strip():
            if len(section) > CHUNK_TARGET:
                section_chunks = chunk_generic(source, section)
                for chunk in section_chunks:
                    chunk["start_line"] += start_line - 1
                    chunk["end_line"] += start_line - 1
                chunks.extend(section_chunks)
            else:
                chunks.append(_make_chunk(source, section, start_line))

    return chunks


def chunk_text(source, text):
    """Choose AST-aware chunking for Python and window chunking otherwise."""
    if Path(source).suffix.lower() == ".py":
        return chunk_python(source, text)
    return chunk_generic(source, text)


def main():
    chunks = []
    file_count = 0

    for path in iter_code_files():
        file_count += 1
        source = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        chunks.extend(chunk_text(source, text))

    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start:start + BATCH_SIZE]
        embeddings = embed_texts([chunk["text"] for chunk in batch])
        if len(embeddings) != len(batch):
            raise RuntimeError("Gemini returned a different number of embeddings than inputs.")
        for chunk, embedding in zip(batch, embeddings):
            chunk["embedding"] = embedding

    index = {"model": MODEL, "chunks": chunks}
    output_path = ROOT / "index.json"
    output_path.write_text(json.dumps(index, ensure_ascii=True), encoding="utf-8")
    print(f"Indexed {len(chunks)} chunks from {file_count} files into {output_path}.")


if __name__ == "__main__":
    main()