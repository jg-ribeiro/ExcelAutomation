from contextlib import asynccontextmanager
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Configuração de caminhos raiz
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app.core.config import LOG_FILE, LOG_MAX_BYTES, LOG_BACKUP_COUNT, SERVE_STATIC
from backend.app.core.database import init_db
from backend.app.core.log_handler import InMemoryBroadcastLogHandler
from backend.app.engine.worker_queue import worker_queue
from backend.app.engine.scheduler_service import SchedulerService
from backend.app.api.routes_jobs import router as jobs_router, set_scheduler
from backend.app.api.routes_executions import router as executions_router
from backend.app.api.routes_alerts import router as alerts_router
from backend.app.api.routes_logs import router as logs_router
from backend.app.api.routes_system import router as system_router
from backend.app.api.routes_auth import router as auth_router

# Configuração do Logger
def setup_logging():
    logger = logging.getLogger("ExcelAutomation")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File Handler com Rotação
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # In-Memory Broadcast Handler (SSE / Terminal UI)
    broadcast_handler = InMemoryBroadcastLogHandler()
    broadcast_handler.setFormatter(formatter)
    logger.addHandler(broadcast_handler)

    return logger

app_logger = setup_logging()

# Inicialização do APScheduler
scheduler_service = SchedulerService(worker_queue)
set_scheduler(scheduler_service)
worker_queue.set_scheduler_service(scheduler_service)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app_logger.info("================================================================================")
    app_logger.info(">>> INICIANDO SERVIDOR WEB E PLATAFORMA DE AUTOMAÇÃO EXCEL")
    app_logger.info("================================================================================")

    # 1. Inicializa banco e tabelas SQLite
    init_db()

    # 2. Inicia Worker de Fila Serializada (Concorrência = 1)
    worker_queue.start()

    # 3. Inicia Agendador APScheduler
    scheduler_service.start()

    yield

    # Encerramento gracioso
    app_logger.info(">>> Encerrando Agendador e Fila de Execução...")
    scheduler_service.shutdown()
    worker_queue.stop()
    app_logger.info(">>> Servidor finalizado com sucesso.")


app = FastAPI(
    title="Excel Automation Web Platform",
    description="Plataforma de gerenciamento e agendamento de automações headless do Microsoft Excel",
    version="2.0.0",
    lifespan=lifespan
)

# Suporte a CORS para desenvolvimento Vite e Nginx
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro dos Routers da API REST
app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(executions_router)
app.include_router(alerts_router)
app.include_router(logs_router)
app.include_router(system_router)

# Suporte condicional para servir o frontend compilado via Python (parametrizado via SERVE_STATIC no .env)
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
if SERVE_STATIC and FRONTEND_DIST.exists():
    app_logger.info("[HTTP] SERVE_STATIC=True: FastAPI montando arquivos estáticos de frontend/dist na raiz.")
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
else:
    app_logger.info("[HTTP] SERVE_STATIC=False: FastAPI operando estritamente como API REST (entrega estática pelo Nginx).")
