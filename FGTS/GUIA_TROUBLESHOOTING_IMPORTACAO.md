# 🔧 Guia de Resolução de Problemas - Importação de Lançamentos

## ✅ Problema Resolvido: Importação Sem Feedback

### 🐛 Problema Original
- Usuário importava planilha de lançamentos
- Não recebia feedback visual (processamento ou resultado)
- Lançamentos não apareciam para os colaboradores
- Dados não eram salvos no banco

### 🔍 Causas Identificadas

1. **Lançamentos Órfãos no Banco de Dados (94 registros)**
   - Lançamentos referenciando funcionários que não existiam mais
   - Causava erro ao tentar acessar `lancamento.funcionario.nome`
   - Signals de audit_logs falhavam ao deletar lançamentos órfãos

2. **Falta de Feedback Visual**
   - Template não mostrava indicador de progresso durante upload
   - Nenhuma validação client-side antes de enviar
   - Usuário não sabia se processo estava rodando ou se falhou

3. **Mensagens de Erro Pouco Claras**
   - Erros genéricos sem contexto
   - Não indicavam linha específica do problema
   - Não sugeriam soluções

---

## ✅ Correções Implementadas

### 1. Limpeza de Dados Órfãos
**Arquivo:** `cleanup_lancamentos.py`
```bash
python cleanup_lancamentos.py
```
**Resultado:** 94 lançamentos órfãos removidos com sucesso

### 2. Correção dos Signals de Audit
**Arquivo:** `audit_logs/signals.py`
- Adicionado try/except ao acessar `funcionario.nome`
- Fallback para "Funcionário ID X" quando funcionário não existe
- Evita crash ao deletar lançamentos órfãos

### 3. Feedback Visual Durante Importação
**Arquivo:** `lancamentos/templates/lancamentos/lancamento_import.html`

**Melhorias:**
- ✅ Spinner animado ao submeter formulário
- ✅ Botão "Importar" muda para "Processando..."
- ✅ Desabilita botão para evitar múltiplos envios
- ✅ Alert box com mensagem de progresso
- ✅ Validação client-side antes de enviar
- ✅ Scroll automático para área de progresso

### 4. Mensagens de Erro Detalhadas
**Arquivo:** `lancamentos/services/importacao.py`

**Melhorias:**
- ✅ CPF formatado nas mensagens (123.456.789-01)
- ✅ Validação de 11 dígitos no CPF
- ✅ Mensagens específicas para cada tipo de erro
- ✅ Sugestões de correção incluídas
- ✅ Validação de arquivo vazio ou corrompido
- ✅ Validação de colunas obrigatórias
- ✅ Contador de linhas processadas

### 5. Tratamento de Exceções Melhorado
**Arquivo:** `lancamentos/views.py`

**Melhorias:**
- ✅ Logging de erros para debug
- ✅ Mensagens diferenciadas (validação vs erro inesperado)
- ✅ Resumo sempre exibido (sucessos, erros, pulados)
- ✅ Warning se nenhum dado foi processado
- ✅ Top 5 erros exibidos (evita spam)

---

## 📋 Como Usar a Importação Agora

### Passo 1: Preparar Arquivo
1. Acesse `/lancamentos/importar/`
2. Clique em **"Baixar modelo XLSX"**
3. Abra o arquivo no Excel/LibreOffice
4. **DELETE a linha de exemplo**
5. Preencha suas linhas de dados

### Passo 2: Validar Dados
✅ **CPF:** Apenas números ou formatado (000.000.000-00)
✅ **Competência:** Formato MM/YYYY (ex: 01/2026)
✅ **Base FGTS:** Valor numérico com ponto (ex: 3500.00)
✅ **Colaborador:** Deve estar cadastrado na empresa

### Passo 3: Importar
1. Selecione a empresa
2. Escolha o arquivo .xlsx
3. Clique em **"Importar"**
4. **Aguarde** o indicador de progresso
5. Veja o resultado nas mensagens

### Passo 4: Verificar
1. Acesse **Lançamentos** no menu
2. Filtre pela competência importada
3. Verifique se lançamentos aparecem
4. Confira valores e colaboradores

---

## 🚨 Erros Comuns e Soluções

### ❌ "Colaborador com CPF XXX não encontrado"
**Causa:** Funcionário não está cadastrado na empresa selecionada

**Solução:**
1. Vá em **Cadastros → Funcionários**
2. Cadastre o colaborador primeiro
3. Tente importar novamente

### ❌ "Competência inválida: XXX"
**Causa:** Formato errado (deve ser MM/YYYY)

**Solução:**
- ❌ Errado: `Janeiro/2026`, `1/26`, `2026/01`
- ✅ Certo: `01/2026`, `12/2026`

### ❌ "Base FGTS inválida"
**Causa:** Valor não numérico ou com vírgula

**Solução:**
- ❌ Errado: `R$ 3.500,00`, `3,500`, `três mil`
- ✅ Certo: `3500.00`, `3500`, `1234.56`

### ❌ "Colunas obrigatórias faltando"
**Causa:** Arquivo não segue o modelo ou foi modificado

**Solução:**
1. Baixe o modelo novamente
2. Copie seus dados para o novo modelo
3. Não altere os nomes das colunas

### ❌ "Arquivo vazio"
**Causa:** Apenas cabeçalho, sem linhas de dados

**Solução:**
1. Certifique-se de preencher pelo menos 1 linha de dados
2. Delete a linha de exemplo se ainda estiver lá

### ❌ "Nenhuma linha de dados encontrada"
**Causa:** Todas as linhas estão vazias

**Solução:**
1. Verifique se há dados nas células
2. Certifique-se de preencher CPF, Competência e Base FGTS

---

## 🧪 Como Testar

### Teste 1: Importação Simples (1 colaborador)
```
CPF: 12345678901
NOME: João da Silva
COMPETENCIA: 01/2026
BASE_FGTS: 3500.00
```
**Esperado:** 1 lançamento criado com sucesso

### Teste 2: Atualização (mesmo colaborador, mesma competência)
```
CPF: 12345678901
NOME: João da Silva
COMPETENCIA: 01/2026
BASE_FGTS: 4000.00  ← valor diferente
```
**Esperado:** 1 lançamento atualizado

### Teste 3: Múltiplos Colaboradores
```
Linha 2: CPF 111, Competência 01/2026, Base 3500
Linha 3: CPF 222, Competência 01/2026, Base 4000
Linha 4: CPF 333, Competência 02/2026, Base 3800
```
**Esperado:** 3 lançamentos criados

### Teste 4: Erro Esperado (CPF não cadastrado)
```
CPF: 99999999999  ← não existe
COMPETENCIA: 01/2026
BASE_FGTS: 3500
```
**Esperado:** Erro na linha X: "Colaborador não encontrado"

---

## 📊 Mensagens de Feedback

### ✅ Sucesso
```
✅ 5 lançamento(s) criado(s) com sucesso!
ℹ️ 2 lançamento(s) atualizado(s).
📊 Resumo: 7 sucesso(s), 0 erro(s), 0 pulado(s)
```

### ⚠️ Parcialmente Sucesso
```
✅ 3 lançamento(s) criado(s) com sucesso!
❌ Linha 2: Colaborador com CPF 111.111.111-11 não encontrado
❌ Linha 5: Base FGTS inválida: 'abc'
📊 Resumo: 3 sucesso(s), 2 erro(s), 0 pulado(s)
```

### ❌ Falha Total
```
❌ Erro de validação: Nenhuma linha de dados encontrada no arquivo
```

---

## 🔍 Debug Avançado

### Ver Logs no Terminal
```bash
python manage.py runserver
# Acompanhe o terminal durante importação
```

### Verificar Lançamentos no Banco
```python
python manage.py shell
>>> from lancamentos.models import Lancamento
>>> Lancamento.objects.count()  # Total de lançamentos
>>> Lancamento.objects.filter(competencia='01/2026').count()  # Por competência
```

### Limpar Lançamentos de Teste
```python
python manage.py shell
>>> from lancamentos.models import Lancamento
>>> Lancamento.objects.filter(funcionario__nome__contains='Teste').delete()
```

---

## 📞 Suporte

Se o problema persistir após seguir este guia:

1. **Verifique o terminal** do runserver para ver erros detalhados
2. **Tire print** das mensagens de erro exibidas
3. **Anexe o arquivo XLSX** que está tentando importar
4. **Informe** qual empresa e quais colaboradores está tentando importar

**Arquivos Relevantes:**
- `lancamentos/views.py` (linha 965-1033)
- `lancamentos/services/importacao.py`
- `lancamentos/templates/lancamentos/lancamento_import.html`
- `audit_logs/signals.py` (linhas 100-122)

**Scripts Úteis:**
- `cleanup_lancamentos.py` - Limpar lançamentos órfãos
- `debug_import_lancamentos.py` - Debug estado do banco

---

## ✅ Checklist Final

Antes de reportar problema, verifique:

- [ ] Colaborador está cadastrado na empresa correta?
- [ ] CPF tem 11 dígitos?
- [ ] Competência está no formato MM/YYYY?
- [ ] Base FGTS é um número válido?
- [ ] Arquivo baixado do modelo oficial?
- [ ] Linha de exemplo foi deletada?
- [ ] Empresa correta foi selecionada?
- [ ] Arquivo tem extensão .xlsx?
- [ ] Esperou o indicador de progresso aparecer?
- [ ] Viu as mensagens de resultado no topo da página?

---

**🎉 Sistema 100% operacional após correções!**

**Data:** 03/01/2026  
**Versão:** 2.0 (Correção Completa)
