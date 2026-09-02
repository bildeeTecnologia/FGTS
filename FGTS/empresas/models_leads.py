from django.db import models
from django.utils import timezone


class LeadEmailFlow(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'
    STATUS_PAUSED = 'paused'
    STATUS_ERROR = 'error'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Ativo'),
        (STATUS_COMPLETED, 'Concluido'),
        (STATUS_PAUSED, 'Pausado'),
        (STATUS_ERROR, 'Erro'),
    ]

    TRIGGER_CREDITS = 'credits_used'
    TRIGGER_ONBOARDING = 'onboarding_partial'

    TRIGGER_CHOICES = [
        (TRIGGER_CREDITS, 'Consumo 3 creditos'),
        (TRIGGER_ONBOARDING, 'Onboarding parcial'),
    ]

    email = models.EmailField(unique=True)
    trigger_source = models.CharField(max_length=40, choices=TRIGGER_CHOICES)
    triggered_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    step = models.PositiveSmallIntegerField(default=0)
    last_sent_at = models.DateTimeField(null=True, blank=True)
    next_send_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, null=True)
    error_count = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Lead - Fluxo Email'
        verbose_name_plural = 'Leads - Fluxo Email'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} - {self.get_status_display()}"
