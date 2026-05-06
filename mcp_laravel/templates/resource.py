def render_collection(entidade: str, namespace: str) -> str:
    return f"""<?php

namespace {namespace};

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
"""


def render_index(entidade: str, namespace: str, linhas_data: str) -> str:
    return f"""<?php

namespace {namespace};

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
"""


def render_edit(entidade: str, namespace: str, linhas_data: str) -> str:
    return f"""<?php

namespace {namespace};

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
"""