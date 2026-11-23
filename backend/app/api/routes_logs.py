import asyncio
import json
from typing import Optional
from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse

from backend.app.core.log_handler import get_recent_logs, subscribe_logs, unsubscribe_logs

router = APIRouter(prefix="/api/logs", tags=["Logs"])


@router.get("")
def list_logs(
    limit: int = Query(200, ge=10, le=1000),
    level: Optional[str] = Query(None, description="Filtrar por nível: INFO, WARNING, ERROR, CRITICAL"),
    search: Optional[str] = Query(None, description="Busca textual na mensagem")
):
    """Retorna os logs mais recentes armazenados no ring-buffer em memória."""
    logs = get_recent_logs(limit=limit, level=level, search=search)
    return {"total": len(logs), "logs": logs}


@router.get("/stream")
async def stream_logs(request: Request):
    """
    Streaming de logs em tempo real via Server-Sent Events (SSE).
    Permite à interface web renderizar os eventos instantaneamente no terminal escuro.
    """
    async def event_generator():
        q = subscribe_logs()
        try:
            # Envia os últimos 30 logs como carga inicial
            initial_logs = get_recent_logs(limit=30)
            for item in initial_logs:
                yield f"data: {json.dumps(item)}\n\n"

            # Transmite novos logs conforme forem emitidos
            while True:
                if await request.is_disconnected():
                    break
                try:
                    entry = await asyncio.wait_for(q.get(), timeout=20.0)
                    yield f"data: {json.dumps(entry)}\n\n"
                except asyncio.TimeoutError:
                    # Envia ping de heartbeat para manter a conexão SSE ativa
                    yield ": ping\n\n"
        finally:
            unsubscribe_logs(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
