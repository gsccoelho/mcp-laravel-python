def render(entidade: str, entidade_lower: str, requests_namespace: str, resources_namespace: str) -> str:
    return f"""<?php

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
                $this->{entidade_lower}RepositoryContract->create($request->all()), 200
            );
        }} catch (\\Exception $e) {{
            return $this->jsonResponse($e->getMessage(), 500);
        }}
    }}

    public function edit($id)
    {{
        try {{
            return $this->jsonResponse(
                new {entidade}EditResource(
                    $this->{entidade_lower}RepositoryContract->edit(['id' => $id])
                ), 200
            );
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
                $this->{entidade_lower}RepositoryContract->update($payload), 200
            );
        }} catch (\\Exception $e) {{
            return $this->jsonResponse($e->getMessage(), 500);
        }}
    }}

    public function delete($id)
    {{
        try {{
            return $this->jsonResponse(
                $this->{entidade_lower}RepositoryContract->delete(['id' => $id]), 200
            );
        }} catch (\\Exception $e) {{
            return $this->jsonResponse($e->getMessage(), 500);
        }}
    }}
}}
"""