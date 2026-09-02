"""
Management command para enviar emails automáticos de trial (LGPD Compliance)

Uso:
    python manage.py send_trial_emails                    # Envia emails automáticos
    python manage.py send_trial_emails --dry-run          # Simula sem enviar

Agendar no cron/task scheduler para rodar diariamente:
    0 9 * * * cd /path/to/project && python manage.py send_trial_emails
"""

from django.core.management.base import BaseCommand
from datetime import date, timedelta
from billing.models import BillingCustomer
from billing.services.trial_email_service import TrialEmailService


class Command(BaseCommand):
    help = 'Envia emails automáticos de aviso para trials expirando ou expirados'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula o envio sem realmente enviar emails'
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        today = date.today()
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write(
            self.style.WARNING(
                f"{'[SIMULAÇÃO] ' if dry_run else ''}ENVIO DE EMAILS - Trial Warnings"
            )
        )
        self.stdout.write("="*80)
        self.stdout.write(f"\n📅 Data: {today.strftime('%d/%m/%Y')}\n")
        
        stats = {
            'expiring_3d': 0,
            'expiring_1d': 0,
            'expired_1d': 0,
            'deletion_2d': 0,
            'errors': []
        }
        
        # 1. TRIALS EXPIRANDO EM 3 DIAS
        self.stdout.write("\n1️⃣ Verificando trials expirando em 3 dias...")
        
        expiring_3d = BillingCustomer.objects.filter(
            status='trial',
            trial_active=True,
            trial_expires=today + timedelta(days=3)
        )
        
        count_3d = expiring_3d.count()
        self.stdout.write(f"   Encontrados: {count_3d}")
        
        for billing in expiring_3d:
            empresa_nome = billing.empresa.nome
            email = billing.email_cobranca
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f"   [DRY RUN] Email seria enviado para: {email} ({empresa_nome})"
                    )
                )
                stats['expiring_3d'] += 1
            else:
                self.stdout.write(f"   📧 Enviando para: {email} ({empresa_nome})...")
                try:
                    success = TrialEmailService.send_trial_expiring_soon(billing, 3)
                    if success:
                        self.stdout.write(
                            self.style.SUCCESS(f"      ✅ Enviado com sucesso")
                        )
                        stats['expiring_3d'] += 1
                    else:
                        raise Exception("Erro no envio")
                except Exception as e:
                    error_msg = f"Erro ao enviar para {email}: {str(e)}"
                    stats['errors'].append(error_msg)
                    self.stdout.write(
                        self.style.ERROR(f"      ❌ {error_msg}")
                    )
        
        # 2. TRIALS EXPIRANDO EM 1 DIA
        self.stdout.write("\n2️⃣ Verificando trials expirando em 1 dia...")
        
        expiring_1d = BillingCustomer.objects.filter(
            status='trial',
            trial_active=True,
            trial_expires=today + timedelta(days=1)
        )
        
        count_1d = expiring_1d.count()
        self.stdout.write(f"   Encontrados: {count_1d}")
        
        for billing in expiring_1d:
            empresa_nome = billing.empresa.nome
            email = billing.email_cobranca
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f"   [DRY RUN] Email seria enviado para: {email} ({empresa_nome})"
                    )
                )
                stats['expiring_1d'] += 1
            else:
                self.stdout.write(f"   📧 Enviando para: {email} ({empresa_nome})...")
                try:
                    success = TrialEmailService.send_trial_expiring_soon(billing, 1)
                    if success:
                        self.stdout.write(
                            self.style.SUCCESS(f"      ✅ Enviado com sucesso")
                        )
                        stats['expiring_1d'] += 1
                    else:
                        raise Exception("Erro no envio")
                except Exception as e:
                    error_msg = f"Erro ao enviar para {email}: {str(e)}"
                    stats['errors'].append(error_msg)
                    self.stdout.write(
                        self.style.ERROR(f"      ❌ {error_msg}")
                    )
        
        # 3. TRIALS EXPIRADOS HÁ 1 DIA (Aviso de 30 dias para exclusão)
        self.stdout.write("\n3️⃣ Verificando trials expirados há 1 dia...")
        
        expired_1d = BillingCustomer.objects.filter(
            status='trial',
            trial_expires=today - timedelta(days=1)
        )
        
        count_exp = expired_1d.count()
        self.stdout.write(f"   Encontrados: {count_exp}")
        
        for billing in expired_1d:
            empresa_nome = billing.empresa.nome
            email = billing.email_cobranca
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f"   [DRY RUN] Email de exclusão seria enviado para: {email} ({empresa_nome})"
                    )
                )
                stats['expired_1d'] += 1
            else:
                self.stdout.write(f"   📧 Enviando aviso de exclusão para: {email} ({empresa_nome})...")
                try:
                    success = TrialEmailService.send_trial_expired_warning(billing, 30)
                    if success:
                        self.stdout.write(
                            self.style.SUCCESS(f"      ✅ Enviado com sucesso")
                        )
                        stats['expired_1d'] += 1
                    else:
                        raise Exception("Erro no envio")
                except Exception as e:
                    error_msg = f"Erro ao enviar para {email}: {str(e)}"
                    stats['errors'].append(error_msg)
                    self.stdout.write(
                        self.style.ERROR(f"      ❌ {error_msg}")
                    )
        
        # 4. TRIALS QUE SERÃO EXCLUÍDOS EM 2 DIAS (28 dias após expiração = 30-2)
        self.stdout.write("\n4️⃣ Verificando trials para exclusão em 2 dias...")
        
        deletion_2d = BillingCustomer.objects.filter(
            status='trial',
            trial_expires=today - timedelta(days=28)  # 30 - 2 = 28 dias atrás
        )
        
        count_del = deletion_2d.count()
        self.stdout.write(f"   Encontrados: {count_del}")
        
        for billing in deletion_2d:
            empresa_nome = billing.empresa.nome
            email = billing.email_cobranca
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f"   [DRY RUN] Email URGENTE seria enviado para: {email} ({empresa_nome})"
                    )
                )
                stats['deletion_2d'] += 1
            else:
                self.stdout.write(f"   🚨 Enviando aviso FINAL para: {email} ({empresa_nome})...")
                try:
                    success = TrialEmailService.send_final_deletion_warning(billing)
                    if success:
                        self.stdout.write(
                            self.style.SUCCESS(f"      ✅ Enviado com sucesso")
                        )
                        stats['deletion_2d'] += 1
                    else:
                        raise Exception("Erro no envio")
                except Exception as e:
                    error_msg = f"Erro ao enviar para {email}: {str(e)}"
                    stats['errors'].append(error_msg)
                    self.stdout.write(
                        self.style.ERROR(f"      ❌ {error_msg}")
                    )
        
        # Resumo final
        self.stdout.write("\n" + "="*80)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\n[SIMULAÇÃO] CONCLUÍDA"
                    "\nNenhum email foi enviado. Execute sem --dry-run para enviar."
                )
            )
        else:
            if stats['errors']:
                self.stdout.write(
                    self.style.WARNING(
                        f"\n⚠️  ENVIO CONCLUÍDO COM ERROS ({len(stats['errors'])} erros)"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("\n✅ ENVIO CONCLUÍDO COM SUCESSO")
                )
        
        total_sent = stats['expiring_3d'] + stats['expiring_1d'] + stats['expired_1d'] + stats['deletion_2d']
        
        self.stdout.write(
            f"\n📊 Estatísticas:"
            f"\n   • Trials expirando em 3 dias: {stats['expiring_3d']} emails"
            f"\n   • Trials expirando em 1 dia: {stats['expiring_1d']} emails"
            f"\n   • Trials expirados (aviso 30 dias): {stats['expired_1d']} emails"
            f"\n   • Avisos finais (exclusão em 2 dias): {stats['deletion_2d']} emails"
            f"\n   • Total de emails enviados: {total_sent}"
        )
        
        if stats['errors']:
            self.stdout.write(
                f"\n   • Erros: {len(stats['errors'])}"
            )
            self.stdout.write("\n\nDetalhes dos erros:")
            for error in stats['errors']:
                self.stdout.write(f"   - {error}")
        
        self.stdout.write("\n" + "="*80 + "\n")
