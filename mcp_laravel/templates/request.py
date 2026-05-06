def render(entidade: str, namespace: str) -> str:
    return f"""<?php

namespace {namespace};

use Illuminate\\Foundation\\Http\\FormRequest;

class {entidade}IndexRequest extends FormRequest
{{
    public function rules()
    {{
        return [];
    }}
}}
"""