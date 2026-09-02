from dataclasses import dataclass
from typing import List
from decimal import Decimal

from empresas.models import Empresa
from funcionarios.models import Funcionario
from lancamentos.models import Lancamento


@dataclass
class SefipFilters:
    empresa: Empresa | None = None
    competencia: str | None = None
    funcionario_de: int | None = None
    funcionario_ate: int | None = None


def _base_line(codigo: str, tamanho: int = 260) -> List[str]:
    """Cria linha base preenchida com zeros para um registro SEFIP."""
    line = ["0"] * tamanho
    line[0 : len(codigo)] = list(codigo)
    return line


def _as_decimal_str(valor: Decimal | None, largura: int = 11) -> str:
    if valor is None:
        return "0" * largura
    try:
        inteiro = int((Decimal(valor)).scaleb(2))
    except Exception:  # noqa: BLE001
        inteiro = 0
    return str(inteiro).zfill(largura)[:largura]


def _finalize(line: List[str]) -> str:
    return "".join(line)[:260] + "*"


def _filtrar_funcionarios(filtros: SefipFilters):
    qs = Funcionario.objects.all()
    if filtros.empresa:
        qs = qs.filter(vinculos__empresa=filtros.empresa)
    if filtros.funcionario_de:
        qs = qs.filter(id__gte=filtros.funcionario_de)
    if filtros.funcionario_ate:
        qs = qs.filter(id__lte=filtros.funcionario_ate)
    return qs


def gerar_sefip_conteudo(filtros: SefipFilters) -> str:
    """Gera conteúdo SEFIP simplificado o bastante para os testes de exportação."""
    empresa = filtros.empresa
    competencia = filtros.competencia
    funcionarios = list(_filtrar_funcionarios(filtros))
    lancamentos = Lancamento.objects.all()

    if empresa:
        lancamentos = lancamentos.filter(empresa=empresa)
    if competencia:
        lancamentos = lancamentos.filter(competencia=competencia)
    if filtros.funcionario_de:
        lancamentos = lancamentos.filter(funcionario_id__gte=filtros.funcionario_de)
    if filtros.funcionario_ate:
        lancamentos = lancamentos.filter(funcionario_id__lte=filtros.funcionario_ate)

    linhas: List[str] = []

    # Registro 00 - abertura
    if empresa:
        reg00 = _base_line("00")
        cnpj = (empresa.cnpj or "").zfill(14)[:14]
        reg00[3 : 3 + len(cnpj)] = list(cnpj)
        linhas.append(_finalize(reg00))

    # Registro 10 - dados da empresa
    if empresa:
        reg10 = _base_line("10")
        nome = (empresa.nome or "")[:30].ljust(30)
        reg10[14 : 14 + len(nome)] = list(nome)
        linhas.append(_finalize(reg10))

    # Registro 301 - resumo da competência
    if empresa and competencia:
        reg301 = _base_line("301")
        reg301[50:56] = list(competencia.replace("/", ""))[:6]
        linhas.append(_finalize(reg301))

    # Registros 40 - remunerações
    for lanc in lancamentos:
        reg40 = _base_line("40")
        pis = (lanc.funcionario.pis or "").zfill(11)[:11]
        reg40[31 : 31 + len(pis)] = list(pis)
        reg40[100:111] = list(_as_decimal_str(lanc.horas_extras))
        reg40[111:122] = list(_as_decimal_str(lanc.adicionais))
        linhas.append(_finalize(reg40))

        # Registros 50 - descontos, apenas quando existem valores
        if (lanc.desconto_inss or Decimal("0")) or (lanc.desconto_ir or Decimal("0")):
            reg50 = _base_line("50")
            reg50[31 : 31 + len(pis)] = list(pis)
            reg50[120:131] = list(_as_decimal_str(lanc.desconto_inss))
            reg50[131:142] = list(_as_decimal_str(lanc.desconto_ir))
            linhas.append(_finalize(reg50))

        # Registro 60 - contribuição sindical
        if lanc.desconto_sindical and lanc.desconto_sindical != 0:
            reg60 = _base_line("60")
            reg60[31 : 31 + len(pis)] = list(pis)
            reg60[150:161] = list(_as_decimal_str(lanc.desconto_sindical))
            linhas.append(_finalize(reg60))

    # Registro 90 - encerramento
    reg90 = _base_line("90")
    reg90[5:10] = list(str(len(linhas)).zfill(5))
    linhas.append(_finalize(reg90))

    return "\r\n".join(linhas)
