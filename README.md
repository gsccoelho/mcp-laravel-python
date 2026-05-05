# 🧩 mcp-laravel

> Servidor **Model Context Protocol (MCP)** em Python para automatizar a criação
> de repositórios, contracts e injeção de dependência no Laravel — direto do seu
> editor com IA.

---

## ✨ O que ele faz

Com um simples prompt para a IA, o servidor gera automaticamente:

| Artefato               | Caminho gerado                                                |
| ---------------------- | ------------------------------------------------------------- |
| **Contract**           | `app/Repositories/Contracts/{Entidade}RepositoryContract.php` |
| **Repository**         | `app/Repositories/Eloquent/{Entidade}RepositoryEloquent.php`  |
| **AppServiceProvider** | Bindings registrados automaticamente                          |

---

## 📋 Pré-requisitos

- **Python 3.10+** instalado e adicionado ao `PATH`

---

## 🚀 Instalação

**Primeira instalação:**

```bash
pip install mcp-laravel
```

**Atualizar para a versão mais recente:**

```bash
pip install --upgrade mcp-laravel
```

---

## ⚙️ Configuração na IDE

Adicione o bloco abaixo ao seu arquivo `mcp.json` (VS Code ou Cursor):

```json
{
  "mcpServers": {
    "mcp-laravel": {
      "command": "python",
      "args": ["-m", "mcp_laravel.app"]
    }
  }
}
```

Após salvar, recarregue a janela do editor:

- **VS Code / Cursor:** `Ctrl+Shift+P` → `Developer: Reload Window`
- **Ou** clique em **Restart** no painel de configurações do MCP

---

## 💬 Como usar

Com o servidor ativo, basta pedir para a IA no chat do seu editor:

```
Crie a estrutura de repositórios e contracts para a model `Cliente` no meu projeto Laravel.
```

O MCP cuidará de tudo — criando os arquivos nos diretórios corretos e
registrando os bindings no `AppServiceProvider`.

---

## 📄 Licença

Distribuído sob a licença **MIT**. Consulte o arquivo [`LICENSE`](LICENSE) para
mais informações.

