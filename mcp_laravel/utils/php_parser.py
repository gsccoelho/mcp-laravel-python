import re
from pathlib import Path


def extrair_fillable(model_path: Path) -> list[str]:
    content = model_path.read_text(encoding='utf-8')
    match = re.search(r'\$fillable\s*=\s*\[([\s\S]*?)\]', content)
    if not match:
        return []
    return re.findall(r"'([^']+)'", match.group(1))


def classificar_campo(campo: str) -> str:
    nome = campo.lower()

    padroes_data = ['dt_', 'data_', '_data', '_dt', 'date_', '_date', 'dat_']
    for p in padroes_data:
        if nome.startswith(p) or nome.endswith(p.strip('_')) or p in nome:
            return 'date'

    padroes_money = [
        'vlr_', 'valor_', 'vl_', 'sal_', 'saldo_', 'preco_',
        'price_', '_valor', '_vlr', '_vl', '_sal', '_saldo',
        'total_', '_total', 'bruto', 'liquido', '_bruto'
    ]
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
    return f"            '{campo}' => (string) $this->{campo},"