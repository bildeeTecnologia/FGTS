import os
from datetime import date
from decimal import Decimal
from typing import List, Tuple
import requests
from django.conf import settings

BASE_PATH = '/rest/v1'
TABLE_NAME = 'indices_fgts'

def _headers():
    url = getattr(settings, 'SUPABASE_API_URL', None) or os.getenv('SUPABASE_URL')
    key = getattr(settings, 'SUPABASE_API_KEY', None) or os.getenv('SUPABASE_KEY')
    if not url or not key:
        return None, None
    headers = {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Accept': 'application/json',
    }
    return url, headers

def fetch_indices_range(start: date, end: date) -> List[Tuple[date, Decimal]]:
    """
    Busca no Supabase (REST) os índices entre datas [start, end), retornando lista (data_base, indice).
    """
    base_url, headers = _headers()
    if not base_url:
        return []
    url = f"{base_url}{BASE_PATH}/{TABLE_NAME}?select=data_base,indice&data_base=gte.{start.isoformat()}&data_base=lt.{end.isoformat()}"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        items = resp.json()
        result = []
        for it in items:
            d = date.fromisoformat(it['data_base'])
            v = Decimal(str(it['indice']))
            result.append((d, v))
        return result
    except Exception:
        return []


def fetch_indice_especifico(competencia: date, data_pagamento: date, tabela: int = 1) -> Decimal:
    """
    Busca o índice específico onde competencia = competencia E data_base = data_pagamento E tabela = tabela.
    Retorna o valor do índice ou None se não encontrar.
    
    REGRA CRÍTICA: Busca EXATA, nunca aproximada.
    """
    base_url, headers = _headers()
    if not base_url:
        return None
    
    url = f"{base_url}{BASE_PATH}/{TABLE_NAME}?select=indice&competencia=eq.{competencia.isoformat()}&data_base=eq.{data_pagamento.isoformat()}&tabela=eq.{tabela}"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        items = resp.json()
        if items and len(items) > 0:
            return Decimal(str(items[0]['indice']))
        return None
    except Exception:
        return None
