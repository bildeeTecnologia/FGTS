from django.db import migrations


class Migration(migrations.Migration):
    """
    O campo empresa_id foi adicionado manualmente ao billing_subscription fora
    das migrations do Django. O modelo Subscription não possui este campo (a empresa
    é acessível via subscription.customer.empresa). Este migration torna a coluna
    nullable para que os INSERTs do Django não violem a constraint NOT NULL.
    """

    dependencies = [
        ('billing', '0009_history_limits'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
              IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'billing_subscription'
                  AND column_name = 'empresa_id'
              ) THEN
                ALTER TABLE public.billing_subscription
                  ALTER COLUMN empresa_id DROP NOT NULL;
              END IF;
            END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
