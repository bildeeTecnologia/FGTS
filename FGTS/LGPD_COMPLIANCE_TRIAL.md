# 🔐 LGPD COMPLIANCE - SISTEMA TRIAL

**Data**: 02 de Janeiro, 2026  
**Status**: ⚠️ CRÍTICO - Sistema NÃO está em conformidade com LGPD  
**Risco Legal**: ALTO - Multa pode chegar a 2% do faturamento (até R$ 50 milhões)

---

## 🚨 PROBLEMA IDENTIFICADO PELO USUÁRIO

### Cenário Real:

```
1. Usuário se cadastra no sistema (trial 7 dias)
2. Cria empresa "ABC Serviços Ltda"
3. Cadastra 10 funcionários:
   
   Funcionário 1:
   - Nome: João da Silva
   - CPF: 123.456.789-00  ← DADO PESSOAL SENSÍVEL
   - PIS: 120.123.456-70  ← DADO PESSOAL SENSÍVEL
   - Data Nascimento: 10/05/1985
   - Endereço: Rua X, 123...
   
   Funcionário 2:
   - Maria Santos
   - CPF: 987.654.321-00  ← DADO PESSOAL SENSÍVEL
   - ...
   
   (Total: 10 pessoas REAIS com dados pessoais verdadeiros)

4. Trial expira em 7 dias
5. Usuário NÃO assina
6. Usuário abandona a conta

❌ O QUE ACONTECE COM OS DADOS?
   → FICAM NO BANCO DE DADOS PARA SEMPRE!
   
❌ VIOLAÇÃO LGPD:
   → Retenção de dados sem finalidade
   → Não informamos prazo de exclusão
   → Não pedimos consentimento adequado
   → Não damos opção de exclusão
```

---

## 📊 ANÁLISE DE CONFORMIDADE LGPD

### ❌ O que NÃO temos (e PRECISAMOS):

| Item LGPD | Status Atual | Risco | Ação Necessária |
|---|---|---|---|
| **Aviso de retenção** | ❌ Não existe | ALTO | Informar "dados serão excluídos em 30 dias" |
| **Exclusão automática** | ❌ Não existe | ALTO | Job que apaga dados após trial+30d |
| **Consentimento explícito** | ❌ Não existe | MÉDIO | Checkbox "Aceito termos LGPD" no cadastro |
| **Política de Privacidade** | ❌ Não existe | ALTO | Documento explicando uso de dados |
| **Email de aviso (trial expirando)** | ❌ Não existe | MÉDIO | "Seu trial expira em 3 dias" |
| **Email de aviso (exclusão)** | ❌ Não existe | ALTO | "Dados serão excluídos em 7 dias" |
| **Opt-out marketing** | ❌ Não existe | BAIXO | "Não quero receber promoções" |
| **Relatório de dados** | ❌ Não existe | MÉDIO | User pode baixar seus dados (LGPD Art. 18) |
| **Exclusão manual** | ❌ Não existe | MÉDIO | User pode deletar conta manualmente |

---

## 🎯 SOLUÇÕES NECESSÁRIAS

### **SOLUÇÃO 1: Política de Retenção de Dados**

**Proposta**:
```
Trial: 7 dias de teste
Trial expirado sem conversão: +30 dias de graça
Total antes de exclusão: 37 dias

Linha do tempo:
Dia 1-7: Trial ativo (pode usar sistema)
Dia 8: Trial expira → EMAIL: "Trial expirou, assine ou dados serão excluídos em 30 dias"
Dia 15: EMAIL: "Ainda tem 22 dias para assinar"
Dia 30: EMAIL: "Últimos 7 dias! Assine ou dados serão excluídos"
Dia 35: EMAIL: "⚠️ Dados serão excluídos em 2 dias"
Dia 37: JOB automático apaga:
        - Todos os funcionários
        - Todos os lançamentos
        - Todas as empresas
        - Billing customer (mantém apenas username/email em lista de "já usou trial")
```

**Justificativa Legal (LGPD)**:
- Art. 6º, III: Dados devem ter finalidade legítima
- Art. 15: Titular tem direito de saber duração do armazenamento
- Art. 16: Titular pode solicitar exclusão a qualquer momento

---

### **SOLUÇÃO 2: Aviso no Banner Trial**

**Localização**: `empresas/templates/base.html`

**Adicionar no banner**:
```html
<div class="alert alert-warning">
    <strong>{{ request.trial_customer.trial_warning_message }}</strong>
    <br>
    <small class="text-muted">
        ⚠️ <strong>Política de Dados:</strong> 
        Após o término do trial, você terá 30 dias para assinar. 
        Caso não assine, <strong>todos os dados cadastrados serão 
        excluídos permanentemente</strong> por questões de conformidade 
        com a LGPD.
    </small>
</div>
```

---

### **SOLUÇÃO 3: Termo de Consentimento no Cadastro**

**Localização**: `usuarios/templates/usuarios/register.html`

**Adicionar antes do botão "Cadastrar"**:
```html
<div class="form-check mb-3">
    <input class="form-check-input" type="checkbox" id="lgpd_consent" 
           name="lgpd_consent" required>
    <label class="form-check-label" for="lgpd_consent">
        Li e concordo com a 
        <a href="{% url 'politica-privacidade' %}" target="_blank">
            Política de Privacidade
        </a> 
        e 
        <a href="{% url 'termos-uso' %}" target="_blank">
            Termos de Uso
        </a>.
        Estou ciente que:
        <ul class="mt-2 small text-muted">
            <li>Meus dados serão utilizados apenas para operação do sistema</li>
            <li>Em modo trial, os dados serão mantidos por até 37 dias</li>
            <li>Após esse prazo sem assinatura, os dados serão excluídos</li>
            <li>Posso solicitar exclusão dos meus dados a qualquer momento</li>
        </ul>
    </label>
</div>
```

---

### **SOLUÇÃO 4: Job de Limpeza Automática**

**Criar arquivo**: `billing/management/commands/cleanup_expired_trials.py`

```python
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from billing.models import BillingCustomer
from empresas.models import Empresa
from funcionarios.models import Funcionario
from lancamentos.models import Lancamento


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
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days_after = options['days']
        
        # Data limite: trials expirados há mais de X dias
        cutoff_date = date.today() - timedelta(days=days_after)
        
        self.stdout.write(
            self.style.WARNING(
                f"\n{'[DRY RUN] ' if dry_run else ''}LIMPEZA LGPD - Trials Expirados"
            )
        )
        self.stdout.write(f"Data de corte: {cutoff_date}")
        
        # Buscar trials expirados há mais de X dias
        expired_trials = BillingCustomer.objects.filter(
            status='trial',
            trial_expires__lt=cutoff_date
        ).select_related('empresa')
        
        total_count = expired_trials.count()
        
        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS("✅ Nenhum trial expirado para limpar")
            )
            return
        
        self.stdout.write(
            self.style.WARNING(
                f"\n⚠️ Encontrados {total_count} trials expirados para limpeza"
            )
        )
        
        deleted_stats = {
            'empresas': 0,
            'funcionarios': 0,
            'lancamentos': 0,
            'billing_customers': 0
        }
        
        for billing in expired_trials:
            empresa = billing.empresa
            empresa_nome = empresa.nome
            
            self.stdout.write(f"\n📋 Processando: {empresa_nome}")
            
            # Contar antes de deletar
            func_count = Funcionario.objects.filter(empresa=empresa).count()
            lanc_count = Lancamento.objects.filter(empresa=empresa).count()
            
            self.stdout.write(f"   - {func_count} funcionários")
            self.stdout.write(f"   - {lanc_count} lançamentos")
            
            if not dry_run:
                # DELETAR EM CASCATA
                # 1. Lançamentos
                Lancamento.objects.filter(empresa=empresa).delete()
                
                # 2. Funcionários
                Funcionario.objects.filter(empresa=empresa).delete()
                
                # 3. Billing Customer
                billing.delete()
                
                # 4. Empresa
                empresa.delete()
                
                deleted_stats['empresas'] += 1
                deleted_stats['funcionarios'] += func_count
                deleted_stats['lancamentos'] += lanc_count
                deleted_stats['billing_customers'] += 1
                
                self.stdout.write(
                    self.style.SUCCESS(f"   ✅ {empresa_nome} deletada")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"   [DRY RUN] {empresa_nome} seria deletada")
                )
        
        # Resumo
        self.stdout.write("\n" + "="*60)
        if dry_run:
            self.stdout.write(
                self.style.WARNING("SIMULAÇÃO CONCLUÍDA (nenhum dado foi deletado)")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("LIMPEZA CONCLUÍDA")
            )
        
        self.stdout.write(
            f"\n📊 Estatísticas:"
            f"\n   - Empresas: {deleted_stats['empresas']}"
            f"\n   - Funcionários: {deleted_stats['funcionarios']}"
            f"\n   - Lançamentos: {deleted_stats['lancamentos']}"
            f"\n   - Billing Customers: {deleted_stats['billing_customers']}"
        )
        self.stdout.write("="*60 + "\n")
```

**Agendar no cron** (Linux) ou **Task Scheduler** (Windows):
```bash
# Rodar todo dia às 2h da manhã
0 2 * * * cd /path/to/project && python manage.py cleanup_expired_trials
```

---

### **SOLUÇÃO 5: Emails Automáticos**

**Criar**: `billing/services/trial_email_service.py`

```python
from django.core.mail import send_mail
from django.conf import settings
from datetime import date


class TrialEmailService:
    
    @staticmethod
    def send_trial_expiring_soon(billing_customer, days_remaining):
        """Email quando trial está para expirar"""
        empresa = billing_customer.empresa
        
        subject = f"⏰ Seu trial expira em {days_remaining} dias"
        
        message = f"""
        Olá,
        
        Seu período de trial no FGTS Web está chegando ao fim!
        
        Empresa: {empresa.nome}
        Dias restantes: {days_remaining}
        Data de expiração: {billing_customer.trial_expires.strftime('%d/%m/%Y')}
        
        Para continuar usando o sistema sem interrupções, assine agora:
        👉 {settings.BASE_URL}/billing/checkout/
        
        ⚠️ IMPORTANTE - Política de Dados (LGPD):
        Após a expiração do trial, você terá 30 dias para assinar.
        Caso não assine, todos os dados cadastrados (funcionários, lançamentos)
        serão EXCLUÍDOS PERMANENTEMENTE para conformidade com a LGPD.
        
        Dúvidas? Responda este email ou acesse nosso suporte.
        
        Atenciosamente,
        Equipe FGTS Web
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[billing_customer.email_cobranca],
            fail_silently=False,
        )
    
    @staticmethod
    def send_trial_expired_warning(billing_customer, days_until_deletion):
        """Email após trial expirar, avisando sobre exclusão"""
        empresa = billing_customer.empresa
        
        subject = f"⚠️ Trial expirado - Dados serão excluídos em {days_until_deletion} dias"
        
        message = f"""
        Olá,
        
        Seu trial no FGTS Web expirou.
        
        Empresa: {empresa.nome}
        Trial expirou em: {billing_customer.trial_expires.strftime('%d/%m/%Y')}
        Exclusão de dados em: {days_until_deletion} dias
        
        📋 ATENÇÃO - Seus dados cadastrados:
        - Funcionários: X cadastrados
        - Lançamentos: Y registros
        - Relatórios: Z gerados
        
        🔒 LGPD - Política de Retenção:
        Por questões de conformidade com a LGPD (Lei Geral de Proteção de Dados),
        manteremos seus dados por mais {days_until_deletion} dias.
        
        Após esse prazo, TODOS OS DADOS SERÃO EXCLUÍDOS PERMANENTEMENTE.
        
        Para assinar e manter seus dados, acesse:
        👉 {settings.BASE_URL}/billing/checkout/
        
        Dúvidas? Entre em contato: suporte@fgtsweb.com.br
        
        Atenciosamente,
        Equipe FGTS Web
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[billing_customer.email_cobranca],
            fail_silently=False,
        )
    
    @staticmethod
    def send_final_deletion_warning(billing_customer):
        """Email 2 dias antes da exclusão final"""
        empresa = billing_customer.empresa
        
        subject = "🚨 URGENTE - Dados serão excluídos em 2 dias"
        
        message = f"""
        Olá,
        
        Este é o ÚLTIMO AVISO antes da exclusão permanente dos seus dados.
        
        Empresa: {empresa.nome}
        Exclusão em: 2 DIAS
        
        ⚠️ O QUE SERÁ EXCLUÍDO:
        - Todos os funcionários cadastrados
        - Todos os lançamentos e relatórios
        - Configurações da empresa
        
        Esta exclusão é IRREVERSÍVEL e necessária por conformidade com a LGPD.
        
        Para IMPEDIR a exclusão e continuar usando, assine AGORA:
        👉 {settings.BASE_URL}/billing/checkout/
        
        Após a exclusão, você poderá criar uma nova conta, mas todos os dados
        atuais serão perdidos permanentemente.
        
        Última chance: Assine em até 2 dias!
        
        Atenciosamente,
        Equipe FGTS Web
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[billing_customer.email_cobranca],
            fail_silently=False,
        )
```

**Agendar envio de emails** (criar command):

```python
# billing/management/commands/send_trial_emails.py
from django.core.management.base import BaseCommand
from datetime import date, timedelta
from billing.models import BillingCustomer
from billing.services.trial_email_service import TrialEmailService


class Command(BaseCommand):
    help = 'Envia emails de aviso para trials expirando ou expirados'
    
    def handle(self, *args, **options):
        today = date.today()
        
        # 1. Trials expirando em 3 dias
        expiring_3d = BillingCustomer.objects.filter(
            status='trial',
            trial_active=True,
            trial_expires=today + timedelta(days=3)
        )
        
        for billing in expiring_3d:
            self.stdout.write(f"📧 Enviando email 3 dias para {billing.empresa.nome}")
            TrialEmailService.send_trial_expiring_soon(billing, 3)
        
        # 2. Trials expirando em 1 dia
        expiring_1d = BillingCustomer.objects.filter(
            status='trial',
            trial_active=True,
            trial_expires=today + timedelta(days=1)
        )
        
        for billing in expiring_1d:
            self.stdout.write(f"📧 Enviando email 1 dia para {billing.empresa.nome}")
            TrialEmailService.send_trial_expiring_soon(billing, 1)
        
        # 3. Trials expirados há 1 dia (aviso de 30 dias)
        expired_1d = BillingCustomer.objects.filter(
            status='trial',
            trial_expires=today - timedelta(days=1)
        )
        
        for billing in expired_1d:
            self.stdout.write(f"📧 Enviando aviso de exclusão para {billing.empresa.nome}")
            TrialEmailService.send_trial_expired_warning(billing, 30)
        
        # 4. Trials que serão excluídos em 2 dias
        deletion_2d = BillingCustomer.objects.filter(
            status='trial',
            trial_expires=today - timedelta(days=28)  # 30-2 = 28 dias atrás
        )
        
        for billing in deletion_2d:
            self.stdout.write(f"🚨 Enviando aviso FINAL para {billing.empresa.nome}")
            TrialEmailService.send_final_deletion_warning(billing)
        
        self.stdout.write(self.style.SUCCESS("✅ Emails enviados com sucesso"))
```

---

### **SOLUÇÃO 6: Política de Privacidade e Termos de Uso**

**Criar páginas**:

1. **`/politica-privacidade/`**
   - Explicar coleta de dados (nome, CPF, PIS, etc)
   - Explicar finalidade (cálculo FGTS)
   - Explicar retenção (trial: 37 dias / assinante: enquanto ativo)
   - Explicar direitos (acesso, correção, exclusão)
   - Explicar segurança (criptografia, acesso restrito)

2. **`/termos-uso/`**
   - Explicar trial (7 dias)
   - Explicar política de cancelamento
   - Explicar exclusão de dados após trial
   - Explicar responsabilidades

**Implementação rápida**:

```python
# fgtsweb/views.py
from django.views.generic import TemplateView

class PoliticaPrivacidadeView(TemplateView):
    template_name = 'fgtsweb/politica_privacidade.html'

class TermosUsoView(TemplateView):
    template_name = 'fgtsweb/termos_uso.html'

# fgtsweb/urls.py
urlpatterns = [
    path('politica-privacidade/', PoliticaPrivacidadeView.as_view(), name='politica-privacidade'),
    path('termos-uso/', TermosUsoView.as_view(), name='termos-uso'),
]
```

---

## 📋 CRONOGRAMA DE IMPLEMENTAÇÃO LGPD

### **URGENTE (Esta semana)**:
```
☐ Criar política de retenção de dados (30 dias após trial)
☐ Adicionar aviso no banner trial sobre exclusão
☐ Criar job de limpeza automática (cleanup_expired_trials)
☐ Agendar job para rodar diariamente
```

### **IMPORTANTE (Próximas 2 semanas)**:
```
☐ Criar sistema de emails automáticos (trial_email_service)
☐ Agendar envio de emails (3 dias, 1 dia, expirado, 2 dias antes exclusão)
☐ Adicionar checkbox LGPD no cadastro
☐ Criar página de Política de Privacidade
☐ Criar página de Termos de Uso
```

### **MELHORIAS (Próximo mês)**:
```
☐ Implementar "Baixar meus dados" (LGPD Art. 18)
☐ Implementar "Excluir minha conta" (manual, antes do prazo)
☐ Implementar opt-out de emails marketing
☐ Criar dashboard LGPD para admin (quantos dados, retenção)
```

---

## ⚖️ FUNDAMENTO LEGAL (LGPD)

### Artigos aplicáveis:

**Art. 6º, III** - Necessidade  
> Dados devem ser limitados ao mínimo necessário para a finalidade

**Art. 15** - Transparência  
> Titular tem direito de saber duração do armazenamento

**Art. 16** - Exclusão  
> Titular pode solicitar exclusão quando dados desnecessários

**Art. 18** - Portabilidade  
> Titular pode solicitar cópia dos dados em formato portável

---

## 🎯 CONCLUSÃO

Você identificou corretamente que **o sistema atual NÃO está em conformidade com LGPD**.

**Situação atual**:
- ❌ Trial user cadastra dados pessoais reais
- ❌ Trial expira, dados ficam no banco PARA SEMPRE
- ❌ Nenhum aviso de exclusão
- ❌ Nenhuma exclusão automática
- ❌ Risco legal de multa ANPD

**Após implementação das soluções**:
- ✅ Trial user é avisado que dados serão excluídos
- ✅ Email de lembrete 3 dias antes de expirar
- ✅ Email após expiração: "30 dias para assinar"
- ✅ Email final: "2 dias para exclusão"
- ✅ Job automático deleta tudo após 37 dias
- ✅ Sistema em conformidade com LGPD

---

**Prioridade**: 🔴 CRÍTICA  
**Impacto Legal**: ALTO  
**Tempo de Implementação**: 2 semanas  
**Custo de NÃO fazer**: Multa ANPD (até R$ 50 milhões) + Processo judicial

