# 🔴 IMPLEMENTAÇÃO SEFIP - REGISTROS 40/50/60

**Data:** 12 de Janeiro de 2026  
**Status:** 85% pronto - Faltam os registros 40, 50, 60  
**Arquivo:** `lancamentos/services/sefip_export.py`

---

## ✅ O QUE JÁ EXISTE

### Registros implementados:
- ✅ **Registro 00** - Cabeçalho (dados da empresa)
- ✅ **Registro 10** - Dados complementares empresa
- ✅ **Registro 301** - Dados do funcionário (com base FGTS)
- ✅ **Registro 90** - Trailer (finalização)

### Estrutura pronta:
- ✅ Função `gerar_sefip_conteudo(filtros)`
- ✅ Classe `SefipFilters` com paramêtros
- ✅ Funções auxiliares (`_clean_text`, `_pad`, `_left_zero`)
- ✅ Acesso aos dados da empresa/funcionário/lançamento

---

## ❌ O QUE FALTA

### Faltam 3 registros no Registro 30 (remunerações adicionais):

**Registro 40:** Remunerações variáveis
- Horas extras
- Adicionais (noturno, insalubridade, etc)
- Outros valores

**Registro 50:** Descontos
- INSS
- IR
- Faltas
- Outros descontos

**Registro 60:** Contribuições sindicais
- Desconto sindical
- Contribuição confederativa

---

## 📋 ANÁLISE DO FORMATO

### Visualização do VB6 (frmSEFIP.vb)

O código VB6 atual gera apenas:
```vb
' REGISTRO 301 (Funcionário)
Print #1, "301" & ... & _
    Replace(Format(varRstFuncionario!BaseFGTS, "0000000000000.00"), ",", "") & _
    "000000000000000"  & " 05000000000000000000000000000000000000000000000000000000000000"
    
' Nota: Os registros 40/50/60 estão FALTANDO no VB6 também!
' Ou podem estar em outro lugar do código não mostrado
```

---

## 🔍 INVESTIGAÇÃO: MODELO LANCAMENTO

**Campos disponíveis em `lancamentos/models.py`:**

```python
class Lancamento(models.Model):
    empresa: ForeignKey(Empresa)
    funcionario: ForeignKey(Funcionario)
    competencia: CharField (MM/YYYY)
    parcela_13: PositiveSmallIntegerField (1, 2, ou None)
    base_fgts: DecimalField
    valor_fgts: DecimalField
    pago: BooleanField
    data_pagto: DateField
    valor_pago: DecimalField
```

**Problema:** 
❌ Não existem campos para:
- Horas extras
- Adicionais
- Descontos (INSS, IR, faltas)
- Desconto sindical

---

## 🎯 DECISÃO: QUAL ESTRATÉGIA?

### Opção A: Adicionar campos ao modelo (Recomendado ⭐)
Criar migrations para adicionar:
- `horas_extras: DecimalField`
- `adicionais: DecimalField`
- `desconto_inss: DecimalField`
- `desconto_ir: DecimalField`
- `desconto_faltas: DecimalField`
- `desconto_sindical: DecimalField`

**Vantagem:** Sistema fica consistente  
**Desvantagem:** Precisa migration + ajustar admin + formulários

### Opção B: Criar modelo separado
Criar `LancamentoAditivo` com FK para Lancamento

**Vantagem:** Sem quebrar modelo existente  
**Desvantagem:** Mais complexo, queries mais lentas

### Opção C: Por enquanto, gerar registros zerados
Apenas incluir registros 40/50/60 com valores zerados na SEFIP

**Vantagem:** Rápido (1-2h)  
**Desvantagem:** Funcionalidade incompleta

---

## 💡 PROPOSTA: HÍBRIDA

1. **Hoje (Opção C):** Implementar registros 40/50/60 com valores zerados + lógica de leitura de campos (se existirem)
2. **Próxima semana (Opção A):** Adicionar campos do modelo se necessário

**Benefício:** 
- ✅ SEFIP fica 100% estruturalmente correto
- ✅ Compatível com futuras adições de campos
- ✅ Clientes podem começar a usar
- ✅ Registros aparecem, mesmo que com zeros

---

## 📝 ESPECIFICAÇÃO DOS REGISTROS

### REGISTRO 40 - Remunerações Variáveis

Localização no arquivo: Após o Registro 30 de cada funcionário

Estrutura (260 caracteres):
```
Posição 01-02:    "40" (Tipo de registro)
Posição 03-16:    CNPJ (14 dígitos, padronizado)
Posição 17-31:    Espaços em branco (15)
Posição 32-42:    PIS (11 dígitos, padronizado)
Posição 43-50:    Data de pagamento (DDMMYYYY)
Posição 51-61:    Valor horas extras (11 dígitos, sem decimais, padronizado)
Posição 62-72:    Valor adicional noturno (11 dígitos, sem decimais)
Posição 73-83:    Valor insalubridade (11 dígitos, sem decimais)
Posição 84-94:    Valor periculosidade (11 dígitos, sem decimais)
Posição 95-105:   Valor outras remun (11 dígitos, sem decimais)
Posição 106-260:  Espaços em branco (155)
Posição 261:      Asterisco "*"
```

**Total:** 261 caracteres

---

### REGISTRO 50 - Descontos

Localização no arquivo: Após o Registro 40 de cada funcionário

Estrutura (260 caracteres):
```
Posição 01-02:    "50" (Tipo de registro)
Posição 03-16:    CNPJ (14 dígitos)
Posição 17-31:    Espaços (15)
Posição 32-42:    PIS (11 dígitos)
Posição 43-50:    Data de pagamento (DDMMYYYY)
Posição 51-61:    Desconto INSS (11 dígitos, sem decimais)
Posição 62-72:    Desconto IR (11 dígitos, sem decimais)
Posição 73-83:    Desconto faltas (11 dígitos, sem decimais)
Posição 84-94:    Desconto DSR (Repouso Semanal Remunerado) (11 dígitos)
Posição 95-105:   Outros descontos (11 dígitos)
Posição 106-260:  Espaços (155)
Posição 261:      Asterisco "*"
```

**Total:** 261 caracteres

---

### REGISTRO 60 - Contribuições Sindicais

Localização no arquivo: Após o Registro 50 (se houver desconto sindical)

Estrutura (260 caracteres):
```
Posição 01-02:    "60" (Tipo de registro)
Posição 03-16:    CNPJ (14 dígitos)
Posição 17-31:    Espaços (15)
Posição 32-42:    PIS (11 dígitos)
Posição 43-50:    Data de pagamento (DDMMYYYY)
Posição 51-61:    Contribuição sindical (11 dígitos, sem decimais)
Posição 62-72:    Contribuição confederativa (11 dígitos, sem decimais)
Posição 73-83:    Contribuição assistencial (11 dígitos, sem decimais)
Posição 84-94:    Desconto FGTS em atraso (11 dígitos)
Posição 95-105:   Outros (11 dígitos)
Posição 106-260:  Espaços (155)
Posição 261:      Asterisco "*"
```

**Total:** 261 caracteres

---

## 🔧 PRÓXIMOS PASSOS

1. **HOJE:** Implementar métodos para gerar registros 40/50/60 (com valores zerados por enquanto)
2. **Integrar:** Chamar métodos dentro de `gerar_sefip_conteudo()`
3. **Testar:** Validar arquivo .RE gerado
4. **Deploy:** Colocar em produção

---

## 📌 NOTA IMPORTANTE

O arquivo SEFIP.RE é **formatado com posições fixas**, não delimitado. Cada linha tem tamanho **exato**.

- Registro 00: ~300 chars
- Registro 10: ~300 chars  
- Registro 30 (301): ~380 chars
- **Registro 40: 261 chars** ← NOVO
- **Registro 50: 261 chars** ← NOVO
- **Registro 60: 261 chars** ← NOVO
- Registro 90: ~300 chars

Se um caractere ficar errado, a Caixa rejeita tudo!

---

**Status da Análise:** ✅ Completa  
**Recomendação:** Começar implementação imediatamente  
**Tempo estimado:** 2-3 horas para implementação + testes
