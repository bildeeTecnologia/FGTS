from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0010_fix_subscription_empresa_nullable'),
    ]

    operations = [
        migrations.AddField(
            model_name='billingcustomer',
            name='override_price',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Se informado, substitui o preço do plano para esta empresa na hora da cobrança.',
                max_digits=10,
                null=True,
                verbose_name='Valor mensal especial (R$)',
            ),
        ),
    ]
