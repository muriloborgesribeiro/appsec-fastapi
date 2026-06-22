import os
import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import (
    AUTH_SRC_DIR,
    DOCS_DIR,
    ML_SRC_DIR,
    RAG_CHUNK_OVERLAP,
    RAG_CHUNK_SIZE,
    RAG_TOP_K,
)

_EXTRA_DOCS = {
    "README.md": os.path.join(os.path.dirname(DOCS_DIR), "README.md"),
}


def _listar_docs() -> list[str]:
    caminhos = []
    if os.path.isdir(DOCS_DIR):
        for fname in sorted(os.listdir(DOCS_DIR)):
            if fname.endswith(".md"):
                caminhos.append(os.path.join(DOCS_DIR, fname))
    if os.path.isdir(ML_SRC_DIR):
        for fname in sorted(os.listdir(ML_SRC_DIR)):
            if fname.endswith(".py") and not fname.startswith("_"):
                caminhos.append(os.path.join(ML_SRC_DIR, fname))
    if os.path.isdir(AUTH_SRC_DIR):
        for fname in sorted(os.listdir(AUTH_SRC_DIR)):
            if fname.endswith(".py") and not fname.startswith("_"):
                caminhos.append(os.path.join(AUTH_SRC_DIR, fname))
    for _, path in _EXTRA_DOCS.items():
        if os.path.isfile(path):
            caminhos.append(path)
    return caminhos


def _chunk_text(texto: str, fonte: str) -> list[dict]:
    chunks = []
    texto_limpo = re.sub(r"\n{3,}", "\n\n", texto.strip())
    inicio = 0
    while inicio < len(texto_limpo):
        fim = min(inicio + RAG_CHUNK_SIZE, len(texto_limpo))
        if fim < len(texto_limpo):
            quebra = texto_limpo.rfind("\n", inicio, fim)
            if quebra > inicio:
                fim = quebra
        chunk = texto_limpo[inicio:fim].strip()
        if chunk:
            chunks.append({"texto": chunk, "fonte": fonte})
        inicio = fim - RAG_CHUNK_OVERLAP if fim < len(texto_limpo) else len(texto_limpo)
    return chunks


def _carregar_chunks() -> list[dict]:
    chunks = []
    for caminho in _listar_docs():
        nome_rel = os.path.relpath(caminho, os.path.dirname(DOCS_DIR))
        try:
            with open(caminho, encoding="utf-8") as f:
                conteudo = f.read()
            chunks.extend(_chunk_text(conteudo, nome_rel))
        except Exception:
            continue
    return chunks


class DocumentStore:
    def __init__(self):
        self._vectorizer: TfidfVectorizer | None = None
        self._matrix: np.ndarray | None = None
        self._chunks: list[dict] = []
        self._carregado = False

    def carregar(self):
        self._chunks = _carregar_chunks()
        if not self._chunks:
            self._carregado = True
            return
        textos = [c["texto"] for c in self._chunks]
        self._vectorizer = TfidfVectorizer(
            analyzer="word",
            token_pattern=r"(?u)\b\w\w+\b",
            max_features=5000,
            stop_words=[
                "de",
                "da",
                "do",
                "em",
                "para",
                "com",
                "um",
                "uma",
                "os",
                "as",
                "e",
                "o",
                "a",
                "que",
                "se",
            ],
        )
        self._matrix = self._vectorizer.fit_transform(textos)
        self._carregado = True

    def buscar(self, pergunta: str, k: int = RAG_TOP_K) -> list[dict]:
        if not self._carregado:
            self.carregar()
        if not self._chunks:
            return []
        if self._vectorizer is None or self._matrix is None:
            return []
        vec_pergunta = self._vectorizer.transform([pergunta])
        similaridades = cosine_similarity(vec_pergunta, self._matrix).flatten()
        indices_top = similaridades.argsort()[::-1][:k]
        indices_top = [i for i in indices_top if similaridades[i] > 0]
        return [
            {
                "texto": self._chunks[i]["texto"],
                "fonte": self._chunks[i]["fonte"],
                "score": float(similaridades[i]),
            }
            for i in indices_top
        ]


_store: DocumentStore | None = None


def get_document_store() -> DocumentStore:
    global _store
    if _store is None:
        _store = DocumentStore()
    return _store
