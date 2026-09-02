import os
import sys

from django.apps import AppConfig

# Management commands que não devem iniciar o scheduler
_SKIP_SCHEDULER_COMMANDS = {
    'migrate', 'makemigrations', 'collectstatic', 'createsuperuser',
    'test', 'send_lead_emails', 'shell', 'dbshell', 'inspectdb',
    'showmigrations', 'sqlmigrate',
}


class EmpresasConfig(AppConfig):
    name = 'empresas'

    def ready(self):
        # Pular em management commands que não precisam do scheduler
        if len(sys.argv) > 1 and sys.argv[1] in _SKIP_SCHEDULER_COMMANDS:
            return

        # No dev server, evitar duplo start (reloader cria dois processos)
        if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') != 'true':
            return

        from empresas import scheduler
        scheduler.start()
