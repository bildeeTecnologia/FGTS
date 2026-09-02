"""
Management command para criar usuário e dados de demonstração.

Uso:
    python manage.py create_demo_user
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date, timedelta
from decimal import Decimal
from random import randint

from usuarios.models import Usuario
from empresas.models import Empresa
from funcionarios.models import Funcionario
from lancamentos.models import Lancamento
from billing.models import BillingCustomer, Plan


class Command(BaseCommand):
    help = 'Cria usuário demo com empresa, colaboradores e lançamentos de exemplo'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Apaga dados demo existentes antes de criar novos',
        )
    
    @transaction.atomic
    def handle(self, *args, **options):
        reset = options.get('reset', False)
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('🎯 CRIANDO USUÁRIO E DADOS DE DEMONSTRAÇÃO'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
        
        # 1. Criar usuário demo
        self.criar_usuario_demo(reset)
        
        # 2. Criar empresa demo
        usuario = Usuario.objects.get(username='demo')
        empresa = self.criar_empresa_demo(usuario, reset)
        
        # 3. Associar plano
        self.criar_plano_demo(empresa)
        
        # 4. Criar funcionários
        funcionarios = self.criar_funcionarios_demo(empresa, reset)
        
        # 5. Criar lançamentos
        self.criar_lancamentos_demo(empresa, funcionarios, reset)
        
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('✅ CONFIGURAÇÃO COMPLETA!'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        self.stdout.write('\n📝 Credenciais de Acesso Demo:')
        self.stdout.write('   URL: http://localhost:8000')
        self.stdout.write('   Usuário: demo')
        self.stdout.write('   Senha: demo123456')
        self.stdout.write('\n💡 Dica: Compartilhe estas credenciais com clientes interessados')
        self.stdout.write('   para que possam testar o sistema antes de contratar!\n')
    
    def criar_usuario_demo(self, reset=False):
        """Cria o usuário demo"""
        username = "demo"
        email = "demo@fgtsweb.com"
        password = "demo123456"
        
        if reset and Usuario.objects.filter(username=username).exists():
            Usuario.objects.filter(username=username).delete()
            self.stdout.write(self.style.WARNING('🗑️  Usuário demo anterior removido'))
        
        usuario, created = Usuario.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': 'Cliente',
                'last_name': 'Demo',
                'is_active': True,
            }
        )
        
        if created:
            usuario.set_password(password)
            usuario.save()
            self.stdout.write(self.style.SUCCESS('✅ Usuário Demo criado!'))
            self.stdout.write(f'   Usuário: {username}')
            self.stdout.write(f'   Senha: {password}')
            self.stdout.write(f'   Email: {email}\n')
        else:
            self.stdout.write(self.style.WARNING('⚠️  Usuário demo já existe!\n'))
    
    def criar_empresa_demo(self, usuario, reset=False):
        """Cria empresa demo com dados realistas"""
        cnpj = '12.345.678/0001-99'
        
        if reset and Empresa.objects.filter(cnpj=cnpj).exists():
            Empresa.objects.filter(cnpj=cnpj).delete()
            self.stdout.write(self.style.WARNING('🗑️  Empresa demo anterior removida'))
        
        empresa, created = Empresa.objects.get_or_create(
            cnpj=cnpj,
            defaults={
                'nome': 'Empresa Demo LTDA',
                'nome_contato': 'João Silva',
                'email': 'contato@empresademo.com.br',
                'fone_contato': '(11) 98765-4321',
                'cep': '01310-100',
                'endereco': 'Avenida Paulista',
                'numero': '1000',
                'bairro': 'Bela Vista',
                'cidade': 'São Paulo',
                'uf': 'SP',
            }
        )
        
        if created:
            empresa.usuarios.add(usuario)
            self.stdout.write(self.style.SUCCESS('✅ Empresa Demo criada!'))
            self.stdout.write(f'   Nome: {empresa.nome}')
            self.stdout.write(f'   CNPJ: {empresa.cnpj}')
            self.stdout.write(f'   Contato: {empresa.nome_contato}')
            self.stdout.write(f'   Email: {empresa.email}\n')
        else:
            # Garantir que o usuário está associado
            if usuario not in empresa.usuarios.all():
                empresa.usuarios.add(usuario)
            self.stdout.write(self.style.WARNING('⚠️  Empresa demo já existe!\n'))
        
        return empresa
    
    def criar_plano_demo(self, empresa):
        """Associa um plano demo à empresa"""
        # Buscar plano Profissional (o mais popular)
        plano = Plan.objects.filter(plan_type='PROFESSIONAL', active=True).first()
        
        if not plano:
            # Se não existir, pegar qualquer plano ativo
            plano = Plan.objects.filter(active=True).first()
        
        if not plano:
            self.stdout.write(self.style.WARNING('⚠️  Nenhum plano disponível para associar!\n'))
            return None
        
        billing, created = BillingCustomer.objects.get_or_create(
            empresa=empresa,
            defaults={
                'plan': plano,
                'email_cobranca': empresa.email,
                'status': 'active',
                'asaas_customer_id': 'demo-customer-id',
            }
        )
        
        if created or not billing.plan:
            if not billing.plan:
                billing.plan = plano
            billing.status = 'active'
            billing.save()
            self.stdout.write(self.style.SUCCESS('✅ Plano associado à empresa!'))
            self.stdout.write(f'   Plano: {plano.get_plan_type_display()}')
            self.stdout.write(f'   Valor: R$ {plano.price_monthly}/mês\n')
    
    def criar_funcionarios_demo(self, empresa, reset=False):
        """Cria 5 funcionários demo com dados realistas"""
        if reset:
            Funcionario.objects.filter(empresa=empresa).delete()
            self.stdout.write(self.style.WARNING('🗑️  Funcionários anteriores removidos'))
        
        nomes_funcionarios = [
            {'nome': 'Maria Silva', 'cpf': '123.456.789-00'},
            {'nome': 'Carlos Santos', 'cpf': '234.567.890-11'},
            {'nome': 'Ana Oliveira', 'cpf': '345.678.901-22'},
            {'nome': 'Pedro Costa', 'cpf': '456.789.012-33'},
            {'nome': 'Fernanda Lima', 'cpf': '567.890.123-44'},
        ]
        
        funcionarios_criados = []
        for info in nomes_funcionarios:
            func, created = Funcionario.objects.get_or_create(
                empresa=empresa,
                cpf=info['cpf'],
                defaults={
                    'nome': info['nome'],
                    'pis': f'10000000{randint(1000, 9999)}',
                    'data_admissao': date(2022, 1, 15),
                }
            )
            if created:
                funcionarios_criados.append(func)
        
        if funcionarios_criados:
            self.stdout.write(self.style.SUCCESS(f'✅ {len(funcionarios_criados)} colaboradores criados!'))
            for func in funcionarios_criados:
                self.stdout.write(f'   - {func.nome} (CPF: {func.cpf})')
            self.stdout.write('')
        else:
            self.stdout.write(self.style.WARNING('⚠️  Colaboradores demo já existem!\n'))
        
        return Funcionario.objects.filter(empresa=empresa)
    
    def criar_lancamentos_demo(self, empresa, funcionarios, reset=False):
        """Cria lançamentos FGTS demo dos últimos 6 meses"""
        if reset:
            Lancamento.objects.filter(empresa=empresa).delete()
            self.stdout.write(self.style.WARNING('🗑️  Lançamentos anteriores removidos'))
        
        if not funcionarios.exists():
            self.stdout.write(self.style.WARNING('⚠️  Nenhum funcionário disponível para criar lançamentos!\n'))
            return
        
        mes_atual = date.today()
        meses = 6
        lancamentos_criados = 0
        
        for i in range(meses):
            data_lancamento = mes_atual - timedelta(days=30 * i)
            ano_mes = data_lancamento.strftime('%Y%m')
            
            for funcionario in funcionarios[:3]:  # Lançamentos para os 3 primeiros
                lancamento, created = Lancamento.objects.get_or_create(
                    empresa=empresa,
                    funcionario=funcionario,
                    ano_mes=ano_mes,
                    defaults={
                        'data_lancamento': data_lancamento,
                        'valor_fgts': Decimal(str(randint(80, 200))),
                        'valor_multa': Decimal(str(randint(10, 40))),
                        'valor_juros': Decimal(str(randint(5, 20))),
                        'pago': False,
                        'data_pagamento': None,
                    }
                )
                if created:
                    lancamentos_criados += 1
        
        if lancamentos_criados > 0:
            self.stdout.write(self.style.SUCCESS(f'✅ {lancamentos_criados} lançamentos demo criados!'))
            self.stdout.write(f'   Período: últimos 6 meses\n')
        else:
            self.stdout.write(self.style.WARNING('⚠️  Lançamentos demo já existem!\n'))
