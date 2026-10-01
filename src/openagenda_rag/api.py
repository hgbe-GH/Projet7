from __future__ import annotations

from typing import Any
import httpx

from fastapi import FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from openagenda_rag.service import OpenAgendaRAGService
from openagenda_rag.settings import load_api_settings


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question utilisateur envoyee au chatbot.")


class SourceResponse(BaseModel):
    event_uid: str | None = None
    chunk_id: str | None = None
    title: str | None = None
    city: str | None = None
    location_name: str | None = None
    first_timing: str | None = None
    last_timing: str | None = None
    canonical_url: str | None = None
    categories: list[str] = Field(default_factory=list)


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceResponse]
    retrieved_chunk_count: int


class RebuildRequest(BaseModel):
    batch_size: int | None = Field(default=None, ge=1)
    chunk_size: int | None = Field(default=None, ge=1)
    chunk_overlap: int | None = Field(default=None, ge=0)
    embedding_model: str | None = None


class RebuildResponse(BaseModel):
    manifest_path: str
    indexed_documents_path: str
    indexed_event_count: int
    indexed_document_count: int
    output_dir: str
    manifest: dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    index_dir: str
    chat_model: str
    embedding_model: str
    top_k: int


def _get_service(request: Request) -> OpenAgendaRAGService:
    return request.app.state.service


def _provider_http_error(exc: httpx.HTTPStatusError) -> HTTPException:
    upstream_status = exc.response.status_code
    if upstream_status == 429:
        return HTTPException(status_code=503, detail="Fournisseur Mistral limité (HTTP 429). Réessayer plus tard ou vérifier les limites du modèle.")
    if upstream_status in (401, 403):
        return HTTPException(status_code=503, detail="Accès au fournisseur Mistral indisponible. Vérifier la configuration côté serveur.")
    return HTTPException(status_code=502, detail="Le fournisseur Mistral a renvoyé une erreur. Aucun résultat généré.")


def create_app(service: OpenAgendaRAGService | None = None) -> FastAPI:
    app = FastAPI(
        title="OpenAgenda RAG API",
        version="0.1.0",
        description=(
            "API REST locale exposee autour du moteur RAG OpenAgenda. "
            "Utilisez /ask pour poser une question et /rebuild pour reconstruire l'index."
        ),
    )
    app.state.service = service or OpenAgendaRAGService.from_env()
    app.state.api_settings = load_api_settings()

    @app.get("/health", response_model=HealthResponse, summary="Verifier l'etat de l'API")
    def health(request: Request) -> HealthResponse:
        return HealthResponse(**_get_service(request).health())

    @app.post("/ask", response_model=AskResponse, summary="Poser une question au chatbot")
    def ask(payload: AskRequest, request: Request) -> AskResponse:
        question = payload.question.strip()
        if not question:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question must not be empty.")
        try:
            response = _get_service(request).ask(question)
        except httpx.HTTPStatusError as exc:
            raise _provider_http_error(exc) from exc
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail="Le fournisseur Mistral ne répond pas. Réessayer plus tard.") from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne du moteur RAG.") from exc
        return AskResponse(**response)

    @app.post("/rebuild", response_model=RebuildResponse, summary="Reconstruire l'index vectoriel FAISS")
    def rebuild(
        payload: RebuildRequest,
        request: Request,
        x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    ) -> RebuildResponse:
        service = _get_service(request)
        configured_token = request.app.state.api_settings.rebuild_token
        if configured_token and x_admin_token != configured_token:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin token.")
        if payload.chunk_size and payload.chunk_overlap is not None and payload.chunk_overlap >= payload.chunk_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="chunk_overlap must be smaller than chunk_size.",
            )
        try:
            response = service.rebuild(
                batch_size=payload.batch_size,
                chunk_size=payload.chunk_size,
                chunk_overlap=payload.chunk_overlap,
                embedding_model=payload.embedding_model,
            )
        except httpx.HTTPStatusError as exc:
            raise _provider_http_error(exc) from exc
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail="Le fournisseur Mistral ne répond pas. Réessayer plus tard.") from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne pendant la reconstruction.") from exc
        return RebuildResponse(**response)

    return app


app = create_app()
