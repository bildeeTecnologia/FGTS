from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, List

from empresas.models import Empresa
from funcionarios.models import Funcionario
from lancamentos.models import Lancamento
from fgtsweb.utils.validators import digits_only, normalize_upper_ascii


class SefipExportError(Exception):
    pass


SEFIP_LINE_LENGTH = 360


@dataclass
class SefipLegacyFilters:
    empresa: Empresa
    competencia: str
    funcionario_de_id: int
    funcionario_ate_id: int


def _space(count: int) -> str:
    return " " * max(count, 0)


def _pad_right(value: str, length: int) -> str:
    value = value or ""
    clipped = value[:length]
    return clipped + _space(length - len(clipped))


def _pad_left(value: str, length: int) -> str:
    value = value or ""
    clipped = value[:length]
    return _space(length - len(clipped)) + clipped


def _norm_text(value: str | None, *, allow_digits: bool = True) -> str:
    return normalize_upper_ascii(value, allow_digits=allow_digits, allow_spaces=True)


def _norm_digits(value: str | None) -> str:
    return digits_only(value)


def _parse_competencia(competencia: str) -> tuple[int, int]:
    if '/' not in competencia:
        raise SefipExportError('Competencia invalida.')
    mes_str, ano_str = competencia.split('/', 1)
    if not mes_str.isdigit() or not ano_str.isdigit():
        raise SefipExportError('Competencia invalida.')
    mes = int(mes_str)
    ano = int(ano_str)
    if mes not in range(1, 13) and mes != 13:
        raise SefipExportError('Competencia invalida.')
    return mes, ano


def _finalize_line(line: str, length: int = SEFIP_LINE_LENGTH) -> str:
    base = (line or "").rstrip("\r\n")
    if base.endswith("*"):
        base = base[:-1]
    if len(base) > length - 1:
        base = base[: length - 1]
    return base + _space(length - 1 - len(base)) + "*"


def _format_base_fgts(valor: Decimal | None) -> str:
    if valor is None:
        return "0" * 15
    valor = Decimal(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    inteiro, frac = str(valor).split(".")
    return inteiro.zfill(13)[:13] + frac[:2]


def _rat_code(percentual_rat: Decimal | int | str | None) -> str:
    if percentual_rat is None:
        return _space(2)
    try:
        valor = Decimal(percentual_rat).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        base = f"{int(valor)}0"
        return f"{int(base):02d}0"
    except Exception:  # noqa: BLE001
        return _space(2)


def _get_admissao(funcionario: Funcionario, lancamento: Lancamento) -> date | None:
    if lancamento.vinculo_id and lancamento.vinculo:
        return lancamento.vinculo.data_admissao
    return funcionario.data_admissao


def _filter_lancamentos(filtros: SefipLegacyFilters) -> List[Lancamento]:
    lancamentos = (
        Lancamento.objects.select_related('funcionario', 'vinculo')
        .filter(
            empresa=filtros.empresa,
            funcionario_id__gte=filtros.funcionario_de_id,
            funcionario_id__lte=filtros.funcionario_ate_id,
        )
    )
    lancamentos = [l for l in lancamentos if _competencia_match(l.competencia, filtros.competencia)]

    def sort_key(lanc: Lancamento):
        pis = _norm_digits(lanc.funcionario.pis)
        admissao = _get_admissao(lanc.funcionario, lanc)
        admissao_key = admissao or date.min
        return (pis, admissao_key)

    return sorted(lancamentos, key=sort_key)


def _competencia_match(lanc_competencia: str | None, filtro_competencia: str) -> bool:
    if not lanc_competencia:
        return False
    lanc = lanc_competencia.strip()
    filtro = filtro_competencia.strip()
    if lanc == filtro:
        return True
    lanc_norm = lanc.replace("/", "")
    filtro_norm = filtro.replace("/", "")
    return lanc_norm == filtro_norm


def gerar_sefip_legacy(filtros: SefipLegacyFilters) -> str:
    empresa = filtros.empresa
    competencia = filtros.competencia

    mes, ano = _parse_competencia(competencia)
    var_data = f"{ano:04d}{mes:02d}"
    if mes == 13:
        var_data = f"{ano:04d}13"

    endereco_empresa = _norm_text(f"{empresa.endereco or ''} {empresa.numero or ''}".strip())
    cep = _norm_digits(empresa.cep)
    fone = _norm_digits(empresa.fone_contato)
    cnpj = _norm_digits(empresa.cnpj)
    razao = _norm_text(empresa.nome)
    bairro = _norm_text(empresa.bairro)
    cidade = _norm_text(empresa.cidade)

    linhas: List[str] = []

    # Registro 00
    reg00 = (
        "00"
        + _space(51)
        + "11"
        + _pad_left(cnpj, 14)
        + _pad_right(razao[:30], 30)
        + "DEPTO PESSOAL"
        + _space(7)
        + _pad_right(endereco_empresa[:50], 50)
        + _pad_right(bairro[:20], 20)
        + cep
        + _pad_right(cidade[:20], 20)
        + (empresa.uf or "")
        + _pad_left(fone, 12)
        + _space(60)
        + (var_data if mes != 13 else f"{ano:04d}13")
        + "1151"
        + _space(9)
        + "1"
        + _space(15)
        + "1"
        + _pad_left(cnpj, 14)
        + _space(18)
        + "*"
    )
    linhas.append(_finalize_line(reg00))

    # Registro 10
    if var_data < "199810":
        rat_code = _space(2)
        terceiros = _space(4)
        gps_codigo = _space(4)
    else:
        rat_code = _rat_code(empresa.percentual_rat)
        terceiros_raw = _norm_digits(empresa.outras_entidades)
        terceiros = terceiros_raw.zfill(4)[:4] if terceiros_raw else _space(4)
        gps_codigo = "2100"

    fpas = _norm_digits(empresa.fpas).zfill(3)[:3] if empresa.fpas else "000"
    simples = str(empresa.optante_simples or 1)
    cnae = _norm_digits(empresa.cnae)

    reg10 = (
        "10"
        + "1"
        + _pad_left(cnpj, 14)
        + "000000000000000000000000000000000000"
        + _pad_right(razao[:40], 40)
        + _pad_right(endereco_empresa[:50], 50)
        + _pad_right(bairro[:20], 20)
        + _norm_digits(cep).zfill(8)[:8]
        + _pad_right(cidade[:20], 20)
        + (empresa.uf or "")
        + _pad_left(fone, 12)
        + "N"
        + cnae
        + "P"
        + rat_code
        + "0"
        + simples
        + fpas
        + terceiros
        + gps_codigo
        + _space(5)
        + "000000000000000"
        + "000000000000000"
        + "000000000000000000000000000000"
        + _space(16)
        + "000000000000000000000000000000000000000000000"
        + _space(4)
        + "*"
    )
    linhas.append(_finalize_line(reg10))

    # Registro 30
    lancamentos = _filter_lancamentos(filtros)
    if not lancamentos:
        raise SefipExportError('Nao existe dados para geracao do arquivo SEFIP.RE.')

    for lancamento in lancamentos:
        funcionario = lancamento.funcionario
        pis = _norm_digits(funcionario.pis)
        admissao = _get_admissao(funcionario, lancamento)
        nascimento = funcionario.data_nascimento
        carteira = _norm_digits(funcionario.carteira_profissional).zfill(7)[:7]
        serie = _norm_digits(funcionario.serie_carteira)
        if not serie or int(serie) == 0:
            serie = "00001"
        else:
            serie = serie.zfill(5)[:5]

        data_admissao = admissao.strftime("%d%m%Y") if admissao else "00000000"
        data_nascimento = nascimento.strftime("%d%m%Y") if nascimento else "00000000"

        funcionario_id = str(funcionario.id)
        funcionario_id = funcionario_id[:11]

        nome = _norm_text(funcionario.nome, allow_digits=False)
        cbo = _norm_digits(funcionario.cbo)[:4].zfill(4)
        base_fgts = _format_base_fgts(lancamento.base_fgts)

        reg30 = (
            "301"
            + _pad_left(cnpj, 14)
            + _space(15)
            + pis
            + data_admissao
            + "01"
            + _pad_right(nome[:70], 70)
            + _pad_left(funcionario_id, 11)
            + carteira
            + serie
            + data_admissao
            + data_nascimento
            + "0"
            + cbo
            + base_fgts
            + "000000000000000  05000000000000000000000000000000000000000000000000000000000000"
            + _space(98)
            + "*"
        )
        linhas.append(_finalize_line(reg30))

        def _safe_decimal(value):
            try:
                return Decimal(value)
            except Exception:  # noqa: BLE001
                return Decimal("0")

        def _get_value(field_name: str) -> Decimal:
            return _safe_decimal(getattr(lancamento, field_name, Decimal("0")))

        def _has_any_value(values: list[Decimal]) -> bool:
            return any(v != 0 for v in values)

        # Registro 40 - Remunerações variáveis
        valores_40 = [
            _get_value('horas_extras'),
            _get_value('adicionais'),
            _get_value('insalubridade'),
            _get_value('periculosidade'),
            _get_value('outras_remuneracoes'),
        ]
        reg40 = (
            "40"
            + _pad_left(cnpj, 14)
            + _space(15)
            + pis
            + "".join(_format_base_fgts(v) for v in valores_40)
            + "*"
        )
        linhas.append(_finalize_line(reg40))

        # Registro 50 - Descontos (INSS, IR e outros) — somente se houver valor
        valores_50 = [
            _get_value('desconto_inss'),
            _get_value('desconto_ir'),
            _get_value('desconto_faltas'),
            _get_value('desconto_dsr'),
            _get_value('outros_descontos'),
        ]
        if _has_any_value(valores_50):
            reg50 = (
                "50"
                + _pad_left(cnpj, 14)
                + _space(15)
                + pis
                + "".join(_format_base_fgts(v) for v in valores_50)
                + "*"
            )
            linhas.append(_finalize_line(reg50))

        # Registro 60 - Contribuições sindicais — somente se houver valor
        valores_60 = [
            _get_value('desconto_sindical'),
            _get_value('contribuicao_confederativa'),
            _get_value('contribuicao_assistencial'),
            _get_value('desconto_fgts_atraso'),
            _get_value('outras_contribuicoes'),
        ]
        if _has_any_value(valores_60):
            reg60 = (
                "60"
                + _pad_left(cnpj, 14)
                + _space(15)
                + pis
                + "".join(_format_base_fgts(v) for v in valores_60)
                + "*"
            )
            linhas.append(_finalize_line(reg60))

    # Registro 90 — total de linhas excluindo o próprio reg90
    total_linhas = str(len(linhas)).zfill(7)[:7]
    reg90 = (
        "90"
        + total_linhas
        + "0" * 44   # demais campos (reservado)
        + "*"
    )
    linhas.append(_finalize_line(reg90))

    return "\r\n".join(linhas)
