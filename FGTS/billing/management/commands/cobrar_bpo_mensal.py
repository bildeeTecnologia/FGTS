"""
Management command: cobrar_bpo_mensal

Gera faturas mensais para todos os escritórios BPO com vencimento hoje.
Execute via cron ou scheduler uma vez por dia:
    python manage.py cobrar_bpo_mensal

Lógica de cobrança (high-water mark):
- Conta CNPJs que eram ativos no INÍCIO do ciclo (último vencimento)
- Suspenções realizadas DENTRO do ciclo atual ainda são cobradas
- A suspenção só reduz a cobrança no ciclo SEGUINTE
- Isso impede o "truque" de suspender antes do vencimento para pagar menos

Exemplo:
  Vencimento: dia 5 | Usuário suspende 10 CNPJs no dia 4
  → Todos os 10 CNPJs foram ativos neste ciclo → cobrados normalmente
  → A partir do próximo mês, sem novas ativações, a fatura será R$ 0
"""

import logging
from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import Q

from billing.models_bpo import ContaBPO, FaturaBPO
from billing.services.asaas_client import AsaasClient

logger = logging.getLogger(__name__)


def _ultimo_vencimento(dia_cobranca: int, hoje: date) -> date:
    """Retorna a data do vencimento anterior (início do ciclo atual)."""
    if hoje.month == 1:
        return date(hoje.year - 1, 12, dia_cobranca)
    return date(hoje.year, hoje.month - 1, dia_cobranca)


def _cnpjs_faturáveis(conta: ContaBPO, ultimo_vencimento: date) -> int:
    """
    Conta CNPJs que devem ser cobrados neste ciclo:
    - CNPJs ativos agora, OU
    - CNPJs suspensos APÓS o último vencimento (usaram o serviço neste ciclo)

    Isso impede que o BPO suspenda empresas no dia anterior ao vencimento
    para zerrar a fatura e reativar logo em seguida.
    """
    return conta.empresas_gerenciadas.filter(
        Q(status='active')
        | Q(status='suspended', data_suspensao__gte=ultimo_vencimento)
    ).count()


class Command(BaseCommand):
    help = 'Gera faturas mensais BPO para escritórios com vencimento hoje'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a execução sem criar cobranças no Asaas',
        )
        parser.add_argument(
            '--dia',
            type=int,
            default=None,
            help='Forçar dia de cobrança específico (padrão: dia de hoje)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        dia_alvo = options['dia'] or date.today().day
        hoje = date.today()
        mes_ref = date(hoje.year, hoje.month, 1)
        ultimo_venc = _ultimo_vencimento(dia_alvo, hoje)

        contas = ContaBPO.objects.filter(
            status='active',
            dia_cobranca=dia_alvo,
            asaas_customer_id__isnull=False,
        ).exclude(asaas_customer_id='')

        if not contas.exists():
            self.stdout.write('Nenhuma conta BPO com vencimento hoje.')
            return

        geradas = 0
        ignoradas = 0
        erros = 0

        for conta in contas:
            # Evita fatura duplicada no mesmo mês
            if FaturaBPO.objects.filter(conta_bpo=conta, mes_referencia=mes_ref).exists():
                ignoradas += 1
                continue

            # High-water mark: conta CNPJs ativos ou suspensos neste ciclo
            cnpjs = _cnpjs_faturáveis(conta, ultimo_venc)
            if cnpjs == 0:
                ignoradas += 1
                continue

            preco = conta.get_effective_preco_por_cnpj()
            valor = (preco * cnpjs).quantize(Decimal('0.01'))

            if valor <= Decimal('0.00'):
                ignoradas += 1
                continue

            descricao = (
                f'FGTS Web BPO — Ref. {hoje.strftime("%m/%Y")} '
                f'— {cnpjs} CNPJ(s) × R$ {preco}'
            )

            if dry_run:
                self.stdout.write(
                    f'[DRY-RUN] {conta.empresa_bpo.nome}: '
                    f'{cnpjs} CNPJs (incl. suspensos neste ciclo) × R$ {preco} = R$ {valor}'
                )
                geradas += 1
                continue

            try:
                client = AsaasClient()
                payment_payload = {
                    'customer': conta.asaas_customer_id,
                    'billingType': conta.billing_type,
                    'value': float(valor),
                    'dueDate': hoje.isoformat(),
                    'description': descricao,
                    'externalReference': f'bpo-{conta.pk}-{mes_ref.strftime("%Y-%m")}',
                }
                resp = client.create_payment(payment_payload)
                asaas_payment_id = resp.get('id')

                FaturaBPO.objects.create(
                    conta_bpo=conta,
                    mes_referencia=mes_ref,
                    cnpjs_cobrados=cnpjs,
                    valor=valor,
                    asaas_payment_id=asaas_payment_id,
                    status='pending',
                )
                geradas += 1
                self.stdout.write(
                    f'Fatura gerada: {conta.empresa_bpo.nome} — R$ {valor} ({asaas_payment_id})'
                )

            except Exception as exc:
                logger.exception('Erro ao gerar fatura BPO para conta pk=%s', conta.pk)
                self.stderr.write(f'ERRO em {conta.empresa_bpo.nome}: {exc}')
                erros += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Resultado: {geradas} fatura(s) gerada(s), '
                f'{ignoradas} ignorada(s), {erros} erro(s).'
            )
        )
