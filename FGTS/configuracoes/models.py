from django.db import models

class Configuracao(models.Model):
	chave = models.CharField(max_length=100, unique=True)
	valor = models.CharField(max_length=255)

	def __str__(self):
		return f"{self.chave}: {self.valor}"
