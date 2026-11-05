# JN X!T Token Optimizer

CLI para OpenAI-compatible, Anthropic e outros adaptadores. Possui modos Normal/Lite/SuperLite, streaming, tokens em tempo real, throughput e sessões persistentes por pasta.

## Instalação

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\jnx.ps1
```

Abra um terminal novo:

```powershell
jnx init
```

## Configuração

```powershell
jnx config provider openai
jnx config providers.openai.api_key SUA_CHAVE
jnx config providers.openai.base_url https://api.openai.com/v1/chat/completions
jnx config mode superlite
```

Anthropic:

```powershell
jnx config provider anthropic
jnx config providers.anthropic.api_key SUA_CHAVE
```

## Sessões persistentes

A sessão é identificada pela pasta atual. Fechar o CMD não apaga a conversa.

```powershell
cd C:\Projetos\MeuApp
jnx ask "analise este projeto"
```

Depois, mesmo fechando o terminal:

```powershell
cd C:\Projetos\MeuApp
jnx ask "continue de onde paramos"
jnx session
```

Arquivos ficam em:

```text
%USERPROFILE%\.jnx\sessions\<id-da-pasta>.json
```

Cada sessão salva:

- mensagens recentes;
- resumo acumulado;
- pasta de origem;
- data de criação;
- contexto usado na próxima chamada.

O resumo é atualizado após cada resposta. O modo Lite ou SuperLite envia o resumo e apenas a janela recente, evitando reenviar toda a conversa.

## Monitoramento em tempo real

Durante streaming:

```text
tokens~1830 | output~410 | 42.3 tok/s
```

Ao terminar:

```text
tokens=2510 | prompt~1830 | output~680 | 38.7 tok/s
Sessão salva e resumida: C:\Users\...\.jnx\sessions\....json
```

Se a API fornecer `usage`, o valor real é usado. Caso contrário, aparece uma estimativa baseada no tamanho UTF-8. O histórico fica em `%USERPROFILE%\.jnx\usage.jsonl`.

## Modos

- `normal`: mantém o prompt sem compactação.
- `lite`: mantém início/fim e resumo da parte central.
- `superlite`: envia resumo acumulado e janela curta, com orçamento limitado.

```powershell
jnx config mode normal
jnx config mode lite
jnx config mode superlite
jnx usage
```

## MCP

O instalador também cria `jnx-mcp`. Ele conecta a um servidor MCP via STDIO, inicializa o protocolo e lista as ferramentas disponíveis:

```powershell
jnx-mcp npx -y @modelcontextprotocol/server-filesystem C:\Projetos\MeuApp
```

Isso permite validar servidores MCP antes de conectá-los ao roteador de tarefas. O bridge usa JSON-RPC sobre STDIO e não envia credenciais para o servidor.
