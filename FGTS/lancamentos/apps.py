from django.apps import AppConfig


class LancamentosConfig(AppConfig):
    name = 'lancamentos'

    def ready(self):
        from . import signals_auditoria  # noqa: F401
