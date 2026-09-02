from django.db import models

class Indice(models.Model):
	competencia = models.CharField(max_length=7)  # Ex: MM/YYYY
	data_indice = models.DateField()
	valor = models.DecimalField(max_digits=12, decimal_places=8)

	def __str__(self):
		return f"{self.competencia} - {self.data_indice}"


class SupabaseIndice(models.Model):
	"""Leitura da tabela Supabase indices_fgts (managed=False, não migrar).

	Colunas reais: id (uuid), competencia (date), tabela (int), data_base (date), indice (decimal).
	Observação: a coluna created_at não existe na tabela; não declare aqui para evitar erro de consulta.
	"""
	competencia = models.DateField()
	tabela = models.IntegerField()
	data_base = models.DateField()
	indice = models.DecimalField(max_digits=12, decimal_places=9)

	class Meta:
		managed = False
		db_table = 'indices_fgts'

	def __str__(self):
		return f"{self.competencia} - {self.data_base}"
