from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0004_empresausuariorole'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='email_confirmed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='usuario',
            name='email_confirmed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
