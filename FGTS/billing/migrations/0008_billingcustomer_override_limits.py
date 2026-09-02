from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('billing', '0007_schema_repair_billing_tables'),
    ]

    operations = [
        migrations.AddField(
            model_name='billingcustomer',
            name='override_max_employees',
            field=models.IntegerField(
                blank=True,
                null=True,
                help_text='Se informado, substitui o limite do plano para esta empresa.',
                verbose_name='Limite especial de colaboradores',
            ),
        ),
        migrations.AddField(
            model_name='billingcustomer',
            name='override_max_companies',
            field=models.IntegerField(
                blank=True,
                null=True,
                help_text='Se informado, substitui o limite do plano para o grupo desta empresa.',
                verbose_name='Limite especial de CNPJs no grupo',
            ),
        ),
    ]
