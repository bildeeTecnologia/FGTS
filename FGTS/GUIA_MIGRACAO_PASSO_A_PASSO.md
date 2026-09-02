# 🚀 GUIA PASSO A PASSO - MIGRAÇÃO COMPLETA PARA PRODUÇÃO

## 📦 Arquivos Criados

- ✅ [backup_producao.sh](backup_producao.sh) - Backup do SQLite atual
- ✅ [.env.production](.env.production) - Variáveis de ambiente
- ✅ [migracao_completa.sh](migracao_completa.sh) - Script de migração
- ✅ [verificacao_pos_deploy.sh](verificacao_pos_deploy.sh) - Verificação final
- ✅ [CORRECAO_PRODUCAO_URGENTE.md](CORRECAO_PRODUCAO_URGENTE.md) - Troubleshooting

---

## 🎯 PASSO A PASSO

### ⏱️ Tempo total estimado: 20-30 minutos

---

### 📍 PASSO 1: Backup do Banco Atual (5 min)

**No terminal do Coolify:**

```bash
bash backup_producao.sh
```

**Ou execute manualmente:**

```bash
python manage.py dumpdata \
  --natural-foreign \
  --natural-primary \
  -e contenttypes \
  -e auth.Permission \
  --indent 2 \
  > backup_producao_$(date +%Y%m%d_%H%M%S).json
```

✅ **Download o arquivo JSON gerado** antes de continuar!

---

### 📍 PASSO 2: Configurar Variáveis no Coolify (5-10 min)

1. **Acesse o painel do Coolify**
2. **Vá em:** Projeto FGTS Web → **Environment Variables**
3. **Adicione cada variável** do arquivo [.env.production](.env.production)

**Variáveis obrigatórias:**

```env
SUPABASE_HOST=db.qbyipfcyqnaptstidphj.supabase.co
SUPABASE_DB=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=your-supabase-password
SUPABASE_PORT=6543
DJANGO_DEBUG=False
```

⚠️ **IMPORTANTE:** Gere uma SECRET_KEY forte:

```bash
# Execute localmente:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

4. **Salve** todas as variáveis
5. **Reinicie** o container no Coolify

---

### 📍 PASSO 3: Executar Migração Completa (10 min)

**No terminal do Coolify (após reiniciar):**

```bash
bash migracao_completa.sh
```

**O script irá:**
- ✅ Verificar variáveis de ambiente
- ✅ Testar conexão com Supabase
- ✅ Aplicar todas as migrações
- ✅ Verificar estrutura das tabelas
- ✅ Importar dados do backup (se encontrar)
- ✅ Validar a migração

---

### 📍 PASSO 4: Verificação Final (5 min)

**No terminal do Coolify:**

```bash
bash verificacao_pos_deploy.sh
```

**O script verifica:**
- ✅ Conexão com banco
- ✅ Status das migrações
- ✅ Estrutura das tabelas
- ✅ Modelos Django
- ✅ Variáveis de ambiente
- ✅ Arquivos estáticos
- ✅ System check
- ✅ URLs principais

---

### 📍 PASSO 5: Teste Manual

**Acesse:** http://fgts.bildee.com.br

1. **Registrar novo usuário:** `/usuario/registrar/`
   - ✅ Deve funcionar sem erro `empresa_id`

2. **Fazer login:** `/usuario/login/`
   - ✅ Deve autenticar corretamente

3. **Criar empresa:** `/empresas/criar/`
   - ✅ Deve salvar no Supabase

4. **Adicionar funcionário**
   - ✅ Deve vincular à empresa

5. **Registrar lançamento**
   - ✅ Deve salvar corretamente

---

## ✅ CHECKLIST DE VERIFICAÇÃO

### Antes de começar:
- [ ] Acesso ao painel do Coolify
- [ ] Acesso ao terminal do container
- [ ] Credenciais do Supabase confirmadas
- [ ] Backup local dos dados importantes

### Durante o processo:
- [ ] Backup do SQLite criado e baixado
- [ ] Variáveis de ambiente configuradas no Coolify
- [ ] Container reiniciado após configurar variáveis
- [ ] Script de migração executado sem erros
- [ ] Script de verificação passou em todos os testes

### Após concluir:
- [ ] Registro de usuário funcionando
- [ ] Login funcionando
- [ ] Empresas sendo salvas no Supabase
- [ ] Funcionários vinculados corretamente
- [ ] Lançamentos salvos corretamente
- [ ] Sem erros nos logs do Coolify

---

## 🆘 TROUBLESHOOTING RÁPIDO

### ❌ Erro: "table usuarios_usuario has no column named empresa_id"

**Solução:**
```bash
python manage.py migrate usuarios
```

### ❌ Erro: "Connection timed out" ao conectar Supabase

**Solução:**
1. Verifique se a porta é **6543** (não 5432)
2. Teste conexão: `nc -zv db.qbyipfcyqnaptstidphj.supabase.co 6543`
3. Verifique firewall do servidor

### ❌ Ainda usando SQLite após configurar variáveis

**Solução:**
1. Verifique se as variáveis foram salvas corretamente
2. Reinicie o container
3. Verifique logs: deve aparecer "PostgreSQL"
4. Execute: `python -c "from django.conf import settings; print(settings.DATABASES['default'])"`

### ❌ Erro: "FATAL: no such user"

**Solução:**
- Usuário deve ser apenas `postgres` (sem sufixo `.qbyipfcyqnaptstidphj`)
- Porta deve ser `6543`

### ❌ Erro ao importar backup

**Solução:**
1. Verifique se o arquivo JSON existe
2. Execute manualmente: `python manage.py loaddata backup_producao_TIMESTAMP.json`
3. Se persistir, importe por partes:
   ```bash
   python manage.py loaddata backup_producao.json --app empresas
   python manage.py loaddata backup_producao.json --app usuarios
   ```

---

## 📊 COMPARAÇÃO: ANTES vs DEPOIS

### ❌ ANTES (Problema)
```
✗ SQLite em produção
✗ Migrações não aplicadas
✗ Erro ao criar usuários
✗ Coluna empresa_id faltando
✗ Dados não sincronizados
```

### ✅ DEPOIS (Solução)
```
✓ PostgreSQL/Supabase em produção
✓ Todas as migrações aplicadas
✓ Registro de usuários funcionando
✓ Estrutura de tabelas completa
✓ Dados sincronizados e seguros
✓ Pronto para escalar
```

---

## 📞 SUPORTE

Se algo der errado:

1. **Verifique os logs:** Coolify → Logs
2. **Execute verificação:** `bash verificacao_pos_deploy.sh`
3. **Consulte:** [CORRECAO_PRODUCAO_URGENTE.md](CORRECAO_PRODUCAO_URGENTE.md)
4. **Teste conexão local:** Use as mesmas credenciais localmente

---

## 🎯 PRÓXIMOS PASSOS (Opcional)

Após estabilizar:

- [ ] Configurar domínio personalizado
- [ ] Habilitar SSL/HTTPS (Let's Encrypt)
- [ ] Configurar backup automático do Supabase
- [ ] Implementar monitoramento (Sentry, etc)
- [ ] Configurar CI/CD para deploys automáticos
- [ ] Revisar SECRET_KEY e credenciais sensíveis
- [ ] Configurar CORS se houver frontend separado
- [ ] Otimizar queries e índices no Supabase

---

## 📈 COMANDOS ÚTEIS

### Ver logs em tempo real:
```bash
# No Coolify, aba "Logs"
# Ou via terminal:
tail -f /var/log/django.log
```

### Verificar conexão ativa:
```bash
python manage.py dbshell
SELECT current_database(), current_user, version();
\q
```

### Listar tabelas:
```bash
python manage.py dbshell
\dt
\q
```

### Contar registros:
```bash
python manage.py shell
from usuarios.models import Usuario
print(Usuario.objects.count())
exit()
```

### Fazer backup incremental:
```bash
python manage.py dumpdata --natural-foreign --natural-primary \
  usuarios empresas funcionarios lancamentos \
  > backup_incremental_$(date +%Y%m%d).json
```

---

## ✅ CONCLUSÃO

Seguindo este guia, você terá:

1. ✅ Backup seguro dos dados atuais
2. ✅ Supabase configurado e conectado
3. ✅ Todas as migrações aplicadas
4. ✅ Dados migrados (se havia)
5. ✅ Sistema validado e funcionando
6. ✅ Produção estável e escalável

**Tempo total:** 20-30 minutos  
**Dificuldade:** Média  
**Risco:** Baixo (com backup)  

---

**Boa sorte! 🚀**
