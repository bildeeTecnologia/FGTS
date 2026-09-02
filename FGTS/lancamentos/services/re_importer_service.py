"""
Serviço unificado de importação de arquivo SEFIP.

Suporta dois formatos de entrada:
  - Arquivo .RE (texto, 360 chars/linha, ISO-8859-1) — gerado pelo SEFIP da Caixa
  - PDF visual do relatório GFIP/SEFIP — extraído via pdfplumber

Pipeline comum: identifica registros (CNPJ, PIS, competência, base_fgts),
resolve Empresa → Funcionario → FuncionarioVinculo e cria/atualiza Lancamentos.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Dict, List, Optional, Tuple

from django.db import transaction

from empresas.models import Empresa
from empresas.models_grupo import FuncionarioVinculo, get_aliquota_fgts
from funcionarios.models import Funcionario
from lancamentos.models import Lancamento


class REImportError(Exception):
    pass


# ---------------------------------------------------------------------------
# Registro normalizado proveniente de qualquer fonte
# ---------------------------------------------------------------------------

class RegistroRE:
    __slots__ = ('cnpj', 'pis', 'nome', 'competencia', 'base_fgts', 'parcela_13', 'admissao_str')

    def __init__(
        self,
        cnpj: str,
        pis: str,
        nome: str,
        competencia: str,
        base_fgts: Decimal,
        parcela_13: Optional[int] = None,
        admissao_str: str = '',
    ):
        self.cnpj = cnpj
        self.pis = pis
        self.nome = nome
        self.competencia = competencia
        self.base_fgts = base_fgts
        self.parcela_13 = parcela_13
        self.admissao_str = admissao_str


# ---------------------------------------------------------------------------
# Parser do arquivo .RE (texto, 360 chars/linha)
# ---------------------------------------------------------------------------

def _parse_base_fgts_re(valor_str: str) -> Decimal:
    """Converte 15 chars (13 inteiros + 2 decimais) em Decimal."""
    s = valor_str.strip()
    if not s or not s.isdigit():
        return Decimal('0.00')
    inteiro = s[:13].lstrip('0') or '0'
    frac = s[13:15] if len(s) >= 15 else '00'
    try:
        return Decimal(f'{inteiro}.{frac}')
    except InvalidOperation:
        return Decimal('0.00')


def _parse_competencia_re(var_data: str) -> str:
    """Converte YYYYMM ou YYYY13 → MM/YYYY ou 13/YYYY."""
    v = var_data.strip()
    if len(v) != 6 or not v.isdigit():
        return ''
    ano = v[:4]
    mes = v[4:6]
    if mes == '13':
        return f'13/{ano}'
    if not ('01' <= mes <= '12'):
        return ''
    return f'{mes}/{ano}'


def parse_re_texto(arquivo_bytes: bytes) -> Tuple[List[RegistroRE], List[str]]:
    """
    Parseia bytes de um arquivo .RE e retorna (registros, erros).
    """
    try:
        conteudo = arquivo_bytes.decode('latin1')
    except Exception:
        raise REImportError(
            'Não foi possível decodificar o arquivo. '
            'Certifique-se de que está no formato ISO-8859-1 (.RE do SEFIP).'
        )

    linhas = conteudo.splitlines()
    if not linhas:
        raise REImportError('O arquivo está vazio.')

    registros: List[RegistroRE] = []
    erros: List[str] = []
    competencia_atual = ''
    cnpj_atual = ''

    for num, linha_raw in enumerate(linhas, 1):
        linha = linha_raw.rstrip('\r\n')
        if linha.endswith('*'):
            linha = linha[:-1]

        if len(linha) < 2:
            continue

        if linha[:2] == '00':
            if len(linha) >= 297:
                comp = _parse_competencia_re(linha[291:297])
                if comp:
                    competencia_atual = comp
            if len(linha) >= 17:
                cnpj_atual = linha[3:17].strip()
            continue

        if linha[:2] in ('10', '40', '50', '60', '90'):
            continue

        if linha[:3] != '301':
            continue

        if len(linha) < 182:
            erros.append(f'Linha {num}: registro 301 truncado ({len(linha)} chars).')
            continue

        if not competencia_atual:
            erros.append(f'Linha {num}: competência não identificada antes do registro 301.')
            continue

        try:
            pis = linha[32:43].strip()
            nome = linha[53:123].strip()
            base_str = linha[167:182]
            base_fgts = _parse_base_fgts_re(base_str)
            cnpj_linha = linha[3:17].strip() or cnpj_atual
        except Exception as exc:
            erros.append(f'Linha {num}: erro ao extrair campos — {exc}')
            continue

        if not pis:
            erros.append(f'Linha {num}: PIS vazio.')
            continue

        registros.append(RegistroRE(
            cnpj=cnpj_linha,
            pis=pis,
            nome=nome,
            competencia=competencia_atual,
            base_fgts=base_fgts,
        ))

    return registros, erros


# ---------------------------------------------------------------------------
# Parser do PDF visual SEFIP (via pdfplumber)
# ---------------------------------------------------------------------------

_PADRAO_A = re.compile(
    r'^(.+?)\s+(\d{3}\.\d{5}\.\d{2}-\d)\s+(\d{2}/\d{2}/\d{4})\s+'
    r'(\d{2}(?:\s+\d{2})?)'
    r'(?:\s+\d{2}/\d{2}/\d{4}\s+\w+)?'
    r'\s+(\d{5})\s*$'
)
_PADRAO_B = re.compile(
    r'^([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s*$'
)


def _br_float(s: str) -> float:
    return float(s.strip().replace('.', '').replace(',', '.'))


def _extrair_meta_pagina(texto: str) -> Dict[str, str]:
    comp = re.search(r'COMP:\s*(\d{2}/\d{4})', texto)
    inscr = re.search(r'INSCRI[CÇ][AÃ]O:\s*([\d./\-]+)', texto)
    empresa = re.search(r'EMPRESA:\s*(.+?)\s+INSCRI', texto)
    return {
        'competencia': comp.group(1).strip() if comp else '',
        'inscricao': re.sub(r'[.\-/]', '', inscr.group(1).strip()) if inscr else '',
        'empresa': empresa.group(1).strip() if empresa else '',
    }


def parse_pdf(pdf_bytes: bytes) -> Tuple[List[RegistroRE], List[str]]:
    """
    Extrai registros de um PDF de relatório SEFIP/GFIP.
    Requer pdfplumber instalado.
    """
    try:
        import pdfplumber
    except ImportError:
        raise REImportError(
            'A biblioteca pdfplumber não está instalada. '
            'Execute: pip install pdfplumber'
        )

    from io import BytesIO
    registros: List[RegistroRE] = []
    erros: List[str] = []

    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            paginas = [page.extract_text() or '' for page in pdf.pages]
    except Exception as exc:
        raise REImportError(f'Não foi possível ler o PDF: {exc}')

    for texto in paginas:
        meta = _extrair_meta_pagina(texto)
        if not meta['competencia']:
            continue

        linhas = texto.split('\n')
        i = 0
        while i < len(linhas):
            linha = linhas[i]
            ma = _PADRAO_A.match(linha)
            if ma:
                nome = ma.group(1).strip()
                pis_mask = ma.group(2)
                admissao_str = ma.group(3)
                pis = re.sub(r'\D', '', pis_mask).zfill(11)

                prox = linhas[i + 1] if (i + 1) < len(linhas) else ''
                mb = _PADRAO_B.match(prox)

                if mb:
                    try:
                        rem_sem_13 = _br_float(mb.group(1))
                        rem_13 = _br_float(mb.group(2))
                    except Exception:
                        i += 1
                        continue

                    base = RegistroRE(
                        cnpj=re.sub(r'\D', '', meta['inscricao']),
                        pis=pis,
                        nome=nome,
                        competencia=meta['competencia'],
                        base_fgts=Decimal(str(rem_sem_13)).quantize(Decimal('0.01')),
                        admissao_str=admissao_str,
                    )
                    registros.append(base)

                    if rem_13 > 0:
                        r13 = RegistroRE(
                            cnpj=re.sub(r'\D', '', meta['inscricao']),
                            pis=pis,
                            nome=nome,
                            competencia=meta['competencia'],
                            base_fgts=Decimal(str(rem_13)).quantize(Decimal('0.01')),
                            parcela_13=2,
                            admissao_str=admissao_str,
                        )
                        registros.append(r13)

                    i += 2
                    continue
            i += 1

    return registros, erros


# ---------------------------------------------------------------------------
# Pipeline de importação compartilhado
# ---------------------------------------------------------------------------

class REImporterService:
    """
    Serviço de importação de arquivos RE/SEFIP.

    Uso:
        svc = REImporterService()
        result = svc.preview(arquivo_bytes, tipo='re_texto', empresa=empresa_obj, max_rows=15)
        result = svc.importar(arquivo_bytes, tipo='re_texto', empresa=empresa_obj, progress_cb=cb)
    """

    TIPOS_VALIDOS = ('re_texto', 'pdf')

    def __init__(self):
        self._empresa_cache: Dict[str, Optional[Empresa]] = {}
        self._funcionario_cache: Dict[str, Optional[Funcionario]] = {}
        self._vinculo_cache: Dict[str, Optional[FuncionarioVinculo]] = {}

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def preview(
        self,
        arquivo_bytes: bytes,
        tipo: str,
        empresa: Optional[Empresa] = None,
        max_rows: int = 15,
    ) -> Dict[str, Any]:
        """
        Retorna preview dos primeiros max_rows registros sem gravar no banco.
        """
        registros, parse_erros = self._parse(arquivo_bytes, tipo)
        total = len(registros)
        amostra = registros[:max_rows]

        rows = []
        for reg in amostra:
            empresa_resolvida = self._resolver_empresa(reg.cnpj, empresa)
            func, vinculo, erro = self._resolver_funcionario_vinculo(
                reg.pis, reg.competencia, empresa_resolvida, reg.admissao_str
            )
            rows.append({
                'cnpj': reg.cnpj,
                'pis': reg.pis,
                'nome_arquivo': reg.nome,
                'competencia': reg.competencia,
                'base_fgts': str(reg.base_fgts),
                'valor_fgts': str((reg.base_fgts * get_aliquota_fgts(vinculo)).quantize(Decimal('0.01'))),
                'parcela_13': reg.parcela_13,
                'empresa_nome': empresa_resolvida.nome if empresa_resolvida else None,
                'funcionario_nome': func.nome if func else None,
                'vinculo_id': vinculo.pk if vinculo else None,
                'status': 'ok' if (func and not erro) else 'error',
                'erro': erro or '',
            })

        linhas_ok = sum(1 for r in rows if r['status'] == 'ok')
        linhas_erro = sum(1 for r in rows if r['status'] == 'error')

        return {
            'total_registros': total,
            'linhas_amostradas': len(amostra),
            'linhas_ok': linhas_ok,
            'linhas_erro': linhas_erro,
            'rows': rows,
            'parse_erros': parse_erros[:10],
        }

    def importar(
        self,
        arquivo_bytes: bytes,
        tipo: str,
        empresa: Optional[Empresa] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Any]:
        """
        Processa todos os registros e cria/atualiza Lancamentos no banco.
        Retorna dict com criados, ignorados, erros, avisos, competencias.
        """
        registros, parse_erros = self._parse(arquivo_bytes, tipo)
        total = len(registros)

        if progress_callback:
            progress_callback(0, total)

        criados = 0
        ignorados = 0
        erros: List[str] = list(parse_erros)
        avisos: List[str] = []
        competencias: List[str] = []

        for idx, reg in enumerate(registros, 1):
            empresa_resolvida = self._resolver_empresa(reg.cnpj, empresa)
            if not empresa_resolvida:
                erros.append(f'Reg {idx}: CNPJ {reg.cnpj} não encontrado na plataforma.')
                continue

            func, vinculo, erro = self._resolver_funcionario_vinculo(
                reg.pis, reg.competencia, empresa_resolvida, reg.admissao_str
            )
            if erro or not func:
                msg = erro or f'Funcionário PIS {reg.pis} não encontrado.'
                avisos.append(f'Reg {idx} ({reg.nome}): {msg} — ignorado.')
                ignorados += 1
                continue

            try:
                with transaction.atomic():
                    lancamento, created = Lancamento.objects.get_or_create(
                        empresa=empresa_resolvida,
                        funcionario=func,
                        vinculo=vinculo,
                        competencia=reg.competencia,
                        parcela_13=reg.parcela_13,
                        defaults={
                            'base_fgts': reg.base_fgts,
                            'valor_fgts': (reg.base_fgts * get_aliquota_fgts(vinculo)).quantize(Decimal('0.01')),
                            'pago': False,
                        },
                    )
            except Exception as exc:
                erros.append(f'Reg {idx} PIS {reg.pis} / {reg.competencia}: {exc}')
                continue

            if created:
                criados += 1
            else:
                ignorados += 1
                avisos.append(
                    f'Reg {idx}: lançamento já existe para PIS {reg.pis} / {reg.competencia} — ignorado.'
                )

            if reg.competencia not in competencias:
                competencias.append(reg.competencia)

            if progress_callback and idx % 50 == 0:
                progress_callback(idx, total)

        if progress_callback:
            progress_callback(total, total)

        return {
            'criados': criados,
            'ignorados': ignorados,
            'erros': erros,
            'avisos': avisos,
            'competencias': competencias,
            'total': total,
        }

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _parse(self, arquivo_bytes: bytes, tipo: str) -> Tuple[List[RegistroRE], List[str]]:
        if tipo == 're_texto':
            return parse_re_texto(arquivo_bytes)
        elif tipo == 'pdf':
            return parse_pdf(arquivo_bytes)
        raise REImportError(f'Tipo desconhecido: {tipo}. Use "re_texto" ou "pdf".')

    def _resolver_empresa(
        self, cnpj: str, empresa_forcada: Optional[Empresa]
    ) -> Optional[Empresa]:
        if empresa_forcada:
            return empresa_forcada
        cnpj_limpo = re.sub(r'\D', '', cnpj)
        if cnpj_limpo in self._empresa_cache:
            return self._empresa_cache[cnpj_limpo]
        resultado = Empresa.objects.filter(cnpj=cnpj_limpo).first()
        self._empresa_cache[cnpj_limpo] = resultado
        return resultado

    def _resolver_funcionario_vinculo(
        self,
        pis: str,
        competencia: str,
        empresa: Optional[Empresa],
        admissao_str: str = '',
    ) -> Tuple[Optional[Funcionario], Optional[FuncionarioVinculo], str]:
        if not empresa:
            return None, None, 'Empresa não identificada.'

        pis_limpo = re.sub(r'\D', '', pis).zfill(11)
        cache_key = f'{pis_limpo}:{empresa.pk}'

        if cache_key in self._funcionario_cache:
            func = self._funcionario_cache[cache_key]
        else:
            func = Funcionario.objects.filter(
                pis=pis_limpo,
                vinculos__empresa=empresa,
            ).first()
            self._funcionario_cache[cache_key] = func

        if not func:
            return None, None, f'Funcionário com PIS {pis_limpo} não encontrado na empresa.'

        # Resolve vínculo ativo na competência
        vinculo_key = f'{pis_limpo}:{empresa.pk}:{competencia}'
        if vinculo_key in self._vinculo_cache:
            vinculo = self._vinculo_cache[vinculo_key]
        else:
            vinculos_qs = FuncionarioVinculo.objects.filter(
                funcionario=func,
                empresa=empresa,
            ).order_by('data_admissao')

            # Tenta filtrar pelo vínculo ativo na competência
            ativos = [v for v in vinculos_qs if v.is_ativo_em_competencia(
                self._competencia_para_yyyymm(competencia)
            )]

            if len(ativos) == 1:
                vinculo = ativos[0]
            elif len(ativos) > 1:
                # Desempata pela data_admissao mais próxima da data do arquivo
                vinculo = self._desempatar_por_admissao(ativos, admissao_str)
            else:
                # Sem vínculo ativo: usa o mais recente (pode ser pós-demissão)
                vinculo = vinculos_qs.last()

            self._vinculo_cache[vinculo_key] = vinculo

        return func, vinculo, ''

    @staticmethod
    def _competencia_para_yyyymm(competencia: str) -> str:
        """Converte MM/YYYY para YYYY-MM (formato aceito por is_ativo_em_competencia)."""
        if '/' in competencia:
            partes = competencia.split('/')
            if len(partes) == 2:
                return f'{partes[1]}-{partes[0].zfill(2)}'
        return competencia

    @staticmethod
    def _desempatar_por_admissao(
        vinculos: List[FuncionarioVinculo],
        admissao_str: str,
    ) -> FuncionarioVinculo:
        """Tenta desempatar por data de admissão quando há múltiplos vínculos ativos."""
        if admissao_str:
            try:
                from datetime import datetime
                adm_date = datetime.strptime(admissao_str, '%d/%m/%Y').date()
                for v in vinculos:
                    if v.data_admissao == adm_date:
                        return v
            except Exception:
                pass
        return vinculos[-1]
