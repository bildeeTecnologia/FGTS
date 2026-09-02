"""
REGRA DE NEGÓCIO CRÍTICA E IMUTÁVEL - BUSCA DE ÍNDICES FGTS
===============================================================

⚠️ ATENÇÃO: ESTA REGRA NUNCA PODE SER ALTERADA OU NEGLIGENCIADA ⚠️

REGRA OBRIGATÓRIA:
-----------------
A busca de índices FGTS DEVE SEMPRE usar a combinação EXATA de:
    competencia = data da competência (início do mês)
    E
    data_base = data de pagamento
    E
    tabela = tabela correta baseada na competência

SELEÇÃO AUTOMÁTICA DA TABELA (OBRIGATÓRIO):
-------------------------------------------
Baseado na Portaria MTE, as tabelas são determinadas pela competência:

Tabela 6 - Não optantes e optantes após 22/09/1971
    Competências: 01/1967 a 09/1989

Tabela 7 - Não optantes e optantes após 22/09/1971
    Competências: 10/1989 a 09/2025

REGRA DE CORTE:
- competencia <= 1989-09-01 → TABELA 6
- competencia >= 1989-10-01 → TABELA 7

NUNCA usar:
- Intervalos de datas
- Busca pelo mais próximo
- Busca pelo mais recente
- Qualquer outra lógica de aproximação
- Tabela fixa sem validar a competência

A tabela indices_fgts contém registros únicos para cada combinação de:
(competencia, data_base, tabela)

Onde:
- competencia: primeiro dia do mês da competência (ex: 2023-01-01 para 01/2023)
- data_base: data exata do pagamento
- tabela: 6 (até 09/1989) ou 7 (10/1989 em diante)

FONTE DA VERDADE:
----------------
- Única e exclusiva: tabela 'indices_fgts' no Supabase
- Acesso via ORM (SupabaseIndice) ou REST API
- SEM fallback para tabelas locais

Esta regra garante:
1. Precisão nos cálculos
2. Conformidade com legislação (Portaria MTE)
3. Auditabilidade
4. Rastreabilidade

Qualquer tentativa de alterar esta lógica deve ser rejeitada.
"""

from datetime import date
from decimal import Decimal
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# DATA DE CORTE OFICIAL: Setembro de 1989
DATA_CORTE_TABELA = date(1989, 9, 1)


class IndiceFGTSService:
    """
    Serviço centralizado e imutável para busca de índices FGTS.
    
    REGRA CRÍTICA: Busca sempre por competencia E data_base exatos.
    Tabela é determinada AUTOMATICAMENTE pela competência.
    """
    
    @staticmethod
    def determinar_tabela(competencia: date) -> int:
        """
        Determina a tabela FGTS correta baseada na competência.
        
        REGRA OFICIAL (Portaria MTE):
        - Tabela 6: Competências de 01/1967 até 09/1989
        - Tabela 7: Competências de 10/1989 até 09/2025
        
        Args:
            competencia: Data da competência (primeiro dia do mês)
            
        Returns:
            int: 6 ou 7 (código da tabela)
        """
        if competencia <= DATA_CORTE_TABELA:
            return 6  # Tabela 6: até 09/1989
        else:
            return 7  # Tabela 7: 10/1989 em diante
    
    @staticmethod
    def buscar_indice(competencia: date, data_pagamento: date, tabela: Optional[int] = None) -> Optional[Decimal]:
        """
        Busca o índice FGTS para uma competência e data de pagamento específicas.
        
        REGRA IMUTÁVEL:
        --------------
        A busca é feita com filtro EXATO:
            competencia = competencia AND data_base = data_pagamento AND tabela = tabela_automatica
        
        A TABELA É DETERMINADA AUTOMATICAMENTE pela competência:
        - Tabela 6: competências até 09/1989
        - Tabela 7: competências de 10/1989 em diante
        
        Args:
            competencia: Data da competência (primeiro dia do mês, ex: 2023-01-01)
            data_pagamento: Data exata do pagamento
            tabela: Código da tabela FGTS (opcional, se None usa determinação automática)
            
        Returns:
            Decimal: Valor do índice se encontrado
            None: Se não existir índice para essa combinação exata
            
        Raises:
            ValueError: Se os parâmetros forem inválidos
        """
        # DETERMINAÇÃO AUTOMÁTICA DA TABELA (se não fornecida)
        if tabela is None:
            tabela = IndiceFGTSService.determinar_tabela(competencia)
            logger.info(f"[ÍNDICE FGTS] Tabela determinada automaticamente: {tabela} para competência {competencia}")
        
        # VALIDAÇÕES OBRIGATÓRIAS
        if not isinstance(competencia, date):
            raise ValueError(f"competencia deve ser date, recebido: {type(competencia)}")
        
        if not isinstance(data_pagamento, date):
            raise ValueError(f"data_pagamento deve ser date, recebido: {type(data_pagamento)}")
        
        if data_pagamento < competencia:
            raise ValueError(
                f"Data de pagamento ({data_pagamento}) não pode ser anterior "
                f"à competência ({competencia})"
            )
        
        # LOG CRÍTICO: Registrar sempre as buscas
        logger.info(
            f"[ÍNDICE FGTS] Buscando índice EXATO: "
            f"competencia={competencia}, data_pagamento={data_pagamento}, tabela={tabela}"
        )
        
        # Tentar via ORM primeiro
        indice = IndiceFGTSService._buscar_via_orm(competencia, data_pagamento, tabela)
        
        # Fallback: REST API
        if indice is None:
            indice = IndiceFGTSService._buscar_via_rest(competencia, data_pagamento, tabela)
        
        if indice is None:
            logger.warning(
                f"[ÍNDICE FGTS] NENHUM ÍNDICE ENCONTRADO para: "
                f"competencia={competencia}, data_pagamento={data_pagamento}, tabela={tabela}"
            )
        else:
            logger.info(
                f"[ÍNDICE FGTS] Índice encontrado: {indice} para "
                f"competencia={competencia}, data_pagamento={data_pagamento}"
            )
        
        return indice
    
    @staticmethod
    def _buscar_via_orm(competencia: date, data_pagamento: date, tabela: int) -> Optional[Decimal]:
        """Busca via ORM Django (SupabaseIndice model), com cache de 24h."""
        try:
            from django.core.cache import cache
            from indices.models import SupabaseIndice

            cache_key = f'indice_fgts_{competencia.strftime("%Y%m")}_{data_pagamento.strftime("%Y%m%d")}_{tabela}'
            cached = cache.get(cache_key)
            if cached is not None:
                return None if cached == '__none__' else Decimal(str(cached))

            # FILTRO EXATO - NUNCA ALTERAR
            indice_obj = SupabaseIndice.objects.filter(
                competencia=competencia,
                data_base=data_pagamento,
                tabela=tabela
            ).first()

            valor = indice_obj.indice if indice_obj else None
            cache.set(cache_key, str(valor) if valor is not None else '__none__', timeout=86400)
            return valor

        except Exception as e:
            logger.error(f"[ÍNDICE FGTS] Erro ao buscar via ORM: {e}")
            return None
    
    @staticmethod
    def _buscar_via_rest(competencia: date, data_pagamento: date, tabela: int) -> Optional[Decimal]:
        """Busca via REST API Supabase."""
        try:
            from indices.services.supabase_client import fetch_indice_especifico
            return fetch_indice_especifico(competencia, data_pagamento, tabela)
            
        except Exception as e:
            logger.error(f"[ÍNDICE FGTS] Erro ao buscar via REST: {e}")
            return None
    
    @staticmethod
    def validar_disponibilidade(competencia: date, data_pagamento: date, tabela: int = 1) -> dict:
        """
        Valida se existe índice disponível para a combinação especificada.
        
        Returns:
            dict com:
                - disponivel: bool
                - indice: Decimal ou None
                - mensagem: str
        """
        indice = IndiceFGTSService.buscar_indice(competencia, data_pagamento, tabela)
        
        if indice is not None:
            return {
                'disponivel': True,
                'indice': indice,
                'mensagem': f'Índice disponível: {indice}'
            }
        else:
            return {
                'disponivel': False,
                'indice': None,
                'mensagem': (
                    f'Nenhum índice encontrado para competência {competencia.strftime("%m/%Y")} '
                    f'e data de pagamento {data_pagamento.strftime("%d/%m/%Y")}'
                )
            }

    @staticmethod
    def obter_ultima_data_base() -> Optional[date]:
        """Retorna a última data_base disponível na tabela indices_fgts."""
        try:
            from indices.models import SupabaseIndice

            return SupabaseIndice.objects.order_by('-data_base').values_list('data_base', flat=True).first()
        except Exception as e:
            logger.error(f"[ÍNDICE FGTS] Erro ao buscar última data_base: {e}")
            return None


# PROIBIR IMPORTAÇÃO DIRETA DE OUTRAS FUNÇÕES
# Use APENAS IndiceFGTSService.buscar_indice()
__all__ = ['IndiceFGTSService']
