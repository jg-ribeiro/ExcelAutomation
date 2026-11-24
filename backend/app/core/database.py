import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.app.core.config import DATABASE_URL
from backend.app.core.models import Base, Job

logger = logging.getLogger("ExcelAutomation")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Necessário para SQLite multi-thread
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency para injeção de sessão do banco no FastAPI."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Cria as tabelas caso não existam e faz seed da automação legada se estiver vazia."""
    logger.info("[DATABASE] Inicializando banco de dados SQLite...")
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        job_count = db.query(Job).count()
        if job_count == 0:
            logger.info("[DATABASE] Nenhum job encontrado. Fazendo seed da automação existente (Moagem 2026)...")
            seed_job = Job(
                name="Placar da Moagem 2026",
                file_path=r"\\usa9fs2\CPC_GI\02 - Agrícola\01 - Diário\2026\01 - Placar da Moagem\00 - Moagem - 2026.xlsm",
                macro_name="SalvarTodos",
                schedule_type="daily",
                schedule_value="03:00",
                is_active=True,
                query_timeout=300,
                lock_timeout=120
            )
            db.add(seed_job)
            db.commit()
            logger.info(f"[DATABASE] Job inicial '{seed_job.name}' cadastrado com sucesso (ID: {seed_job.id}).")
        else:
            logger.info(f"[DATABASE] Banco pronto. {job_count} job(s) cadastrado(s).")
