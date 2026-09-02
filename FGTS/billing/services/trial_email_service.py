"""
Serviço para envio de emails automáticos relacionados ao trial (LGPD Compliance)

Emails enviados:
1. Trial expirando (3 dias antes)
2. Trial expirando (1 dia antes)
3. Trial expirado - aviso de 30 dias para exclusão
4. Últimos dias - aviso de exclusão iminente (2 dias antes)
"""

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from datetime import date


class TrialEmailService:
    """Serviço para envio de emails relacionados ao trial"""
    
    @staticmethod
    def send_trial_expiring_soon(billing_customer, days_remaining):
        """
        Email quando trial está para expirar
        
        Args:
            billing_customer: BillingCustomer instance
            days_remaining: int (dias restantes)
        """
        empresa = billing_customer.empresa
        
        subject = f"⏰ Seu trial FGTS Web expira em {days_remaining} {'dia' if days_remaining == 1 else 'dias'}"
        
        # Contar dados cadastrados
        from funcionarios.models import Funcionario
        from lancamentos.models import Lancamento
        
        func_count = Funcionario.objects.filter(empresa=empresa).count()
        lanc_count = Lancamento.objects.filter(empresa=empresa).count()
        
        message = f"""
Olá!

Seu período de trial no FGTS Web está chegando ao fim.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 INFORMAÇÕES DO TRIAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Empresa: {empresa.nome}
Dias restantes: {days_remaining} {'dia' if days_remaining == 1 else 'dias'}
Data de expiração: {billing_customer.trial_expires.strftime('%d/%m/%Y')}

Dados cadastrados até agora:
• {func_count} funcionários
• {lanc_count} lançamentos

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💳 ASSINE AGORA E CONTINUE USANDO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Para continuar usando o sistema sem interrupções, assine agora:

👉 {settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000'}/billing/checkout/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  IMPORTANTE - Política de Dados (LGPD)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Após a expiração do trial, você terá 30 dias para assinar.

Caso não assine nesse período, todos os dados cadastrados 
(funcionários, lançamentos, configurações) serão EXCLUÍDOS 
PERMANENTEMENTE para conformidade com a Lei Geral de 
Proteção de Dados (LGPD).

Esta exclusão é automática e irreversível.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Dúvidas? Responda este email ou acesse nosso suporte.

Atenciosamente,
Equipe FGTS Web
"""
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[billing_customer.email_cobranca],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Erro ao enviar email para {billing_customer.email_cobranca}: {str(e)}")
            return False
    
    @staticmethod
    def send_trial_expired_warning(billing_customer, days_until_deletion=30):
        """
        Email após trial expirar, avisando sobre exclusão
        
        Args:
            billing_customer: BillingCustomer instance
            days_until_deletion: int (dias até exclusão, padrão 30)
        """
        empresa = billing_customer.empresa
        
        subject = "⚠️ Trial FGTS Web expirado - Dados serão excluídos em 30 dias"
        
        # Contar dados
        from funcionarios.models import Funcionario
        from lancamentos.models import Lancamento
        
        func_count = Funcionario.objects.filter(empresa=empresa).count()
        lanc_count = Lancamento.objects.filter(empresa=empresa).count()
        
        message = f"""
Olá!

Seu trial no FGTS Web expirou.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 STATUS DO TRIAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Empresa: {empresa.nome}
Trial expirou em: {billing_customer.trial_expires.strftime('%d/%m/%Y')}
Exclusão de dados em: {days_until_deletion} dias

Seus dados cadastrados:
• {func_count} funcionários
• {lanc_count} lançamentos
• Relatórios e configurações

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 LGPD - Política de Retenção de Dados
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Por questões de conformidade com a Lei Geral de Proteção 
de Dados (LGPD), manteremos seus dados por mais {days_until_deletion} dias.

Após esse prazo, TODOS OS DADOS SERÃO EXCLUÍDOS 
PERMANENTEMENTE de forma automática e irreversível.

Isso inclui:
✗ Todos os funcionários cadastrados
✗ Todos os lançamentos e relatórios
✗ Configurações da empresa
✗ Histórico de cálculos

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💳 ASSINE AGORA E MANTENHA SEUS DADOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Para assinar e manter todos os seus dados, acesse:

👉 {settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000'}/billing/checkout/

Planos a partir de R$ 99,90/mês com todas as funcionalidades.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Você receberá lembretes periódicos nos próximos {days_until_deletion} dias.

Dúvidas? Entre em contato: suporte@fgtsweb.com.br

Atenciosamente,
Equipe FGTS Web
"""
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[billing_customer.email_cobranca],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Erro ao enviar email para {billing_customer.email_cobranca}: {str(e)}")
            return False
    
    @staticmethod
    def send_final_deletion_warning(billing_customer):
        """
        Email 2 dias antes da exclusão final
        
        Args:
            billing_customer: BillingCustomer instance
        """
        empresa = billing_customer.empresa
        
        subject = "🚨 URGENTE - Dados FGTS Web serão excluídos em 2 DIAS"
        
        # Contar dados
        from funcionarios.models import Funcionario
        from lancamentos.models import Lancamento
        
        func_count = Funcionario.objects.filter(empresa=empresa).count()
        lanc_count = Lancamento.objects.filter(empresa=empresa).count()
        
        message = f"""
🚨 ÚLTIMO AVISO - AÇÃO URGENTE NECESSÁRIA 🚨

Este é o ÚLTIMO AVISO antes da exclusão permanente dos seus dados.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ EXCLUSÃO EM 2 DIAS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Empresa: {empresa.nome}
Exclusão automática em: 2 DIAS
Data: {(billing_customer.trial_expires + __import__('datetime').timedelta(days=30)).strftime('%d/%m/%Y')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  O QUE SERÁ EXCLUÍDO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✗ {func_count} funcionários cadastrados
✗ {lanc_count} lançamentos registrados
✗ Todos os relatórios e cálculos
✗ Todas as configurações da empresa
✗ Todo o histórico de uso

Esta exclusão é AUTOMÁTICA, IRREVERSÍVEL e necessária 
por conformidade com a LGPD (Lei Geral de Proteção de Dados).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💳 ASSINE AGORA E IMPEÇA A EXCLUSÃO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Para IMPEDIR a exclusão e continuar usando, assine AGORA:

👉 {settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000'}/billing/checkout/

⏰ Você tem apenas 48 horas!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Após a exclusão, você poderá criar uma nova conta, mas todos 
os dados atuais serão perdidos permanentemente.

Última chance: Assine nos próximos 2 dias!

Suporte urgente: suporte@fgtsweb.com.br
WhatsApp: (11) 9 9999-9999

Atenciosamente,
Equipe FGTS Web
"""
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[billing_customer.email_cobranca],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Erro ao enviar email para {billing_customer.email_cobranca}: {str(e)}")
            return False
    
    @staticmethod
    def send_deletion_complete_notification(email, empresa_nome):
        """
        Email informando que dados foram excluídos (após exclusão)
        
        Args:
            email: str (email do usuário)
            empresa_nome: str (nome da empresa que foi deletada)
        """
        subject = "✓ Dados FGTS Web excluídos conforme LGPD"
        
        message = f"""
Olá,

Informamos que os dados da empresa "{empresa_nome}" foram 
excluídos do sistema FGTS Web conforme nossa Política de 
Retenção de Dados e em conformidade com a LGPD.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ DADOS EXCLUÍDOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Todos os funcionários cadastrados
• Todos os lançamentos e relatórios
• Configurações da empresa
• Histórico de uso

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 QUER USAR O SISTEMA NOVAMENTE?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Você pode criar uma nova conta a qualquer momento:

👉 {settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000'}/registro/

Terá direito a um novo período de trial de 7 dias.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Obrigado por testar o FGTS Web!

Atenciosamente,
Equipe FGTS Web
"""
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Erro ao enviar email para {email}: {str(e)}")
            return False
