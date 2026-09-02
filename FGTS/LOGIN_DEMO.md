# 🎯 Login Demo para Clientes

Este sistema permite criar um usuário de demonstração com dados completos para que clientes possam testar o FGTS Web antes de contratar.

## 📋 O que inclui o Demo?

- **Usuário Demo** - Acesso completo ao sistema
- **Empresa Demo** - Empresa fictícia com dados realistas
- **5 Colaboradores** - Funcionários para teste
- **Lançamentos FGTS** - 6 meses de dados de exemplo
- **Plano Profissional** - Ativo por padrão

## 🚀 Como Criar o Login Demo

### Opção 1: Usando Management Command (Recomendado)

```bash
# Ativar virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\Activate.ps1  # Windows

# Criar demo
python manage.py create_demo_user

# Para resetar dados demo anteriores
python manage.py create_demo_user --reset
```

### Opção 2: Usando Script Direto

```bash
python scripts/criar_usuario_demo.py
```

## 📝 Credenciais Demo

Após criar o demo, use estas credenciais:

```
URL: http://localhost:8000
Usuário: demo
Senha: demo123456
Email: demo@fgtsweb.com
```

## 👥 Dados Demo Inclusos

### Empresa
- **Nome**: Empresa Demo LTDA
- **CNPJ**: 12.345.678/0001-99
- **Cidade**: São Paulo, SP
- **Contato**: João Silva

### Colaboradores Demo
1. Maria Silva (CPF: 123.456.789-00)
2. Carlos Santos (CPF: 234.567.890-11)
3. Ana Oliveira (CPF: 345.678.901-22)
4. Pedro Costa (CPF: 456.789.012-33)
5. Fernanda Lima (CPF: 567.890.123-44)

### Lançamentos
- 6 meses de lançamentos FGTS
- Valores aleatórios entre R$ 80 e R$ 300
- Alguns com multa e juros

## 💡 Como Usar com Clientes

1. **Envie as credenciais** do demo para o cliente
2. **O cliente acessa** http://seu-dominio.com e faz login
3. **Explora o sistema** com dados realistas
4. **Pode criar uma empresa real** depois se gostar

## 🔒 Segurança

- Demo é apenas para demonstração
- Use um domínio diferente ou crie subdomain para "demo.seusistema.com"
- Mude a senha regularmente
- Limpe dados demo antes de usar em produção

## 🛠️ Personalizações

Você pode editar o arquivo `usuarios/management/commands/create_demo_user.py` para:

- Mudar nomes de colaboradores
- Adicionar mais lançamentos
- Criar múltiplas empresas demo
- Alterar valores monetários
- Incluir dados de outros módulos

## 📊 Exemplo de Uso

```bash
# Criar demo inicial
python manage.py create_demo_user

# Depois de um tempo, resetar dados
python manage.py create_demo_user --reset

# Agora o cliente vê dados "frescos"
```

## ❓ FAQ

**P: O cliente pode excluir dados demo?**
R: Sim, ele tem acesso total. Você pode resetar com `--reset` quando precisar.

**P: E se quiser mais de um demo?**
R: Edite o comando para criar múltiplos usuários (demo2, demo3, etc).

**P: Os dados demo aparecem para todos?**
R: Não, é multi-tenant. Cada usuário demo vê apenas sua empresa.

**P: Posso testar todos os recursos?**
R: Sim! O plano Profissional tem todos os recursos principais ativados.
