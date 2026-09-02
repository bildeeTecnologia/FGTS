from django.db import models

class CoefJam(models.Model):
	data_pagamento = models.DateField()
	competencia = models.CharField(max_length=7)  # Ex: MM/YYYY
	valor = models.DecimalField(max_digits=12, decimal_places=8)

	def __str__(self):
		return f"{self.data_pagamento} - {self.competencia}"
