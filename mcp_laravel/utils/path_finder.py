from pathlib import Path


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
    candidatos = [
        projeto_path / 'app' / 'Http' / tipo,
        projeto_path / 'app' / tipo,
        projeto_path / 'src' / 'Http' / tipo,
        projeto_path / 'src' / tipo,
    ]
    for caminho in candidatos:
        if caminho.exists():
            rel = (
                caminho.relative_to(projeto_path / 'app')
                if (projeto_path / 'app') in caminho.parents
                else caminho.relative_to(projeto_path / 'src')
            )
            namespace = 'App\\' + '\\'.join(rel.parts)
            return caminho, namespace

    padrao = projeto_path / 'app' / 'Http' / tipo
    return padrao, f'App\\Http\\{tipo}'