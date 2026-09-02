import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fgtsweb.settings')
django.setup()

from lancamentos.models import Lancamento

# Contar lançamentos com parcela_13
count = Lancamento.objects.filter(parcela_13__isnull=False).count()
print(f'Lançamentos com parcela_13 preenchido: {count}')

# Mostrar exemplos
lancamentos = Lancamento.objects.filter(parcela_13__isnull=False).select_related('funcionario').values('id', 'competencia', 'parcela_13', 'funcionario__nome')[:10]
print('\nExemplos:')
for l in lancamentos:
    parcela_nome = '1ª Parcela' if l['parcela_13'] == 1 else '2ª Parcela'
    print(f"  ID {l['id']}: {l['funcionario__nome']} - {l['competencia']} - {parcela_nome}")

if count == 0:
    print("\n⚠️ NÃO HÁ LANÇAMENTOS COM PARCELA_13 PREENCHIDO")
    print("Para testar a funcionalidade do 13º:")
    print("1. Acesse 'Novo Lançamento'")
    print("2. Preencha os dados normalmente")
    print("3. No campo 'Parcela do 13º Salário', escolha '1ª Parcela' ou '2ª Parcela'")
    print("4. Salve o lançamento")
    print("5. Gere o relatório novamente para ver o rótulo '(13º 1ª)' ou '(13º 2ª)'")
