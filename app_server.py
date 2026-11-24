import uvicorn
import sys
from pathlib import Path

# Adiciona raiz ao path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.core.config import SERVER_HOST, SERVER_PORT
from backend.app.main import app

def main():
    print("================================================================================")
    print(f"Iniciando Plataforma de Automação Excel (FastAPI + Uvicorn na porta {SERVER_PORT})...")
    print(f"Acesse a interface web em: http://127.0.0.1:{SERVER_PORT}")
    print(f"Documentação da API em:   http://127.0.0.1:{SERVER_PORT}/docs")
    print("================================================================================")
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT, log_level="info")

if __name__ == "__main__":
    main()
