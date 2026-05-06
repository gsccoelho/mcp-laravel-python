from pathlib import Path
from mcp_laravel.utils.path_finder import encontrar_pasta_repositorio
from mcp_laravel.utils.provider_updater import atualizar_provider
from mcp_laravel.templates import contract as tpl_contract
from mcp_laravel.templates import eloquent as tpl_eloquent


def register(mcp):

    @mcp.tool()
    def gerar_repositories(caminhoProjeto: str, entidade: str) -> str:
        """Gera a estrutura completa de contratos e repositórios com detecção automática de pastas."""
        try:
            projeto_path = Path(caminhoProjeto).resolve()
            resultado = _gerar_repositories(projeto_path, entidade)
            return resultado
        except Exception as e:
            return f"Erro ao gerar repositórios: {str(e)}"


def _gerar_repositories(projeto_path: Path, entidade: str) -> str:
    """Função interna reutilizável pelo tool de controller."""
    model_path = projeto_path / 'app' / 'Models' / f"{entidade}.php"

    if not model_path.exists():
        return f"❌ Erro: A model {entidade}.php não foi encontrada em {model_path}."

    contract_dir = encontrar_pasta_repositorio(projeto_path, 'Contracts')
    eloquent_dir = encontrar_pasta_repositorio(projeto_path, 'Eloquent')

    contract_path = contract_dir / f"{entidade}RepositoryContract.php"
    eloquent_path = eloquent_dir / f"{entidade}RepositoryEloquent.php"

    contract_path.parent.mkdir(parents=True, exist_ok=True)
    eloquent_path.parent.mkdir(parents=True, exist_ok=True)

    contract_path.write_text(tpl_contract.render(entidade), encoding='utf-8')
    eloquent_path.write_text(tpl_eloquent.render(entidade), encoding='utf-8')

    provider_path = projeto_path / 'app' / 'Providers' / 'AppServiceProvider.php'
    atualizar_provider(provider_path, entidade)

    return f"✅ Estrutura de {entidade} criada com sucesso em: {projeto_path}"