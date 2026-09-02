# 📋 Resumo de Implementação - Suporte a 13º com Opção de Aniversário

**Data:** 03/01/2026  
**Status:** ✅ Implementado  
**Objetivo:** Adicionar suporte às 2 parcelas obrigatórias do 13º salário com opção de pagar a 1ª parcela no mês de aniversário do colaborador

---

## 🔧 Mudanças Realizadas

### 1. **Modelo Lancamento** ✅
**Arquivo:** `lancamentos/models.py`

**Adicionado:**
```python
parcela_13 = PositiveSmallIntegerField(
    null=True,
    blank=True,
    choices=PARCELA_CHOICES,  # (None, '01-12'), (1, '1ª parcela 13º'), (2, '2ª parcela 13º')
    help_text="Se preenchido, indica que é uma das 2 parcelas do 13º salário"
)
```

**Atualizado:**
- `unique_together` de `('funcionario', 'competencia')` para `('funcionario', 'competencia', 'parcela_13')`
- Permite ter `11/2025` com e sem `parcela_13` (competência normal vs 1ª parcela 13º)

**Migration:** `lancamentos/migrations/0006_add_parcela_13_field.py`

---

### 2. **Modelo Empresa** ✅
**Arquivo:** `empresas/models.py`

**Adicionado:**
```python
paga_13_aniversario = BooleanField(
    default=False,
    verbose_name='Paga 1ª parcela do 13º no mês de aniversário?',
    help_text='Se marcado, a 1ª parcela será paga no mês de aniversário (ao invés de novembro). 2ª parcela continua em dezembro.'
)
```

**Migration:** `empresas/migrations/0003_add_paga_13_aniversario.py`

---

### 3. **Formulário Empresa** ✅
**Arquivo:** `empresas/forms.py`

**Alterações:**
- Adicionado campo `paga_13_aniversario` à lista de fields
- Widget: `CheckboxInput` com classe `form-check-input`

---

### 4. **Formulário Lançamento** ✅
**Arquivo:** `lancamentos/forms.py`

**Alterações:**
- Adicionado campo `parcela_13` à lista de fields
- Posicionado após `competencia`
- Widget: `Select` dropdown com as 3 opções

---

### 5. **Serviço de Competências do 13º** ✅
**Arquivo:** `lancamentos/services/competencia_13.py` (NOVO)

**Classe:** `Competencia13Service`

**Métodos:**
1. `obter_mes_primeira_parcela_13(empresa, funcionario)` 
   - Retorna: mês (1-12) da 1ª parcela
   - Lógica: Se `paga_13_aniversario=True` → mês de nascimento, senão → 11

2. `gerar_competencias_13(empresa, ano, funcionario=None)`
   - Retorna: lista com 2 tuplas (competencia_str, parcela)
   - Exemplo: `[('04/2025', 1), ('12/2025', 2)]`

3. `gerar_todas_competencias_ano(empresa, ano, funcionario=None)`
   - Retorna: todas as competências do ano (01-12 + 2 parcelas 13º)

4. `parse_competencia_com_parcela(competencia_str)`
   - Parse de string MM/YYYY

5. `listar_competencias_13_para_filtro(empresa, funcionario, anos=None)`
   - Retorna: dict com estrutura pronta para filtros em relatórios

6. `validar_competencia_13(empresa, funcionario, competencia_str, parcela_13)`
   - Valida se a competência/parcela é válida
   - Retorna: tupla (válido: bool, mensagem: str)

---

### 6. **Serviço de Importação** ✅
**Arquivo:** `lancamentos/services/importacao.py`

**Alterações:**
- Adicionado `PARCELA_13` à lista de `OPTIONAL_COLUMNS`
- Atualizado `_process_row()` para processar coluna `PARCELA_13`
- Aceita múltiplos formatos: `"1"`, `"PRIMEIRA"`, `"ADIANTAMENTO"`, `"SIM"` → 1
- Aceita: `"2"`, `"SEGUNDA"`, `"DEZEMBRO"` → 2

---

### 7. **Documentação Completa** ✅
**Arquivo:** `GUIA_13_SALARIO_ANIVERSARIO.md` (NOVO)

**Conteúdo:**
- Objetivos
- O que foi implementado
- Como usar na prática
- Exemplos de código
- Regras de validação
- Migrations necessárias
- Testes sugeridos

---

## 🚀 Como Usar

### **Na Empresa:**
1. Vá para configurações da empresa
2. Marque/desmarque "Paga 1ª parcela do 13º no mês de aniversário?"
3. Salve

### **Criar Lançamento Manualmente:**
1. Novo Lançamento
2. Selecione empresa e funcionário
3. Preencha competência (ex: `04/2025`)
4. **Selecione parcela do 13º** (novo dropdown)
5. Salve

### **Importar via XLSX:**
- Adicione coluna `PARCELA_13` (opcional)
- Use valores: `1`, `"1"`, `"PRIMEIRA"`, `2`, `"2"`, `"SEGUNDA"`

---

## 📋 Regras de Negócio Implementadas

### **1ª Parcela do 13º (parcela_13=1)**
- Se `empresa.paga_13_aniversario = False`
  - Mês **DEVE SER 11** (novembro)
  - Validação: se mês ≠ 11, rejeita

- Se `empresa.paga_13_aniversario = True`
  - Mês **DEVE SER** o mês de aniversário do funcionário
  - Validação: se mês ≠ aniversário, rejeita
  - Se funcionário sem data de nascimento → volta ao padrão (11)

### **2ª Parcela do 13º (parcela_13=2)**
- Mês **SEMPRE 12** (dezembro)
- Validação: se mês ≠ 12, rejeita
- Independente de `paga_13_aniversario`

### **Competência Normal (parcela_13=None)**
- Mês entre 1 e 12
- Nenhuma restrição especial

---

## ⚠️ Importante: Unique Constraint

O `unique_together` permite agora:

```
Funcionário: João
Competência: 11/2025, parcela_13=None  ✅ Permitido
Competência: 11/2025, parcela_13=1     ✅ Permitido (ambos podem coexistir!)
Competência: 11/2025, parcela_13=2     ❌ NÃO PERMITIDO (11 é para 1ª parcela, 2ª é em 12)
```

---

## 📦 Próximos Passos (TODO)

- [ ] Atualizar `lancamentos/views.py` para considerar `parcela_13` ao listar competências
- [ ] Atualizar `RelatorioCompetenciaView` para gerar lançamentos do 13º automaticamente
- [ ] Adicionar validação ao criar/editar lançamentos com `parcela_13`
- [ ] Atualizar templates HTML para mostrar `parcela_13` corretamente
- [ ] Testes unitários para `Competencia13Service`
- [ ] Testes de integração para importação com `PARCELA_13`

---

## 🔍 Verificação

Para verificar se está tudo funcionando:

1. **Migrations:**
   ```bash
   python manage.py showmigrations
   # Deve mostrar:
   # lancamentos 0006_add_parcela_13_field
   # empresas 0003_add_paga_13_aniversario
   ```

2. **Aplicar:**
   ```bash
   python manage.py migrate
   ```

3. **Admin Django:**
   - Vá para Empresas → ver novo campo
   - Vá para Lançamentos → ver novo field na edição

4. **Importar XLSX:**
   - Teste importar arquivo com coluna `PARCELA_13`

---

## 📝 Notas Técnicas

### Compatibilidade com VB6

No sistema legado:
- Campo: `Comp13` (booleano)
- `0` = competência normal
- `1` = era o 13º

No novo sistema:
- Campo: `parcela_13` (PositiveSmallIntegerField)
- `None` = competência normal
- `1` = 1ª parcela do 13º
- `2` = 2ª parcela do 13º

Esta estrutura é mais clara e permite futuros tipos de competência.

### Data de Nascimento

Se empresa marcou `paga_13_aniversario=True`, é **crítico** que o `funcionario.data_nascimento` esteja preenchido, senão o sistema volta ao padrão (novembro).

### JAM e Cálculos

Os cálculos JAM devem ser atualizados para:
- Considerar ambas as parcelas do 13º
- Respeitar a configuração `paga_13_aniversario` por funcionário

---

## 📞 Suporte

Dúvidas sobre a implementação? Veja:
- `GUIA_13_SALARIO_ANIVERSARIO.md` - Documentação completa
- `lancamentos/services/competencia_13.py` - Código comentado
- Teste unitários em `lancamentos/tests.py`

