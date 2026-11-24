import uvicorn
import sys
from pathlib import Path

# Adiciona raiz ao path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.main import app

def main():
    print("================================================================================")
    print("Iniciando Plataforma de Automação Excel (FastAPI + Uvicorn na porta 8000)...")
    print("Acesse a interface web em: http://127.0.0.1:8000")
    print("Documentação da API em:   http://127.0.0.1:8000/docs")
    print("================================================================================")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    main()
