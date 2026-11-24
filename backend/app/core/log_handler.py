import asyncio
from collections import deque
from datetime import datetime
import json
import logging
from typing import Dict, List, Optional, Set
import threading

from backend.app.core.config import RING_BUFFER_CAPACITY

# Fila circular em memória para acesso ultrarrápido aos logs recentes
log_buffer: deque = deque(maxlen=RING_BUFFER_CAPACITY)
_buffer_lock = threading.Lock()

# Conjunto de filas ativas para streaming SSE
_subscribers: Set[asyncio.Queue] = set()
_subscribers_lock = threading.Lock()


class InMemoryBroadcastLogHandler(logging.Handler):
    """
    Handler de log customizado que:
    1. Armazena as mensagens formatadas em uma fila circular em memória.
    2. Transmite instantaneamente para todos os clientes conectados ao Server-Sent Events (SSE).
    """

    def emit(self, record: logging.LogRecord):
        try:
            entry = {
                "id": f"{record.created:.6f}",
                "timestamp": datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S"),
                "level": record.levelname,
                "name": record.name,
                "message": record.getMessage()
            }

            with _buffer_lock:
                log_buffer.append(entry)

            # Transmite para subscribers assíncronos
            with _subscribers_lock:
                for q in list(_subscribers):
                    try:
                        q.put_nowait(entry)
                    except Exception:
                        pass
        except Exception:
            self.handleError(record)


def get_recent_logs(
    limit: int = 200,
    level: Optional[str] = None,
    search: Optional[str] = None
) -> List[Dict]:
    """Retorna logs recentes com filtros aplicados."""
    with _buffer_lock:
        logs = list(log_buffer)

    if level:
        level_upper = level.upper()
        logs = [entry for entry in logs if entry["level"] == level_upper]

    if search:
        search_lower = search.lower()
        logs = [
            entry for entry in logs
            if search_lower in entry["message"].lower() or search_lower in entry["name"].lower()
        ]

    return logs[-limit:]


def subscribe_logs() -> asyncio.Queue:
    """Registra um novo subscriber para streaming SSE."""
    q = asyncio.Queue(maxsize=100)
    with _subscribers_lock:
        _subscribers.add(q)
    return q


def unsubscribe_logs(q: asyncio.Queue):
    """Remove um subscriber SSE."""
    with _subscribers_lock:
        _subscribers.discard(q)
