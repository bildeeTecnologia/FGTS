"""
Ajusta data_admissao de vínculos para a competência do lançamento mais antigo já
registrado, quando a data cadastrada é posterior a esse lançamento (comum em
transferências legadas onde a data de admissão original foi mantida por engano).

Uso:
    python manage.py ajustar_data_admissao              # apenas relatório (dry-run)
    python manage.py ajustar_data_admissao --apply       # aplica os ajustes aplicáveis
"""
from django.core.management.base import BaseCommand

from empresas.services.ajuste_admissao import aplicar_ajustes_admissao, sugerir_ajustes_admissao


class Command(BaseCommand):
    help = (
        "Ajusta data_admissao de vínculos para a competência do lançamento mais antigo "
        "registrado, quando ela é anterior à data_admissao cadastrada."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Aplica os ajustes aplicáveis. Sem esta flag, apenas mostra o relatório (dry-run).',
        )

    def handle(self, *args, **options):
        apply_changes = options['apply']
        sugestoes = sugerir_ajustes_admissao()

        aplicaveis = [s for s in sugestoes if s['aplicavel']]
        bloqueadas = [s for s in sugestoes if not s['aplicavel']]

        self.stdout.write("\n" + "=" * 72)
        self.stdout.write(self.style.WARNING(
            f"{'[APLICANDO] ' if apply_changes else '[DRY-RUN] '}"
            "AJUSTE DE DATA_ADMISSAO PELO 1º LANÇAMENTO"
        ))
        self.stdout.write("=" * 72)
        self.stdout.write(f"\nVínculos com ajuste aplicável: {len(aplicaveis)}")
        self.stdout.write(f"Vínculos bloqueados (sobreposição): {len(bloqueadas)}\n")

        for s in aplicaveis:
            v = s['vinculo']
            self.stdout.write(
                f"- Vínculo #{v.pk} | {v.funcionario.nome} | {v.empresa.nome}: "
                f"{s['data_atual'].strftime('%d/%m/%Y')} → {s['data_sugerida'].strftime('%d/%m/%Y')}"
            )

        if bloqueadas:
            self.stdout.write(self.style.ERROR("\nBloqueados (revisar manualmente):"))
            for s in bloqueadas:
                v = s['vinculo']
                self.stdout.write(
                    f"- Vínculo #{v.pk} | {v.funcionario.nome} | {v.empresa.nome}: "
                    f"sugestão {s['data_sugerida'].strftime('%d/%m/%Y')} — {s['motivo_bloqueio']}"
                )

        if not aplicaveis:
            self.stdout.write(self.style.SUCCESS("\nNenhum ajuste aplicável no momento.\n"))
            return

        if apply_changes:
            total = aplicar_ajustes_admissao([s['vinculo'].pk for s in aplicaveis])
            self.stdout.write(self.style.SUCCESS(f"\n✔ {total} vínculo(s) ajustado(s).\n"))
        else:
            self.stdout.write(self.style.WARNING(
                "\nNenhuma alteração aplicada (dry-run). Rode novamente com --apply para corrigir.\n"
            ))
