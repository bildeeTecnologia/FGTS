# Merge migration to reconcile 0004_plan_max_companies and 0005_feedback
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0004_plan_max_companies'),
        ('billing', '0005_feedback'),
    ]

    operations = []
