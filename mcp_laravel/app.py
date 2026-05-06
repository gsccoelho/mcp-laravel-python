from mcp.server.fastmcp import FastMCP
from pathlib import Path
import re

mcp = FastMCP("mcp-laravel-python")


def encontrar_pasta_repositorio(projeto_path: Path, tipo: str) -> Path:
    possiveis_locais = [
        projeto_path / 'app' / 'Repositories',
        projeto_path / 'src' / 'Repositories',
        projeto_path / 'app' / 'Core' / 'Repositories',
    ]
    for local_base in possiveis_locais:
        if local_base.exists():
            return local_base / tipo
    return projeto_path / 'app' / 'Repositories' / tipo


def encontrar_pasta_http(projeto_path: Path, tipo: str) -> tuple[Path, str]:
    """
    Detecta onde estão Requests ou Resources no projeto.
    Retorna (Path, namespace_base)
    tipo: 'Requests' ou 'Resources'
    """
    candidatos = [
        projeto_path / 'app' / 'Http' / tipo,
        projeto_path / 'app' / tipo,
        projeto_path / 'src' / 'Http' / tipo,
        projeto_path / 'src' / tipo,
    ]
    for caminho in candidatos:
        if caminho.exists():
            # Determina namespace baseado no caminho real encontrado
            partes = caminho.relative_to(projeto_path).parts  # ex: ('app', 'Http', 'Requests')
            namespace = 'App\\' + '\\'.join(p for p in partes[1:] if p != 'app')
            # Reconstrói namespace corretamente
            rel = caminho.relative_to(projeto_path / 'app') if (projeto_path / 'app') in caminho.parents else caminho.relative_to(projeto_path / 'src')
            partes_rel = rel.parts
            namespace = 'App\\' + '\\'.join(partes_rel)
            return caminho, namespace

    # Padrão: app/Http/Requests ou app/Http/Resources
    padrao = projeto_path / 'app' / 'Http' / tipo
    return padrao, f'App\\Http\\{tipo}'


def extrair_fillable(model_path: Path) -> list[str]:
    """Lê o $fillable da model e retorna a lista de campos."""
    content = model_path.read_text(encoding='utf-8')
    match = re.search(r'\$fillable\s*=\s*\[([\s\S]*?)\]', content)
    if not match:
        return []
    interior = match.group(1)
    campos = re.findall(r"'([^']+)'", interior)
    return campos


def classificar_campo(campo: str) -> str:
    """
    Retorna o tipo de cast a aplicar no Resource.
    'date'     -> campos de data
    'money'    -> campos monetários
    'string'   -> padrão
    """
    nome = campo.lower()

    # Padrões de data
    padroes_data = ['dt_', 'data_', '_data', '_dt', 'date_', '_date', 'dat_']
    for p in padroes_data:
        if nome.startswith(p) or nome.endswith(p.strip('_')) or p in nome:
            return 'date'

    # Padrões monetários
    padroes_money = ['vlr_', 'valor_', 'vl_', 'sal_', 'saldo_', 'preco_', 'preco',
                     'price_', '_valor', '_vlr', '_vl', '_sal', '_saldo',
                     'total_', '_total', 'bruto', 'liquido', 'liquido_', '_bruto']
    for p in padroes_money:
        if nome.startswith(p) or nome.endswith(p.strip('_')) or p.strip('_') in nome:
            return 'money'

    return 'string'


def montar_linha_resource(campo: str) -> str:
    tipo = classificar_campo(campo)
    if tipo == 'date':
        return (
            f"            '{campo}' => (string) ($this->{campo} "
            f"? $this->_extractDate($this->{campo}, 'd/m/Y', 'Y-m-d H:i:s') : null),"
        )
    elif tipo == 'money':
        return (
            f"            '{campo}' => 'R$ ' . number_format("
            f"(float) ($this->{campo} ?? 0), 2, ',', '.'),"
        )
    else:
        return f"            '{campo}' => (string) $this->{campo},"


@mcp.tool()
def gerar_repositories(caminhoProjeto: str, entidade: str) -> str:
    """Gera a estrutura completa de contratos e repositórios com detecção automática de pastas."""
    try:
        projeto_path = Path(caminhoProjeto).resolve()
        model_path = projeto_path / 'app' / 'Models' / f"{entidade}.php"

        if not model_path.exists():
            return f"❌ Erro: A model {entidade}.php não foi encontrada em {model_path}."

        contract_dir = encontrar_pasta_repositorio(projeto_path, 'Contracts')
        eloquent_dir = encontrar_pasta_repositorio(projeto_path, 'Eloquent')

        paths = {
            "contract": contract_dir / f"{entidade}RepositoryContract.php",
            "eloquent": eloquent_dir / f"{entidade}RepositoryEloquent.php",
        }

        provider_path = projeto_path / 'app' / 'Providers' / 'AppServiceProvider.php'

        for p in paths.values():
            p.parent.mkdir(parents=True, exist_ok=True)

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

        paths["eloquent"].write_text(f"""<?php

namespace App\\Repositories\\Eloquent;

use App\\Repositories\\Contracts\\{entidade}RepositoryContract;
use Illuminate\\Support\\Facades\\DB;
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
            $query->where(DB::raw('lower(name)'), 'like', '%' . strtolower($filters['name']) . '%');

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
        return $this->model->where('id', $payload['id'])->first();
    }}

    public function update(array $payload)
    {{
        $record = $this->model->where('id', $payload['id'])->first();
        $record->update($payload);
        return $record;
    }}

    public function delete(array $payload)
    {{
        $record = $this->model->where('id', $payload['id'])->first();
        return $record->delete();
    }}
}}""", encoding='utf-8')

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
                        f"""public function register(): void\n    {{\n{binding_line}"""
                    )
                else:
                    provider_content = provider_content.replace(
                        "public function register()\n    {",
                        f"""public function register()\n    {{\n{binding_line}"""
                    )

            provider_path.write_text(provider_content, encoding='utf-8')

        return f"✅ Estrutura de {entidade} criada com sucesso em: {projeto_path}"

    except Exception as e:
        return f"Erro ao gerar CRUD dinâmico: {str(e)}"


@mcp.tool()
def gerar_controller_e_rotas(caminhoProjeto: str, entidade: str, confirmarUso: bool = False) -> str:
    """Gera controller, rotas, Requests e Resources para o Laravel/Lumen."""
    try:
        projeto_path = Path(caminhoProjeto).resolve()
        entidade_lower = entidade.lower()
        model_path = projeto_path / 'app' / 'Models' / f"{entidade}.php"

        # 1. Validação da model
        if not model_path.exists():
            return f"❌ Erro: A model {entidade}.php não foi encontrada em {model_path}."

        # 2. Validação dos repositórios
        contract_dir = encontrar_pasta_repositorio(projeto_path, 'Contracts')
        eloquent_dir = encontrar_pasta_repositorio(projeto_path, 'Eloquent')

        contract_path = contract_dir / f"{entidade}RepositoryContract.php"
        eloquent_path = eloquent_dir / f"{entidade}RepositoryEloquent.php"

        if not contract_path.exists() or not eloquent_path.exists():
            if not confirmarUso:
                return (
                    f"⚠️ Repositórios não encontrados para a model {entidade}. "
                    f"Execute novamente passando `confirmarUso=True` para criá-los automaticamente."
                )
            else:
                res_repo = gerar_repositories(caminhoProjeto, entidade)
                if "❌" in res_repo or "Erro" in res_repo:
                    return f"❌ Falha ao criar repositórios automaticamente: {res_repo}"

        # 3. Detecta pastas de Requests e Resources
        requests_base, requests_namespace_base = encontrar_pasta_http(projeto_path, 'Requests')
        resources_base, resources_namespace_base = encontrar_pasta_http(projeto_path, 'Resources')

        requests_dir = requests_base / entidade
        resources_dir = resources_base / entidade

        requests_dir.mkdir(parents=True, exist_ok=True)
        resources_dir.mkdir(parents=True, exist_ok=True)

        requests_namespace = f"{requests_namespace_base}\\{entidade}"
        resources_namespace = f"{resources_namespace_base}\\{entidade}"

        # 4. Lê o $fillable da model
        campos = extrair_fillable(model_path)
        linhas_data = '\n'.join(montar_linha_resource(c) for c in campos) if campos else "            // TODO: adicionar campos do $fillable"

        # 5. Gera IndexRequest
        request_path = requests_dir / f"{entidade}IndexRequest.php"
        request_path.write_text(f"""<?php

namespace {requests_namespace};

use Illuminate\\Foundation\\Http\\FormRequest;

class {entidade}IndexRequest extends FormRequest
{{
    public function rules()
    {{
        return [];
    }}
}}
""", encoding='utf-8')

        # 6. Gera IndexCollection
        collection_path = resources_dir / f"{entidade}IndexCollection.php"
        collection_path.write_text(f"""<?php

namespace {resources_namespace};

use App\\Http\\Resources\\Table\\BaseTableCollection;

class {entidade}IndexCollection extends BaseTableCollection
{{
    public function toArray($request)
    {{
        return [
            'data' => $this->collection,
            'paginate' => $this->baseTable()
        ];
    }}
}}
""", encoding='utf-8')

        # 7. Gera IndexResource com campos do $fillable
        resource_path = resources_dir / f"{entidade}IndexResource.php"
        resource_path.write_text(f"""<?php

namespace {resources_namespace};

use UnismUtils\\Traits\\UtilsTrait;
use Illuminate\\Http\\Resources\\Json\\JsonResource;

class {entidade}IndexResource extends JsonResource
{{
    use UtilsTrait;

    public function toArray($request)
    {{
        $data = [
{linhas_data}
        ];

        return $data;
    }}
}}
""", encoding='utf-8')

        # 7b. Gera EditResource
        resource_edit_path = resources_dir / f"{entidade}EditResource.php"
        resource_edit_path.write_text(f"""<?php

namespace {resources_namespace};

use UnismUtils\\Traits\\UtilsTrait;
use Illuminate\\Http\\Resources\\Json\\JsonResource;

class {entidade}EditResource extends JsonResource
{{
    use UtilsTrait;

    public function toArray($request)
    {{
        $data = [
{linhas_data}
        ];

        return $data;
    }}
}}
""", encoding='utf-8')

        # 8. Gera Controller
        controller_path = projeto_path / 'app' / 'Http' / 'Controllers' / f"{entidade}Controller.php"
        controller_path.parent.mkdir(parents=True, exist_ok=True)

        controller_path.write_text(f"""<?php

namespace App\\Http\\Controllers;

use App\\Repositories\\Contracts\\{entidade}RepositoryContract;
use {requests_namespace}\\{entidade}IndexRequest;
use {resources_namespace}\\{entidade}IndexCollection;
use {resources_namespace}\\{entidade}EditResource;
use Illuminate\\Http\\Request;

class {entidade}Controller extends Controller
{{
    private ${entidade_lower}RepositoryContract;

    public function __construct({entidade}RepositoryContract ${entidade_lower}RepositoryContract)
    {{
        parent::__construct();
        $this->{entidade_lower}RepositoryContract = ${entidade_lower}RepositoryContract;
    }}

    public function index({entidade}IndexRequest $request)
    {{
        try {{
            return new {entidade}IndexCollection(
                $this->{entidade_lower}RepositoryContract->table($request->all())
            );
        }} catch (\\Exception $e) {{
            return $this->jsonResponse($e->getMessage(), 500);
        }}
    }}

    public function store(Request $request)
    {{
        try {{
            return $this->jsonResponse(
                $this->{entidade_lower}RepositoryContract->create($request->all()),
                200
            );
        }} catch (\\Exception $e) {{
            return $this->jsonResponse($e->getMessage(), 500);
        }}
    }}

    public function edit($id)
    {{
        try {{
            $response = $this->jsonResponse(
                new {entidade}EditResource(
                    $this->{entidade_lower}RepositoryContract->edit(['id' => $id])
                ),
                200
            );
            return $response;
        }} catch (\\Exception $e) {{
            return $this->jsonResponse($e->getMessage(), 500);
        }}
    }}

    public function update(Request $request, $id)
    {{
        try {{
            $payload = $request->all();
            $payload['id'] = $id;
            return $this->jsonResponse(
                $this->{entidade_lower}RepositoryContract->update($payload),
                200
            );
        }} catch (\\Exception $e) {{
            return $this->jsonResponse($e->getMessage(), 500);
        }}
    }}

    public function delete($id)
    {{
        try {{
            return $this->jsonResponse(
                $this->{entidade_lower}RepositoryContract->delete(['id' => $id]),
                200
            );
        }} catch (\\Exception $e) {{
            return $this->jsonResponse($e->getMessage(), 500);
        }}
    }}
}}
""", encoding='utf-8')

        # 9. Atualiza api.php
        routes_path = projeto_path / 'routes' / 'api.php'
        controller_class = f"{entidade}Controller"

        route_group_content = (
            f"    $router->group(['prefix' => '{entidade_lower}'], function () use ($router) {{\n"
            f"        $router->get('/', [{controller_class}::class, 'index']);\n"
            f"        $router->post('/', [{controller_class}::class, 'store']);\n"
            f"        $router->get('/{{id}}', [{controller_class}::class, 'edit']);\n"
            f"        $router->put('/{{id}}', [{controller_class}::class, 'update']);\n"
            f"        $router->delete('/{{id}}', [{controller_class}::class, 'delete']);\n"
            f"    }});"
        )

        if routes_path.exists():
            content = routes_path.read_text(encoding='utf-8')

            # --- Passo A: Consolida os use de Controllers ---



# --- Passo A: Consolida os use de Controllers ---
            controllers_encontrados = set()

            # Captura bloco use App\Http\Controllers\{ ... };
            bloco_match = re.search(
                r'use App\\Http\\Controllers\\\{([^}]*)\}',
                content
            )
            if bloco_match:
                for nome in re.findall(r'([A-Za-z0-9]+Controller)', bloco_match.group(1)):
                    controllers_encontrados.add(nome)

            # Captura uses individuais
            for m in re.finditer(r'use App\\Http\\Controllers\\([A-Za-z0-9]+Controller);', content):
                controllers_encontrados.add(m.group(1))

            # Adiciona o novo controller
            controllers_encontrados.add(controller_class)

            # Só prossegue se coletou ao menos 1 controller (segurança)
            if not controllers_encontrados:
                controllers_encontrados.add(controller_class)

            # Remove bloco e uses individuais existentes
            content = re.sub(r'use App\\Http\\Controllers\\\{[^}]*\};\n?', '', content)
            content = re.sub(r'use App\\Http\\Controllers\\[A-Za-z0-9]+Controller;\n?', '', content)

            # Monta novo bloco consolidado
            controllers_sorted = sorted(controllers_encontrados)
            linhas_controllers = ',\n    '.join(controllers_sorted)
            novo_bloco_use = "use App\\Http\\Controllers\\{\n    " + linhas_controllers + "\n};"

            # Insere usando lambda para evitar interpretação de \ como escape de regex
            if '/** @var' in content:
                content = re.sub(
                    r'/\*\* @var [^\*]*\*/',
                    lambda m: m.group(0) + '\n\n' + novo_bloco_use,
                    content,
                    count=1
                )
            else:
                content = re.sub(
                    r'<\?php\s*\n',
                    lambda m: '<?php\n\n' + novo_bloco_use + '\n',
                    content,
                    count=1
                )

            content = re.sub(r'\n{3,}', '\n\n', content)



            #--------------------------------------------------------------------------------------------------------------------------


            # Monta o novo bloco consolidado
            # controllers_encontrados = set()
            # controllers_sorted = sorted(controllers_encontrados)
            # linhas_controllers = ',\n    '.join(controllers_sorted)
            # novo_bloco_use = f"use App\\Http\\Controllers\\{{\n    {linhas_controllers}\n}};"

            # # Insere o bloco após /** @var ... */ se existir, senão após <?php
            # # IMPORTANTE: usa lambda no re.sub para evitar interpretação de \ como escape de regex
            # if '/** @var' in content:
            #     content = re.sub(
            #         r'(/\*\* @var \\Laravel\\Lumen\\Routing\\Router \$router \*/\n)',
            #         lambda m: m.group(1) + '\n' + novo_bloco_use + '\n',
            #         content
            #     )
            # else:
            #     content = re.sub(
            #         r'(<\?php\s*\n)',
            #         lambda m: '<?php\n\n' + novo_bloco_use + '\n',
            #         content,
            #         count=1
            #     )


            #--------------------------------------------------------------------------------------------------------------------------
            # controllers_encontrados = set()

            # bloco_match = re.search(r'use App\\Http\\Controllers\\\{([\s\S]*?)\};', content)
            # if bloco_match:
            #     for nome in re.findall(r'([A-Za-z]+Controller)', bloco_match.group(1)):
            #         controllers_encontrados.add(nome)

            # for m in re.finditer(r'use App\\Http\\Controllers\\([A-Za-z]+Controller);', content):
            #     controllers_encontrados.add(m.group(1))

            # controllers_encontrados.add(controller_class)

            # content = re.sub(r'use App\\Http\\Controllers\\\{[\s\S]*?\};\n?', '', content)
            # content = re.sub(r'use App\\Http\\Controllers\\[A-Za-z]+Controller;\n?', '', content)

            # controllers_sorted = sorted(controllers_encontrados)
            # linhas_controllers = ',\n    '.join(controllers_sorted)
            # novo_bloco_use = f"use App\\Http\\Controllers\\{{\n    {linhas_controllers}\n}};"

            # if '/** @var' in content:
            #     content = re.sub(
            #         r'(/\*\* @var \\Laravel\\Lumen\\Routing\\Router \$router \*/\n)',
            #         f'\\1\n{novo_bloco_use}\n',
            #         content
            #     )
            # else:
            #     content = re.sub(
            #         r'(<\?php\s*\n)',
            #         f'<?php\n\n{novo_bloco_use}\n',
            #         content,
            #         count=1
            #     )

            # content = re.sub(r'\n{3,}', '\n\n', content)

            # --- Passo B: Insere rota dentro do grupo principal ---
            if f"'prefix' => '{entidade_lower}'" not in content:
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
            routes_path.write_text(f"""<?php

/** @var \\Laravel\\Lumen\\Routing\\Router $router */

use App\\Http\\Controllers\\{{
    {entidade}Controller
}};

$router->group(['prefix' => '{entidade_lower}'], function () use ($router) {{
    $router->get('/', [{entidade}Controller::class, 'index']);
    $router->post('/', [{entidade}Controller::class, 'store']);
    $router->get('/{{id}}', [{entidade}Controller::class, 'edit']);
    $router->put('/{{id}}', [{entidade}Controller::class, 'update']);
    $router->delete('/{{id}}', [{entidade}Controller::class, 'delete']);
}});
""", encoding='utf-8')

        return (
            f"✅ Estrutura de {entidade} criada com sucesso!\n"
            f"   📁 Request:    {request_path}\n"
            f"   📁 Collection: {collection_path}\n"
            f"   📁 Resource:   {resource_path}\n"
            f"   📁 Controller: {controller_path}\n"
            f"   📁 Rotas:      {routes_path}"
        )

    except Exception as e:
        return f"Erro ao gerar controller e rotas: {str(e)}"


if __name__ == "__main__":
    mcp.run()