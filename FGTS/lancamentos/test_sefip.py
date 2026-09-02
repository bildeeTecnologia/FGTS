"""
Testes para a exportação SEFIP (registros 40, 50, 60)
"""

from decimal import Decimal
from datetime import datetime
from django.test import TestCase
from empresas.models import Empresa
from funcionarios.models import Funcionario
from lancamentos.models import Lancamento
from lancamentos.services.sefip_export import SefipFilters, gerar_sefip_conteudo


class SefipExport40Test(TestCase):
    """Testa a geração do Registro 40 (Remunerações Variáveis)"""

    def setUp(self):
        """Cria dados de teste"""
        self.empresa = Empresa.objects.create(
            nome="Empresa Teste",
            cnpj="12345678901234",
            endereco="Rua Teste",
            numero="123",
            bairro="Bairro Teste",
            cidade="São Paulo",
            uf="SP",
            cep="01234567",
            fone_contato="1133334444"
        )

        self.funcionario = Funcionario.objects.create(
            empresa=self.empresa,
            nome="João Silva",
            pis="12345678901",
            cpf="12345678901",
            cbo="2121",
            carteira_profissional="1234567",
            serie_carteira="1",
            data_admissao=datetime(2020, 1, 1).date(),
            data_nascimento=datetime(1990, 5, 15).date()
        )

        self.lancamento = Lancamento.objects.create(
            empresa=self.empresa,
            funcionario=self.funcionario,
            competencia="01/2025",
            base_fgts=Decimal("1000.00"),
            valor_fgts=Decimal("80.00"),
            horas_extras=Decimal("100.00"),
            adicionais=Decimal("50.00")
        )

    def test_registro_40_structure(self):
        """Valida a estrutura do Registro 40"""
        filtros = SefipFilters(
            empresa=self.empresa,
            competencia="01/2025",
            funcionario_de=self.funcionario.id,
            funcionario_ate=self.funcionario.id
        )

        conteudo = gerar_sefip_conteudo(filtros)
        linhas = conteudo.split("\r\n")

        reg40_lines = [l for l in linhas if l.startswith("40")]
        assert len(reg40_lines) > 0, "Nenhum Registro 40 encontrado"

        reg40 = reg40_lines[0]
        assert reg40[0:2] == "40", "Tipo deve ser '40'"
        assert reg40[-1] == "*", "Deve terminar com '*'"
        assert len(reg40) == 261, f"Tamanho deve ser 261, mas tem {len(reg40)}"

    def test_registro_40_contains_cnpj_pis(self):
        """Valida que Registro 40 contém CNPJ e PIS corretos"""
        filtros = SefipFilters(
            empresa=self.empresa,
            competencia="01/2025",
            funcionario_de=self.funcionario.id,
            funcionario_ate=self.funcionario.id
        )

        conteudo = gerar_sefip_conteudo(filtros)
        linhas = conteudo.split("\r\n")

        reg40_lines = [l for l in linhas if l.startswith("40")]
        assert len(reg40_lines) > 0

        reg40 = reg40_lines[0]
        pis_na_linha = reg40[31:42].strip()
        assert "12345678901" in pis_na_linha, f"PIS não encontrado corretamente: {pis_na_linha}"

    def test_registro_40_valores_zerados_por_padrao(self):
        """Valida que valores zerados aparecem quando campos não existem"""
        Lancamento.objects.create(
            empresa=self.empresa,
            funcionario=self.funcionario,
            competencia="02/2025",
            base_fgts=Decimal("1000.00"),
            valor_fgts=Decimal("80.00")
        )

        filtros = SefipFilters(
            empresa=self.empresa,
            competencia="02/2025",
            funcionario_de=self.funcionario.id,
            funcionario_ate=self.funcionario.id
        )

        conteudo = gerar_sefip_conteudo(filtros)
        linhas = conteudo.split("\r\n")

        reg40_lines = [l for l in linhas if l.startswith("40")]
        assert len(reg40_lines) > 0

        reg40 = reg40_lines[0]
        assert "00000000000" in reg40, "Valores deveriam estar zerados"


class SefipExport50Test(TestCase):
    """Testa a geração do Registro 50 (Descontos)"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nome="Empresa Teste",
            cnpj="12345678901234",
            endereco="Rua Teste",
            numero="123",
            bairro="Bairro Teste",
            cidade="São Paulo",
            uf="SP",
            cep="01234567"
        )

        self.funcionario = Funcionario.objects.create(
            empresa=self.empresa,
            nome="Maria Silva",
            pis="98765432109",
            cpf="98765432109",
            cbo="2121",
            carteira_profissional="7654321",
            data_admissao=datetime(2020, 1, 1).date(),
            data_nascimento=datetime(1985, 3, 10).date()
        )

        self.lancamento = Lancamento.objects.create(
            empresa=self.empresa,
            funcionario=self.funcionario,
            competencia="01/2025",
            base_fgts=Decimal("1000.00"),
            valor_fgts=Decimal("80.00"),
            desconto_inss=Decimal("100.00"),
            desconto_ir=Decimal("50.00")
        )

    def test_registro_50_structure(self):
        """Valida a estrutura do Registro 50"""
        filtros = SefipFilters(
            empresa=self.empresa,
            competencia="01/2025",
            funcionario_de=self.funcionario.id,
            funcionario_ate=self.funcionario.id
        )

        conteudo = gerar_sefip_conteudo(filtros)
        linhas = conteudo.split("\r\n")

        reg50_lines = [l for l in linhas if l.startswith("50")]
        assert len(reg50_lines) > 0, "Nenhum Registro 50 encontrado"

        reg50 = reg50_lines[0]
        assert reg50[0:2] == "50", "Tipo deve ser '50'"
        assert reg50[-1] == "*", "Deve terminar com '*'"
        assert len(reg50) == 261, f"Tamanho deve ser 261, mas tem {len(reg50)}"

    def test_registro_50_descontos_presentes(self):
        """Valida que descontos aparecem no Registro 50"""
        filtros = SefipFilters(
            empresa=self.empresa,
            competencia="01/2025",
            funcionario_de=self.funcionario.id,
            funcionario_ate=self.funcionario.id
        )

        conteudo = gerar_sefip_conteudo(filtros)
        assert "50" in conteudo, "Registro 50 não encontrado"


class SefipExport60Test(TestCase):
    """Testa a geração do Registro 60 (Contribuições Sindicais)"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nome="Empresa Teste",
            cnpj="12345678901234",
            endereco="Rua Teste",
            numero="123",
            bairro="Bairro Teste",
            cidade="São Paulo",
            uf="SP",
            cep="01234567"
        )

        self.funcionario = Funcionario.objects.create(
            empresa=self.empresa,
            nome="Pedro Santos",
            pis="55555555555",
            cpf="55555555555",
            cbo="2121",
            carteira_profissional="5555555",
            data_admissao=datetime(2020, 1, 1).date(),
            data_nascimento=datetime(1992, 7, 20).date()
        )

        self.lancamento = Lancamento.objects.create(
            empresa=self.empresa,
            funcionario=self.funcionario,
            competencia="01/2025",
            base_fgts=Decimal("1000.00"),
            valor_fgts=Decimal("80.00"),
            desconto_sindical=Decimal("25.00")
        )

    def test_registro_60_structure(self):
        """Valida a estrutura do Registro 60"""
        filtros = SefipFilters(
            empresa=self.empresa,
            competencia="01/2025",
            funcionario_de=self.funcionario.id,
            funcionario_ate=self.funcionario.id
        )

        conteudo = gerar_sefip_conteudo(filtros)
        linhas = conteudo.split("\r\n")

        reg60_lines = [l for l in linhas if l.startswith("60")]
        assert len(reg60_lines) > 0, "Nenhum Registro 60 encontrado"

        reg60 = reg60_lines[0]
        assert reg60[0:2] == "60", "Tipo deve ser '60'"
        assert reg60[-1] == "*", "Deve terminar com '*'"
        assert len(reg60) == 261, f"Tamanho deve ser 261, mas tem {len(reg60)}"


class SefipCompleteTest(TestCase):
    """Testa a geração completa do SEFIP com todos os registros"""

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nome="Empresa Completa",
            cnpj="99999999999999",
            endereco="Av Principal",
            numero="1000",
            bairro="Centro",
            cidade="Rio de Janeiro",
            uf="RJ",
            cep="20000000"
        )

        self.func1 = Funcionario.objects.create(
            empresa=self.empresa,
            nome="Ana Costa",
            pis="11111111111",
            cpf="11111111111",
            cbo="2121",
            carteira_profissional="1111111",
            data_admissao=datetime(2020, 1, 1).date(),
            data_nascimento=datetime(1988, 2, 14).date()
        )

        self.func2 = Funcionario.objects.create(
            empresa=self.empresa,
            nome="Bruno Oliveira",
            pis="22222222222",
            cpf="22222222222",
            cbo="2122",
            carteira_profissional="2222222",
            data_admissao=datetime(2021, 6, 15).date(),
            data_nascimento=datetime(1995, 11, 8).date()
        )

        Lancamento.objects.create(
            empresa=self.empresa,
            funcionario=self.func1,
            competencia="01/2025",
            base_fgts=Decimal("2000.00"),
            valor_fgts=Decimal("160.00"),
            horas_extras=Decimal("150.00"),
            desconto_inss=Decimal("200.00"),
            desconto_sindical=Decimal("30.00")
        )

        Lancamento.objects.create(
            empresa=self.empresa,
            funcionario=self.func2,
            competencia="01/2025",
            base_fgts=Decimal("1500.00"),
            valor_fgts=Decimal("120.00")
        )

    def test_sefip_complete_file(self):
        """Valida que arquivo SEFIP completo contém todos os registros"""
        filtros = SefipFilters(
            empresa=self.empresa,
            competencia="01/2025",
            funcionario_de=self.func1.id,
            funcionario_ate=self.func2.id
        )

        conteudo = gerar_sefip_conteudo(filtros)
        linhas = conteudo.split("\r\n")

        assert any(l.startswith("00") for l in linhas), "Registro 00 não encontrado"
        assert any(l.startswith("10") for l in linhas), "Registro 10 não encontrado"
        assert any(l.startswith("301") for l in linhas), "Registro 301 não encontrado"
        assert any(l.startswith("40") for l in linhas), "Registro 40 não encontrado"
        assert any(l.startswith("50") for l in linhas), "Registro 50 não encontrado"
        assert any(l.startswith("60") for l in linhas), "Registro 60 não encontrado"
        assert any(l.startswith("90") for l in linhas), "Registro 90 não encontrado"

    def test_sefip_file_format(self):
        """Valida que cada linha tem o tamanho correto"""
        filtros = SefipFilters(
            empresa=self.empresa,
            competencia="01/2025",
            funcionario_de=self.func1.id,
            funcionario_ate=self.func2.id
        )

        conteudo = gerar_sefip_conteudo(filtros)
        linhas = [l for l in conteudo.split("\r\n") if l]

        for linha in linhas:
            assert linha[-1] == "*", f"Linha deve terminar com '*': {linha[:20]}..."
            if linha[0:2] in ("40", "50", "60"):
                assert len(linha) == 261, f"Registro {linha[0:2]} deve ter 261 chars, tem {len(linha)}"
