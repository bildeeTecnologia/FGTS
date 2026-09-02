# ✅ CHECKLIST PÓS-IMPLEMENTAÇÃO

## 🎯 O que já está pronto

### Landing Page
- ✅ Hero section remodelada com badge "7 DIAS GRÁTIS"
- ✅ Card lateral destacando trial (sem demo)
- ✅ Seção "Como funciona o teste grátis?"
- ✅ Planos com badges de trial
- ✅ CTA final otimizada
- ✅ Footer com links de privacidade
- ✅ 4 menções à conformidade LGPD
- ✅ Trust elements adicionados
- ✅ Responsividade mantida

### Sistema Trial
- ✅ Modelo BillingCustomer com campos trial
- ✅ TrialWarningMiddleware (redireciona expirados)
- ✅ Banner com avisos LGPD (vermelho/amarelo)
- ✅ Comando `cleanup_expired_trials` (deleta dados)
- ✅ Comando `send_trial_emails` (avisos automáticos)
- ✅ TrialEmailService com 4 templates
- ✅ Política de 37 dias (7 trial + 30 retenção)

### Documentação
- ✅ LGPD_COMPLIANCE_TRIAL.md
- ✅ LGPD_IMPLEMENTADO.md
- ✅ TRANSICAO_DEMO_PARA_TRIAL.md
- ✅ LANDING_PAGE_ANTES_DEPOIS.md
- ✅ RESUMO_IMPLEMENTACAO_LANDING.md
- ✅ Este checklist

---

## 🔴 URGENTE - Fazer Antes do Deploy

### 1. Configurar Email (SMTP)

**Localização:** `fgtsweb/settings.py`

```python
# Adicionar no final do arquivo
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # ou seu provedor
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'seu-email@dominio.com'
EMAIL_HOST_PASSWORD = 'sua-senha-app'  # usar senha de app, não senha normal
DEFAULT_FROM_EMAIL = 'FGTS Web <noreply@fgtsweb.com>'
```

**⚠️ Testar antes do deploy:**
```bash
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Teste', 'Corpo do email', 'noreply@fgtsweb.com', ['seu-email@teste.com'])
```

---

### 2. Agendar Comandos (Task Scheduler/Cron)

#### Windows (Task Scheduler)

**Comando 1: Limpar trials expirados**
- Nome: "FGTS - Limpar Trials Expirados"
- Frequência: Diária, 02:00 AM
- Comando:
  ```cmd
  cd C:\Users\...\FGTS-PYTHON
  python manage.py cleanup_expired_trials --force
  ```

**Comando 2: Enviar emails de trial**
- Nome: "FGTS - Enviar Emails Trial"
- Frequência: Diária, 08:00 AM
- Comando:
  ```cmd
  cd C:\Users\...\FGTS-PYTHON
  python manage.py send_trial_emails
  ```

**Instruções detalhadas:** Ver `LGPD_IMPLEMENTADO.md`

---

### 3. Criar Páginas Legais (Links no Footer)

#### 3.1 Política de Privacidade

**Arquivo:** `empresas/templates/legal/privacy_policy.html`

**Conteúdo mínimo obrigatório:**
- Dados coletados (nome, email, CPF, PIS de funcionários)
- Finalidade (gestão de FGTS)
- Base legal (consentimento + legítimo interesse)
- Compartilhamento (não compartilhamos)
- Retenção (7 dias trial + 30 dias ou até exclusão)
- Direitos do usuário (acesso, retificação, exclusão)
- Contato do DPO/responsável

**Template básico:**
```django
{% extends 'base.html' %}
{% block title %}Política de Privacidade - FGTS Web{% endblock %}
{% block content %}
<div class="container py-5">
  <h1>Política de Privacidade</h1>
  <p class="text-muted">Última atualização: 31/12/2024</p>
  
  <h2>1. Dados Coletados</h2>
  <p>...</p>
  
  <h2>2. Finalidade</h2>
  <p>...</p>
  
  <!-- Continuar com todos os pontos LGPD -->
</div>
{% endblock %}
```

**URL:** Adicionar em `fgtsweb/urls.py`
```python
path('privacidade/', TemplateView.as_view(template_name='legal/privacy_policy.html'), name='privacy-policy'),
```

---

#### 3.2 Termos de Uso

**Arquivo:** `empresas/templates/legal/terms_of_service.html`

**Conteúdo mínimo:**
- Aceitação dos termos
- Descrição do serviço
- Período de trial (7 dias)
- Planos e pagamento
- Propriedade intelectual
- Limitação de responsabilidade
- Cancelamento e reembolso
- Modificações nos termos

**URL:** Adicionar em `fgtsweb/urls.py`
```python
path('termos/', TemplateView.as_view(template_name='legal/terms_of_service.html'), name='terms-of-service'),
```

---

### 4. Atualizar Links no Footer

**Arquivo:** `empresas/templates/landing.html` (linha ~360)

```html
<!-- FOOTER -->
<section class="py-4" style="background:#fff">
  <div class="container d-flex flex-column flex-md-row align-items-center justify-content-between">
    <div class="text-muted small">
      FGTS Web © 2025 • Gestão profissional de FGTS em atraso
    </div>
    <div class="small">
      <a href="{% url 'privacy-policy' %}" class="text-decoration-none me-3">Política de Privacidade</a>
      <a href="{% url 'terms-of-service' %}" class="text-decoration-none me-3">Termos de Uso</a>
      <a href="{% url 'register' %}" class="text-decoration-none fw-bold" style="color: #27ae60;">
        <i class="bi bi-gift-fill me-1"></i> Teste Grátis
      </a>
    </div>
  </div>
</section>
```

---

## 🟡 IMPORTANTE - Fazer em Breve

### 5. Adicionar Checkbox LGPD no Registro

**Arquivo:** `usuarios/templates/usuarios/register.html`

**Adicionar antes do botão submit:**
```html
<div class="form-check mb-3">
  <input class="form-check-input" type="checkbox" name="aceito_termos" id="aceitoTermos" required>
  <label class="form-check-label small" for="aceitoTermos">
    Li e aceito a <a href="{% url 'privacy-policy' %}" target="_blank">Política de Privacidade</a> 
    e os <a href="{% url 'terms-of-service' %}" target="_blank">Termos de Uso</a>. 
    Entendo que durante o trial meus dados serão armazenados e, caso não assine um plano, 
    serão excluídos automaticamente após 37 dias conforme a LGPD.
  </label>
</div>
```

**Validar no backend:** `usuarios/views.py`
```python
def register(request):
    if request.method == 'POST':
        aceito_termos = request.POST.get('aceito_termos')
        if not aceito_termos:
            messages.error(request, 'Você precisa aceitar os termos para continuar.')
            return render(request, 'usuarios/register.html')
        # ... resto do código
```

---

### 6. Testar Fluxo Completo

**Cenário de teste:**

1. **Registro**
   - [ ] Acesse `/usuario/register/`
   - [ ] Preencha formulário (use email real)
   - [ ] Verifique checkbox LGPD visível
   - [ ] Clique "Criar Conta"
   - [ ] Verifique se foi criado BillingCustomer com `trial_active=True`

2. **Uso do Trial**
   - [ ] Crie uma empresa
   - [ ] Adicione funcionários (máximo 10 no trial)
   - [ ] Crie lançamentos
   - [ ] Verifique banner amarelo (se >3 dias restantes)

3. **Avisos de Expiração**
   - [ ] Simule trial expirando em 2 dias (alterar `trial_expires` no admin)
   - [ ] Recarregue página, verifique banner vermelho
   - [ ] Clique em link do banner, veja se redireciona para checkout

4. **Expiração**
   - [ ] Simule trial expirado (alterar `trial_expires` para ontem)
   - [ ] Tente acessar dashboard
   - [ ] Verifique se middleware redireciona para checkout

5. **Emails (se SMTP configurado)**
   - [ ] Simule trial expirando em 3 dias
   - [ ] Execute `python manage.py send_trial_emails`
   - [ ] Verifique se email chegou
   - [ ] Repita para 1 dia, expirado, 2 dias para deletar

6. **Cleanup**
   - [ ] Simule trial expirado há 31 dias
   - [ ] Execute `python manage.py cleanup_expired_trials --dry-run`
   - [ ] Verifique output (deve mostrar 1 trial para limpar)
   - [ ] Execute sem `--dry-run --force`
   - [ ] Verifique se dados foram excluídos

---

## 🟢 OPCIONAL - Melhorias Futuras

### 7. Analytics e Tracking

**Google Analytics:**
```html
<!-- Adicionar em base.html antes de </head> -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

**Eventos para trackear:**
- Clique em "Começar Teste Grátis"
- Registro concluído
- Primeira empresa criada
- Trial convertido em pago
- Trial expirado sem conversão

---

### 8. Otimizações de Conversão

**A/B Testing:**
- [ ] Testar "7 DIAS GRÁTIS" vs "EXPERIMENTE GRÁTIS"
- [ ] Testar botão verde vs azul
- [ ] Testar "Começar Teste Grátis" vs "Criar Conta Grátis"

**Prova Social:**
- [ ] Adicionar contador de empresas cadastradas
- [ ] Adicionar depoimentos de clientes
- [ ] Adicionar logos de empresas que usam

**FAQ:**
- [ ] Seção com perguntas frequentes sobre trial
- [ ] "O que acontece após os 7 dias?"
- [ ] "Preciso de cartão de crédito?"
- [ ] "Meus dados são seguros?"

---

### 9. Recursos Adicionais

**Email de Boas-Vindas:**
- [ ] Criar template de boas-vindas ao trial
- [ ] Incluir guia rápido de uso
- [ ] Links para tutoriais

**Dashboard de Métricas:**
- [ ] Criar página admin para ver trials ativos
- [ ] Gráfico de conversão trial → pago
- [ ] Taxa de ativação (primeira empresa criada)

**Notificações In-App:**
- [ ] Toast notification ao criar conta
- [ ] Progresso do trial no dashboard
- [ ] Checklist de onboarding

---

## 📊 Monitoramento (Após Deploy)

### Métricas Diárias
- [ ] Visitantes únicos
- [ ] Taxa de registro (conversão landing → conta)
- [ ] Trials ativos
- [ ] Taxa de ativação (conta → primeira empresa)

### Métricas Semanais
- [ ] Taxa de conversão (trial → pago)
- [ ] Trials expirados sem conversão
- [ ] Receita gerada por trials convertidos
- [ ] Feedback dos usuários (se tiver formulário)

### Métricas Mensais
- [ ] MRR (Monthly Recurring Revenue)
- [ ] CAC (Customer Acquisition Cost)
- [ ] LTV (Lifetime Value)
- [ ] Churn rate

---

## 🚨 Troubleshooting

### Problema: Emails não estão sendo enviados
**Solução:**
1. Verificar configuração SMTP em `settings.py`
2. Testar com `python manage.py shell` e `send_mail()`
3. Verificar se Gmail permite "app de terceiros" (se usando Gmail)
4. Gerar senha de app específica no Gmail

---

### Problema: Comando cleanup não está deletando
**Solução:**
1. Verificar se há trials com `trial_expires` < hoje - 30 dias
2. Executar com `--dry-run` para ver o que seria deletado
3. Verificar logs no terminal
4. Verificar permissões do banco de dados

---

### Problema: Banner não aparece
**Solução:**
1. Verificar se middleware está ativo em `settings.py`
2. Verificar se `request.trial_customer` existe no contexto
3. Verificar se `trial_expires` está configurado no BillingCustomer
4. Limpar cache do navegador (Ctrl+F5)

---

## 📞 Recursos de Suporte

### Documentação Local
- `LGPD_COMPLIANCE_TRIAL.md` - Análise LGPD completa
- `LGPD_IMPLEMENTADO.md` - Como usar os comandos
- `TRANSICAO_DEMO_PARA_TRIAL.md` - Por que mudamos
- `LANDING_PAGE_ANTES_DEPOIS.md` - Comparação visual
- `RESUMO_IMPLEMENTACAO_LANDING.md` - Visão geral completa

### Comandos Úteis
```bash
# Verificar trials ativos
python manage.py shell
>>> from billing.models import BillingCustomer
>>> BillingCustomer.objects.filter(trial_active=True).count()

# Verificar trials expirados
>>> from datetime import date
>>> BillingCustomer.objects.filter(trial_expires__lt=date.today()).count()

# Testar comando de limpeza (dry-run)
python manage.py cleanup_expired_trials --dry-run

# Testar comando de emails (dry-run)
python manage.py send_trial_emails --dry-run

# Ver ajuda de um comando
python manage.py cleanup_expired_trials --help
```

---

## ✅ Status Geral

### Implementação: 90% ✅

| Componente | Status | Prioridade |
|------------|--------|------------|
| Landing page | ✅ 100% | - |
| Sistema trial | ✅ 100% | - |
| Banner LGPD | ✅ 100% | - |
| Comandos de cleanup | ✅ 100% | - |
| Comandos de email | ✅ 100% | - |
| Documentação | ✅ 100% | - |
| **Configuração SMTP** | ⏳ 0% | 🔴 URGENTE |
| **Agendamento comandos** | ⏳ 0% | 🔴 URGENTE |
| **Política Privacidade** | ⏳ 0% | 🔴 URGENTE |
| **Termos de Uso** | ⏳ 0% | 🔴 URGENTE |
| Checkbox LGPD registro | ⏳ 0% | 🟡 IMPORTANTE |
| Teste completo fluxo | ⏳ 0% | 🟡 IMPORTANTE |

---

## 🎯 Priorização para Próximos Dias

### Dia 1 (Hoje) - URGENTE
1. ✅ Landing page remodelada (FEITO)
2. ⏳ Configurar SMTP (30 min)
3. ⏳ Criar Política de Privacidade básica (1 hora)
4. ⏳ Criar Termos de Uso básicos (1 hora)

### Dia 2 - IMPORTANTE
5. ⏳ Adicionar checkbox LGPD no registro (30 min)
6. ⏳ Testar fluxo completo (1 hora)
7. ⏳ Agendar comandos no Task Scheduler (30 min)

### Dia 3 - OPCIONAL
8. ⏳ Configurar Google Analytics (30 min)
9. ⏳ Criar FAQ sobre trial (1 hora)
10. ⏳ Email de boas-vindas (1 hora)

---

## 🚀 Deploy Checklist

Antes de fazer deploy em produção:

- [ ] SMTP configurado e testado
- [ ] Política de Privacidade publicada
- [ ] Termos de Uso publicados
- [ ] Checkbox LGPD no registro
- [ ] Comandos agendados (Task Scheduler/cron)
- [ ] Fluxo completo testado localmente
- [ ] Backup do banco de dados
- [ ] Variáveis de ambiente configuradas (se usar)
- [ ] SSL/HTTPS ativo no domínio

---

**Última atualização:** 31/12/2024  
**Próxima revisão:** Após configurar SMTP e criar páginas legais

---

## 💡 Dica Final

**NÃO FAÇA DEPLOY SEM:**
1. Configurar SMTP (emails não vão funcionar)
2. Criar Política de Privacidade (obrigatório por lei)
3. Criar Termos de Uso (proteção legal)
4. Agendar comandos de cleanup (LGPD obrigatório)

Essas 4 coisas são **OBRIGATÓRIAS** antes do deploy em produção! 🚨
