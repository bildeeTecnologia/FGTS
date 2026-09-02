# ⚡ Guia Rápido - Implementação 13º com Aniversário

## ✅ O Que Foi Feito

Você pediu para adicionar uma configuração na empresa para que a **1ª parcela do 13º** seja paga no **mês de aniversário do colaborador** ao invés de novembro. Isso foi totalmente implementado!

---

## 🎯 Resumo da Solução

### **Antes (Sistema Atual)**
- Apenas 12 competências (01-12)
- Faltava as 2 parcelas do 13º

### **Depois (Implementado Agora)**
- 12 competências normais (01-12) + 2 parcelas do 13º
- Campo na empresa: "Paga 1ª parcela do 13º no mês de aniversário?"
- Se SIM → 1ª parcela no mês de nascimento do funcionário
- Se NÃO → 1ª parcela em novembro (padrão)
- 2ª parcela sempre em dezembro

---

## 📦 Arquivos Modificados/Criados

| Arquivo | Tipo | O Que Mudou |
|---------|------|-----------|
| `empresas/models.py` | ✏️ Modificado | Adicionado campo `paga_13_aniversario` |
| `empresas/forms.py` | ✏️ Modificado | Adicionado checkbox do novo campo |
| `lancamentos/models.py` | ✏️ Modificado | Adicionado campo `parcela_13` |
| `lancamentos/forms.py` | ✏️ Modificado | Adicionado dropdown `parcela_13` |
| `lancamentos/services/importacao.py` | ✏️ Modificado | Suporta coluna `PARCELA_13` em XLSX |
| `lancamentos/services/competencia_13.py` | ✨ **NOVO** | Serviço com toda a lógica do 13º |
| `lancamentos/migrations/0006_*` | ✨ **NOVO** | Migration para `parcela_13` |
| `empresas/migrations/0003_*` | ✨ **NOVO** | Migration para `paga_13_aniversario` |
| `GUIA_13_SALARIO_ANIVERSARIO.md` | 📖 **NOVO** | Documentação completa |
| `RESUMO_13_ANIVERSARIO_IMPLEMENTADO.md` | 📖 **NOVO** | Resumo técnico |

---

## 🚀 Como Usar

### **Passo 1: Aplicar Migrations**

```bash
cd "c:\Users\Gt_Soluções\OneDrive\Desktop\Projetos\PJT-FGTS PYTHON\FGTS-PYTHON"
python manage.py migrate
```

Isso vai criar os campos na empresa e nos lançamentos.

### **Passo 2: Configurar a Empresa**

1. Acesse o painel administrativo
2. Vá para **Empresas**
3. Edite a empresa
4. Marque/desmarque: **"Paga 1ª parcela do 13º no mês de aniversário?"**
5. Salve

### **Passo 3: Criar Lançamentos do 13º**

**Via interface web:**
1. Novo Lançamento
2. Selecione empresa e funcionário
3. Digite competência: `11/2025` (para 1ª parcela) ou `12/2025` (para 2ª)
4. **NOVO:** Selecione "Parcela do 13º" = "13º Salário - 1ª Parcela" ou "13º Salário - 2ª Parcela"
5. Preencha base FGTS
6. Salve

**Via importação XLSX:**
1. Prepare um arquivo com as colunas:
   - `CPF_FUNCIONARIO`
   - `NOME_FUNCIONARIO`
   - `COMPETENCIA` (ex: `04/2025` para aniversário em abril)
   - `BASE_FGTS`
   - `PARCELA_13` (ex: `1` para 1ª parcela, `2` para 2ª parcela)
2. Importe o arquivo
3. Pronto!

---

## 📋 Exemplo Prático

### **Cenário: Empresa ABC**

**Configuração:**
- ✅ Marcado: "Paga 1ª parcela do 13º no mês de aniversário?"

**Funcionário: João (nascimento: 04/1990)**

Lançamentos gerados:
| Competência | Parcela 13 | Mês de Pagamento | Descrição |
|-------------|-----------|------------------|-----------|
| 01/2025 | — | Janeiro | Normal |
| 02/2025 | — | Fevereiro | Normal |
| 03/2025 | — | Março | Normal |
| 04/2025 | 1ª | Abril | 🆕 1ª parcela 13º no aniversário |
| 05/2025 | — | Maio | Normal |
| ... | — | ... | ... |
| 12/2025 | — | Dezembro | Normal |
| 12/2025 | 2ª | Dezembro | 2ª parcela 13º |

**Funcionário: Maria (nascimento: 06/1985)**

Lançamentos gerados:
| Competência | Parcela 13 | Mês de Pagamento | Descrição |
|-------------|-----------|------------------|-----------|
| ... | — | ... | ... |
| 06/2025 | 1ª | Junho | 🆕 1ª parcela 13º no aniversário |
| ... | — | ... | ... |
| 12/2025 | 2ª | Dezembro | 2ª parcela 13º |

---

## 💡 Lógica Implementada

### **Quando `paga_13_aniversario = TRUE`**

```python
mês_1ª_parcela_13 = data_nascimento.month
# Exemplo: 04/1990 → mês 4 (abril)

Lançamento 1: competencia='04/2025', parcela_13=1  # 1ª parcela em abril
Lançamento 2: competencia='12/2025', parcela_13=2  # 2ª parcela em dezembro
```

### **Quando `paga_13_aniversario = FALSE`** (padrão)

```python
mês_1ª_parcela_13 = 11  # Novembro (padrão)

Lançamento 1: competencia='11/2025', parcela_13=1  # 1ª parcela em novembro
Lançamento 2: competencia='12/2025', parcela_13=2  # 2ª parcela em dezembro
```

---

## 🔧 Serviço `Competencia13Service`

Para usar em código Python:

```python
from lancamentos.services.competencia_13 import Competencia13Service

# Descobrir em qual mês a 1ª parcela deve ser paga
mes = Competencia13Service.obter_mes_primeira_parcela_13(empresa, funcionario)
# Retorna: 4 (abril) se aniversário em abril e empresa marcou opção
# Retorna: 11 (novembro) caso contrário

# Gerar as 2 competências do 13º para um ano
competencias = Competencia13Service.gerar_competencias_13(empresa, 2025, funcionario)
# Retorna: [('04/2025', 1), ('12/2025', 2)]

# Validar uma competência do 13º
valido, mensagem = Competencia13Service.validar_competencia_13(
    empresa, funcionario, '04/2025', 1
)
# Retorna: (True, "Competência do 13º válida")
```

---

## ⚠️ Regras Importantes

### **1ª Parcela do 13º (parcela_13=1)**
- Mês definido pela configuração `paga_13_aniversario`
- Se `False`: **SEMPRE NOVEMBRO (11)**
- Se `True`: **MÊS DE ANIVERSÁRIO DO FUNCIONÁRIO**
- ⚠️ Se funcionário não tiver data de nascimento → volta ao padrão (novembro)

### **2ª Parcela do 13º (parcela_13=2)**
- **SEMPRE DEZEMBRO (12)**, sem exceção
- Independente da configuração da empresa

### **Competências Normais (parcela_13=None)**
- Meses 01 a 12
- Nenhuma restrição especial

---

## 🧪 Como Testar

### **Teste 1: Criar lançamento 13º com aniversário**
```
1. Empresa: XYZ (com paga_13_aniversario=TRUE)
2. Funcionário: João (nascimento 04/1990)
3. Criar: competencia='04/2025', parcela_13=1
4. Esperado: ✅ Aceitar

5. Criar: competencia='11/2025', parcela_13=1
6. Esperado: ❌ Rejeitar (1ª parcela deve ser em abril, não novembro)
```

### **Teste 2: Criar lançamento 13º sem aniversário**
```
1. Empresa: ABC (com paga_13_aniversario=FALSE)
2. Qualquer funcionário
3. Criar: competencia='11/2025', parcela_13=1
4. Esperado: ✅ Aceitar

5. Criar: competencia='04/2025', parcela_13=1
6. Esperado: ❌ Rejeitar (1ª parcela deve ser em novembro, não abril)
```

### **Teste 3: Importar XLSX**
```
Arquivo com colunas:
CPF | NOME | COMPETENCIA | BASE_FGTS | PARCELA_13
123 | João | 04/2025 | 3500 | 1
123 | João | 12/2025 | 3500 | 2

Esperado: ✅ 2 lançamentos criados corretamente
```

---

## 📞 Documentação Adicional

Para aprofundar:

1. **`GUIA_13_SALARIO_ANIVERSARIO.md`** - Documentação completa com exemplos
2. **`RESUMO_13_ANIVERSARIO_IMPLEMENTADO.md`** - Detalhes técnicos
3. **`lancamentos/services/competencia_13.py`** - Código comentado
4. **`lancamentos/models.py`** - Campo `parcela_13`
5. **`empresas/models.py`** - Campo `paga_13_aniversario`

---

## ✨ Resumo

✅ **Criado:** Campo na empresa para ativar pagamento do 13º no aniversário  
✅ **Criado:** Campo de parcela (1 ou 2) nos lançamentos  
✅ **Criado:** Serviço completo de validação e geração de competências do 13º  
✅ **Atualizado:** Formulários para incluir novos campos  
✅ **Atualizado:** Importação XLSX para aceitar `PARCELA_13`  
✅ **Criado:** Migrations necessárias  
✅ **Criado:** Documentação completa  

**Próximo passo:** Aplicar `python manage.py migrate` e começar a usar! 🚀

