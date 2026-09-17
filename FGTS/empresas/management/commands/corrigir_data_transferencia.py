"""
Corrige vínculos transferidos cuja data_demissao ficou registrada no dia 1º do mês
(deveria ser o último dia do mês ANTERIOR — mesmo mês da admissão na empresa destino).

Escopo: somente vínculos com motivo_saida='transferencia' (status='transferido') e
data_demissao no dia 1. Não mexe na data_admissao do vínculo de destino.

Uso:
    python manage.py corrigir_data_transferencia               # apenas relatório (dry-run)
    python manage.py corrigir_data_transferencia --apply        # aplica as correções
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from empresas.models_grupo import FuncionarioVinculo


class Command(BaseCommand):
    help = (
        "Corrige data_demissao de vínculos transferidos registrada no dia 1º do mês "
        "(ajusta para o último dia do mês anterior)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Aplica as correções. Sem esta flag, apenas mostra o relatório (dry-run).',
        )

    def handle(self, *args, **options):
        apply_changes = options['apply']

        candidatos = FuncionarioVinculo.objects.filter(
            motivo_saida='transferencia',
            data_demissao__day=1,
        ).select_related('funcionario', 'empresa').order_by('empresa__nome', 'funcionario__nome')

        total = candidatos.count()
        self.stdout.write("\n" + "=" * 72)
        self.stdout.write(self.style.WARNING(
            f"{'[APLICANDO] ' if apply_changes else '[DRY-RUN] '}"
            "CORREÇÃO DE DATA_DEMISSAO EM TRANSFERÊNCIAS"
        ))
        self.stdout.write("=" * 72)
        self.stdout.write(f"\nVínculos encontrados: {total}\n")

        if total == 0:
            self.stdout.write(self.style.SUCCESS("Nenhum vínculo para corrigir.\n"))
            return

        corrigidos = 0
        for vinculo in candidatos:
            data_antiga = vinculo.data_demissao
            data_nova = data_antiga - timedelta(days=1)
            self.stdout.write(
                f"- Vínculo #{vinculo.pk} | {vinculo.funcionario.nome} | {vinculo.empresa.nome}: "
                f"{data_antiga.strftime('%d/%m/%Y')} → {data_nova.strftime('%d/%m/%Y')}"
            )
            if apply_changes:
                with transaction.atomic():
                    vinculo.data_demissao = data_nova
                    vinculo.save(update_fields=['data_demissao'])
                corrigidos += 1

        if apply_changes:
            self.stdout.write(self.style.SUCCESS(f"\n✔ {corrigidos} vínculo(s) corrigido(s).\n"))
        else:
            self.stdout.write(self.style.WARNING(
                f"\nNenhuma alteração aplicada (dry-run). Rode novamente com --apply para corrigir.\n"
            ))
