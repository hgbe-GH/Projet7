from __future__ import annotations

from pathlib import Path
from typing import Any

from openagenda_rag.indexing import rebuild_index_artifacts
from openagenda_rag.rag import answer_question, build_chat_model, build_retriever
from openagenda_rag.settings import IndexSettings, RagSettings, load_index_settings, load_rag_settings


class OpenAgendaRAGService:
    def __init__(self, rag_settings: RagSettings, index_settings: IndexSettings):
        self.rag_settings = rag_settings
        self.index_settings = index_settings
        self._retriever: Any = None
        self._chat_model: Any = None

    @classmethod
    def from_env(cls) -> "OpenAgendaRAGService":
        return cls(
            rag_settings=load_rag_settings(),
            index_settings=load_index_settings(),
        )

    def _resolve_path(self, path: Path) -> Path:
        if path.is_absolute():
            return path
        return Path.cwd() / path

    def _ensure_runtime(self) -> tuple[Any, Any]:
        api_key = self.rag_settings.mistral_api_key
        if not api_key:
            raise ValueError("MISTRAL_API_KEY or MISTRALAI_API_KEY is required.")

        if self._retriever is None:
            self._retriever = build_retriever(
                index_output_dir=self._resolve_path(self.rag_settings.index_output_dir),
                embedding_model=self.rag_settings.embedding_model,
                api_key=api_key,
                top_k=self.rag_settings.top_k,
            )
        if self._chat_model is None:
            self._chat_model = build_chat_model(
                model_name=self.rag_settings.chat_model,
                api_key=api_key,
                temperature=self.rag_settings.temperature,
                max_tokens=self.rag_settings.max_tokens,
            )
        return self._retriever, self._chat_model

    def ask(self, question: str) -> dict[str, Any]:
        retriever, chat_model = self._ensure_runtime()
        return answer_question(question=question, retriever=retriever, chat_model=chat_model)

    def ask_for_evaluation(self, question: str) -> dict[str, Any]:
        retriever, chat_model = self._ensure_runtime()
        return answer_question(
            question=question,
            retriever=retriever,
            chat_model=chat_model,
            include_contexts=True,
        )

    def rebuild(
        self,
        *,
        batch_size: int | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        embedding_model: str | None = None,
    ) -> dict[str, Any]:
        api_key = self.rag_settings.mistral_api_key
        if not api_key:
            raise ValueError("MISTRAL_API_KEY or MISTRALAI_API_KEY is required.")

        input_path = self._resolve_path(self.index_settings.input_path)
        output_dir = self._resolve_path(self.index_settings.output_dir)
        payload = rebuild_index_artifacts(
            input_path=input_path,
            output_dir=output_dir,
            embedding_model=embedding_model or self.index_settings.embedding_model,
            api_key=api_key,
            batch_size=batch_size or self.index_settings.batch_size,
            chunk_size=chunk_size or self.index_settings.chunk_size,
            chunk_overlap=self.index_settings.chunk_overlap if chunk_overlap is None else chunk_overlap,
            rebuild_requested=True,
        )
        self._retriever = None
        self._chat_model = None
        if embedding_model:
            self.rag_settings.embedding_model = embedding_model
            self.index_settings.embedding_model = embedding_model
        if batch_size:
            self.index_settings.batch_size = batch_size
        if chunk_size:
            self.index_settings.chunk_size = chunk_size
        if chunk_overlap is not None:
            self.index_settings.chunk_overlap = chunk_overlap
        return payload

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "index_dir": str(self._resolve_path(self.rag_settings.index_output_dir)),
            "chat_model": self.rag_settings.chat_model,
            "embedding_model": self.rag_settings.embedding_model,
            "top_k": self.rag_settings.top_k,
        }
