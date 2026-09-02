from django.core.management.base import BaseCommand, CommandError
from coefjam.models import CoefJam
from datetime import datetime
from decimal import Decimal

class Command(BaseCommand):
    help = 'Importa coeficientes JAM de um arquivo texto (formato: competencia;valor)'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, required=True, help='Caminho do arquivo CoefJAM')

    def handle(self, *args, **options):
        path = options['path']
        try:
            with open(path, 'r', encoding='utf-8') as f:
                linhas = f.readlines()
        except Exception as e:
            raise CommandError(f'Erro ao ler arquivo: {e}')

        count = 0
        for raw in linhas:
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            sep = ';' if ';' in line else (',' if ',' in line else None)
            if not sep:
                continue
            k, v = [p.strip() for p in line.split(sep)[:2]]
            # competencia mm/yyyy ou yyyy-mm
            data = None
            for fmt in ('%m/%Y', '%Y-%m'):
                try:
                    data = datetime.strptime(k, fmt)
                    break
                except ValueError:
                    continue
            if not data:
                continue
            valor = None
            try:
                valor = Decimal(v.replace(',', '.'))
            except Exception:
                continue

            CoefJam.objects.update_or_create(
                competencia=f"{data.year}-{data.month:02}",
                defaults={'data_pagamento': data.date(), 'valor': valor}
            )
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Importados {count} coeficientes JAM de {path}'))
