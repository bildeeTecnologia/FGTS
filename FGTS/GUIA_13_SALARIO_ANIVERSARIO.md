# 📋 Configuração e Uso do 13º Salário com Opção de Aniversário

## 🎯 Objetivo

Implementar suporte às **2 parcelas obrigatórias do 13º salário**, com opção de que a empresa pague a **1ª parcela no mês de aniversário** do colaborador (ao invés de novembro).

---

## 📦 O Que Foi Implementado

### 1. **Campo na Empresa** (empresas/models.py)

```python
paga_13_aniversario = BooleanField(
    default=False,
    verbose_name='Paga 1ª parcela do 13º no mês de aniversário?',
    help_text='Se marcado, a 1ª parcela será paga no mês de aniversário (ao invés de novembro). 2ª parcela sempre em dezembro.'
)
```

**Como usar:**
- Acesse as configurações da empresa
- Marque a opção: "Paga 1ª parcela do 13º no mês de aniversário?"
- Salve as alterações

---

### 2. **Campo no Lançamento** (lancamentos/models.py)

```python
parcela_13 = PositiveSmallIntegerField(
    null=True,
    blank=True,
    choices=[(1, '13º Salário - 1ª Parcela'), (2, '13º Salário - 2ª Parcela')],
    help_text='Se preenchido, indica que é uma das 2 parcelas do 13º salário'
)
```

**Valores possíveis:**
- `None`: Competência normal (01-12)
- `1`: 1ª parcela do 13º
- `2`: 2ª parcela do 13º

---

### 3. **Serviço de Competências** (lancamentos/services/competencia_13.py)

Classe `Competencia13Service` com métodos úteis:

#### `obter_mes_primeira_parcela_13(empresa, funcionario)`
Retorna o mês em que a 1ª parcela do 13º deve ser paga.

```python
from lancamentos.services.competencia_13 import Competencia13Service

mes = Competencia13Service.obter_mes_primeira_parcela_13(empresa, funcionario)
# Retorna: 4 (se aniversário em abril e paga_13_aniversario=True)
# Retorna: 11 (novembro padrão se paga_13_aniversario=False)
```

#### `gerar_competencias_13(empresa, ano, funcionario=None)`
Gera as 2 competências do 13º para um ano.

```python
comps = Competencia13Service.gerar_competencias_13(empresa, 2025, funcionario)
# Retorna: [('04/2025', 1), ('12/2025', 2)]
#   se aniversário em abril e paga_13_aniversario=True
```

#### `gerar_todas_competencias_ano(empresa, ano, funcionario=None)`
Gera TODAS as competências do ano (01-12 + 2 parcelas do 13º).

```python
comps = Competencia13Service.gerar_todas_competencias_ano(empresa, 2025, funcionario)
# Retorna: ['01/2025', '02/2025', ..., '12/2025', '04/2025', '12/2025']
#   (últimas 2 são as parcelas do 13º)
```

#### `validar_competencia_13(empresa, funcionario, competencia_str, parcela_13)`
Valida se uma competência com parcela_13 é válida.

```python
valido, msg = Competencia13Service.validar_competencia_13(
    empresa, funcionario, '04/2025', 1
)
# Retorna: (True, "Competência do 13º válida")
# ou: (False, "1ª parcela do 13º deve ser em 04, não em 11")
```

---

## 🔧 Como Usar na Prática

### **Importar Lançamentos com 13º**

**Arquivo XLSX agora aceita coluna opcional `PARCELA_13`:**

| CPF | NOME | COMPETENCIA | BASE_FGTS | PARCELA_13 |
|-----|------|-------------|-----------|------------|
| 12345678901 | João | 04/2025 | 3500.00 | 1 |
| 12345678901 | João | 12/2025 | 3500.00 | 2 |
| 98765432109 | Maria | 03/2025 | 4000.00 | 1 |
| 98765432109 | Maria | 12/2025 | 4000.00 | 2 |

**Valores aceitos para `PARCELA_13`:**
- `1`, `"1"`, `"PRIMEIRA"`, `"ADIANTAMENTO"`, `"SIM"` → 1ª parcela
- `2`, `"2"`, `"SEGUNDA"`, `"DEZEMBRO"` → 2ª parcela
- Vazio ou outro valor → Competência normal (01-12)

---

### **Criar Lançamento Manualmente**

1. Clique em "Novo Lançamento"
2. Selecione a empresa e funcionário
3. Preencha a competência (ex: `04/2025`)
4. **Selecione a parcela do 13º** (novo campo)
   - "Competência Normal (01-12)" para meses normais
   - "13º Salário - 1ª Parcela" para 1ª parcela
   - "13º Salário - 2ª Parcela" para 2ª parcela
5. Preencha base FGTS e demais campos
6. Salve

---

### **Regras de Validação**

#### **1ª Parcela do 13º**
- **Se `paga_13_aniversario = False`**: Mês deve ser **11 (novembro)**
- **Se `paga_13_aniversario = True`**: Mês deve ser o **mês de aniversário do funcionário**
  - Exemplo: Se nascimento em 04/1990, mês deve ser 04
  - Se funcionário sem data de nascimento → volta ao padrão (novembro)

#### **2ª Parcela do 13º**
- Sempre **12 (dezembro)**, independente da configuração da empresa

#### **Competência Normal (01-12)**
- Mês entre 1 e 12
- Campo `parcela_13 = None`

---

## 🚀 Exemplos de Uso em Views

### **Relatorio de Competência**

O sistema agora deve considerar as 2 parcelas do 13º ao gerar relatórios:

```python
# Isto deve ser atualizado em lancamentos/views.py
competencias_list = list(
    lancamentos_qs.values_list('competencia', flat=True)
    .distinct()
    .order_by('competencia')
)

# As competências do 13º virão como: 04/2025 (se aniversário abril)
# e 12/2025, ambas com parcela_13 preenchido
```

---

## 📝 Migrations Necessárias

Executar em sequência:

```bash
# 1. Adicionar campo parcela_13 ao Lancamento
python manage.py makemigrations lancamentos --name add_parcela_13_field

# 2. Adicionar campo paga_13_aniversario à Empresa
python manage.py makemigrations empresas --name add_paga_13_aniversario_field

# 3. Aplicar migrations
python manage.py migrate
```

---

## ⚠️ Pontos Importantes

### **Unique Constraint Atualizado**

O campo `unique_together` foi atualizado para:

```python
unique_together = ('funcionario', 'competencia', 'parcela_13')
```

Isso permite:
- João com `competencia='11/2025'` + `parcela_13=None` (competência normal)
- João com `competencia='11/2025'` + `parcela_13=1` (1ª parcela do 13º)
- Ambos podem coexistir no banco

### **Data de Nascimento é Obrigatória**

Se a empresa marcou `paga_13_aniversario=True`, o funcionário **deve ter `data_nascimento` preenchida**, senão o sistema voltará ao padrão (novembro).

### **Compatibilidade com Código Legado VB6**

O campo `Comp13` (booleano no VB6) foi refatorado para `parcela_13` (0, 1 ou 2 no Django) porque:
- VB6: `Comp13 = 1` significava "é o 13º"
- Django: `parcela_13 = 1` significa "é a 1ª parcela do 13º"
- Django: `parcela_13 = 2` significa "é a 2ª parcela do 13º"

---

## 🔍 Testes Sugeridos

### **Teste 1: Competências Normais**
- Criar lançamento com `competencia='01/2025'`, `parcela_13=None`
- Deve aceitar

### **Teste 2: 13º com Aniversário = False**
- Empresa com `paga_13_aniversario=False`
- Criar 2 lançamentos:
  - `competencia='11/2025'`, `parcela_13=1` ✅
  - `competencia='12/2025'`, `parcela_13=2` ✅
  - `competencia='04/2025'`, `parcela_13=1` ❌ (deveria rejeitar)

### **Teste 3: 13º com Aniversário = True**
- Funcionário com `data_nascimento='1990-04-15'`
- Empresa com `paga_13_aniversario=True`
- Criar 2 lançamentos:
  - `competencia='04/2025'`, `parcela_13=1` ✅
  - `competencia='12/2025'`, `parcela_13=2` ✅
  - `competencia='11/2025'`, `parcela_13=1` ❌ (deveria rejeitar)

### **Teste 4: Importação XLSX**
- Importar arquivo com coluna `PARCELA_13`
- Validar se lançamentos foram criados corretamente

---

## 📚 Documentação Adicional

- [Modelo Lancamento](lancamentos/models.py) - Campo `parcela_13`
- [Modelo Empresa](empresas/models.py) - Campo `paga_13_aniversario`
- [Serviço Competencia13](lancamentos/services/competencia_13.py) - Lógica de negócio
- [Formulário Lançamento](lancamentos/forms.py) - Campo `parcela_13` adicionado

