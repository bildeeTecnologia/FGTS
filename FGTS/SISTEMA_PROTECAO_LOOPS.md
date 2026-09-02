# 🛡️ Sistema de Proteção Contra Loops Infinitos

## Overview

Implementado sistema robusto de detecção e prevenção de loops infinitos na classe `RelatorioCompetenciaView`. O sistema interrompe o processamento quando detecta comportamentos anormais que podem indicar loops ou recursão excessiva.

## Mecanismos de Proteção

### 1. **Limite de Iterações por Competência**
- **Máximo**: 10 iterações por competência
- **Comportamento**: Se uma mesma competência for processada mais de 10 vezes na mesma requisição, o sistema interrompe com erro
- **Uso**: Previne loops que reprocessam a mesma competência repetidamente
- **Configurável**: `MAX_ITERACOES_POR_COMPETENCIA = 10`

```python
if contador > self.MAX_ITERACOES_POR_COMPETENCIA:
    raise Exception("🛑 LOOP DETECTADO: Competência foi processada 11+ vezes...")
```

### 2. **Timeout Global**
- **Máximo**: 60 segundos por requisição
- **Comportamento**: Se o processamento total exceder 60 segundos, interrompe
- **Uso**: Previne loops infinitos que consomem CPU continuamente
- **Configurável**: `TIMEOUT_GLOBAL_SEGUNDOS = 60`

```python
tempo_decorrido = time.time() - self.tempo_inicio
if tempo_decorrido > self.TIMEOUT_GLOBAL_SEGUNDOS:
    raise Exception("🛑 TIMEOUT: Processamento levou mais de 60s...")
```

### 3. **Avisos Progressivos**
- **Limite de Aviso**: 70% do limite de iterações (7/10)
- **Comportamento**: Log de warning quando aproximando do limite
- **Uso**: Ajuda diagnosticar problemas antes do erro crítico

```
⚠️ AVISO DE LOOP: Competência '01/2024' já foi processada 7 vezes (70% do limite).
```

### 4. **Rastreamento de Competências**
- **Estrutura**: `dict {competencia_str: contador}`
- **Comportamento**: Cada requisição começa com contador zerado (reset automático)
- **Uso**: Cada competência é independente

```python
self.competencias_processadas = {}  # Reset em cada form_valid()
self.tempo_inicio = None            # Reset em cada form_valid()
```

## Fluxo de Execução

```
form_valid() início
  ↓
Reset de contadores (tempo_inicio=None, competencias_processadas={})
  ↓
Try: Processar competências
  ├─ Para cada competência:
  │   ├─ Chamar _verificar_loop(competencia_str)
  │   │   ├─ Verificar timeout global
  │   │   ├─ Incrementar contador da competência
  │   │   ├─ Verificar se excedeu limite
  │   │   └─ Log de aviso se aproximando do limite
  │   └─ Chamar _compute_for(...)
  │
  └─ Retornar resultados com avisos
  
Except: Capturar exceções de loop
  ↓
Retornar erro na interface com mensagem clara
```

## Exemplos de Comportamento

### Cenário 1: Processamento Normal
```
Competência 01/2024 → contador=1 ✓
Competência 02/2024 → contador=1 ✓
Competência 03/2024 → contador=1 ✓
→ Resultado: OK
```

### Cenário 2: Loop Detectado
```
Competência 01/2024 → contador=1 ✓
Competência 01/2024 → contador=2 ✓ (aviso 70%)
Competência 01/2024 → contador=3 ✓
Competência 01/2024 → contador=4 ✓
Competência 01/2024 → contador=5 ✓
Competência 01/2024 → contador=6 ✓
Competência 01/2024 → contador=7 ✓ ⚠️ AVISO
Competência 01/2024 → contador=8 ✓
Competência 01/2024 → contador=9 ✓
Competência 01/2024 → contador=10 ✓
Competência 01/2024 → contador=11 ✗ 🛑 EXCEÇÃO
→ Resultado: "🛑 LOOP DETECTADO: Competência foi processada 11 vezes..."
```

### Cenário 3: Timeout
```
Competência 01/2024 → 5s ✓
Competência 02/2024 → 15s ✓
Competência 03/2024 → 25s ✓
Competência 04/2024 → 35s ✓
Competência 05/2024 → 45s ✓
Competência 06/2024 → 55s ✓
Competência 07/2024 → 65s ✗ 🛑 EXCEÇÃO
→ Resultado: "🛑 TIMEOUT: Processamento levou mais de 60s..."
```

## Tratamento de Erros

Todos os erros de loop são capturados no `except` do `form_valid()`:

```python
except Exception as e:
    logger.error(f"🛑 Erro em RelatorioCompetenciaView.form_valid: {str(e)}")
    return render(self.request, self.template_name, {
        'form': form,
        'erro': f"🛑 Erro ao processar relatório: {str(e)}"
    })
```

**Resultado na interface**:
```
🛑 Erro ao processar relatório: 🛑 LOOP DETECTADO: Competência 01/2024 foi processada 11 vezes...
```

## Configurações

Para ajustar os limites, edite `lancamentos/views.py`:

```python
class RelatorioCompetenciaView(LoginRequiredMixin, FormView):
    # Aumentar limite de iterações para 20
    MAX_ITERACOES_POR_COMPETENCIA = 20
    
    # Aumentar timeout para 120 segundos
    TIMEOUT_GLOBAL_SEGUNDOS = 120
```

## Logs de Monitoramento

O sistema registra eventos importantes:

```
INFO  [ÍNDICE FGTS] Buscando índice EXATO: competencia=2024-01-01...
WARNING ⚠️ AVISO DE LOOP: Competência 01/2024 já foi processada 7 vezes (70% do limite)
ERROR 🛑 Erro em RelatorioCompetenciaView.form_valid: 🛑 LOOP DETECTADO...
```

Visualize os logs com:
```bash
tail -f logs/django.log | grep "LOOP\|TIMEOUT\|AVISO"
```

## Testes Recomendados

### Teste 1: Verificar Reset Entre Requisições
```python
# Requisição 1: Processar 01/2024 e 02/2024
# Esperado: Ambas com contador=1

# Requisição 2: Processar 01/2024 novamente
# Esperado: contador resetado para 1 (não 3)
```

### Teste 2: Verificar Aviso em 70%
```python
# Forçar processamento 7 vezes da mesma competência
# Esperado: ⚠️ AVISO após 7ª iteração
```

### Teste 3: Verificar Timeout
```python
# Criar competências que levem 15s cada
# Processar 5+ competências (75s total)
# Esperado: Timeout em ~60s
```

## Troubleshooting

### Problema: "LOOP DETECTADO" mesmo com processamento normal
- **Causa**: Possível recursão inesperada em `_compute_for()`
- **Solução**: Adicionar logs em `_compute_for()` para diagnosticar

### Problema: Timeout acionado prematuramente
- **Causa**: Processamento muito lento (BD, rede, etc)
- **Solução**: Aumentar `TIMEOUT_GLOBAL_SEGUNDOS`

### Problema: Sem avisos antes do erro
- **Causa**: Contador já acima de 70% quando ativado
- **Solução**: Aumentar `MAX_ITERACOES_POR_COMPETENCIA` ou revisar lógica

## Integração com Sistema de Avisos

Os erros de loop são capturados como mensagens de erro contextualizadas e exibidos na interface HTML:

```html
<!-- relatorio_competencia.html -->
{% if avisos %}
  <div class="alert alert-warning">
    <strong>Avisos durante o processamento:</strong>
    <ul>
      {% for aviso in avisos %}
        <li>{{ aviso }}</li>
      {% endfor %}
    </ul>
  </div>
{% endif %}
```

Erros bloqueadores aparecem como:
```html
{% if erro %}
  <div class="alert alert-danger">{{ erro }}</div>
{% endif %}
```

## Próximos Passos

1. ✅ Implementado detector de loop
2. ⏳ Monitorar logs por 24h
3. ⏳ Ajustar limites conforme necessário
4. ⏳ Implementar alertas automáticos se acionado > 1x/dia
