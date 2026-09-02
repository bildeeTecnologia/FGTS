# 🚀 COMECE AGORA - Instruções Passo a Passo (12/01/2026)

**Objetivo Today:** Completar SEFIP registros 40/50/60 (1-2 dias)  
**Status:** 85% pronto → completar 15%  
**Tempo:** 6-7 horas de trabalho focado

---

## ⚡ INÍCIO RÁPIDO (Próximos 5 minutos)

### 1️⃣ Abra os arquivos necessários

```bash
# Terminal - navegue até projeto
cd c:\Users\Gt_Soluções\OneDrive\Desktop\Projetos\PJT-FGTS\ PYTHON\FGTS-PYTHON

# Abra VS Code
code .

# Arquivos que precisa abrir:
# 1. BASE_CONHECIMENTO/frmSEFIP.vb (especificação)
# 2. lancamentos/services/sefip_export.py (código atual)
# 3. lancamentos/tests/test_sefip.py (testes)
```

### 2️⃣ Entenda o que já existe

**Arquivo: lancamentos/services/sefip_export.py**

```python
# VERIFICAR O QUE JÁ EXISTE:
✅ Classe SefipExportService
✅ Método gerar_sefip() - orquestra tudo
✅ gerar_registro_00() - cabeçalho ✅
✅ gerar_registro_10() - empresa ✅
✅ gerar_registro_30() - funcionário ✅
✅ gerar_registro_90() - totalização ✅

# O QUE FALTA:
❌ gerar_registro_40() - remunerações variáveis
❌ gerar_registro_50() - descontos
❌ gerar_registro_60() - contribuições sindicais
```

---

## 🔍 PASSO 1: ENTENDER A ESPECIFICAÇÃO SEFIP

### Arquivo: [BASE_CONHECIMENTO/frmSEFIP.vb](BASE_CONHECIMENTO/frmSEFIP.vb)

**O que fazer:**
1. Abra o arquivo VB6
2. Procure por "Tipo 40", "Tipo 50", "Tipo 60"
3. Anote:
   - Posição de cada campo
   - Tipo de dados (número, texto)
   - Tamanho em caracteres
   - Regras de validação

**Exemplo do VB6 que você deve encontrar:**

```vb
' TIPO 40 - Remunerações Variáveis
' Posição 1-2: "40"
' Posição 3-16: CNPJ (14 dígitos)
' Posição 17-27: PIS (11 dígitos)
' ... mais campos
' Total: 100 caracteres

Function GeraTipo40(lancamento) As String
    Dim linha As String
    linha = "40"  ' Tipo
    linha = linha & Format(empresa.CNPJ, "00000000000000")  ' CNPJ
    linha = linha & Format(funcionario.PIS, "00000000000")   ' PIS
    ' ... continua
    GeraTipo40 = linha
End Function
```

---

## 💻 PASSO 2: IMPLEMENTAR REGISTRO 40

### Local: `lancamentos/services/sefip_export.py`

**Copie este template:**

```python
def gerar_registro_40(self, lancamento: 'Lancamento') -> str:
    """
    Registro 40: Remunerações Variáveis
    
    Campos (posição-tamanho-tipo):
    1-2:    '40' (tipo)
    3-16:   CNPJ empresa (14 dígitos)
    17-27:  PIS funcionário (11 dígitos)
    28-35:  Data (DDMMYYYY)
    36-46:  Valor horas extras (11 dígitos, 2 casas decimais)
    47-57:  Valor adicionais (11 dígitos, 2 casas decimais)
    58-68:  Valor outros (11 dígitos, 2 casas decimais)
    ... (mais campos até 100 chars total)
    """
    
    # Buscar dados do lançamento
    empresa = lancamento.empresa
    funcionario = lancamento.funcionario
    
    # Iniciar linha
    linha = "40"  # Tipo
    
    # CNPJ (14 dígitos)
    cnpj = empresa.cnpj.replace("-", "").replace(".", "")
    linha += cnpj.zfill(14)
    
    # PIS (11 dígitos)
    pis = funcionario.pis.replace("-", "").replace(".", "")
    linha += pis.zfill(11)
    
    # Data (DDMMYYYY)
    data = lancamento.competencia.strftime("%d%m%Y")
    linha += data
    
    # Valores (11 dígitos com 2 casas decimais)
    horas_extras = int(lancamento.horas_extras * 100)  # Converter para centavos
    adicionais = int(lancamento.adicionais * 100)
    outros = int(lancamento.outros_valores * 100)
    
    linha += str(horas_extras).zfill(11)
    linha += str(adicionais).zfill(11)
    linha += str(outros).zfill(11)
    
    # Validar tamanho (deve ser 100 caracteres)
    if len(linha) < 100:
        linha += " " * (100 - len(linha))  # Preencher com espaços
    elif len(linha) > 100:
        linha = linha[:100]  # Truncar se necessário
    
    return linha
```

**Pontos importantes:**
- Remover formatação de números (-, .)
- Usar `zfill()` para preencher com zeros à esquerda
- Validar tamanho final (100 caracteres)
- Comentar o código bem

---

## 💻 PASSO 3: IMPLEMENTAR REGISTRO 50

### Local: Mesmo arquivo

**Padrão similar ao 40:**

```python
def gerar_registro_50(self, lancamento: 'Lancamento') -> str:
    """
    Registro 50: Descontos
    
    Campos:
    1-2:    '50' (tipo)
    3-16:   CNPJ (14 dígitos)
    17-27:  PIS (11 dígitos)
    28-35:  Data (DDMMYYYY)
    36-46:  Desconto INSS (11 dígitos)
    47-57:  Desconto IR (11 dígitos)
    58-68:  Desconto faltas (11 dígitos)
    ... (até 100 chars)
    """
    
    # Usar mesmo padrão de Registro 40
    linha = "50"  # Tipo
    
    # CNPJ, PIS, Data (igual ao 40)
    cnpj = lancamento.empresa.cnpj.replace("-", "").replace(".", "")
    linha += cnpj.zfill(14)
    
    pis = lancamento.funcionario.pis.replace("-", "").replace(".", "")
    linha += pis.zfill(11)
    
    data = lancamento.competencia.strftime("%d%m%Y")
    linha += data
    
    # Descontos
    inss = int(lancamento.desconto_inss * 100)
    ir = int(lancamento.desconto_ir * 100)
    faltas = int(lancamento.desconto_faltas * 100)
    
    linha += str(inss).zfill(11)
    linha += str(ir).zfill(11)
    linha += str(faltas).zfill(11)
    
    # Preencher até 100 caracteres
    if len(linha) < 100:
        linha += " " * (100 - len(linha))
    
    return linha
```

---

## 💻 PASSO 4: IMPLEMENTAR REGISTRO 60

### Local: Mesmo arquivo

**Padrão similar:**

```python
def gerar_registro_60(self, lancamento: 'Lancamento') -> str:
    """
    Registro 60: Contribuições Sindicais
    
    Campos:
    1-2:    '60' (tipo)
    3-16:   CNPJ (14 dígitos)
    17-27:  PIS (11 dígitos)
    28-35:  Data (DDMMYYYY)
    36-46:  Desconto sindical (11 dígitos)
    ... (até 100 chars)
    """
    
    linha = "60"  # Tipo
    
    # CNPJ, PIS, Data
    cnpj = lancamento.empresa.cnpj.replace("-", "").replace(".", "")
    linha += cnpj.zfill(14)
    
    pis = lancamento.funcionario.pis.replace("-", "").replace(".", "")
    linha += pis.zfill(11)
    
    data = lancamento.competencia.strftime("%d%m%Y")
    linha += data
    
    # Desconto sindical
    sindical = int(lancamento.desconto_sindical * 100)
    linha += str(sindical).zfill(11)
    
    # Preencher até 100 caracteres
    if len(linha) < 100:
        linha += " " * (100 - len(linha))
    
    return linha
```

---

## ✅ PASSO 5: INTEGRAR NA FUNÇÃO PRINCIPAL

### Modificar `gerar_sefip()` para incluir novos registros

**Localizar em lancamentos/services/sefip_export.py:**

```python
def gerar_sefip(self, empresa_id: int, competencia: str) -> str:
    """Gera arquivo SEFIP completo"""
    
    linhas = []
    
    # ... código existente ...
    
    # NOVO: Iterar lançamentos e gerar registros 40/50/60
    for lancamento in lancamentos:
        linhas.append(self.gerar_registro_40(lancamento))
        linhas.append(self.gerar_registro_50(lancamento))
        # Só incluir registro 60 se houver desconto sindical
        if lancamento.desconto_sindical > 0:
            linhas.append(self.gerar_registro_60(lancamento))
    
    # ... resto do código ...
    
    return "\n".join(linhas)
```

---

## 🧪 PASSO 6: CRIAR TESTES

### Arquivo: `lancamentos/tests/test_sefip.py`

**Adicione testes para novos registros:**

```python
def test_sefip_registro_40():
    """Testa geração de registro 40"""
    service = SefipExportService()
    lancamento = criar_lancamento_teste(
        horas_extras=100.50,
        adicionais=50.25
    )
    
    linha = service.gerar_registro_40(lancamento)
    
    # Validar formato
    assert linha.startswith("40")
    assert len(linha) == 100
    assert linha[2:16] == empresa.cnpj_formatado
    
def test_sefip_registro_50():
    """Testa geração de registro 50"""
    service = SefipExportService()
    lancamento = criar_lancamento_teste(
        desconto_inss=100.00,
        desconto_ir=50.00
    )
    
    linha = service.gerar_registro_50(lancamento)
    
    assert linha.startswith("50")
    assert len(linha) == 100

def test_sefip_completo():
    """Testa arquivo SEFIP completo com todos registros"""
    service = SefipExportService()
    arquivo = service.gerar_sefip(empresa_id=1, competencia="01/2025")
    
    # Validar presença de registros
    assert "00" in arquivo  # Cabeçalho
    assert "10" in arquivo  # Empresa
    assert "30" in arquivo  # Funcionário
    assert "40" in arquivo  # Variáveis (NOVO)
    assert "50" in arquivo  # Descontos (NOVO)
    assert "90" in arquivo  # Totalização
```

---

## 🧪 PASSO 7: EXECUTAR TESTES

### Terminal:

```bash
# Rodar testes SEFIP
python manage.py test lancamentos.tests.test_sefip -v 2

# Rodar teste específico
python manage.py test lancamentos.tests.test_sefip.SefipTestCase.test_sefip_registro_40 -v 2

# Ver cobertura
coverage run --source='.' manage.py test
coverage report
```

---

## 📊 PASSO 8: VALIDAR ARQUIVO GERADO

### Teste manual:

```bash
# Entrar no shell Django
python manage.py shell

# Testar geração
>>> from lancamentos.services.sefip_export import SefipExportService
>>> service = SefipExportService()
>>> arquivo = service.gerar_sefip(empresa_id=1, competencia="01/2025")
>>> print(arquivo[:200])  # Ver primeiras linhas
>>> len(arquivo.split('\n'))  # Contar linhas
>>> 
>>> # Salvar em arquivo para validar
>>> with open('/tmp/teste_sefip.re', 'w') as f:
...     f.write(arquivo)
>>> 
>>> # Validar cada linha tem 100 caracteres
>>> for i, linha in enumerate(arquivo.split('\n')):
...     if len(linha) != 100:
...         print(f"Linha {i}: {len(linha)} caracteres (ERRO!)")
```

---

## ✅ CHECKLIST DE CONCLUSÃO

**Para considerar SEFIP 100% completo:**

- [ ] Registro 40 implementado e funcionando
- [ ] Registro 50 implementado e funcionando
- [ ] Registro 60 implementado e funcionando
- [ ] Todos testes passando
- [ ] Arquivo .RE gerado válido (100 chars por linha)
- [ ] Nenhuma exceção em produção
- [ ] Documentação atualizada
- [ ] Code review aprovado
- [ ] Deploy validado

---

## 🎯 RESULTADO ESPERADO

Após completar esses passos:

```
✅ SEFIP 100% funcional
✅ Registros 40, 50, 60 gerando corretamente
✅ Arquivo .RE válido para Caixa Econômica
✅ Primeiro bloqueador derrubado
✅ Pronto para legacy import e conferência
✅ Sistema 2 passos mais perto de produção
```

---

## 🚨 SE ALGO DER ERRADO

**Erro 1: AttributeError em horas_extras**
```python
# Solução: Verificar se campo existe no modelo
if hasattr(lancamento, 'horas_extras'):
    valor = lancamento.horas_extras
else:
    valor = 0
```

**Erro 2: Tamanho de linha errado**
```python
# Solução: Debugar
print(f"Tamanho linha: {len(linha)} (esperado 100)")
print(f"Conteúdo: '{linha}'")
```

**Erro 3: Teste falhando**
```python
# Solução: Executar em modo verboso
python manage.py test lancamentos -v 2 --traceback
```

---

## 📞 PRÓXIMOS PASSOS APÓS SEFIP

1. **Amanhã:** Legacy Import Web UI
2. **Amanhã:** Conferência Integration
3. **Próxima semana:** Testes E2E + Deploy

---

**Tempo estimado:** 6-7 horas (pode fazer em 1-2 dias)  
**Complexidade:** ⚡⚡ Média  
**Impacto:** ⭐⭐⭐⭐⭐ MÁXIMO

💡 **Dica:** Comece cedo, trabalhe focado, faça pequenos testes a cada implementação. Não espere fazer tudo de uma vez.

🚀 **Você consegue!** Faltam apenas 3 registros simples. 85% já está pronto!
