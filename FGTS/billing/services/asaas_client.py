import os
import time
import logging
import requests

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10
MAX_RETRIES = 3
RETRY_BACKOFF = 1  # segundos


class AsaasClient:
    def __init__(self):
        # Permite ASAAS_ENV ou flag ASAAS_SANDBOX=True para ativar sandbox
        sandbox_flag = (os.getenv('ASAAS_SANDBOX', '').lower() == 'true')
        env = os.getenv('ASAAS_ENV') or ('sandbox' if sandbox_flag else 'production')
        self.env = env
        self.base_url = 'https://sandbox.asaas.com/api/v3' if env == 'sandbox' else 'https://www.asaas.com/api/v3'

        # Prioriza chave explícita; se sandbox, tenta chave sandbox
        self.api_key = os.getenv('ASAAS_API_KEY')
        if env == 'sandbox':
            self.api_key = os.getenv('ASAAS_API_KEY_SANDBOX') or self.api_key

        if not self.api_key:
            raise ValueError('Configure ASAAS_API_KEY (e ASAAS_ENV) ou ASAAS_API_KEY_SANDBOX para usar o checkout Asaas.')

    def _headers(self):
        return {
            'Content-Type': 'application/json',
            'access_token': self.api_key,
        }

    def _request(self, method, path, **kwargs):
        """Faz request com retry automático para erros transientes (5xx, timeout)."""
        url = f"{self.base_url}{path}"
        kwargs.setdefault('headers', self._headers())
        kwargs.setdefault('timeout', DEFAULT_TIMEOUT)

        last_exc = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = requests.request(method, url, **kwargs)
                if resp.status_code >= 500 and attempt < MAX_RETRIES:
                    logger.warning('Asaas %s %s retornou %s (tentativa %d/%d)', method, path, resp.status_code, attempt, MAX_RETRIES)
                    time.sleep(RETRY_BACKOFF * attempt)
                    continue
                resp.raise_for_status()
                return resp.json()
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_exc = exc
                if attempt < MAX_RETRIES:
                    logger.warning('Asaas %s %s falhou (tentativa %d/%d): %s', method, path, attempt, MAX_RETRIES, exc)
                    time.sleep(RETRY_BACKOFF * attempt)
                    continue
                raise
        raise last_exc  # pragma: no cover

    # -- Criação --

    def create_customer(self, payload: dict) -> dict:
        return self._request('POST', '/customers', json=payload)

    def create_subscription(self, payload: dict) -> dict:
        return self._request('POST', '/subscriptions', json=payload)

    def create_payment(self, payload: dict) -> dict:
        return self._request('POST', '/payments', json=payload)

    # -- Consulta --

    def get_customer(self, customer_id: str) -> dict:
        return self._request('GET', f'/customers/{customer_id}')

    def get_subscription(self, subscription_id: str) -> dict:
        return self._request('GET', f'/subscriptions/{subscription_id}')

    def get_payment(self, payment_id: str) -> dict:
        return self._request('GET', f'/payments/{payment_id}')

    def list_payments(self, subscription_id: str) -> dict:
        return self._request('GET', f'/subscriptions/{subscription_id}/payments')

    # -- Cancelamento --

    def cancel_subscription(self, subscription_id: str) -> dict:
        return self._request('DELETE', f'/subscriptions/{subscription_id}')

    def cancel_payment(self, payment_id: str) -> dict:
        return self._request('DELETE', f'/payments/{payment_id}')
