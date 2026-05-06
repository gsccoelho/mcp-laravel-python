from pathlib import Path
from mcp_laravel.utils.path_finder import encontrar_pasta_repositorio, encontrar_pasta_http
from mcp_laravel.utils.php_parser import extrair_fillable, montar_linha_resource
from mcp_laravel.services.routes_service import atualizar_rotas
from mcp_laravel.templates import controller as tpl_controller
from mcp_laravel.templates import request as tpl_request
from mcp_laravel.templates import resource as tpl_resource


def register(mcp):

    @mcp.tool()
    def gerar_controller_e_rotas(caminhoProjeto: str, entidade: str, confirmarUso: bool = False) -> str:
        """Gera controller, rotas, Requests e Resources para o Laravel/Lumen."""
        try:
            projeto_path = Path(caminhoProjeto).resolve()
            entidade_lower = entidade.lower()
            model_path = projeto_path / 'app' / 'Models' / f"{entidade}.php"

            if not model_path.exists():
                return f"❌ Erro: A model {entidade}.php não foi encontrada em {model_path}."

            contract_dir = encontrar_pasta_repositorio(projeto_path, 'Contracts')
            eloquent_dir = encontrar_pasta_repositorio(projeto_path, 'Eloquent')
            contract_path = contract_dir / f"{entidade}RepositoryContract.php"
            eloquent_path = eloquent_dir / f"{entidade}RepositoryEloquent.php"

            if not contract_path.exists() or not eloquent_path.exists():
                if not confirmarUso:
                    return (
                        f"⚠️ Repositórios não encontrados para a model {entidade}. "
                        f"Execute novamente com `confirmarUso=True` para criá-los automaticamente."
                    )
                from mcp_laravel.tools.repositories import _gerar_repositories
                resultado = _gerar_repositories(projeto_path, entidade)
                if "❌" in resultado:
                    return resultado

            requests_base, requests_ns = encontrar_pasta_http(projeto_path, 'Requests')
            resources_base, resources_ns = encontrar_pasta_http(projeto_path, 'Resources')

            requests_dir = (requests_base / entidade)
            resources_dir = (resources_base / entidade)
            requests_dir.mkdir(parents=True, exist_ok=True)
            resources_dir.mkdir(parents=True, exist_ok=True)

            requests_namespace = f"{requests_ns}\\{entidade}"
            resources_namespace = f"{resources_ns}\\{entidade}"

            campos = extrair_fillable(model_path)
            linhas_data = (
                '\n'.join(montar_linha_resource(c) for c in campos)
                if campos else "            // TODO: adicionar campos do $fillable"
            )

            # Gera os arquivos via templates
            _escrever(requests_dir / f"{entidade}IndexRequest.php",
                      tpl_request.render(entidade, requests_namespace))

            _escrever(resources_dir / f"{entidade}IndexCollection.php",
                      tpl_resource.render_collection(entidade, resources_namespace))

            _escrever(resources_dir / f"{entidade}IndexResource.php",
                      tpl_resource.render_index(entidade, resources_namespace, linhas_data))

            _escrever(resources_dir / f"{entidade}EditResource.php",
                      tpl_resource.render_edit(entidade, resources_namespace, linhas_data))

            controller_path = projeto_path / 'app' / 'Http' / 'Controllers' / f"{entidade}Controller.php"
            controller_path.parent.mkdir(parents=True, exist_ok=True)
            _escrever(controller_path,
                      tpl_controller.render(entidade, entidade_lower, requests_namespace, resources_namespace))

            routes_path = projeto_path / 'routes' / 'api.php'
            atualizar_rotas(routes_path, entidade, f"{entidade}Controller")

            return (
                f"✅ Estrutura de {entidade} criada com sucesso!\n"
                f"   📁 Request:    {requests_dir / f'{entidade}IndexRequest.php'}\n"
                f"   📁 Collection: {resources_dir / f'{entidade}IndexCollection.php'}\n"
                f"   📁 Resource:   {resources_dir / f'{entidade}IndexResource.php'}\n"
                f"   📁 Controller: {controller_path}\n"
                f"   📁 Rotas:      {routes_path}"
            )

        except Exception as e:
            return f"Erro ao gerar controller e rotas: {str(e)}"


def _escrever(path: Path, conteudo: str) -> None:
    path.write_text(conteudo, encoding='utf-8')