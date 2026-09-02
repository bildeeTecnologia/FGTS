from django.db import models
from uuid import uuid4
from .models_feature import * 
from .models_grupo import *
from .models_relatorio import RelatorioPremium
from .models_leads import LeadEmailFlow

class EmailLog(models.Model):
	email = models.EmailField()
	data_envio = models.DateTimeField(auto_now_add=True)
	status = models.CharField(max_length=20)  # 'sucesso' ou 'erro'
	mensagem = models.TextField(blank=True, null=True)  # mensagem de erro ou info
	relatorio = models.ForeignKey('RelatorioPremium', on_delete=models.CASCADE, null=True, blank=True)

	class Meta:
		verbose_name = 'Log de Envio de E-mail'
		verbose_name_plural = 'Logs de Envio de E-mail'
		ordering = ['-data_envio']

	def __str__(self):
		return f"{self.email} - {self.status} - {self.data_envio:%d/%m/%Y %H:%M}"

class Empresa(models.Model):
	OPTANTE_SIMPLES_CHOICES = [
		(1, 'Não Optante'),
		(2, 'Optante'),
	]
	
	# OBS: o banco atual usa PK na coluna "id". Mantemos o atributo "codigo"
	# por compatibilidade no código, mapeando para a coluna correta.
	codigo = models.AutoField(primary_key=True, db_column='id')
	grupo = models.ForeignKey('GrupoEmpresa', null=True, blank=True, on_delete=models.SET_NULL, related_name='empresas', verbose_name='Grupo Econômico')
	# Deriva a noção de matriz: a empresa é matriz se for a empresa_principal do grupo
	@property
	def is_matriz(self):
		return bool(self.grupo and self.grupo.empresa_principal_id == self.codigo)
	nome = models.CharField(max_length=255, verbose_name='Nome')
	cnpj = models.CharField(max_length=20, unique=True, verbose_name='CNPJ')
	codigo_folha = models.CharField(max_length=30, blank=False, verbose_name='Codigo Folha')
	endereco = models.CharField(max_length=255, blank=True, verbose_name='Endereço')
	numero = models.CharField(max_length=10, blank=True, verbose_name='Número')
	bairro = models.CharField(max_length=100, blank=True, verbose_name='Bairro')
	cep = models.CharField(max_length=10, blank=True, verbose_name='CEP')
	cidade = models.CharField(max_length=100, blank=True, verbose_name='Cidade')
	uf = models.CharField(max_length=2, blank=True, verbose_name='UF')
	nome_contato = models.CharField(max_length=255, blank=True, verbose_name='Nome Contato')
	fone_contato = models.CharField(max_length=20, blank=True, verbose_name='Fone de Contato')
	cnae = models.CharField(max_length=10, blank=True, verbose_name='CNAE')
	from decimal import Decimal
	percentual_rat = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('1.00'), verbose_name='% RAT')
	optante_simples = models.IntegerField(choices=OPTANTE_SIMPLES_CHOICES, default=1, verbose_name='Optante Simples')
	fpas = models.CharField(max_length=10, blank=True, verbose_name='FPAS')
	outras_entidades = models.CharField(max_length=10, blank=True, verbose_name='Outras Entidades')
	email = models.EmailField(blank=True, verbose_name='e-Mail')
	paga_13_aniversario = models.BooleanField(
		default=False,
		verbose_name='Paga 1ª parcela do 13º no mês de aniversário?',
		help_text='Se marcado, a 1ª parcela do 13º será paga no mês de aniversário do colaborador (ao invés de novembro). A 2ª parcela continua sendo paga em dezembro.'
	)
	validar_meses_parcela_13 = models.BooleanField(
		default=True,
		verbose_name='Validar meses das parcelas do 13º?',
		help_text='Se marcado, a importação exige que as parcelas do 13º sejam nos meses esperados (novembro/dezembro ou aniversário/dezembro). Desmarque para empresas que pagam o 13º em meses diferentes.'
	)

	@property
	def id(self):
		"""Compatibilidade: expõe PK como id para testes e código legado."""
		return self.codigo

	@property
	def codigo_exibicao(self):
		return self.codigo_folha or str(self.codigo)

	def save(self, *args, **kwargs):
		if not self.codigo_folha:
			self.codigo_folha = self._generate_codigo_folha()
		super().save(*args, **kwargs)

	@classmethod
	def _generate_codigo_folha(cls):
		while True:
			codigo = f"CF{uuid4().hex[:8].upper()}"
			if not cls.objects.filter(codigo_folha=codigo).exists():
				return codigo

	def __str__(self):
		return self.nome
	
	class Meta:
		verbose_name = 'Empresa'
		verbose_name_plural = 'Empresas'
