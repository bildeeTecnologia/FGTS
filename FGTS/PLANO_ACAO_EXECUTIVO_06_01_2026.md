# 🚀 PLANO DE AÇÃO EXECUTIVO - PRÓXIMAS 14 DIAS

**Data:** 06 de Janeiro de 2026  
**Objetivo:** Atingir 100% de funcionalidades do sistema legado + 5 features novas  
**Status Atual:** 76% (19 de 25 funcionalidades)  
**Meta:** 13 de Janeiro de 2026  

---

## 📊 RESUMO EXECUTIVO

```
HOJE (06/01/2026):      76% COMPLETO (19/25 funcionalidades)
DIA 13 (13/01/2026):    100% COMPLETO (25/25 funcionalidades)

TEMPO TOTAL:            7-8 dias úteis
COMPLEXIDADE:           MÉDIA (85% código já existe)
BLOQUEADOR:             NENHUM (tudo pronto para implementar)

GANHO:
├─ ✅ Compliance obrigatória SEFIP
├─ ✅ Migração fácil de clientes antigos
├─ ✅ Conferência de qualidade dos dados
└─ ✅ Paridade 100% com sistema legado
```

---

## 🎯 ATIVIDADES CRÍTICAS (6-8 dias)

### Semana 1: SEGUNDA-FEIRA (06/01) até QUINTA (09/01)

#### 🔴 ATIVIDADE 1: SEFIP Export - Registros 40/50/60
**Prazo:** 06-07 de Janeiro (1-2 dias)  
**Complexidade:** ⚡⚡ Média  
**Status Atual:** 85% (registros 00, 10, 30, 90 prontos)  
**Bloqueador:** NÃO (registro 30 reutilizável)  
**Prioridade:** 🔴 CRÍTICA (compliance obrigatória)  

**O que fazer:**

1. **Estudar formato SEFIP oficial** (30 min)
   ```
   Registros faltando:
   ├─ 40: Remunerações variáveis (horas extras, adicionais)
   ├─ 50: Descontos (INSS, IR, faltas)
   └─ 60: Contribuições sindicais (desconto sindical)
   
   Referência: Documentação Caixa Econômica Federal
   ```

2. **Implementar Registro 40** (2h)
   ```python
   # lancamentos/services/sefip_export.py
   
   def gerar_registro_40(self, lancamento):
       """
       Tipo 40: Remunerações variáveis
       Campos: tipo(2) + CNPJ(14) + PIS(11) + ... + valor(11)
       """
       # Buscar valores extras (horas extras, adicionais)
       # Formatar com posições fixas
       # Validar comprimento (100 chars)
       return linha_40
   ```

3. **Implementar Registro 50** (2h)
   ```python
   def gerar_registro_50(self, lancamento):
       """
       Tipo 50: Descontos
       Campos: tipo(2) + CNPJ(14) + PIS(11) + ... + desconto(11)
       """
       # Buscar descontos aplicados
       # INSS, IR, faltas
       # Formatar igual ao 40
       return linha_50
   ```

4. **Implementar Registro 60** (2h)
   ```python
   def gerar_registro_60(self, lancamento):
       """
       Tipo 60: Contribuições sindicais
       Campos: tipo(2) + CNPJ(14) + PIS(11) + ... + sindical(11)
       """
       # Se empresa tem convênio sindical
       # Buscar desconto sindical
       # Formatar igual aos anteriores
       return linha_60
   ```

5. **Testes com dados reais** (2h)
   ```python
   # lancamentos/tests/test_sefip.py
   
   def test_sefip_completo():
       """Gera arquivo SEFIP com todos registros"""
       resultado = service.gerar_sefip(empresa, competencia)
       
       # Validar linhas
       assert "00" in resultado  # Cabeçalho
       assert "10" in resultado  # Empresa
       assert "30" in resultado  # Funcionário
       assert "40" in resultado  # Variáveis (novo)
       assert "50" in resultado  # Descontos (novo)
       assert "60" in resultado  # Sindical (novo)
       assert "90" in resultado  # Totaliza
   ```

6. **Integração na view** (1h)
   ```python
   # lancamentos/views.py
   
   class SefipExportView(LoginRequiredMixin, View):
       def post(self, request):
           empresa_id = request.POST.get('empresa')
           competencia = request.POST.get('competencia')
           
           try:
               arquivo = SefipExportService().gerar_sefip(
                   empresa_id=empresa_id,
                   competencia=competencia
               )
               return FileResponse(arquivo, as_attachment=True)
           except Exception as e:
               return JsonResponse({'erro': str(e)}, status=400)
   ```

**Entregáveis:**
- ✅ Código registros 40/50/60
- ✅ Testes unitários
- ✅ Integração na view
- ✅ Template HTML form
- ✅ Validação de dados

**Aceitação:**
- Gera arquivo válido .RE
- Importa sem erros na Caixa
- Testes passam 100%

---

#### 🔴 ATIVIDADE 2: Legacy Importer - Web Interface
**Prazo:** 07-08 de Janeiro (2-3 dias)  
**Complexidade:** ⚡⚡⚡ Alta  
**Status Atual:** 100% código, falta web  
**Bloqueador:** NÃO (serviço já existe)  
**Prioridade:** 🔴 CRÍTICA (onboarding clientes)  

**O que fazer:**

1. **Criar formulário de upload** (2h)
   ```python
   # lancamentos/forms.py
   
   class LegacyImportForm(forms.Form):
       arquivo = forms.FileField(
           label='Arquivo .TXT legado',
           help_text='Formato: ID_EMPRESA_ANO.txt'
       )
       empresa = forms.ModelChoiceField(queryset=Empresa.objects.all())
       validar_apenas = forms.BooleanField(
           label='Apenas validar (preview)',
           required=False,
           initial=True
       )
   ```

2. **Criar view com preview** (3h)
   ```python
   # lancamentos/views.py
   
   class LegacyImportView(LoginRequiredMixin, FormView):
       form_class = LegacyImportForm
       template_name = 'lancamentos/legacy_import.html'
       
       def form_valid(self, form):
           arquivo = form.cleaned_data['arquivo']
           empresa = form.cleaned_data['empresa']
           
           # Parse e validação
           service = LegacyImportService()
           dados = service.parse_txt_file(arquivo)
           erros = service.validate_data(dados)
           
           if erros:
               # Mostrar erros no template
               return render(self.request, 'legacy_import_erros.html', {
                   'erros': erros,
                   'total': len(dados),
               })
           
           # Preview dos 10 primeiros
           preview = dados[:10]
           return render(self.request, 'legacy_import_preview.html', {
               'preview': preview,
               'total': len(dados),
               'arquivo': arquivo.name,
           })
   ```

3. **Confirmar importação** (2h)
   ```python
   class LegacyImportConfirmView(LoginRequiredMixin, View):
       def post(self, request):
           # Importar de verdade
           service = LegacyImportService()
           resultado = service.import_to_db(
               arquivo=request.session['temp_file'],
               empresa_id=request.POST['empresa']
           )
           
           return JsonResponse({
               'criados': resultado['criados'],
               'erros': resultado['erros'],
               'avisos': resultado['avisos'],
           })
   ```

4. **Templates HTML** (2h)
   ```html
   <!-- lancamentos/templates/legacy_import.html -->
   <form method="post" enctype="multipart/form-data">
       {% csrf_token %}
       {{ form.as_p }}
       <button type="submit">Validar Arquivo</button>
   </form>
   
   <!-- legacy_import_preview.html -->
   <table class="table">
       <thead>
           <tr>
               <th>CPF</th><th>Nome</th><th>Competência</th><th>Base</th>
           </tr>
       </thead>
       <tbody>
           {% for item in preview %}
               <tr>
                   <td>{{ item.cpf }}</td>
                   <td>{{ item.nome }}</td>
                   <td>{{ item.competencia }}</td>
                   <td>{{ item.base }}</td>
               </tr>
           {% endfor %}
       </tbody>
   </table>
   <p>Total de registros: {{ total }}</p>
   <form method="post" action="{% url 'legacy_import_confirm' %}">
       {% csrf_token %}
       <button type="submit">IMPORTAR {{ total }} REGISTROS</button>
   </form>
   ```

5. **Testar com arquivo real** (2h)
   ```bash
   # Criar arquivo teste
   $ cat > test_legacy.txt << 'EOF'
   COMP: 01/01/2025
   REM SEM 13
   CPF: 12345678901
   NOME: JOÃO SILVA
   BASE: 3500.00
   ...
   EOF
   
   # Testar upload
   $ python manage.py test lancamentos.tests.test_legacy_import
   ```

**Entregáveis:**
- ✅ Form upload + validação
- ✅ Preview com 10 primeiros
- ✅ Confirmação importação
- ✅ Testes E2E
- ✅ Documentação uso

**Aceitação:**
- Upload aceita arquivo .txt
- Mostra preview corretamente
- Importação cria lançamentos
- Log de erros completo

---

#### 🔴 ATIVIDADE 3: Conferência de Lançamentos
**Prazo:** 09 de Janeiro (1 dia)  
**Complexidade:** ⚡ Baixa  
**Status Atual:** 100% código (models_conferencia.py)  
**Bloqueador:** NÃO (models prontos)  
**Prioridade:** 🟡 ALTA (qualidade dados)  

**O que fazer:**

1. **Migration Django** (30 min)
   ```python
   # lancamentos/migrations/0007_add_conferencia.py
   
   class Migration(migrations.Migration):
       dependencies = [
           ('lancamentos', '0006_lancamento_parcela_13'),
       ]
       
       operations = [
           # Adicionar campo conferido
           migrations.AddField(
               model_name='lancamento',
               name='conferido',
               field=models.BooleanField(default=False),
           ),
           migrations.AddField(
               model_name='lancamento',
               name='conferido_em',
               field=models.DateTimeField(null=True, blank=True),
           ),
           migrations.AddField(
               model_name='lancamento',
               name='conferido_por',
               field=models.ForeignKey(
                   null=True,
                   blank=True,
                   to=settings.AUTH_USER_MODEL,
                   on_delete=models.SET_NULL,
                   related_name='lancamentos_conferidos'
               ),
           ),
       ]
   ```

2. **Registrar no Admin Django** (30 min)
   ```python
   # lancamentos/admin.py
   
   class LancamentoAdmin(admin.ModelAdmin):
       list_filter = ['empresa', 'conferido', 'competencia']
       list_display = ['empresa', 'funcionario', 'competencia', 'conferido']
       actions = ['marcar_conferido', 'marcar_nao_conferido']
       
       def marcar_conferido(self, request, queryset):
           for lancamento in queryset:
               lancamento.conferido = True
               lancamento.conferido_em = timezone.now()
               lancamento.conferido_por = request.user
               lancamento.save()
           self.message_user(request, f'{len(queryset)} marcados como conferido')
       
       def marcar_nao_conferido(self, request, queryset):
           queryset.update(conferido=False)
   ```

3. **Views de conferência** (2h)
   ```python
   # lancamentos/views.py
   
   class LancamentoConferenciaListView(LoginRequiredMixin, ListView):
       model = Lancamento
       template_name = 'lancamentos/conferencia_list.html'
       paginate_by = 20
       
       def get_queryset(self):
           # Mostrar só não conferidos
           return Lancamento.objects.filter(
               empresa__usuario=self.request.user,
               conferido=False
           ).order_by('competencia', 'funcionario')
   
   class LancamentoConferenciaDetailView(LoginRequiredMixin, DetailView):
       model = Lancamento
       template_name = 'lancamentos/conferencia_detail.html'
       
       def post(self, request, pk):
           lancamento = self.get_object()
           lancamento.conferido = True
           lancamento.conferido_em = timezone.now()
           lancamento.conferido_por = request.user
           lancamento.save()
           
           return JsonResponse({'ok': True})
   ```

4. **Templates** (2h)
   ```html
   <!-- lancamentos/templates/lancamentos/conferencia_list.html -->
   <div class="alert alert-warning">
       ⚠️ {{ object_list|length }} lançamentos pendentes de conferência
   </div>
   
   <table class="table">
       <thead>
           <tr>
               <th>Competência</th>
               <th>Funcionário</th>
               <th>Base FGTS</th>
               <th>Parcela 13º</th>
               <th>Status</th>
           </tr>
       </thead>
       <tbody>
           {% for lancamento in object_list %}
               <tr>
                   <td>{{ lancamento.competencia|date:"m/Y" }}</td>
                   <td>{{ lancamento.funcionario.nome }}</td>
                   <td>R$ {{ lancamento.base_fgts|floatformat:2 }}</td>
                   <td>{{ lancamento.get_parcela_13_display }}</td>
                   <td>
                       <a href="{% url 'lancamento_conferencia_detail' lancamento.pk %}">
                           Conferir
                       </a>
                   </td>
               </tr>
           {% endfor %}
       </tbody>
   </table>
   ```

5. **Validação na consolidação** (1h)
   ```python
   # lancamentos/services/relatorio.py
   
   def pode_consolidar(empresa, competencia):
       """Verifica se pode consolidar sem erros"""
       nao_conferidos = Lancamento.objects.filter(
           empresa=empresa,
           competencia__year=competencia.year,
           competencia__month=competencia.month,
           conferido=False
       ).count()
       
       if nao_conferidos > 0:
           raise ValueError(
               f'{nao_conferidos} lançamentos não conferidos. '
               f'Confira antes de consolidar.'
           )
       return True
   ```

**Entregáveis:**
- ✅ Migration + campo modelo
- ✅ Admin customizado
- ✅ Views conferência
- ✅ Templates
- ✅ Validação consolidação

**Aceitação:**
- Campo conferido aparece no modelo
- Admin permite marcar como conferido
- View lista não conferidos
- Impede consolidação sem conferência

---

## 🟡 ATIVIDADES IMPORTANTES (2-3 dias)

### Semana 2: SEXTA-FEIRA (10/01) até SEGUNDA (13/01)

#### Atividade 4: Relatórios Adicionais
**Prazo:** 10-11 de Janeiro (2-3 dias)  
**Opção A: Só essencial** (1 dia)  
**Opção B: Completo com gráficos** (3 dias)  

**Opção A - Essencial (recomendado):**
```python
# lancamentos/views.py

class RelatorioPorFuncionarioView(LoginRequiredMixin, DetailView):
    model = Funcionario
    template_name = 'relatorio_funcionario.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Todos os lançamentos do funcionário
        lançamentos = Lancamento.objects.filter(
            funcionario=self.object
        ).order_by('competencia')
        
        context['lancamentos'] = lançamentos
        context['total_fgts'] = sum(l.valor_fgts for l in lançamentos)
        context['total_base'] = sum(l.base_fgts for l in lançamentos)
        
        return context
```

**Opção B - Com gráficos (Chart.js):**
```html
<!-- Adiciona Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<canvas id="graficoFuncionario"></canvas>

<script>
const ctx = document.getElementById('graficoFuncionario').getContext('2d');
new Chart(ctx, {
    type: 'line',
    data: {
        labels: {{ competencias|safe }},
        datasets: [{
            label: 'Base FGTS',
            data: {{ bases|safe }},
        }, {
            label: 'Valor FGTS',
            data: {{ fgts_valores|safe }},
        }]
    }
});
</script>
```

---

## 🟢 ATIVIDADES FINAL (1-2 dias)

### Testes E2E + Deploy
**Prazo:** 12-13 de Janeiro (1-2 dias)  

```bash
# Rodar testes
python manage.py test lancamentos --verbosity=2

# Checklist antes do deploy
[ ] SEFIP valida com dados reais
[ ] Legacy importer funciona
[ ] Conferência bloqueia consolidação
[ ] Relatórios carregam rápido
[ ] Backup automático funcionando
[ ] Logs sendo registrados

# Deploy
python manage.py collectstatic
python manage.py migrate
docker build -t fgts:latest .
docker push ...
```

---

## 📋 CHECKLIST DIÁRIO

### SEGUNDA 06/01 (HOJE)
- [ ] Ler registros 40/50/60 documentação SEFIP
- [ ] Começar implementação registro 40
- [ ] Criar form legacy import

### TERÇA 07/01
- [ ] Finalizar registros 40/50/60
- [ ] Testar SEFIP com dados reais
- [ ] Continuar legacy importer

### QUARTA 08/01
- [ ] Finalizar legacy importer
- [ ] Testes legacy import
- [ ] Começar conferência

### QUINTA 09/01
- [ ] Finalizar conferência
- [ ] Testes integração
- [ ] Code review de tudo

### SEXTA 10/01
- [ ] Deploy staging
- [ ] Testes E2E
- [ ] Ajustes encontrados

### SEGUNDA 13/01
- [ ] Última validação
- [ ] Deploy produção
- [ ] 🏁 100% COMPLETO

---

## 📞 SUPORTE DURANTE IMPLEMENTAÇÃO

### Em caso de dúvida
1. **Documentação:** Leia `ANALISE_COMPLETA_SISTEMA_06_01_2026.md`
2. **Código referência:** `lancamentos/services/sefip_export.py` (85% pronto)
3. **Testes:** Copie padrão de `lancamentos/tests/test_calculo.py`
4. **Modelos:** Use `models_conferencia.py` como referência

---

## 🎯 SUCESSO FINAL

Quando todas as atividades forem completas:

✅ **Exportar SEFIP** → Clientes podem enviar para Caixa Econômica  
✅ **Importar legado** → Clientes migram facilmente do VB6  
✅ **Conferir dados** → Qualidade garantida antes de consolidar  
✅ **100% paridade** → Nenhuma funcionalidade faltando  

**Resultado:** Sistema pronto para vender e onboarding de clientes reais! 🚀

---

**Preparado em:** 06 de Janeiro de 2026  
**Próxima atualização:** Amanhã (07/01) com progresso do dia  
**Contato:** Ver ANALISE_COMPLETA_SISTEMA_06_01_2026.md para detalhes técnicos
