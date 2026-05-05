from mcp.server.fastmcp import FastMCP
from pathlib import Path

mcp = FastMCP("mcp-laravel-python")

def encontrar_pasta_repositorio(projeto_path: Path, tipo: str) -> Path:
    """
    Verifica dinamicamente onde os repositórios estão no projeto.
    tipo pode ser 'Contracts' ou 'Eloquent'
    """
    # Lista de possíveis locais onde você costuma guardar os repositórios
    possiveis_locais = [
        projeto_path / 'app' / 'Repositories',
        projeto_path / 'src' / 'Repositories',
        projeto_path / 'app' / 'Core' / 'Repositories',
    ]
    
    # Verifica qual local existe no projeto atual
    for local_base in possiveis_locais:
        if local_base.exists():
            return local_base / tipo
            
    # Fallback padrão caso nenhum seja encontrado
    return projeto_path / 'app' / 'Repositories' / tipo

@mcp.tool()
def gerar_repositories(caminhoProjeto: str, entidade: str) -> str:
    """Gera a estrutura completa de contratos e repositórios com detecção automática de pastas."""
    try:
        projeto_path = Path(caminhoProjeto)
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
            
            # Atualiza o padrão do grupo de use com strings normais para evitar erro do Python
            if "use App\\Repositories\\Contracts\\{" in provider_content and contract_use_line not in provider_content:
                search_str = "use App\\Repositories\\Contracts\\{\n"
                replace_str = search_str + contract_use_line + "\n"
                provider_content = provider_content.replace(search_str, replace_str)
                
            if "use App\\Repositories\\Eloquent\\{" in provider_content and eloquent_use_line not in provider_content:
                search_str = "use App\\Repositories\\Eloquent\\{\n"
                replace_str = search_str + eloquent_use_line + "\n"
                provider_content = provider_content.replace(search_str, replace_str)
                
            # Fallback caso os grupos ainda não existam no arquivo
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

        return f"✅ Estrutura de {entidade} criada com sucesso e diretório detectado automaticamente!"
    
    except Exception as e:
        return f"Erro ao gerar CRUD dinâmico: {str(e)}"

if __name__ == "__main__":
    mcp.run()