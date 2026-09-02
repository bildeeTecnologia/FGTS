import re
from decimal import Decimal
from datetime import datetime
from django.core.management.base import BaseCommand
from coefjam.models import CoefJam


class Command(BaseCommand):
    help = 'Importa coeficientes JAM do arquivo tblCoefjam.txt para o banco de dados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='BASE_CONHECIMENTO/tblCoefjam.txt',
            help='Caminho do arquivo tblCoefjam.txt (padrão: BASE_CONHECIMENTO/tblCoefjam.txt)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpar registros existentes antes de importar'
        )

    def handle(self, *args, **options):
        arquivo = options['file']
        
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'Arquivo não encontrado: {arquivo}')
            )
            return

        # Padrão regex para extrair: |   dd/mm/yyyy   |   valor   |
        pattern = re.compile(r'\|\s*(\d{2})/(\d{2})/(\d{4})\s*\|\s*([\d,\.]+)\s*\|')
        
        matches = pattern.findall(conteudo)
        
        if not matches:
            self.stdout.write(
                self.style.ERROR('Nenhum coeficiente encontrado no arquivo.')
            )
            return

        self.stdout.write(f'Encontrados {len(matches)} registros no arquivo.')

        if options['clear']:
            CoefJam.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Tabela CoefJam limpa.'))

        registros_criados = 0
        erros = 0

        for dia, mes, ano, valor_str in matches:
            try:
                # Converter valor: "0,068652" → Decimal('0.068652')
                valor_dec = Decimal(valor_str.replace(',', '.'))
                
                # Data de competência: sempre 01 do mês
                data_competencia = datetime.strptime(f'01/{mes}/{ano}', '%d/%m/%Y').date()
                
                # Formato de competência: MM/YYYY
                competencia_fmt = f'{mes}/{ano}'
                
                # Data de pagamento: use a data original como data de pagamento
                data_pagamento = datetime.strptime(f'{dia}/{mes}/{ano}', '%d/%m/%Y').date()
                
                # Criar ou atualizar registro
                obj, criado = CoefJam.objects.update_or_create(
                    competencia=competencia_fmt,
                    data_pagamento=data_pagamento,
                    defaults={'valor': valor_dec}
                )
                
                if criado:
                    registros_criados += 1
                    
            except Exception as e:
                erros += 1
                self.stdout.write(
                    self.style.WARNING(f'Erro ao processar {dia}/{mes}/{ano}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Importação concluída!\n'
                f'  Registros criados: {registros_criados}\n'
                f'  Erros: {erros}\n'
                f'  Total na tabela: {CoefJam.objects.count()}'
            )
        )
