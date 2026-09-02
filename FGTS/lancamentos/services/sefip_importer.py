"""
Importador de arquivo SEFIP.RE legado.

Lê o arquivo de 360 chars/linha (ISO-8859-1) gerado pelo SEFIP da Caixa
e cria Lancamentos correspondentes para a empresa selecionada.

Campos extraídos do registro 301:
  [0:3]    → tipo "301"
  [3:17]   → CNPJ empresa (14 chars, pad-esquerda)
  [32:43]  → PIS funcionário (11 chars)
  [53:123] → nome (70 chars, pad-direita)
  [167:182]→ base FGTS (15 chars: 13 inteiros + 2 decimais)

Campos extraídos do registro 00 (cabeçalho):
  [291:297]→ competência no formato YYYYMM ou YYYY13
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Dict, List

from empresas.models import Empresa
from funcionarios.models import Funcionario
from lancamentos.models import Lancamento


class SefipImportError(Exception):
    pass


class SefipImporter:
    """Parser e importador de arquivo SEFIP.RE."""

    def __init__(self):
        self.criados: int = 0
        self.ignorados: int = 0
        self.erros: List[str] = []
        self.avisos: List[str] = []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_base_fgts(valor_str: str) -> Decimal:
        """
        Converte 15 chars (13 inteiros + 2 decimais) em Decimal.
        Exemplo: "000000000300000" → Decimal("3000.00")
        """
        s = valor_str.strip()
        if not s or not s.isdigit():
            return Decimal("0.00")
        inteiro = s[:13].lstrip("0") or "0"
        frac = s[13:15] if len(s) >= 15 else "00"
        try:
            return Decimal(f"{inteiro}.{frac}")
        except InvalidOperation:
            return Decimal("0.00")

    @staticmethod
    def _parse_competencia(var_data: str) -> str:
        """
        Converte YYYYMM ou YYYY13 → MM/YYYY ou 13/YYYY.
        Retorna string vazia se inválido.
        """
        v = var_data.strip()
        if len(v) != 6 or not v.isdigit():
            return ""
        ano = v[:4]
        mes = v[4:6]
        if mes == "13":
            return f"13/{ano}"
        if not ("01" <= mes <= "12"):
            return ""
        return f"{mes}/{ano}"

    @staticmethod
    def _normalizar_linha(linha: str) -> str:
        """Remove newlines e asterisco final."""
        linha = linha.rstrip("\r\n")
        if linha.endswith("*"):
            linha = linha[:-1]
        return linha

    # ------------------------------------------------------------------
    # Parser principal
    # ------------------------------------------------------------------

    def importar(self, arquivo_bytes: bytes, empresa: Empresa) -> Dict:
        """
        Processa os bytes do arquivo .RE e cria Lancamentos.

        Retorna dict com: criados, ignorados, erros, avisos, competencias.
        """
        try:
            conteudo = arquivo_bytes.decode("latin1")
        except Exception:
            raise SefipImportError(
                "Não foi possível decodificar o arquivo. "
                "Certifique-se de que está no formato ISO-8859-1 (.RE / .TXT do SEFIP)."
            )

        linhas = conteudo.splitlines()
        if not linhas:
            raise SefipImportError("O arquivo está vazio.")

        competencia_atual = ""
        competencias_encontradas: list[str] = []

        for num, linha_raw in enumerate(linhas, 1):
            linha = self._normalizar_linha(linha_raw)

            if len(linha) < 2:
                continue

            tipo = linha[:3].rstrip()  # alguns arquivos têm "00 " etc.

            # --- Registro 00: extrai competência ---
            if linha[:2] == "00":
                if len(linha) >= 297:
                    var_data = linha[291:297]
                    comp = self._parse_competencia(var_data)
                    if comp:
                        competencia_atual = comp
                        if comp not in competencias_encontradas:
                            competencias_encontradas.append(comp)
                continue

            # Registros que não interessam para importação
            if linha[:2] in ("10", "40", "50", "60", "90"):
                continue

            # --- Registro 301: dados do trabalhador ---
            if linha[:3] != "301":
                continue

            if len(linha) < 182:
                self.erros.append(
                    f"Linha {num}: registro 301 truncado ({len(linha)} chars, mínimo 182)."
                )
                continue

            if not competencia_atual:
                self.erros.append(
                    f"Linha {num}: competência não identificada — "
                    "verifique se o registro 00 está presente antes do 301."
                )
                continue

            self._processar_reg301(linha, num, competencia_atual, empresa)

        return {
            "criados": self.criados,
            "ignorados": self.ignorados,
            "erros": self.erros,
            "avisos": self.avisos,
            "competencias": competencias_encontradas,
        }

    # ------------------------------------------------------------------
    # Processa um registro 301
    # ------------------------------------------------------------------

    def _processar_reg301(
        self,
        linha: str,
        num: int,
        competencia: str,
        empresa: Empresa,
    ) -> None:
        try:
            pis = linha[32:43].strip()
            nome = linha[53:123].strip()
            base_str = linha[167:182] if len(linha) >= 182 else ""
            base_fgts = self._parse_base_fgts(base_str)
        except Exception as exc:
            self.erros.append(f"Linha {num}: erro ao extrair campos — {exc}")
            return

        if not pis:
            self.erros.append(f"Linha {num}: PIS vazio, registro ignorado.")
            return

        # Localiza funcionário pelo PIS
        funcionario = Funcionario.objects.filter(pis=pis).first()
        if not funcionario:
            self.avisos.append(
                f"Linha {num}: funcionário PIS {pis}"
                f"{' (' + nome + ')' if nome else ''} não encontrado — ignorado."
            )
            self.ignorados += 1
            return

        # Cria ou ignora duplicata
        try:
            lancamento, created = Lancamento.objects.get_or_create(
                empresa=empresa,
                funcionario=funcionario,
                competencia=competencia,
                vinculo=None,
                defaults={
                    "base_fgts": base_fgts,
                    "valor_fgts": (base_fgts * Decimal("0.08")).quantize(Decimal("0.01")),  # SEFIP não tem vínculo: CLT padrão
                    "pago": False,
                },
            )
        except Exception as exc:
            self.erros.append(
                f"Linha {num}: PIS {pis} / {competencia} — erro ao salvar: {exc}"
            )
            return

        if created:
            self.criados += 1
        else:
            self.ignorados += 1
            self.avisos.append(
                f"Linha {num}: lançamento já existe para PIS {pis} "
                f"competência {competencia} — ignorado."
            )
