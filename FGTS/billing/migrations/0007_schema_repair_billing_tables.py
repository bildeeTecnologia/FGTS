from django.db import migrations


REPAIR_SQL = r"""
-- Repair/align billing schema (PostgreSQL / Supabase)
-- This migration is intentionally defensive: it fixes missing tables/columns
-- even when django_migrations says previous migrations ran (e.g. manual/faked deploys).

-- 1) Ensure missing columns on billing_subscription
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'billing_subscription'
  ) THEN
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema = 'public'
        AND table_name = 'billing_subscription'
        AND column_name = 'created_at'
    ) THEN
      ALTER TABLE public.billing_subscription ADD COLUMN created_at timestamp with time zone;
      UPDATE public.billing_subscription SET created_at = NOW() WHERE created_at IS NULL;
    END IF;

    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema = 'public'
        AND table_name = 'billing_subscription'
        AND column_name = 'updated_at'
    ) THEN
      ALTER TABLE public.billing_subscription ADD COLUMN updated_at timestamp with time zone;
      UPDATE public.billing_subscription SET updated_at = NOW() WHERE updated_at IS NULL;
    END IF;
  END IF;
END $$;

-- 2) Ensure billing_payment table exists (and minimum columns)
CREATE TABLE IF NOT EXISTS public.billing_payment (
  id bigserial PRIMARY KEY,
  asaas_payment_id varchar(100) NULL,
  amount numeric(10, 2) NOT NULL,
  due_date date NOT NULL,
  pay_date date NULL,
  status varchar(20) NOT NULL DEFAULT 'pending',
  invoice_url varchar(200) NULL,
  created_at timestamp with time zone NOT NULL DEFAULT NOW(),
  updated_at timestamp with time zone NOT NULL DEFAULT NOW(),
  subscription_id bigint NOT NULL
);

DO $$
BEGIN
  -- Add missing columns if table exists but is incomplete
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'billing_payment'
  ) THEN
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema = 'public' AND table_name = 'billing_payment' AND column_name = 'subscription_id'
    ) THEN
      ALTER TABLE public.billing_payment ADD COLUMN subscription_id bigint;
    END IF;
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema = 'public' AND table_name = 'billing_payment' AND column_name = 'created_at'
    ) THEN
      ALTER TABLE public.billing_payment ADD COLUMN created_at timestamp with time zone;
      UPDATE public.billing_payment SET created_at = NOW() WHERE created_at IS NULL;
    END IF;
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema = 'public' AND table_name = 'billing_payment' AND column_name = 'updated_at'
    ) THEN
      ALTER TABLE public.billing_payment ADD COLUMN updated_at timestamp with time zone;
      UPDATE public.billing_payment SET updated_at = NOW() WHERE updated_at IS NULL;
    END IF;
  END IF;
END $$;

-- Add FK if missing (best-effort)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'billing_payment'
  ) AND EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'billing_subscription'
  ) THEN
    IF NOT EXISTS (
      SELECT 1
      FROM information_schema.table_constraints tc
      WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = 'public'
        AND tc.table_name = 'billing_payment'
        AND tc.constraint_name = 'billing_payment_subscription_id_fk'
    ) THEN
      BEGIN
        ALTER TABLE public.billing_payment
          ADD CONSTRAINT billing_payment_subscription_id_fk
          FOREIGN KEY (subscription_id)
          REFERENCES public.billing_subscription (id)
          ON DELETE CASCADE;
      EXCEPTION WHEN OTHERS THEN
        -- ignore if cannot be added due to existing data/constraints
        NULL;
      END;
    END IF;
  END IF;
END $$;

-- 3) Ensure billing_feedback table exists
CREATE TABLE IF NOT EXISTS public.billing_feedback (
  id bigserial PRIMARY KEY,
  tipo varchar(20) NOT NULL,
  titulo varchar(255) NOT NULL,
  mensagem text NOT NULL,
  email_resposta varchar(254) NULL,
  respondido boolean NOT NULL DEFAULT false,
  resposta text NULL,
  criado_em timestamp with time zone NOT NULL DEFAULT NOW(),
  atualizado_em timestamp with time zone NOT NULL DEFAULT NOW(),
  empresa_id bigint NOT NULL
);

-- Add FK if missing (best-effort)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'billing_feedback'
  ) AND EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'empresas_empresa'
  ) THEN
    IF NOT EXISTS (
      SELECT 1
      FROM information_schema.table_constraints tc
      WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = 'public'
        AND tc.table_name = 'billing_feedback'
        AND tc.constraint_name = 'billing_feedback_empresa_id_fk'
    ) THEN
      BEGIN
        ALTER TABLE public.billing_feedback
          ADD CONSTRAINT billing_feedback_empresa_id_fk
          FOREIGN KEY (empresa_id)
          REFERENCES public.empresas_empresa (id)
          ON DELETE CASCADE;
      EXCEPTION WHEN OTHERS THEN
        NULL;
      END;
    END IF;
  END IF;
END $$;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0006_plan_max_companies"),
    ]

    operations = [
        migrations.RunSQL(sql=REPAIR_SQL, reverse_sql=migrations.RunSQL.noop),
    ]
