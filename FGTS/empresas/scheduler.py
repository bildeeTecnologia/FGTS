import logging

from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore

logger = logging.getLogger(__name__)


def _run_send_lead_emails():
    from django.core.management import call_command
    call_command('send_lead_emails')


def start():
    scheduler = BackgroundScheduler(timezone='UTC')
    scheduler.add_jobstore(DjangoJobStore(), 'default')

    scheduler.add_job(
        _run_send_lead_emails,
        'interval',
        hours=1,
        id='send_lead_emails',
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    logger.info('Scheduler iniciado: send_lead_emails a cada hora.')
    scheduler.start()
