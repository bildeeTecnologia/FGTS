from django.core.management.base import BaseCommand, CommandError
from indices.models import Indice
from datetime import datetime
from decimal import Decimal

class Command(BaseCommand):
    help = 'Importa índices de um arquivo texto (formato flexível: data;valor ou competencia;valor)'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, required=True, help='Caminho do arquivo de índices')

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
            # tenta separar por ; , ou espaço
            for sep in (';', ',', '\t', ' '):
                if sep in line:
                    parts = [p for p in line.split(sep) if p]
                    break
            else:
                parts = [line]

            if len(parts) < 2:
                continue
            k, v = parts[0].strip(), parts[1].strip()
            # tenta data yyyy-mm ou yyyy-mm-dd
            data = None
            for fmt in ('%Y-%m-%d', '%Y-%m'):
                try:
                    data = datetime.strptime(k, fmt).date()
                    break
                except ValueError:
                    continue
            if data is None:
                # tenta competencia mm/yyyy
                try:
                    m, y = k.split('/')
                    data = datetime.strptime(f'{y}-{m}-01', '%Y-%m-%d').date()
                except Exception:
                    continue
            try:
                valor = Decimal(v.replace(',', '.'))
            except Exception:
                continue

            Indice.objects.update_or_create(
                competencia=data,
                defaults={'data_indice': data, 'valor': valor}
            )
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Importados {count} índices de {path}'))
