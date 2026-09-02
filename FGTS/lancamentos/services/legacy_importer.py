"""
Importador de dados legados do sistema VB6.
Implementação simples usada apenas pelos testes de integração legada.
"""

import csv
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Tuple

from empresas.models import Empresa
from funcionarios.models import Funcionario
from lancamentos.models import Lancamento


class LegacyDataImporter:
    """Importa dados históricos do sistema legado VB6"""

    def __init__(self):
        self.erros: List[str] = []
        self.avisos: List[str] = []
        self.linhas_processadas = 0
        self.registros_criados = 0
        self.registros_duplicados = 0

    def importar_empresas(self, arquivo_csv: str) -> Tuple[int, List[str]]:
        """Importa empresas de CSV simples (cnpj, razao_social, endereco)."""
        criados = 0
        try:
            with open(arquivo_csv, "r", encoding="latin1") as f:
                reader = csv.DictReader(f)
                for linha_num, row in enumerate(reader, 2):
                    try:
                        cnpj = (row.get("cnpj") or row.get("CNPJ") or "").strip()
                        if not cnpj:
                            self.avisos.append(f"Linha {linha_num}: CNPJ vazio, pulando")
                            continue

                        if Empresa.objects.filter(cnpj=cnpj).exists():
                            self.registros_duplicados += 1
                            continue

                        nome = (row.get("razao_social") or row.get("RazaoSocial") or "").strip() or cnpj
                        endereco = (row.get("endereco") or row.get("Endereco") or "").strip()

                        empresa = Empresa(
                            nome=nome,
                            cnpj=cnpj,
                            endereco=endereco,
                        )
                        empresa.save()
                        criados += 1
                        self.linhas_processadas += 1
                    except Exception as exc:  # noqa: BLE001
                        self.erros.append(f"Linha {linha_num}: {exc}")
        except FileNotFoundError:
            self.erros.append(f"Arquivo não encontrado: {arquivo_csv}")
        except Exception as exc:  # noqa: BLE001
            self.erros.append(f"Erro ao importar empresas: {exc}")

        self.registros_criados += criados
        return criados, self.erros

    def importar_funcionarios(self, arquivo_csv: str, empresa_id: int | None = None) -> Tuple[int, List[str]]:
        """Importa funcionários (pis,nome,data_admissao,cpf) vinculando à empresa informada."""
        criados = 0
        empresa = None
        if empresa_id:
            try:
                empresa = Empresa.objects.get(pk=empresa_id)
            except Empresa.DoesNotExist:
                self.erros.append(f"Empresa {empresa_id} não encontrada")
                return 0, self.erros

        try:
            with open(arquivo_csv, "r", encoding="latin1") as f:
                reader = csv.DictReader(f)
                for linha_num, row in enumerate(reader, 2):
                    try:
                        pis = (row.get("pis") or row.get("PIS") or "").strip()
                        nome = (row.get("nome") or row.get("Nome") or "").strip()
                        cpf = (row.get("cpf") or row.get("CPF") or "").strip() or "00000000000"
                        data_adm = self._parse_data(row.get("data_admissao") or row.get("DataAdmissao"))

                        if not pis or not nome:
                            self.avisos.append(f"Linha {linha_num}: dados obrigatórios ausentes")
                            continue

                        if Funcionario.objects.filter(pis=pis).exists():
                            self.registros_duplicados += 1
                            continue

                        funcionario = Funcionario(
                            nome=nome,
                            pis=pis,
                            cpf=cpf,
                            data_nascimento=self._parse_data(row.get("data_nascimento") or row.get("DataNascimento")),
                        )
                        funcionario.empresa = empresa
                        if data_adm:
                            funcionario.data_admissao = data_adm
                        funcionario.save()
                        criados += 1
                        self.linhas_processadas += 1
                    except Exception as exc:  # noqa: BLE001
                        self.erros.append(f"Linha {linha_num}: {exc}")
        except FileNotFoundError:
            self.erros.append(f"Arquivo não encontrado: {arquivo_csv}")
        except Exception as exc:  # noqa: BLE001
            self.erros.append(f"Erro ao importar funcionários: {exc}")

        self.registros_criados += criados
        return criados, self.erros

    def importar_lancamentos(self, arquivo_csv: str, empresa_id: int | None = None) -> Tuple[int, List[str]]:
        """Importa lançamentos simples (pis,competencia,base_fgts,data_pagto) para empresa informada."""
        criados = 0
        empresa = None
        if empresa_id:
            try:
                empresa = Empresa.objects.get(pk=empresa_id)
            except Empresa.DoesNotExist:
                self.erros.append(f"Empresa {empresa_id} não encontrada")
                return 0, self.erros

        try:
            with open(arquivo_csv, "r", encoding="latin1") as f:
                reader = csv.DictReader(f)
                for linha_num, row in enumerate(reader, 2):
                    try:
                        pis = (row.get("pis") or "").strip()
                        competencia = (row.get("competencia") or "").strip()
                        if not pis or not competencia:
                            self.avisos.append(f"Linha {linha_num}: dados obrigatórios ausentes")
                            continue

                        funcionario = Funcionario.objects.filter(pis=pis).first()
                        if not funcionario:
                            self.avisos.append(f"Linha {linha_num}: funcionário com PIS {pis} não encontrado")
                            continue

                        base_fgts = Decimal((row.get("base_fgts") or "0").replace(",", "."))
                        data_pagto = self._parse_data(row.get("data_pagto") or row.get("data_pagamento"))

                        lancamento, created = Lancamento.objects.get_or_create(
                            empresa=empresa or funcionario.empresa,
                            funcionario=funcionario,
                            competencia=competencia,
                            defaults={
                                "base_fgts": base_fgts,
                                "valor_fgts": base_fgts * Decimal("0.08"),  # Legado sem vínculo: CLT padrão
                                "pago": False,
                                "data_pagto": data_pagto,
                            },
                        )
                        if created:
                            criados += 1
                            self.linhas_processadas += 1
                        else:
                            self.registros_duplicados += 1
                    except Exception as exc:  # noqa: BLE001
                        self.erros.append(f"Linha {linha_num}: {exc}")
        except FileNotFoundError:
            self.erros.append(f"Arquivo não encontrado: {arquivo_csv}")
        except Exception as exc:  # noqa: BLE001
            self.erros.append(f"Erro ao importar lançamentos: {exc}")

        self.registros_criados += criados
        return criados, self.erros

    @staticmethod
    def _parse_data(data_str: str | None):
        """Tenta parsear data em formatos comuns"""
        if not data_str or not str(data_str).strip():
            return None

        data_str = str(data_str).strip()
        formatos = ["%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%Y-%m-%d", "%d%m%Y", "%Y%m%d"]
        for fmt in formatos:
            try:
                return datetime.strptime(data_str, fmt).date()
            except ValueError:
                continue
        return None

    def relatorio(self) -> Dict:
        """Retorna relatório da importação"""
        return {
            "linhas_processadas": self.linhas_processadas,
            "registros_criados": self.registros_criados,
            "registros_duplicados": self.registros_duplicados,
            "erros": self.erros,
            "avisos": self.avisos,
            "total_problemas": len(self.erros) + len(self.avisos),
        }
