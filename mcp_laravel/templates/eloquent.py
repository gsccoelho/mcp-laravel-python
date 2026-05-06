def render(entidade: str) -> str:
    return f"""<?php

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
}}"""