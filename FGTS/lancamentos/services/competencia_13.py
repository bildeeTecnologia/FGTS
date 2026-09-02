"""
Serviço para gerenciar lógica de competências do 13º salário.

Regras:
- Toda empresa tem 2 parcelas obrigatórias do 13º (1ª e 2ª)
- Se empresa.paga_13_aniversario = False: 1ª parcela em 11/YYYY, 2ª em 12/YYYY
- Se empresa.paga_13_aniversario = True: 1ª parcela no mês de aniversário do colaborador, 2ª em 12/YYYY
- Se empresa.validar_meses_parcela_13 = False: aceita qualquer mês para as parcelas do 13º
"""

from datetime import datetime
from dateutil.relativedelta import relativedelta
from lancamentos.models import Lancamento


class Competencia13Service:
    """Serviço para gerenciar as duas parcelas do 13º salário"""
    
    @staticmethod
    def obter_mes_primeira_parcela_13(empresa, funcionario):
        """
        Retorna o mês (1-12) em que a 1ª parcela do 13º deve ser paga.
        
        Args:
            empresa: Instância de Empresa
            funcionario: Instância de Funcionario
            
        Returns:
            int: Mês (1-12) ou None se não souber a data de nascimento
        """
        if not empresa.paga_13_aniversario:
            return 11  # Novembro é o padrão
        
        # Se paga no aniversário, usar mês de nascimento
        if funcionario.data_nascimento:
            return funcionario.data_nascimento.month
        
        # Se não tem data de nascimento, volta ao padrão
        return 11
    
    @staticmethod
    def gerar_competencias_13(empresa, ano, funcionario=None):
        """
        Gera as 2 competências do 13º para um ano específico.
        
        Args:
            empresa: Instância de Empresa
            ano: Ano (int)
            funcionario: Instância de Funcionario (se None, retorna as competências genéricas)
            
        Returns:
            list: Lista com 2 tuplas (competencia_str, parcela) 
                  Ex: [('11/2025', 1), ('12/2025', 2)]
                  ou [('04/2025', 1), ('12/2025', 2)] se paga_13_aniversario=True e aniversário em abril
        """
        competencias = []
        
        if empresa.paga_13_aniversario and funcionario:
            mes_primeira = Competencia13Service.obter_mes_primeira_parcela_13(empresa, funcionario)
            competencias.append((f"{mes_primeira:02d}/{ano}", 1))
        else:
            competencias.append((f"11/{ano}", 1))
        
        competencias.append((f"12/{ano}", 2))
        
        return competencias
    
    @staticmethod
    def gerar_todas_competencias_ano(empresa, ano, funcionario=None):
        """
        Gera TODAS as competências do ano (01-12 + 2 parcelas do 13º).
        
        Args:
            empresa: Instância de Empresa
            ano: Ano (int)
            funcionario: Instância de Funcionario (se None, apenas 01-12 + 11,12)
            
        Returns:
            list: Lista com strings MM/YYYY e MM/YYYY (com parcela_13) para o 13º
                  Exemplo: ['01/2025', '02/2025', ..., '12/2025', '11/2025', '12/2025']
                  Onde as últimas duas são as parcelas do 13º
        """
        competencias = []
        
        # Meses normais 01-12
        for mes in range(1, 13):
            competencias.append(f"{mes:02d}/{ano}")
        
        # 2 Parcelas do 13º
        competencias_13 = Competencia13Service.gerar_competencias_13(empresa, ano, funcionario)
        for comp_str, _ in competencias_13:
            competencias.append(comp_str)
        
        return competencias
    
    @staticmethod
    def parse_competencia_com_parcela(competencia_str):
        """
        Parse uma string de competência e detecta se é 13º.
        
        Args:
            competencia_str: String no formato 'MM/YYYY'
            
        Returns:
            dict: {'mes': int, 'ano': int, 'parcela_13': int or None}
            
        Example:
            - '01/2025' -> {'mes': 1, 'ano': 2025, 'parcela_13': None}
            - '11/2025' -> {'mes': 11, 'ano': 2025, 'parcela_13': None}
            - Para identificar 13º, use contexto de empresa/funcionário
        """
        try:
            parts = competencia_str.split('/')
            mes = int(parts[0])
            ano = int(parts[1])
            return {'mes': mes, 'ano': ano, 'parcela_13': None}
        except (ValueError, IndexError):
            return None
    
    @staticmethod
    def listar_competencias_13_para_filtro(empresa, funcionario, anos=None):
        """
        Lista as competências do 13º para um funcionário em determinados anos.
        Útil para aplicar filtros em relatórios.
        
        Args:
            empresa: Instância de Empresa
            funcionario: Instância de Funcionario
            anos: List[int] ou None (se None, usa 2024-2026)
            
        Returns:
            dict: {ano: [{'competencia': 'MM/YYYY', 'parcela': 1 or 2}, ...]}
        """
        if anos is None:
            anos = [2024, 2025, 2026]
        
        resultado = {}
        for ano in anos:
            competencias_13 = Competencia13Service.gerar_competencias_13(empresa, ano, funcionario)
            resultado[ano] = [
                {'competencia': comp, 'parcela': parcela}
                for comp, parcela in competencias_13
            ]
        
        return resultado
    
    @staticmethod
    def validar_competencia_13(empresa, funcionario, competencia_str, parcela_13):
        """
        Valida se uma competência com parcela_13 é válida para um funcionário/empresa.
        
        Args:
            empresa: Instância de Empresa
            funcionario: Instância de Funcionario
            competencia_str: String no formato 'MM/YYYY'
            parcela_13: 1 ou 2
            
        Returns:
            tuple: (válido: bool, mensagem: str)
        """
        if not parcela_13:
            # Sem parcela_13 definida, é competência normal
            try:
                mes = int(competencia_str.split('/')[0])
                if 1 <= mes <= 12:
                    return (True, "Competência normal válida")
                else:
                    return (False, f"Mês {mes} inválido para competência normal (deve ser 01-12)")
            except:
                return (False, "Formato de competência inválido")
        
        # Com parcela_13, validar regras
        if parcela_13 not in [1, 2]:
            return (False, "Parcela do 13º deve ser 1 ou 2")

        # Se a empresa não exige validação de meses, qualquer mês é aceito
        if not getattr(empresa, 'validar_meses_parcela_13', True):
            return (True, "Competência do 13º válida")

        if parcela_13 == 1:
            # 1ª parcela
            mes_esperado = Competencia13Service.obter_mes_primeira_parcela_13(empresa, funcionario)
            mes_real = int(competencia_str.split('/')[0])
            if mes_real != mes_esperado:
                return (False, f"1ª parcela do 13º deve ser em {mes_esperado:02d}, não em {mes_real:02d}")
        
        elif parcela_13 == 2:
            # 2ª parcela sempre em dezembro
            mes_real = int(competencia_str.split('/')[0])
            if mes_real != 12:
                return (False, "2ª parcela do 13º deve ser em dezembro (12)")
        
        return (True, "Competência do 13º válida")

