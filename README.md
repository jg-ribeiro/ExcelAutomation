# Plataforma Web de Automação do Microsoft Excel (Headless)

Esta aplicação evoluiu de um script estático para uma **plataforma web completa de gerenciamento e agendamento de automações do Microsoft Excel via COM**. Ela foi projetada para rodar em modo *headless* em uma VM Windows sob a conta de domínio dedicada:

```text
USACUCAR2000\svc_giautomacao
```

---

## Recursos e Arquitetura

1. **Multi-Arquivo e Multi-Agendamento**:
   - Cadastro dinâmico de planilhas (`.xlsm`, `.xlsx`) via interface web.
   - Cada arquivo possui sua própria regra de agendamento: **diário em horário fixo** (ex: `03:00`) ou **intervalo recorrente** (ex: a cada `10m`, `30m`, `1h`).
   - Macros VBA customizadas (ex: `SalvarTodos`) disparadas após a atualização síncrona das consultas.
2. **Execução Estritamente Serializada (Concorrência = 1)**:
   - Devido ao comportamento do Excel COM sob contas de serviço no Windows, **apenas 1 instância do Excel é executada por vez**.
   - Fila FIFO thread-safe (`worker_queue.py`) com bloqueio global: execuções concorrentes aguardam ordeiramente na fila, eliminando travamentos de sessão.
3. **Persistência em Banco SQLite (`automation.db`)**:
   - Armazenamento de metadados dos jobs, histórico completo de execuções com durações reais, alertas de sobreposição e snippets de log.
4. **Detector Inteligente de Sobreposição com Auto-Pause**:
   - Calcula continuamente a média móvel de duração de cada planilha.
   - Se a duração média ocupar $\ge 85\%$ do intervalo agendado (ex: job que dura 20 min rodando a cada 10 min), o sistema emite alerta destacado de risco de sobreposição.
   - Se nenhuma ação corretiva for tomada após 3 ciclos consecutivos de sobreposição (ou prazo limite), o sistema **pausa automaticamente o job** (sem excluí-lo), protegendo o servidor e a fila.
5. **Visualizador de Logs em Tempo Real (Terminal Escuro)**:
   - Console estilizado nos padrões do design system (`BulkSendingTerminal`) com streaming contínuo via Server-Sent Events (SSE).
   - Filtros por nível (INFO, WARN, ERROR, CRITICAL), busca textual, auto-rolagem, cópia e download de logs.
6. **Interface Moderna em React + TypeScript**:
   - Desenvolvida com **Vite**, **React 19**, **TypeScript** e **Tailwind CSS**.
   - Design System corporativo Indoxa: tipografia **Outfit**, paleta **Slate**, cartões brancos com elevação suave e medidores visuais de margem temporal.
7. **Suporte a Nginx e Servidor Standalone**:
   - A aplicação pode rodar de forma independente via FastAPI na porta `8000`, servindo os arquivos compilados do React em `frontend/dist`.
   - Inclui arquivo de configuração pronto para o **Nginx** (`nginx/excel_automation.conf`) na porta `80`.

---

## Estrutura do Projeto

```text
ExcelAutomationVM/
├── backend/
│   ├── app/
│   │   ├── api/                     # Rotas REST e streaming SSE
│   │   │   ├── routes_jobs.py       # CRUD de planilhas e disparo manual
│   │   │   ├── routes_executions.py # Histórico de execuções
│   │   │   ├── routes_alerts.py     # Alertas de sobreposição e conflito
│   │   │   ├── routes_logs.py       # Streaming SSE de logs
│   │   │   └── routes_system.py     # Status da fila e saúde do sistema
│   │   ├── core/                    # Configurações, modelos e SQLite
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── models.py
│   │   │   └── log_handler.py
│   │   ├── engine/                  # Motores de execução
│   │   │   ├── worker_queue.py      # Fila serializada (Lock global = 1)
│   │   │   ├── scheduler_service.py # APScheduler dinâmico
│   │   │   ├── conflict_detector.py # Algoritmo de sobreposição e auto-pause
│   │   │   └── dynamic_runner.py    # Executor dinâmico integrado a COM
│   │   └── main.py                  # Aplicação FastAPI
│   └── tests/                       # Testes unitários e de integração
├── frontend/                        # Interface React + TypeScript + Vite
│   ├── src/
│   │   ├── components/              # Componentes do design system
│   │   ├── services/api.ts          # Cliente da API
│   │   ├── types/                   # Tipagens TypeScript
│   │   └── App.tsx                  # Aplicação principal
│   └── dist/                        # Build estático de produção
├── nginx/
│   └── excel_automation.conf        # Configuração do proxy reverso para Nginx
├── app_server.py                    # Servidor web unificado (FastAPI + Worker + Scheduler)
├── excel_manager.py                 # Gerenciador COM com force-kill e watchdog de modais
├── file_guard.py                    # Verificador de lock de arquivos em rede UNC
├── requirements.txt                 # Dependências Python atualizadas
└── automation.db                    # Banco de dados SQLite persistente
```

---

## Como Executar

### 1. Iniciar o Servidor Web e Agendador

Execute o servidor unificado:

```powershell
.\.venv\Scripts\python.exe app_server.py
```

A aplicação iniciará o Uvicorn, o banco SQLite, a fila serializada e o agendador na porta **8000**:
- **Interface Web**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Documentação da API (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Executar com Nginx

O Nginx instalado em `C:\nginx` já está configurado para servir a aplicação na porta padrão `80`:

```powershell
# Iniciar o Nginx
C:\nginx\nginx.exe -p C:\nginx

# Recarregar configurações se necessário
C:\nginx\nginx.exe -p C:\nginx -s reload
```

Com o Nginx ativo, acesse diretamente: [http://localhost](http://localhost)

---

## Configuração do Serviço no Windows (NSSM)

Para manter o serviço em execução contínua no Windows após reinicializações:

1. No NSSM, configure o serviço para executar `app_server.py`:
   - **Path**: `C:\Auteq\ExcelAutomationVM\.venv\Scripts\python.exe`
   - **Startup directory**: `C:\Auteq\ExcelAutomationVM`
   - **Arguments**: `app_server.py`
2. Na aba **Log on**, configure a conta de serviço:
   ```text
   USACUCAR2000\svc_giautomacao
   ```
3. Garanta que a conta possua privilégios de **Log on as a service** e permissões DCOM configuradas conforme o manual original.
