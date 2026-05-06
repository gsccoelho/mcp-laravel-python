from pathlib import Path


def atualizar_provider(provider_path: Path, entidade: str) -> None:
    if not provider_path.exists():
        return

    content = provider_path.read_text(encoding='utf-8')

    contract_class = f"{entidade}RepositoryContract"
    eloquent_class = f"{entidade}RepositoryEloquent"

    if "use App\\Repositories\\Contracts\\{" in content and f"    {contract_class}," not in content:
        content = content.replace(
            "use App\\Repositories\\Contracts\\{\n",
            f"use App\\Repositories\\Contracts\\{{\n    {contract_class},\n"
        )

    if "use App\\Repositories\\Eloquent\\{" in content and f"    {eloquent_class}," not in content:
        content = content.replace(
            "use App\\Repositories\\Eloquent\\{\n",
            f"use App\\Repositories\\Eloquent\\{{\n    {eloquent_class},\n"
        )

    if f"{contract_class}," not in content and "use App\\Repositories\\Contracts\\{" not in content:
        content = content.replace(
            "use Illuminate\\Support\\ServiceProvider;",
            f"use Illuminate\\Support\\ServiceProvider;\nuse App\\Repositories\\Contracts\\{contract_class};\nuse App\\Repositories\\Eloquent\\{eloquent_class};"
        )

    binding_line = f"        $this->app->bind({contract_class}::class, {eloquent_class}::class);"

    if binding_line not in content:
        for assinatura in ["public function register(): void\n    {", "public function register()\n    {"]:
            if assinatura in content:
                content = content.replace(
                    assinatura,
                    assinatura.replace("{", f"{{\n{binding_line}")
                )
                break

    provider_path.write_text(content, encoding='utf-8')