from mcp.server.fastmcp import FastMCP
from pathlib import Path

mcp = FastMCP("mcp-laravel-python")

def encontrar_pasta_repositorio(projeto_path: Path, tipo: str) -> Path:
    """
    Verifica dinamicamente onde os repositórios estão no projeto.
    tipo pode ser 'Contracts' ou 'Eloquent'
    """
    possiveis_locais = [
        projeto_path / 'app' / 'Repositories',
        projeto_path / 'src' / 'Repositories',
        projeto_path / 'app' / 'Core' / 'Repositories',
    ]
    
    for local_base in possiveis_locais:
        if local_base.exists():
            return local_base / tipo
            
    return projeto_path / 'app' / 'Repositories' / tipo

@mcp.tool()
def gerar_repositories(caminhoProjeto: str, entidade: str) -> str:
    """Gera a estrutura completa de contratos e repositórios com detecção automática de pastas."""
    try:
        projeto_path = Path(caminhoProjeto).resolve()
        model_path = projeto_path / 'app' / 'Models' / f"{entidade}.php"
        
        # 1. Validação da Model
        if not model_path.exists():
            return f"❌ Erro: A model {entidade}.php não foi encontrada em {model_path}."

        # 2. Identificação dinâmica dos caminhos
        contract_dir = encontrar_pasta_repositorio(projeto_path, 'Contracts')
        eloquent_dir = encontrar_pasta_repositorio(projeto_path, 'Eloquent')
        
        paths = {
            "contract": contract_dir / f"{entidade}RepositoryContract.php",
            "eloquent": eloquent_dir / f"{entidade}RepositoryEloquent.php",
        }
        
        provider_path = projeto_path / 'app' / 'Providers' / 'AppServiceProvider.php'
        
        # 3. Cria os diretórios caso não existam
        for p in paths.values():
            p.parent.mkdir(parents=True, exist_ok=True)
            
        # 4. Escreve o Contract
        paths["contract"].write_text(f"""<?php

namespace App\\Repositories\\Contracts;

interface {entidade}RepositoryContract
{{
    /**
     * Table contract
     *
     * @return Collection
     */
    public function table(array $filters);

    /**
     * Create contract
     *
     * @param array $payload
     * @return Model
     */
    public function create(array $payload);

    /**
     * Edit contract
     *
     * @return Collection
     */
    public function edit(array $payload);
    
    /**
     * Update contract
     *
     * @return Model
     */
    public function update(array $payload);
    
    /**
     * Delete contract
     *
     * @return bool
     */
    public function delete(array $payload);
}}""", encoding='utf-8')

        # 5. Escreve o Repository Eloquent
        paths["eloquent"].write_text(f"""<?php

namespace App\\Repositories\\Eloquent;

use App\\Repositories\\Contracts\\{entidade}RepositoryContract;
use App\\Models\\{entidade};

class {entidade}RepositoryEloquent implements {entidade}RepositoryContract
{{
    private $model;

    public function __construct({entidade} $model)
    {{
        $this->model = $model;
    }}

    public function table(array $filters)
    {{
    
        $query = $this->model->select('*');
        
        $this->filterQuery($query, $filters);
        $this->filterAdvanced($query, $filters);

        if ((isset($filters['collumn']) && $filters['collumn'] != '') && (isset($filters['order']) && $filters['order'] != ''))
            $query->orderBy($filters['collumn'], $filters['order']);        
        
        return $query->paginate($filters['per_page']);
    }}

    public function filterQuery($query, $filters)
    {{
        if (isset($filters['name']) && $filters['name'] != '')
            $query->where('name', 'like', '%' . $filters['name'] . '%');

        if (isset($filters['codigo']) && $filters['codigo'] != '')
            $query->where('codigo', $filters['codigo']);

        if (isset($filters['data']) && $filters['data'] != '')
            $query->where('data', $filters['data']);

        return $query;
    }}

    public function filterAdvanced($query, $filters)
    {{
        if (isset($filters['campoPesquisa']) && $filters['campoPesquisa'] != '') {{
            $camposPesquisa = ['codigo_1', 'codigo_2',];
            $valorPesquisa = strtolower($filters['campoPesquisa']);

            $query->where(function ($sql) use ($camposPesquisa, $valorPesquisa) {{
                foreach ($camposPesquisa as $campo)
                    $sql->orWhere(DB::raw("lower({{$campo}})"), 'like', "%{{$valorPesquisa}}%");
            }});
        }}
        return $query;
    }}

    public function create(array $payload)
    {{
        return $this->model->create($payload);
    }}

    public function edit(array $payload)
    {{
        return $this->model::findOrFail($payload['id']);
    }}

    public function update(array $payload)
    {{
        $record = $this->model::findOrFail($payload['id']);
        $record->update($payload);
        return $record;
    }}

    public function delete(array $payload)
    {{
        $record = $this->model::findOrFail($payload['id']);
        return $record->delete();
    }}
}}""", encoding='utf-8')

       # 6. Atualiza o AppServiceProvider dinamicamente
        if provider_path.exists():
            provider_content = provider_path.read_text(encoding='utf-8')
            
            contract_class = f"{entidade}RepositoryContract"
            eloquent_class = f"{entidade}RepositoryEloquent"
            
            contract_use_line = f"    {contract_class},"
            eloquent_use_line = f"    {eloquent_class},"
            
            if "use App\\Repositories\\Contracts\\{" in provider_content and contract_use_line not in provider_content:
                search_str = "use App\\Repositories\\Contracts\\{\n"
                replace_str = search_str + contract_use_line + "\n"
                provider_content = provider_content.replace(search_str, replace_str)
                
            if "use App\\Repositories\\Eloquent\\{" in provider_content and eloquent_use_line not in provider_content:
                search_str = "use App\\Repositories\\Eloquent\\{\n"
                replace_str = search_str + eloquent_use_line + "\n"
                provider_content = provider_content.replace(search_str, replace_str)
                
            if f"{contract_class}," not in provider_content and "use App\\Repositories\\Contracts\\{" not in provider_content:
                provider_content = provider_content.replace(
                    "use Illuminate\\Support\\ServiceProvider;",
                    f"use Illuminate\\Support\\ServiceProvider;\nuse App\\Repositories\\Contracts\\{contract_class};\nuse App\\Repositories\\Eloquent\\{eloquent_class};"
                )
                
            binding_line = f"        $this->app->bind({contract_class}::class, {eloquent_class}::class);"
            
            if binding_line not in provider_content:
                if "public function register(): void" in provider_content:
                    provider_content = provider_content.replace(
                        "public function register(): void\n    {",
                        f"""public function register(): void
    {{
{binding_line}"""
                    )
                else:
                    provider_content = provider_content.replace(
                        "public function register()\n    {",
                        f"""public function register()
    {{
{binding_line}"""
                    )
                
            provider_path.write_text(provider_content, encoding='utf-8')

        return f"✅ Estrutura de {entidade} criada com sucesso em: {projeto_path}"
    
    except Exception as e:
        return f"Erro ao gerar CRUD dinâmico: {str(e)}"


@mcp.tool()
def gerar_controller_e_rotas(caminhoProjeto: str, entidade: str, confirmarUso: bool = False) -> str:
    """Gera a controller e rotas de forma limpa e 100% genérica para o Laravel/Lumen."""
    import re

    try:
        projeto_path = Path(caminhoProjeto).resolve()
        entidade_lower = entidade.lower()
        
        # 1. Validação da existência dos repositórios
        contract_dir = encontrar_pasta_repositorio(projeto_path, 'Contracts')
        eloquent_dir = encontrar_pasta_repositorio(projeto_path, 'Eloquent')
        
        contract_path = contract_dir / f"{entidade}RepositoryContract.php"
        eloquent_path = eloquent_dir / f"{entidade}RepositoryEloquent.php"
        
        if not contract_path.exists() or not eloquent_path.exists():
            if not confirmarUso:
                return (f"⚠️ Repositórios não encontrados para a model {entidade}. "
                        f"Deseja criar a estrutura de repositórios e a controller automaticamente? "
                        f"Execute a ferramenta novamente passando `confirmarUso=True` para confirmar.")
            else:
                res_repo = gerar_repositories(caminhoProjeto, entidade)
                if "❌" in res_repo or "Erro" in res_repo:
                    return f"❌ Falha ao criar repositórios automaticamente: {res_repo}"
                    
        # 2. Cria o arquivo de Controller
        controller_path = projeto_path / 'app' / 'Http' / 'Controllers' / f"{entidade}Controller.php"
        controller_path.parent.mkdir(parents=True, exist_ok=True)
        
        controller_path.write_text(f"""<?php

namespace App\\Http\\Controllers;

use App\\Repositories\\Contracts\\{entidade}RepositoryContract;
use Illuminate\\Http\\Request;

class {entidade}Controller extends Controller
{{
    private ${entidade_lower}RepositoryContract;

    public function __construct({entidade}RepositoryContract ${entidade_lower}RepositoryContract)
    {{
        parent::__construct();
        $this->{entidade_lower}RepositoryContract = ${entidade_lower}RepositoryContract;
    }}

    public function index(Request $request)
    {{
        return $this->{entidade_lower}RepositoryContract->table($request->all());
    }}

    public function store(Request $request)
    {{
        return $this->{entidade_lower}RepositoryContract->create($request->all());
    }}

    public function show($id)
    {{
        return $this->{entidade_lower}RepositoryContract->edit(['id' => $id]);
    }}

    public function update(Request $request, $id)
    {{
        $payload = $request->all();
        $payload['id'] = $id;
        return $this->{entidade_lower}RepositoryContract->update($payload);
    }}

    public function destroy($id)
    {{
        return $this->{entidade_lower}RepositoryContract->delete(['id' => $id]);
    }}
}}""", encoding='utf-8')

        # 3. Atualiza o arquivo de rotas
        routes_path = projeto_path / 'routes' / 'api.php'

        if routes_path.exists():
            content = routes_path.read_text(encoding='utf-8')
            controller_class = f"{entidade}Controller"

            # ----------------------------------------------------------------
            # PASSO A: Consolidar todos os use App\Http\Controllers em um único bloco
            # ----------------------------------------------------------------

            # Coleta todos os controllers já declarados (individual ou em bloco)
            controllers_encontrados = set()

            # Captura do bloco use App\Http\Controllers\{ ... };
            bloco_match = re.search(
                r'use App\\Http\\Controllers\\\{([\s\S]*?)\};',
                content
            )
            if bloco_match:
                interior = bloco_match.group(1)
                for nome in re.findall(r'([A-Za-z]+Controller)', interior):
                    controllers_encontrados.add(nome)

            # Captura de uses individuais: use App\Http\Controllers\XxxController;
            for m in re.finditer(r'use App\\Http\\Controllers\\([A-Za-z]+Controller);', content):
                controllers_encontrados.add(m.group(1))

            # Adiciona o novo controller
            controllers_encontrados.add(controller_class)

            # Remove TODOS os uses de controllers existentes (individuais e em bloco)
            content = re.sub(r'use App\\Http\\Controllers\\\{[\s\S]*?\};\n?', '', content)
            content = re.sub(r'use App\\Http\\Controllers\\[A-Za-z]+Controller;\n?', '', content)

            # Monta o novo bloco consolidado (ordenado, sem vírgula no último)
            controllers_sorted = sorted(controllers_encontrados)
            linhas_controllers = ',\n    '.join(controllers_sorted)
            novo_bloco_use = f"use App\\Http\\Controllers\\{{\n    {linhas_controllers}\n}};"

            # Insere o bloco após /** @var ... */ se existir, senão após <?php
            if '/** @var' in content:
                content = re.sub(
                    r'(/\*\* @var \\Laravel\\Lumen\\Routing\\Router \$router \*/\n)',
                    f'\\1\n{novo_bloco_use}\n',
                    content
                )
            else:
                content = re.sub(
                    r'(<\?php\s*\n)',
                    f'<?php\n\n{novo_bloco_use}\n',
                    content,
                    count=1
                )

            # Remove linhas em branco duplicadas excessivas (mais de 2 seguidas)
            content = re.sub(r'\n{3,}', '\n\n', content)

            # ----------------------------------------------------------------
            # PASSO B: Inserir o grupo de rotas dentro do $router->group principal
            # ----------------------------------------------------------------

            route_group_content = (
                f"    $router->group(['prefix' => '{entidade_lower}'], function () use ($router) {{\n"
                f"        $router->get('/', [{controller_class}::class, 'index']);\n"
                f"        $router->post('/', [{controller_class}::class, 'store']);\n"
                f"        $router->get('/{{id}}', [{controller_class}::class, 'show']);\n"
                f"        $router->put('/{{id}}', [{controller_class}::class, 'update']);\n"
                f"        $router->delete('/{{id}}', [{controller_class}::class, 'destroy']);\n"
                f"    }});"
            )

            # Verifica se a rota já existe
            if f"'prefix' => '{entidade_lower}'" not in content:
                # Encontra o grupo principal balanceando chaves
                main_group_start = content.find('$router->group(')
                if main_group_start != -1:
                    depth = 0
                    main_group_end = -1
                    for i, ch in enumerate(content[main_group_start:]):
                        if ch == '{':
                            depth += 1
                        elif ch == '}':
                            depth -= 1
                            if depth == 0:
                                main_group_end = main_group_start + i
                                break

                    if main_group_end != -1:
                        # Insere antes do fechamento });
                        content = (
                            content[:main_group_end]
                            + '\n' + route_group_content + '\n'
                            + content[main_group_end:]
                        )
                    else:
                        content += f"\n{route_group_content}\n"
                else:
                    content += f"\n{route_group_content}\n"

            routes_path.write_text(content, encoding='utf-8')

        else:
            # Arquivo não existe: cria do zero
            routes_path.write_text(f"""<?php

/** @var \\Laravel\\Lumen\\Routing\\Router $router */

use App\\Http\\Controllers\\{{
    {entidade}Controller
}};

$router->group(['prefix' => '{entidade_lower}'], function () use ($router) {{
    $router->get('/', [{entidade}Controller::class, 'index']);
    $router->post('/', [{entidade}Controller::class, 'store']);
    $router->get('/{{id}}', [{entidade}Controller::class, 'show']);
    $router->put('/{{id}}', [{entidade}Controller::class, 'update']);
    $router->delete('/{{id}}', [{entidade}Controller::class, 'destroy']);
}});
""", encoding='utf-8')

        return f"✅ Controller e rotas criadas com sucesso de forma 100% genérica em: {projeto_path}"
        
    except Exception as e:
        return f"Erro ao gerar controller e rotas: {str(e)}"

if __name__ == "__main__":
    mcp.run()