# REGRA DE NEGÓCIO CRÍTICA E IMUTÁVEL

## ⚠️ BUSCA DE ÍNDICES FGTS - NUNCA ALTERAR ⚠️

---

## **1. A REGRA**

A busca de índices FGTS **DEVE SEMPRE** usar a combinação **EXATA** de:

```
competencia = data_da_competencia (primeiro dia do mês)
E
data_base = data_de_pagamento (data exata)
E
tabela = codigo_tabela_fgts (geralmente 1)
```

### **Exemplo Correto:**
```python
# Para calcular FGTS de janeiro/2023 pago em 23/12/2025
competencia = date(2023, 1, 1)  # 01/01/2023
data_pagamento = date(2025, 12, 23)  # 23/12/2025

indice = IndiceFGTSService.buscar_indice(competencia, data_pagamento, tabela=1)
```

---

## **2. O QUE É PROIBIDO**

### ❌ **NUNCA fazer:**

1. **Busca por intervalo de datas**
   ```python
   # ERRADO! NUNCA FAZER ISSO!
   indices = buscar_entre(competencia, data_pagamento)
   indice = max(indices)  # ❌ INCORRETO
   ```

2. **Busca pelo mais próximo**
   ```python
   # ERRADO! NUNCA FAZER ISSO!
   indice = buscar_mais_proximo(competencia, data_pagamento)  # ❌ INCORRETO
   ```

3. **Busca pelo mais recente**
   ```python
   # ERRADO! NUNCA FAZER ISSO!
   indice = buscar_mais_recente(competencia)  # ❌ INCORRETO
   ```

4. **Aproximações ou estimativas**
   ```python
   # ERRADO! NUNCA FAZER ISSO!
   if indice is None:
       indice = estimar_indice(...)  # ❌ INCORRETO
   ```

---

## **3. FONTE DA VERDADE**

### **Única e Exclusiva:**
- **Tabela:** `indices_fgts` no Supabase
- **Acesso:** Via `IndiceFGTSService.buscar_indice()`

### **Estrutura da Tabela:**
```sql
CREATE TABLE indices_fgts (
    id UUID PRIMARY KEY,
    competencia DATE NOT NULL,      -- Primeiro dia do mês
    data_base DATE NOT NULL,        -- Data de pagamento
    tabela INTEGER NOT NULL,        -- Código da tabela FGTS
    indice DECIMAL(12,9) NOT NULL,  -- Valor do índice
    created_at TIMESTAMP,
    UNIQUE(competencia, data_base, tabela)
);
```

---

## **4. COMO USAR CORRETAMENTE**

### **Implementação Obrigatória:**

```python
from indices.services.indice_service import IndiceFGTSService

# Buscar índice
indice = IndiceFGTSService.buscar_indice(
    competencia=date(2023, 1, 1),
    data_pagamento=date(2025, 12, 23),
    tabela=1
)

if indice is None:
    # NÃO aproximar, NÃO estimar
    # Retornar erro para o usuário
    raise ValueError("Índice não encontrado para esta competência e data")

# Usar o índice no cálculo
valor_corrigido = valor_fgts * indice
```

---

## **5. POR QUE ESTA REGRA É IMUTÁVEL**

### **Razões Legais:**
1. **Conformidade Legislativa:** Índices FGTS são definidos por lei federal
2. **Auditoria:** Órgãos fiscalizadores exigem rastreabilidade exata
3. **Responsabilidade Civil:** Erros podem gerar processos judiciais

### **Razões Técnicas:**
1. **Precisão:** Aproximações geram valores incorretos
2. **Reprodutibilidade:** Mesmo cálculo deve dar mesmo resultado sempre
3. **Integridade:** Dados devem corresponder exatamente aos registros oficiais

### **Razões de Negócio:**
1. **Confiabilidade:** Clientes confiam nos cálculos
2. **Reputação:** Erros comprometem credibilidade
3. **Compliance:** Sistema deve ser certificável

---

## **6. VALIDAÇÕES E PROTEÇÕES**

### **Implementadas:**
1. ✅ Validação de tipos (date obrigatório)
2. ✅ Validação de lógica (data pagamento >= competência)
3. ✅ Logs de auditoria em toda busca
4. ✅ Serviço centralizado (`IndiceFGTSService`)
5. ✅ Testes automatizados
6. ✅ Documentação inline no código

### **Testes Críticos:**
```bash
# Executar testes da regra imutável
python manage.py test indices.tests.test_regra_imutavel
```

Todos os testes **DEVEM PASSAR**. Falha = Violação da regra.

---

## **7. MANUTENÇÃO E EVOLUÇÃO**

### **O que PODE ser alterado:**
- Performance da busca (otimizações de query)
- Tratamento de erros (melhorar mensagens)
- Logs e monitoramento
- Validações adicionais

### **O que NUNCA pode ser alterado:**
- ❌ Lógica de filtro (competencia E data_base exatos)
- ❌ Fonte de dados (indices_fgts do Supabase)
- ❌ Tipo de busca (exata, nunca aproximada)
- ❌ Retorno None quando não encontrar

---

## **8. CHECKLIST PARA CODE REVIEW**

Ao revisar código relacionado a índices FGTS, verificar:

- [ ] Usa `IndiceFGTSService.buscar_indice()`?
- [ ] Passa `competencia` e `data_pagamento` como `date`?
- [ ] Não faz busca por intervalo?
- [ ] Não aproxima valores?
- [ ] Trata corretamente `None` (erro, não aproximação)?
- [ ] Logs de auditoria presentes?
- [ ] Testes cobrem o caso de uso?

---

## **9. CONTATOS E RESPONSÁVEIS**

**Responsável pela Regra:**
- Esta regra é de **responsabilidade compartilhada** entre:
  - Desenvolvedor Líder
  - Analista de Negócios
  - Compliance/Jurídico

**Em caso de dúvidas:**
1. Consultar este documento
2. Revisar código em `indices/services/indice_service.py`
3. Executar testes em `indices/tests/test_regra_imutavel.py`
4. **Nunca presumir** - sempre confirmar

---

## **10. HISTÓRICO DE ALTERAÇÕES**

| Data | Versão | Alteração | Autor |
|------|--------|-----------|-------|
| 30/12/2025 | 1.0 | Criação da regra imutável | Sistema |

---

**⚠️ IMPORTANTE:**
Este documento é parte da documentação oficial do sistema e deve ser mantido atualizado com qualquer alteração relacionada à busca de índices FGTS.
