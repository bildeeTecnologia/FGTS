from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from io import StringIO
from empresas.models import Empresa
from funcionarios.models import Funcionario
from lancamentos.models import Lancamento
from lancamentos.forms import LegacyImportForm
import csv


class LegacyImportFormTest(TestCase):
    """Testes para o formulário de importação legada"""
    
    def setUp(self):
        """Prepara dados de teste"""
        self.empresa = Empresa.objects.create(
            nome='Empresa Teste Ltda',
            cnpj='12345678000195'
        )
    
    def test_form_valid_funcionarios(self):
        """Testa validação do formulário para importar funcionários"""
        # Cria arquivo CSV simulado
        csv_content = StringIO()
        csv_writer = csv.DictWriter(csv_content, fieldnames=['pis', 'nome', 'data_admissao', 'cpf'])
        csv_writer.writeheader()
        csv_writer.writerow({
            'pis': '12345678901',
            'nome': 'João da Silva',
            'data_admissao': '01/01/2020',
            'cpf': '12345678901'
        })
        
        csv_file = SimpleUploadedFile(
            'test.csv',
            csv_content.getvalue().encode('latin1'),
            content_type='text/csv'
        )
        
        form_data = {
            'csv_file': csv_file,
            'import_type': 'funcionarios',
            'empresa': self.empresa.id,
            'skip_duplicates': True
        }
        
        form = LegacyImportForm(data=form_data, files={'csv_file': csv_file}, user=None)
        self.assertTrue(form.is_valid())
    
    def test_form_empresa_required_for_funcionarios(self):
        """Testa que empresa é obrigatória para importar funcionários"""
        csv_content = StringIO()
        csv_writer = csv.DictWriter(csv_content, fieldnames=['pis', 'nome', 'data_admissao'])
        csv_writer.writeheader()
        csv_writer.writerow({
            'pis': '12345678901',
            'nome': 'João da Silva',
            'data_admissao': '01/01/2020'
        })
        
        csv_file = SimpleUploadedFile(
            'test.csv',
            csv_content.getvalue().encode('latin1'),
            content_type='text/csv'
        )
        
        form_data = {
            'csv_file': csv_file,
            'import_type': 'funcionarios',
            'skip_duplicates': True
        }
        
        form = LegacyImportForm(data=form_data, files={'csv_file': csv_file}, user=None)
        self.assertFalse(form.is_valid())
        self.assertIn('Empresa é obrigatória', str(form.errors))
    
    def test_form_invalid_file_extension(self):
        """Testa validação de extensão de arquivo"""
        invalid_file = SimpleUploadedFile(
            'test.txt',
            b'content',
            content_type='text/plain'
        )
        
        form_data = {
            'csv_file': invalid_file,
            'import_type': 'empresas',
            'skip_duplicates': True
        }
        
        form = LegacyImportForm(data=form_data, files={'csv_file': invalid_file}, user=None)
        self.assertFalse(form.is_valid())
    
    def test_form_file_size_limit(self):
        """Testa limite de tamanho de arquivo"""
        # Cria arquivo maior que 20MB
        large_content = b'x' * (21 * 1024 * 1024)
        
        large_file = SimpleUploadedFile(
            'large.csv',
            large_content,
            content_type='text/csv'
        )
        
        form_data = {
            'csv_file': large_file,
            'import_type': 'empresas',
            'skip_duplicates': True
        }
        
        form = LegacyImportForm(data=form_data, files={'csv_file': large_file}, user=None)
        self.assertFalse(form.is_valid())


class LegacyImportViewTest(TestCase):
    """Testes para a view de importação legada"""
    
    def setUp(self):
        """Prepara dados de teste"""
        self.client = Client()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.empresa = Empresa.objects.create(
            nome='Empresa Teste Ltda',
            cnpj='12345678000195'
        )
    
    def test_legacy_import_view_requires_login(self):
        """Testa que view de importação legada requer login"""
        response = self.client.get(reverse('legacy-import'))
        self.assertEqual(response.status_code, 302)  # Redireciona para login
        self.assertIn('/login/', response.url)
    
    def test_legacy_import_view_get(self):
        """Testa acesso à página de importação legada"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('legacy-import'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lancamentos/legacy_import.html')
        self.assertIn('form', response.context)
    
    def test_legacy_import_result_requires_login(self):
        """Testa que view de resultado requer login"""
        response = self.client.get(reverse('legacy-import-result'))
        self.assertEqual(response.status_code, 302)
    
    def test_legacy_import_result_redirect_without_session(self):
        """Testa redirecionamento quando não há resultado anterior"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('legacy-import-result'))
        
        # Deve redirecionar para legacy-import
        self.assertEqual(response.status_code, 302)
        self.assertIn('legacy-import', response.url)


class LegacyImportIntegrationTest(TestCase):
    """Testes de integração para importação legada"""
    
    def setUp(self):
        """Prepara dados de teste"""
        self.empresa = Empresa.objects.create(
            nome='Empresa Teste Ltda',
            cnpj='12345678000195'
        )
    
    def test_import_empresas_csv(self):
        """Testa importação de empresas a partir de CSV"""
        from lancamentos.services.legacy_importer import LegacyDataImporter
        import tempfile
        
        # Cria arquivo CSV temporário
        csv_content = """cnpj,razao_social,endereco
12345678000195,Empresa Teste Ltda,Rua das Flores 123
98765432000100,Outra Empresa Ltda,Avenida Principal 456
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', encoding='latin1', delete=False) as f:
            f.write(csv_content)
            f.flush()
            
            importer = LegacyDataImporter()
            criados, erros = importer.importar_empresas(f.name)
            
            # Valida resultado
            self.assertGreater(criados, 0)
            self.assertIsInstance(erros, list)
    
    def test_import_funcionarios_csv(self):
        """Testa importação de funcionários a partir de CSV"""
        from lancamentos.services.legacy_importer import LegacyDataImporter
        import tempfile
        
        csv_content = """pis,nome,data_admissao,cpf
12345678901,João da Silva,01/01/2020,12345678901
98765432109,Maria Santos,15/02/2021,98765432109
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', encoding='latin1', delete=False) as f:
            f.write(csv_content)
            f.flush()
            
            importer = LegacyDataImporter()
            criados, erros = importer.importar_funcionarios(f.name, empresa_id=self.empresa.id)
            
            self.assertIsInstance(criados, int)
            self.assertIsInstance(erros, list)
    
    def test_import_lancamentos_csv(self):
        """Testa importação de lançamentos a partir de CSV"""
        from lancamentos.services.legacy_importer import LegacyDataImporter
        import tempfile
        
        # Cria funcionário primeiro
        Funcionario.objects.create(
            pis='12345678901',
            nome='João da Silva',
            empresa=self.empresa,
            data_admissao='2020-01-01'
        )
        
        csv_content = """pis,competencia,base_fgts,data_pagto
12345678901,01/2025,5000.00,15/01/2025
12345678901,02/2025,5100.00,15/02/2025
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', encoding='latin1', delete=False) as f:
            f.write(csv_content)
            f.flush()
            
            importer = LegacyDataImporter()
            criados, erros = importer.importar_lancamentos(f.name, empresa_id=self.empresa.id)
            
            self.assertIsInstance(criados, int)
            self.assertIsInstance(erros, list)
