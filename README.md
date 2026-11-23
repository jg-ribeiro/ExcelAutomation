# Automação de Excel em modo headless

Esta aplicação automatiza o Microsoft Excel com Python e `pywin32`. Ela é
executada sem interface gráfica em uma VM Windows e é registrada como um
**Windows Service pelo NSSM (Non-Sucking Service Manager)**.

O serviço deve executar usando a conta de domínio dedicada:

```text
USACUCAR2000\svc_giautomacao
```

## Pré-requisitos

- Microsoft Excel instalado e licenciado na VM.
- Python e as dependências de `requirements.txt` instaladas.
- A conta `USACUCAR2000\svc_giautomacao` com acesso ao diretório da aplicação
  e aos arquivos que serão processados.
- Permissão de compartilhamento **e** NTFS para a conta no caminho de rede
  utilizado pelos workbooks, por exemplo `\\usa9fs2\CPC_GI\...`.
- A conta deve possuir o direito local **Log on as a service**, pois o NSSM a
  utiliza para executar o processo.

## Configuração do serviço no NSSM

No NSSM, configure o serviço para iniciar o interpretador Python do ambiente
virtual e informe o módulo/script da automação como argumento. Em **Log on**,
selecione a conta:

```text
USACUCAR2000\svc_giautomacao
```

Use a senha vigente da conta e configure o diretório de trabalho como a pasta
da aplicação. O mais importante é que o processo Python e o Excel criado por
ele tenham uma identidade coerente: a conta do serviço deve ser a mesma conta
autorizada no DCOM.

Após alterar a identidade, senha ou permissões da conta, reinicie o serviço
NSSM antes de testar novamente.

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

Como o Python e o Excel rodam na mesma VM, as permissões locais são as
necessárias. Permissões remotas só são necessárias se a ativação COM vier de
outra máquina.

### Identity

Em **Identity**, use uma das opções abaixo:

- **The launching user**: recomendada quando o processo iniciado pelo NSSM já
  roda como `USACUCAR2000\svc_giautomacao`.
- **This user**: alternativa para forçar o Excel a sempre iniciar com
  `USACUCAR2000\svc_giautomacao`; informe usuário e senha atualizados.

Não use **The interactive user** neste cenário. Um Windows Service não dispõe
de uma sessão de desktop interativa confiável.

### Limites globais do DCOM

Se a configuração específica do Excel não resolver, verifique os limites da
máquina em:

```text
Component Services
  > Computers
  > My Computer
  > Properties
  > COM Security
  > Launch and Activation Permissions
  > Edit Limits
```

Adicione `USACUCAR2000\svc_giautomacao` e permita **Local Launch** e
**Local Activation**. Esses limites têm precedência e podem bloquear a
ativação mesmo quando a permissão de `Microsoft Excel Application` está
correta.

## Diagnóstico

O erro abaixo indica que a conta que executa o serviço não tem permissão DCOM
para criar a instância do Excel:

```text
pywintypes.com_error: (-2147024891, 'Access is denied.', None, None)
```

Código hexadecimal equivalente: `0x80070005` (`E_ACCESSDENIED`). Verifique,
nesta ordem:

1. A guia **Log on** do serviço NSSM usa `USACUCAR2000\svc_giautomacao`.
2. A conta possui **Log on as a service**.
3. As permissões DCOM locais foram concedidas à conta.
4. A identidade DCOM não está definida como **The interactive user**.
5. O serviço foi reiniciado após as alterações.
6. Após o Excel iniciar, a conta tem acesso ao compartilhamento e às pastas
   dos workbooks.

Consulte também os eventos DCOM no **Event Viewer** (`Windows Logs > System`)
para identificar permissões ou AppIDs bloqueados.

## Observação sobre suporte

O Microsoft Office foi concebido para uso interativo. A Microsoft não oferece
suporte formal à automação não assistida de Office em serviços, DCOM, ASP.NET
ou processos semelhantes. Portanto, monitore o serviço: caixas de diálogo
invisíveis, complementos, atualização do Office e ausência de perfil do
usuário podem causar travamentos.

Referências:

- [Considerations for server-side Automation of Office](https://support.microsoft.com/en-US/Visio/considerations-for-server-side-automation-of-office)
- [Setting Process-Wide Security Using DCOMCNFG](https://learn.microsoft.com/en-us/windows/win32/com/setting-processwide-security-using-dcomcnfg)
