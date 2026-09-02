# Função utilitária para checar permissão de recurso
def empresa_tem_recurso(empresa, recurso):
    if not empresa:
        return False
    try:
        features = empresa.features
        return getattr(features, recurso, False)
    except Exception:
        return False
from django.db import models


class EmpresaFeature(models.Model):
    RECURSOS = [
        ("exportar_funcionarios", "Exportar Funcionários"),
        ("importar_funcionarios", "Importar Funcionários"),
        ("criar_funcionario", "Criar Funcionário"),
        ("editar_funcionario", "Editar Funcionário"),
        ("excluir_funcionario", "Excluir Funcionário"),
        ("gerar_relatorio", "Gerar Relatório"),
        ("criar_lancamento", "Criar Lançamento"),
        ("editar_lancamento", "Editar Lançamento"),
        ("excluir_lancamento", "Excluir Lançamento"),
        ("exportar_lancamentos", "Exportar Lançamentos"),
        ("gerar_sefip", "Gerar SEFIP.RE"),
        ("importar_re_sefip", "Importar RE / SEFIP"),
        ("importar_extrato_cef", "Importar Extrato Analítico CEF"),
        ("relatorio_posicao_fgts", "Relatório de Posição FGTS"),
        # Adicione outros recursos conforme necessário
    ]
    empresa = models.OneToOneField('empresas.Empresa', on_delete=models.CASCADE, related_name="features")
    # Flags para cada recurso
    exportar_funcionarios = models.BooleanField(default=False)
    importar_funcionarios = models.BooleanField(default=False)
    criar_funcionario = models.BooleanField(default=False)
    editar_funcionario = models.BooleanField(default=False)
    excluir_funcionario = models.BooleanField(default=False)
    gerar_relatorio = models.BooleanField(default=False)
    criar_lancamento = models.BooleanField(default=False)
    editar_lancamento = models.BooleanField(default=False)
    excluir_lancamento = models.BooleanField(default=False)
    exportar_lancamentos = models.BooleanField(default=False)
    gerar_sefip = models.BooleanField(default=False)
    importar_re_sefip = models.BooleanField(default=False)
    importar_extrato_cef = models.BooleanField(default=False)
    relatorio_posicao_fgts = models.BooleanField(default=False, verbose_name="Relatório de Posição FGTS")

    def __str__(self):
        return f"Permissões de recursos para {self.empresa.nome}"
