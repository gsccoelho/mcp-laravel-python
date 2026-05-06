def render(entidade: str) -> str:
    return f"""<?php

namespace App\\Repositories\\Contracts;

interface {entidade}RepositoryContract
{{
    public function table(array $filters);
    public function create(array $payload);
    public function edit(array $payload);
    public function update(array $payload);
    public function delete(array $payload);
}}"""