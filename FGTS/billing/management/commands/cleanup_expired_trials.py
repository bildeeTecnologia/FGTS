"""
Management command para limpar dados de trials expirados (LGPD Compliance)

Uso:
    python manage.py cleanup_expired_trials                    # Deleta trials expirados há 30+ dias
    python manage.py cleanup_expired_trials --dry-run          # Simula sem deletar
    python manage.py cleanup_expired_trials --days 45          # Deleta após 45 dias

Agendar no cron/task scheduler:
    0 2 * * * cd /path/to/project && python manage.py cleanup_expired_trials
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from billing.models import BillingCustomer
from empresas.models import Empresa
from funcionarios.models import Funcionario
from lancamentos.models import Lancamento
from django.db import transaction


class Command(BaseCommand):
    help = 'Limpa dados de trials expirados há mais de 30 dias (LGPD compliance)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a limpeza sem deletar dados'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Dias após expiração para deletar (padrão: 30)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força deleção sem confirmação'
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days_after = options['days']
        force = options['force']
        
        # Data limite: trials expirados há mais de X dias
        cutoff_date = date.today() - timedelta(days=days_after)
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write(
            self.style.WARNING(
                f"{'[SIMULAÇÃO] ' if dry_run else ''}LIMPEZA LGPD - Trials Expirados"
            )
        )
        self.stdout.write("="*80)
        self.stdout.write(f"\n📅 Data de hoje: {date.today().strftime('%d/%m/%Y')}")
        self.stdout.write(f"📅 Data de corte: {cutoff_date.strftime('%d/%m/%Y')}")
        self.stdout.write(f"📊 Buscando trials expirados há mais de {days_after} dias...\n")
        
        # Buscar trials expirados há mais de X dias
        expired_trials = BillingCustomer.objects.filter(
            status='trial',
            trial_expires__lt=cutoff_date
        ).select_related('empresa')
        
        total_count = expired_trials.count()
        
        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS("\n✅ Nenhum trial expirado para limpar\n")
            )
            return
        
        # Calcular totais antes de deletar
        total_funcionarios = 0
        total_lancamentos = 0
        
        trial_details = []
        
        for billing in expired_trials:
            empresa = billing.empresa
            func_count = Funcionario.objects.filter(empresa=empresa).count()
            lanc_count = Lancamento.objects.filter(empresa=empresa).count()
            
            total_funcionarios += func_count
            total_lancamentos += lanc_count
            
            days_expired = (date.today() - billing.trial_expires).days
            
            trial_details.append({
                'billing': billing,
                'empresa': empresa,
                'funcionarios': func_count,
                'lancamentos': lanc_count,
                'days_expired': days_expired
            })
        
        # Mostrar resumo
        self.stdout.write(
            self.style.WARNING(
                f"\n⚠️  ATENÇÃO: {total_count} trials serão processados"
            )
        )
        self.stdout.write(
            f"\n📊 Estatísticas totais:"
            f"\n   • Empresas: {total_count}"
            f"\n   • Funcionários: {total_funcionarios}"
            f"\n   • Lançamentos: {total_lancamentos}"
            f"\n"
        )
        
        # Mostrar detalhes de cada trial
        self.stdout.write("\n📋 Detalhes dos trials a serem deletados:\n")
        
        for idx, detail in enumerate(trial_details, 1):
            empresa = detail['empresa']
            billing = detail['billing']
            
            self.stdout.write(
                f"\n{idx}. {empresa.nome}"
                f"\n   CNPJ: {empresa.cnpj or 'N/A'}"
                f"\n   Trial expirou: {billing.trial_expires.strftime('%d/%m/%Y')} "
                f"({detail['days_expired']} dias atrás)"
                f"\n   Email: {billing.email_cobranca or 'N/A'}"
                f"\n   Dados: {detail['funcionarios']} funcionários, "
                f"{detail['lancamentos']} lançamentos"
            )
        
        # Confirmação
        if not dry_run and not force:
            self.stdout.write("\n" + "="*80)
            self.stdout.write(
                self.style.ERROR(
                    "\n⚠️  ATENÇÃO: Esta ação é IRREVERSÍVEL!"
                    "\n   Todos os dados acima serão EXCLUÍDOS PERMANENTEMENTE."
                    "\n   Isso inclui funcionários, lançamentos e configurações."
                )
            )
            
            confirm = input("\n\nDigite 'CONFIRMAR' para prosseguir ou Enter para cancelar: ")
            
            if confirm != 'CONFIRMAR':
                self.stdout.write(
                    self.style.WARNING("\n❌ Operação cancelada pelo usuário\n")
                )
                return
        
        # Processar deleção
        self.stdout.write("\n" + "="*80)
        self.stdout.write(
            self.style.WARNING(
                f"\n{'[SIMULAÇÃO] ' if dry_run else ''}Processando deleção..."
            )
        )
        self.stdout.write("="*80 + "\n")
        
        deleted_stats = {
            'empresas': 0,
            'funcionarios': 0,
            'lancamentos': 0,
            'billing_customers': 0,
            'errors': []
        }
        
        for detail in trial_details:
            billing = detail['billing']
            empresa = detail['empresa']
            empresa_nome = empresa.nome
            
            try:
                if not dry_run:
                    with transaction.atomic():
                        # DELETAR EM CASCATA
                        # 1. Lançamentos
                        lanc_deleted = Lancamento.objects.filter(empresa=empresa).delete()[0]
                        
                        # 2. Funcionários
                        func_deleted = Funcionario.objects.filter(empresa=empresa).delete()[0]
                        
                        # 3. Billing Customer
                        billing.delete()
                        
                        # 4. Empresa (e UsuarioEmpresa via CASCADE)
                        empresa.delete()
                        
                        deleted_stats['empresas'] += 1
                        deleted_stats['funcionarios'] += func_deleted
                        deleted_stats['lancamentos'] += lanc_deleted
                        deleted_stats['billing_customers'] += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"   ✅ {empresa_nome} - Deletada "
                            f"({detail['funcionarios']} func, {detail['lancamentos']} lanc)"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"   [DRY RUN] {empresa_nome} seria deletada "
                            f"({detail['funcionarios']} func, {detail['lancamentos']} lanc)"
                        )
                    )
                    
            except Exception as e:
                error_msg = f"Erro ao deletar {empresa_nome}: {str(e)}"
                deleted_stats['errors'].append(error_msg)
                self.stdout.write(
                    self.style.ERROR(f"   ❌ {error_msg}")
                )
        
        # Resumo final
        self.stdout.write("\n" + "="*80)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\n[SIMULAÇÃO] CONCLUÍDA"
                    "\nNenhum dado foi deletado. Execute sem --dry-run para deletar."
                )
            )
        else:
            if deleted_stats['errors']:
                self.stdout.write(
                    self.style.WARNING(
                        f"\n⚠️  LIMPEZA CONCLUÍDA COM ERROS ({len(deleted_stats['errors'])} erros)"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("\n✅ LIMPEZA CONCLUÍDA COM SUCESSO")
                )
        
        self.stdout.write(
            f"\n📊 Estatísticas finais:"
            f"\n   • Empresas deletadas: {deleted_stats['empresas']}"
            f"\n   • Funcionários deletados: {deleted_stats['funcionarios']}"
            f"\n   • Lançamentos deletados: {deleted_stats['lancamentos']}"
            f"\n   • Billing customers deletados: {deleted_stats['billing_customers']}"
        )
        
        if deleted_stats['errors']:
            self.stdout.write(
                f"\n   • Erros: {len(deleted_stats['errors'])}"
            )
            self.stdout.write("\n\nDetalhes dos erros:")
            for error in deleted_stats['errors']:
                self.stdout.write(f"   - {error}")
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Comando concluído em {date.today().strftime('%d/%m/%Y às %H:%M:%S')}"
            )
        )
        self.stdout.write("="*80 + "\n")
