from django.apps import AppConfig


class AuditLogsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit_logs'
    verbose_name = 'Auditoria de Logs'

    def ready(self):
        import audit_logs.signals
