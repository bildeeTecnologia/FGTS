# 🔗 Guia de Integração - Legacy Import no Menu

## Como Integrar a Atividade 2 ao Menu Principal

### 1. Localize o Template Base (Menu)

Você precisa encontrar e editar o template que contém o menu principal. Geralmente está em:
- `templates/base.html`
- `templates/navbar.html`
- `templates/menu.html`
- ou em `templates/includes/sidebar.html`

### 2. Adicione o Link de Legacy Import

#### Opção A: Menu Dropdown (Mais Profissional)

```html
<!-- Em seu template de menu/navbar -->
<li class="nav-item dropdown">
    <a class="nav-link dropdown-toggle" href="#" id="importarDropdown" role="button" data-bs-toggle="dropdown">
        <i class="bi bi-upload me-2"></i>Importar
    </a>
    <ul class="dropdown-menu" aria-labelledby="importarDropdown">
        <li>
            <a class="dropdown-item" href="{% url 'legacy-import' %}">
                <i class="bi bi-upload me-2"></i>Dados Legados (VB6)
            </a>
        </li>
        <li><hr class="dropdown-divider"></li>
        <li>
            <small class="text-muted ps-3">Sistema Legado Migrado</small>
        </li>
    </ul>
</li>
```

#### Opção B: Menu Simples (Direto)

```html
<!-- Em seu template de menu/navbar -->
<li class="nav-item">
    <a class="nav-link" href="{% url 'legacy-import' %}">
        <i class="bi bi-upload me-2"></i>Importar Dados Legados
    </a>
</li>
```

#### Opção C: Sidebar com Card (Dashboard)

```html
<!-- Em dashboard ou homepage -->
<div class="col-md-6 col-lg-4 mb-4">
    <a href="{% url 'legacy-import' %}" class="text-decoration-none">
        <div class="card border-0 shadow-sm h-100 hover-card">
            <div class="card-body d-flex flex-column align-items-center text-center">
                <div class="display-6 text-success mb-3">
                    <i class="bi bi-upload"></i>
                </div>
                <h5 class="card-title">Importar Dados Legados</h5>
                <p class="card-text text-muted small">
                    Importe empresas, funcionários e lançamentos do sistema anterior (VB6)
                </p>
                <small class="text-primary fw-bold">Acessar →</small>
            </div>
        </div>
    </a>
</div>
```

### 3. Verifique o Arquivo URLs Principal

Certifique-se de que `urls_novos_recursos.py` está incluído no `urls.py` principal:

```python
# projeto/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # ... outras URLs ...
    
    # Incluir as URLs de novos recursos
    path('lancamentos/', include('lancamentos.urls_novos_recursos')),
]
```

### 4. Teste a Integração

Após fazer as mudanças:

1. **Reinicie o servidor Django:**
   ```bash
   python manage.py runserver
   ```

2. **Acesse a URL diretamente:**
   ```
   http://localhost:8000/lancamentos/legacy-import/
   ```

3. **Verifique o menu:**
   - O link deve aparecer no menu
   - Clique e deve ir para a página de importação

### 5. Estilos Bootstrap (Se Necessário)

Se o hover no card não funcionar, adicione CSS customizado:

```css
/* Adicione a qualquer arquivo CSS do seu projeto */

.hover-card {
    transition: all 0.3s ease;
    cursor: pointer;
}

.hover-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 1rem 3rem rgba(0, 0, 0, 0.175) !important;
    background-color: #f8f9fa;
}
```

---

## 📱 Integração em Diferentes Layouts

### Bootstrap Navbar (Topo)

```html
<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <div class="container-fluid">
        <a class="navbar-brand" href="/">FGTS Web</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
            <ul class="navbar-nav ms-auto">
                <li class="nav-item">
                    <a class="nav-link" href="{% url 'lancamento-list' %}">Lançamentos</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="{% url 'legacy-import' %}">
                        <i class="bi bi-upload me-2"></i>Importar
                    </a>
                </li>
            </ul>
        </div>
    </div>
</nav>
```

### Sidebar (Lateral)

```html
<aside class="sidebar">
    <nav class="nav flex-column">
        <a class="nav-link" href="{% url 'lancamento-list' %}">
            <i class="bi bi-file-text me-2"></i>Lançamentos
        </a>
        <a class="nav-link" href="{% url 'legacy-import' %}">
            <i class="bi bi-upload me-2"></i>Importar Dados Legados
        </a>
    </nav>
</aside>
```

### Dashboard com Widgets

```html
<!-- Seção de Ações Rápidas -->
<div class="container mt-5">
    <h3 class="mb-4">Ações Rápidas</h3>
    <div class="row">
        <div class="col-md-3">
            <a href="{% url 'legacy-import' %}" class="btn btn-outline-primary w-100 py-3">
                <i class="bi bi-upload d-block fs-3 mb-2"></i>
                Importar Dados
            </a>
        </div>
        <div class="col-md-3">
            <a href="{% url 'lancamento-list' %}" class="btn btn-outline-secondary w-100 py-3">
                <i class="bi bi-list d-block fs-3 mb-2"></i>
                Ver Lançamentos
            </a>
        </div>
    </div>
</div>
```

---

## 🔐 Integração com Controle de Acesso

Se seu projeto usa permissões customizadas, adicione verificação:

```html
<!-- Template com verificação de permissão -->
{% if user.is_authenticated %}
    {% if user.has_perm 'lancamentos.import_legacy_data' %}
        <li class="nav-item">
            <a class="nav-link" href="{% url 'legacy-import' %}">
                <i class="bi bi-upload me-2"></i>Importar
            </a>
        </li>
    {% endif %}
{% endif %}
```

Ou usando `EmpresaScopeMixin`:

```html
<!-- Se usar empresa scope -->
{% if user_empresas %}
    <li class="nav-item">
        <a class="nav-link" href="{% url 'legacy-import' %}">
            <i class="bi bi-upload me-2"></i>Importar Dados
        </a>
    </li>
{% endif %}
```

---

## 📊 Integração com Dashboard

Adicionar card na página inicial/dashboard:

```html
<!-- template: dashboard.html ou home.html -->

<div class="container-fluid py-4">
    <div class="row mb-4">
        <div class="col-12">
            <h2>Dashboard</h2>
        </div>
    </div>
    
    <!-- Seção de Importações -->
    <div class="row">
        <div class="col-lg-6">
            <div class="card">
                <div class="card-header bg-success text-white">
                    <h5 class="mb-0">
                        <i class="bi bi-upload me-2"></i>Importar Dados Legados
                    </h5>
                </div>
                <div class="card-body">
                    <p class="text-muted">
                        Importe empresas, funcionários e lançamentos do sistema anterior (VB6).
                    </p>
                    <a href="{% url 'legacy-import' %}" class="btn btn-success">
                        <i class="bi bi-upload me-2"></i>Acessar Importação
                    </a>
                </div>
            </div>
        </div>
        
        <div class="col-lg-6">
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0">
                        <i class="bi bi-file-text me-2"></i>Lançamentos
                    </h5>
                </div>
                <div class="card-body">
                    <p class="text-muted">
                        Gerencie e visualize todos os lançamentos de FGTS.
                    </p>
                    <a href="{% url 'lancamento-list' %}" class="btn btn-primary">
                        <i class="bi bi-list me-2"></i>Ver Lançamentos
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>
```

---

## 🧪 Teste de Integração

Após integrar ao menu, execute este script para validar:

```bash
# Teste de URL
python manage.py shell

>>> from django.urls import reverse
>>> reverse('legacy-import')
'/lancamentos/legacy-import/'
>>> reverse('legacy-import-result')
'/lancamentos/legacy-import/resultado/'

# Teste de View
>>> from django.test import Client
>>> from django.contrib.auth.models import User
>>> client = Client()
>>> user = User.objects.first()
>>> client.login(username=user.username, password='password')
>>> response = client.get('/lancamentos/legacy-import/')
>>> response.status_code
200
```

---

## 📝 Checklist de Integração

```
[ ] URLs registradas em urls_novos_recursos.py
[ ] urls_novos_recursos.py incluído em urls.py principal
[ ] Link adicionado ao template de menu/navbar
[ ] Link testado manualmente no navegador
[ ] Acesso sem login redireciona para login
[ ] Acesso com login exibe a página corretamente
[ ] Formulário valida campos obrigatórios
[ ] Upload de arquivo funciona
[ ] Página de resultado exibe dados corretamente
[ ] Links no dashboard funcionam
[ ] Estilos estão consistentes com o resto do site
```

---

## 🐛 Troubleshooting

### Problema: "Página não encontrada (404)"
**Solução:** Verifique se `urls_novos_recursos.py` está incluído no `urls.py` principal:
```python
path('lancamentos/', include('lancamentos.urls_novos_recursos')),
```

### Problema: "Redireciona para login mesmo autenticado"
**Solução:** Adicione usuário às empresas permitidas no `billing_customer` ou use admin para ativar.

### Problema: "Formulário não valida arquivo"
**Solução:** Certifique-se de que arquivo é um CSV válido em encoding Latin1:
```bash
# Converter arquivo para Latin1 (Windows/Excel)
iconv -f UTF-8 -t ISO-8859-1 arquivo_utf8.csv > arquivo_latin1.csv
```

### Problema: "Upload falha com erro 413"
**Solução:** Aumente o tamanho máximo de upload no Django:
```python
# settings.py
FILE_UPLOAD_MAX_MEMORY_SIZE = 20971520  # 20MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 20971520  # 20MB
```

---

## 📞 Suporte de Integração

Se precisar de suporte:

1. **Verifique os arquivos criados:**
   - `lancamentos/forms.py` (LegacyImportForm)
   - `lancamentos/views.py` (LegacyImportView, LegacyImportResultView)
   - `lancamentos/urls_novos_recursos.py` (URLs registradas)

2. **Execute os testes:**
   ```bash
   python manage.py test lancamentos.tests_legacy_import
   ```

3. **Consulte a documentação:**
   - `ATIVIDADE_2_LEGACY_IMPORT_CONCLUSAO.md`
   - `ATIVIDADE_2_STATUS_VISUAL.md`

---

*Última atualização: 02 de Janeiro de 2026*
