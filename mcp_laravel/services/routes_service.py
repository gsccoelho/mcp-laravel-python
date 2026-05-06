import re
from pathlib import Path


def atualizar_rotas(routes_path: Path, entidade: str, controller_class: str) -> None:
    entidade_lower = entidade.lower()

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
        content = _consolidar_use_controllers(content, controller_class)
        content = re.sub(r'\n{3,}', '\n\n', content)
        if f"'prefix' => '{entidade_lower}'" not in content:
            content = _inserir_grupo_rota(content, route_group_content)
        routes_path.write_text(content, encoding='utf-8')
    else:
        _criar_arquivo_rotas(routes_path, entidade, controller_class, route_group_content)


def _consolidar_use_controllers(content: str, novo_controller: str) -> str:
    controllers = set()

    bloco_match = re.search(r'use App\\Http\\Controllers\\\{([^}]*)\}', content)
    if bloco_match:
        for nome in re.findall(r'([A-Za-z0-9]+Controller)', bloco_match.group(1)):
            controllers.add(nome)

    for m in re.finditer(r'use App\\Http\\Controllers\\([A-Za-z0-9]+Controller);', content):
        controllers.add(m.group(1))

    controllers.add(novo_controller)

    content = re.sub(r'use App\\Http\\Controllers\\\{[^}]*\};\n?', '', content)
    content = re.sub(r'use App\\Http\\Controllers\\[A-Za-z0-9]+Controller;\n?', '', content)

    linhas = ',\n    '.join(sorted(controllers))
    novo_bloco = "use App\\Http\\Controllers\\{\n    " + linhas + "\n};"

    if '/** @var' in content:
        content = re.sub(
            r'/\*\* @var [^\*]*\*/',
            lambda m: m.group(0) + '\n\n' + novo_bloco,
            content, count=1
        )
    else:
        content = re.sub(
            r'<\?php\s*\n',
            lambda m: '<?php\n\n' + novo_bloco + '\n',
            content, count=1
        )

    return content


def _inserir_grupo_rota(content: str, route_group_content: str) -> str:
    main_group_start = content.find('$router->group(')
    if main_group_start == -1:
        return content + f"\n{route_group_content}\n"

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

    if main_group_end == -1:
        return content + f"\n{route_group_content}\n"

    return content[:main_group_end] + '\n' + route_group_content + '\n' + content[main_group_end:]


def _criar_arquivo_rotas(routes_path: Path, entidade: str, controller_class: str, route_group_content: str) -> None:
    entidade_lower = entidade.lower()
    routes_path.write_text(f"""<?php

/** @var \\Laravel\\Lumen\\Routing\\Router $router */

use App\\Http\\Controllers\\{{
    {controller_class}
}};

$router->group(['prefix' => '{entidade_lower}'], function () use ($router) {{
{route_group_content}
}});
""", encoding='utf-8')