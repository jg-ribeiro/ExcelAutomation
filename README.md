# Automação de Excel em modo headless

Esta aplicação automatiza o Microsoft Excel com Python e `pywin32`. Ela é
executada sem interface gráfica em uma VM Windows e é registrada como um
**Windows Service pelo NSSM (Non-Sucking Service Manager)**.

O serviço deve executar usando a conta de domínio dedicada:

```text
USACUCAR2000\svc_giautomacao
```

---

## Camada de Segurança e Resiliência

A aplicação conta com uma camada de segurança projetada para impedir travamentos e bloqueios de arquivos:

1. **Eliminação Garantida de Processos Zumbis**:
   - Cada instância criada via COM tem seu PID do Windows capturado imediatamente.
   - O encerramento ocorre via Context Manager (`ExcelSession`).
   - Se o Excel não encerrar normalmente após o grace period (15s), o script executa `kill` forçado **apenas naquele PID específico**.
2. **Atualização Síncrona das Consultas**:
   - As conexões Power Query / OLEDB / ODBC têm `BackgroundQuery` forçado para `False`.
   - Isso elimina qualquer risco de a macro `SalvarTodos` rodar antes do término da atualização dos dados.
3. **Proteção de Timeout nas Consultas**:
   - Se a atualização das consultas exceder o tempo limite configurado (`QUERY_REFRESH_TIMEOUT`), a aplicação aborta e elimina o processo, impedindo congelamento por problemas de rede ou banco.
4. **Guarda de Bloqueio de Arquivo (`file_guard`)**:
   - Antes de iniciar, verifica se o workbook de rede está livre para gravação. Se outro usuário ou processo estiver com o arquivo aberto, aguarda com retry ou emite diagnóstico claro com o nome do usuário.
5. **Supressão de Diálogos Modais**:
   - Além de `DisplayAlerts = False` e `Interactive = False`, uma thread monitora e descarta caixas de diálogo modais invisíveis (`#32770`).
6. **Blindagem do Agendador**:
   - Falhas ou exceções em uma execução diária são capturadas e logadas sem interromper o serviço do `scheduler.py` para os dias seguintes.

---

## Estrutura do Projeto

```text
ExcelAutomationVM/
├── config.py             # Configurações centralizadas (caminhos, timeouts, horários)
├── excel_manager.py      # Gerenciador de ciclo de vida do Excel (PID, ContextManager, Kill)
├── file_guard.py         # Verificação de locks de arquivo e detecção de proprietários
├── runner.py             # Rotina principal de execução com todas as proteções
├── mock_simple.py        # Módulo de compatibilidade (redireciona para runner.py)
├── scheduler.py          # Agendador resiliente diário com heartbeats
├── requirements.txt      # Dependências (pywin32, schedule)
└── README.md             # Esta documentação
```

---

## Pré-requisitos

- Microsoft Excel instalado e licenciado na VM.
- Python e as dependências de `requirements.txt` instaladas.
- A conta `USACUCAR2000\svc_giautomacao` com acesso ao diretório da aplicação
  e aos arquivos que serão processados.
- Permissão de compartilhamento **e** NTFS para a conta no caminho de rede
  utilizado pelos workbooks, por exemplo `\\usa9fs2\CPC_GI\...`.
- A conta deve possuir o direito local **Log on as a service**, pois o NSSM a
  utiliza para executar o processo.

---

## Configuração do serviço no NSSM

No NSSM, configure o serviço para iniciar o interpretador Python do ambiente
virtual e informe o script `scheduler.py` (ou `runner.py`) como argumento:

- **Path**: `C:\Auteq\ExcelAutomationVM\.venv\Scripts\python.exe`
- **Startup directory**: `C:\Auteq\ExcelAutomationVM`
- **Arguments**: `scheduler.py`

Em **Log on**, selecione a conta:

```text
USACUCAR2000\svc_giautomacao
```

---

## Execução Manual e Testes

Para testar a automação manualmente via terminal a qualquer momento:

```powershell
# Executa a rotina imediatamente
.\.venv\Scripts\python.exe runner.py

# Ou inicia o scheduler executando um ciclo de imediato para teste
.\.venv\Scripts\python.exe scheduler.py --now
```

---

## Permissões DCOM do Excel

O Excel é instanciado pela aplicação por meio de COM:

```python
excel = win32.DispatchEx("Excel.Application")
```

Para permitir que esse comando funcione a partir do serviço, abra `dcomcnfg`
como administrador e acesse:

```text
Component Services
  > Computers
  > My Computer
  > DCOM Config
  > Microsoft Excel Application
  > Properties
```

### Security

Em **Launch and Activation Permissions**, selecione **Customize** e clique em
**Edit**. Adicione `USACUCAR2000\svc_giautomacao` e permita:

- Local Launch
- Local Activation

Em **Access Permissions**, também selecione **Customize** e clique em
**Edit**. Adicione a mesma conta e permita:

- Local Access

### Identity

Em **Identity**, use:
- **The launching user**: recomendada quando o processo iniciado pelo NSSM já
  roda como `USACUCAR2000\svc_giautomacao`.
- **This user**: alternativa para forçar o Excel a sempre iniciar com
  `USACUCAR2000\svc_giautomacao`.
