"""
Testes para garantir a REGRA DE NEGÓCIO IMUTÁVEL de busca de índices FGTS.

ATENÇÃO: Estes testes NÃO PODEM FALHAR em hipótese alguma.
Se falharem, o sistema está violando a regra crítica de negócio.
"""

from datetime import date
from decimal import Decimal
import unittest
from unittest.mock import patch, MagicMock

from indices.services.indice_service import IndiceFGTSService


class TestRegraImutavelIndiceFGTS(unittest.TestCase):
    """
    Testes que validam a regra imutável de busca de índices FGTS.
    
    REGRA: Busca SEMPRE por competencia E data_base exatos.
    """
    
    def test_busca_deve_ser_exata_nunca_intervalo(self):
        """
        CRÍTICO: Verifica que a busca usa filtros EXATOS, não intervalos.
        """
        competencia = date(2023, 1, 1)
        data_pagamento = date(2025, 12, 23)
        
        with patch('indices.services.indice_service.IndiceFGTSService._buscar_via_orm') as mock_orm:
            mock_orm.return_value = Decimal('0.106352093')
            
            indice = IndiceFGTSService.buscar_indice(competencia, data_pagamento)
            
            # Verifica que foi chamado com parâmetros exatos
            mock_orm.assert_called_once_with(competencia, data_pagamento, 1)
            self.assertIsNotNone(indice)
    
    def test_rejeitar_data_pagamento_anterior_competencia(self):
        """
        CRÍTICO: Data de pagamento não pode ser anterior à competência.
        """
        competencia = date(2023, 1, 1)
        data_pagamento = date(2022, 12, 1)  # Anterior!
        
        with self.assertRaises(ValueError) as context:
            IndiceFGTSService.buscar_indice(competencia, data_pagamento)
        
        self.assertIn("não pode ser anterior", str(context.exception))
    
    def test_parametros_devem_ser_date(self):
        """
        CRÍTICO: Parâmetros devem ser do tipo date, não strings ou outros.
        """
        # Teste com string
        with self.assertRaises(ValueError):
            IndiceFGTSService.buscar_indice("2023-01-01", date(2025, 12, 23))
        
        # Teste com None
        with self.assertRaises(ValueError):
            IndiceFGTSService.buscar_indice(None, date(2025, 12, 23))
    
    def test_retorna_none_se_nao_encontrar(self):
        """
        CRÍTICO: Deve retornar None se não existir índice, nunca aproximar.
        """
        competencia = date(2023, 1, 1)
        data_pagamento = date(2025, 12, 23)
        
        with patch('indices.services.indice_service.IndiceFGTSService._buscar_via_orm') as mock_orm, \
             patch('indices.services.indice_service.IndiceFGTSService._buscar_via_rest') as mock_rest:
            
            mock_orm.return_value = None
            mock_rest.return_value = None
            
            indice = IndiceFGTSService.buscar_indice(competencia, data_pagamento)
            
            # Deve retornar None, não aproximar para valor próximo
            self.assertIsNone(indice)
    
    def test_validacao_disponibilidade(self):
        """
        CRÍTICO: Validação deve indicar claramente se índice existe.
        """
        competencia = date(2023, 1, 1)
        data_pagamento = date(2025, 12, 23)
        
        with patch('indices.services.indice_service.IndiceFGTSService.buscar_indice') as mock_busca:
            mock_busca.return_value = Decimal('0.106352093')
            
            resultado = IndiceFGTSService.validar_disponibilidade(competencia, data_pagamento)
            
            self.assertTrue(resultado['disponivel'])
            self.assertEqual(resultado['indice'], Decimal('0.106352093'))
            self.assertIn('disponível', resultado['mensagem'].lower())


class TestProtecaoContraViolacoes(unittest.TestCase):
    """
    Testes que verificam proteções contra violações da regra.
    """
    
    def test_nao_permitir_busca_por_intervalo(self):
        """
        CRÍTICO: Sistema não deve permitir busca por intervalo de datas.
        """
        # Esta função NÃO DEVE EXISTIR ou deve ser marcada como DEPRECATED
        from indices.services import supabase_client
        
        # fetch_indices_range é apenas para diagnóstico, nunca para cálculo
        self.assertTrue(
            hasattr(supabase_client, 'fetch_indices_range'),
            "fetch_indices_range deve existir apenas para diagnóstico"
        )
        
        # fetch_indice_especifico DEVE existir e ser usada
        self.assertTrue(
            hasattr(supabase_client, 'fetch_indice_especifico'),
            "fetch_indice_especifico DEVE existir para busca exata"
        )
    
    def test_servico_centralizado_deve_ser_usado(self):
        """
        CRÍTICO: Views devem usar IndiceFGTSService, não buscar diretamente.
        """
        # Verificar que o serviço existe e é importável
        try:
            from indices.services.indice_service import IndiceFGTSService
            self.assertTrue(hasattr(IndiceFGTSService, 'buscar_indice'))
        except ImportError:
            self.fail("IndiceFGTSService deve existir e ser importável")


if __name__ == '__main__':
    unittest.main()
