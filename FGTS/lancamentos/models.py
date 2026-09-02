from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from empresas.models import Empresa
from empresas.models_grupo import get_aliquota_fgts
from funcionarios.models import Funcionario
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.conf import settings

class Lancamento(models.Model):
	PARCELA_CHOICES = [
		(None, 'Competência Normal (01-12)'),
		(1, '13º Salário - 1ª Parcela'),
		(2, '13º Salário - 2ª Parcela'),
	]
	
	empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='lancamentos')
	funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='lancamentos')
	vinculo = models.ForeignKey(
		'empresas.FuncionarioVinculo',
		on_delete=models.PROTECT,
		null=True,
		blank=True,
		related_name='lancamentos',
		help_text='Opcional. Identifica a "cadeira" (vínculo) do funcionário para esta competência.'
	)
	competencia = models.CharField(max_length=7)  # Ex: MM/YYYY ou 13/YYYY para 13º
	parcela_13 = models.PositiveSmallIntegerField(
		null=True, 
		blank=True, 
		choices=PARCELA_CHOICES,
		help_text="Se preenchido, indica que é uma das 2 parcelas do 13º salário"
	)
	base_fgts = models.DecimalField(max_digits=12, decimal_places=2)
	valor_fgts = models.DecimalField(max_digits=12, decimal_places=2)
	horas_extras = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=Decimal('0.00'), help_text="Valores variáveis como horas extras")
	adicionais = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=Decimal('0.00'), help_text="Adicionais salariais")
	desconto_inss = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=Decimal('0.00'), help_text="Desconto de INSS")
	desconto_ir = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=Decimal('0.00'), help_text="Desconto de IR")
	desconto_sindical = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=Decimal('0.00'), help_text="Contribuição sindical")
	FONTE_CONFIRMACAO_CHOICES = [
		('manual', 'Manual (não verificado)'),
		('extrato_analitico', 'Extrato Analítico CEF (confirmado)'),
	]
	pago = models.BooleanField(default=False, help_text="FGTS foi pago?")
	data_pagto = models.DateField(null=True, blank=True, verbose_name="Data de Pagamento", help_text="Data em que o FGTS foi efetivamente pago")
	valor_pago = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Valor Pago")
	pago_em = models.DateTimeField(null=True, blank=True, verbose_name="Marcado como pago em", help_text="Data/hora em que foi registrado como pago no sistema")
	fonte_confirmacao_pagamento = models.CharField(
		max_length=20,
		choices=FONTE_CONFIRMACAO_CHOICES,
		null=True,
		blank=True,
		db_index=True,
		verbose_name="Fonte de Confirmação",
		help_text="Como o pagamento foi confirmado: manualmente pelo usuário ou via Extrato Analítico da CEF.",
	)
	criado_em = models.DateTimeField(auto_now_add=True)
	atualizado_em = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.empresa} - {self.funcionario} - {self.competencia}"
	
	def save(self, *args, **kwargs):
		"""
		Sobrescreve o save para:
		1. Registrar automaticamente quando marcar como pago
		2. Atualizar lançamentos posteriores quando houver mudança na base_fgts (cascata de reajuste)
		"""
		# Garantir consistência do vínculo (quando informado)
		if self.vinculo_id:
			if not self.empresa_id:
				self.empresa_id = self.vinculo.empresa_id
			if not self.funcionario_id:
				self.funcionario_id = self.vinculo.funcionario_id
			# Se usuário tentou salvar inconsistente, força coerência
			if self.empresa_id != self.vinculo.empresa_id:
				self.empresa_id = self.vinculo.empresa_id
			if self.funcionario_id != self.vinculo.funcionario_id:
				self.funcionario_id = self.vinculo.funcionario_id

		# Detectar se é uma edição e se a base_fgts mudou
		base_fgts_mudou = False
		if self.pk:  # Se já existe no banco (edição)
			try:
				lancamento_antigo = Lancamento.objects.get(pk=self.pk)
				if lancamento_antigo.base_fgts != self.base_fgts:
					base_fgts_mudou = True
			except Lancamento.DoesNotExist:
				pass

		# Recalcular valor_fgts sempre que a base mudar
		if self.base_fgts is not None:
			aliquota = get_aliquota_fgts(self.vinculo if self.vinculo_id else None)
			valor_calculado = (self.base_fgts * aliquota).quantize(Decimal('0.01'))
			if base_fgts_mudou or self.valor_fgts is None or self.valor_fgts != valor_calculado:
				self.valor_fgts = valor_calculado
		
		# Controle de pagamento: registrar timestamp
		if self.pago and not self.pago_em:
			self.pago_em = timezone.now()
		elif not self.pago:
			self.pago_em = None
			self.fonte_confirmacao_pagamento = None

		# Marcação manual: preserva fonte CEF, define 'manual' se ainda sem fonte
		if self.pago and not self.fonte_confirmacao_pagamento:
			self.fonte_confirmacao_pagamento = 'manual'
		
		# Salvar o lançamento atual
		super().save(*args, **kwargs)
		
		# Se houve mudança na base_fgts, atualizar todos os lançamentos posteriores
		if base_fgts_mudou:
			self.atualizar_lancamentos_posteriores()

	def clean(self):
		super().clean()

		# Se vínculo foi informado, derive empresa/funcionário dele
		if self.vinculo_id:
			if self.empresa_id and self.empresa_id != self.vinculo.empresa_id:
				raise ValidationError({'vinculo': 'Vínculo não pertence à empresa selecionada.'})
			if self.funcionario_id and self.funcionario_id != self.vinculo.funcionario_id:
				raise ValidationError({'vinculo': 'Vínculo não pertence ao funcionário selecionado.'})
			self.empresa_id = self.vinculo.empresa_id
			self.funcionario_id = self.vinculo.funcionario_id

		if not self.competencia:
			return

		# Garantir que empresa e funcionário estejam definidos antes das validações
		if not self.empresa_id:
			raise ValidationError({'empresa': 'Empresa é obrigatória.'})
		if not self.funcionario_id:
			raise ValidationError({'funcionario': 'Funcionário é obrigatório.'})

		try:
			mes, ano = map(int, self.competencia.split('/'))
		except Exception:
			raise ValidationError({'competencia': 'Competência deve estar no formato MM/YYYY.'})

		if mes < 1 or mes > 12:
			raise ValidationError({'competencia': 'Mês deve estar entre 01 e 12.'})

		# Limite de histórico por plano/empresa
		try:
			billing_customer = self.empresa.billing_customer
			max_history_months = billing_customer.get_effective_max_history_months()
			if max_history_months is not None and max_history_months > 0:
				competencia_date = datetime(ano, mes, 1).date()
				today = datetime.today().date()
				current_month = datetime(today.year, today.month, 1).date()
				min_date = current_month - relativedelta(months=max_history_months - 1)
				if competencia_date < min_date:
					raise ValidationError({
						'competencia': (
							f"Competência fora do limite do seu plano: "
							f"máximo de {max_history_months} meses de histórico."
						)
					})
		except Exception:
			pass

		# Validação das parcelas do 13º
		if self.parcela_13:
			if getattr(self.empresa, 'validar_meses_parcela_13', True):
				if self.parcela_13 == 1:
					mes_esperado = 11
					if getattr(self.empresa, 'paga_13_aniversario', False):
						aniversario = getattr(self.funcionario, 'data_nascimento', None)
						if aniversario:
							mes_esperado = aniversario.month
					if mes != mes_esperado:
						raise ValidationError({'competencia': f"1ª parcela do 13º deve ser em {mes_esperado:02d}/{ano}."})
				elif self.parcela_13 == 2:
					if mes != 12:
						raise ValidationError({'competencia': '2ª parcela do 13º deve ser em 12.'})
		else:
			# Competência normal já validada pelo intervalo do mês acima
			pass

		# Bloquear duplicidade por vínculo + competência + parcela_13
		if self.competencia:
			dup_qs = Lancamento.objects.filter(
				competencia=self.competencia,
				parcela_13=self.parcela_13,
			)
			if self.vinculo_id:
				dup_qs = dup_qs.filter(vinculo_id=self.vinculo_id)
			else:
				dup_qs = dup_qs.filter(funcionario_id=self.funcionario_id, vinculo__isnull=True)
			if self.pk:
				dup_qs = dup_qs.exclude(pk=self.pk)
			if dup_qs.exists():
				parcela_label = f" (13º {self.parcela_13}ª parcela)" if self.parcela_13 else ""
				raise ValidationError({
					'competencia': f"Já existe lançamento para este vínculo na competência {self.competencia}{parcela_label}."
				})
	
	def atualizar_lancamentos_posteriores(self):
		"""
		Atualiza todos os lançamentos posteriores do mesmo funcionário com a nova base_fgts.
		Isso implementa a cascata de reajuste salarial.
		"""
		try:
			# Converter competência atual para data
			mes, ano = map(int, self.competencia.split('/'))
			data_atual = datetime(ano, mes, 1)
			
			# Buscar todos os lançamentos posteriores do mesmo funcionário (ou do mesmo vínculo, quando aplicável)
			filtro = {'funcionario': self.funcionario}
			if self.vinculo_id:
				filtro = {'vinculo_id': self.vinculo_id}

			lancamentos_posteriores = Lancamento.objects.filter(
			**filtro,
			parcela_13__isnull=True,  # Não propagar para parcelas de 13° salário
		).select_related('vinculo__tipo_vinculo').order_by('competencia')

			# Filtrar apenas os meses posteriores ao atual
			for lancamento in lancamentos_posteriores:
				try:
					mes_l, ano_l = map(int, lancamento.competencia.split('/'))
					data_lancamento = datetime(ano_l, mes_l, 1)

					# Se for posterior, atualizar
					if data_lancamento > data_atual:
						aliquota = get_aliquota_fgts(lancamento.vinculo)
						lancamento.base_fgts = self.base_fgts
						lancamento.valor_fgts = (self.base_fgts * aliquota).quantize(Decimal('0.01'))
						# Usar update direto para evitar recursão infinita
						Lancamento.objects.filter(pk=lancamento.pk).update(
							base_fgts=lancamento.base_fgts,
							valor_fgts=lancamento.valor_fgts
						)
				except:
					continue
					
		except Exception as e:
			# Não interromper o fluxo em caso de erro na cascata
			pass
	
	@staticmethod
	def obter_base_fgts_anterior(funcionario, competencia_str, vinculo=None):
		"""
		Obtém a base FGTS do mês anterior.
		Se não encontrar, retorna None e o sistema usa o mês anterior recursivamente.
		Exemplo: competencia_str = "01/2025" retorna a base de 12/2024
		"""
		try:
			mes, ano = map(int, competencia_str.split('/'))
			data_atual = datetime(ano, mes, 1)
			data_anterior = data_atual - relativedelta(months=1)
			competencia_anterior = data_anterior.strftime('%m/%Y')
			
			filtro = {'funcionario': funcionario, 'competencia': competencia_anterior}
			if vinculo is not None:
				filtro = {'vinculo': vinculo, 'competencia': competencia_anterior}

			lancamento_anterior = Lancamento.objects.filter(**filtro).first()
			
			if lancamento_anterior:
				return lancamento_anterior.base_fgts
			else:
				# Se não encontrou, tenta o mês anterior ao anterior
				if data_anterior.month > 1 or data_anterior.year > 2020:
					return Lancamento.obter_base_fgts_anterior(funcionario, competencia_anterior, vinculo=vinculo)
		except:
			pass
		
		return None

	class Meta:
		verbose_name = 'Lançamento'
		verbose_name_plural = 'Lançamentos'
		# Permite mais de um lançamento no mesmo mês para o mesmo CPF, desde que seja em vínculos diferentes.
		# Mantém compatibilidade com registros legados (vinculo nulo).
		unique_together = ('empresa', 'funcionario', 'competencia', 'parcela_13', 'vinculo')
		indexes = [
			models.Index(fields=['empresa', 'competencia'], name='idx_lanc_empresa_comp'),
			models.Index(fields=['funcionario', 'competencia'], name='idx_lanc_func_comp'),
			models.Index(fields=['vinculo', 'competencia', 'parcela_13'], name='idx_lanc_vinc_comp_p13'),
			models.Index(fields=['empresa', 'competencia', 'pago'], name='idx_lanc_emp_comp_pago'),
		]


class ImportacaoLancamento(models.Model):
	STATUS_CHOICES = [
		('preview', 'Aguardando confirmação'),
		('pending', 'Aguardando'),
		('processing', 'Processando'),
		('done', 'Concluído'),
		('error', 'Erro'),
	]

	usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='importacoes_lancamento')
	empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True)
	arquivo = models.FileField(upload_to='importacoes/lancamentos/')
	nome_arquivo = models.CharField(max_length=255)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
	linhas_total = models.IntegerField(null=True, blank=True)
	linhas_processadas = models.IntegerField(default=0)
	criado_em = models.DateTimeField(auto_now_add=True)
	atualizado_em = models.DateTimeField(auto_now=True)
	resultado_json = models.JSONField(null=True, blank=True)
	preview_resultado = models.JSONField(null=True, blank=True)
	mensagem_erro = models.TextField(blank=True)

	# Opções escolhidas pelo usuário no momento do upload
	recalcular_fgts = models.BooleanField(
		default=True,
		verbose_name='Recalcular FGTS',
		help_text='True = forçar 8% da base; False = manter o valor VALOR_FGTS do arquivo.',
	)
	aplicar_jam = models.BooleanField(
		default=False,
		verbose_name='Aplicar correção JAM',
		help_text='Aplica juros acumulados (JAM) até a data de referência sobre o valor FGTS importado.',
	)
	extrato_analitico = models.BooleanField(
		default=False,
		verbose_name='Extrato Analítico',
		help_text='Todos os lançamentos pagos desta importação serão marcados como confirmados pelo Extrato Analítico da CEF.',
	)
	data_referencia_jam = models.DateField(
		null=True,
		blank=True,
		verbose_name='Data de referência JAM',
		help_text='Data até a qual o JAM é calculado. Se em branco, usa a data de hoje.',
	)

	class Meta:
		ordering = ['-criado_em']
		verbose_name = 'Importação de Lançamentos'
		verbose_name_plural = 'Importações de Lançamentos'


class ImportacaoResponsabilidade(models.Model):
	"""Registro de aceite de responsabilidade do usuário na confirmação do import."""

	importacao = models.OneToOneField(
		ImportacaoLancamento,
		on_delete=models.CASCADE,
		related_name='responsabilidade',
	)
	usuario = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		related_name='responsabilidades_importacao',
	)
	# Espelho das opções no momento da confirmação (imutável após criação)
	recalcular_fgts_escolha = models.BooleanField()
	aplicar_jam_escolha = models.BooleanField()
	data_referencia_jam_escolha = models.DateField(null=True, blank=True)
	# Checkbox explícito de aceite
	aceite_responsabilidade = models.BooleanField(default=False)
	# Texto exato exibido ao usuário (para rastreabilidade legal)
	texto_termos = models.TextField()
	# Contexto de rede
	ip_address = models.GenericIPAddressField(null=True, blank=True)
	user_agent = models.TextField(blank=True)
	criado_em = models.DateTimeField(auto_now_add=True)
	# Contadores preenchidos após o job de background
	linhas_valor_do_arquivo = models.IntegerField(default=0)
	linhas_jam_aplicado = models.IntegerField(default=0)

	class Meta:
		verbose_name = 'Responsabilidade de Importação'
		verbose_name_plural = 'Responsabilidades de Importação'

	def __str__(self):
		return f"Responsabilidade import #{self.importacao_id} — {self.usuario}"


class ImportacaoRE(models.Model):
	"""Rastreia cada importação de arquivo SEFIP.RE ou PDF do relatório SEFIP."""

	TIPO_FONTE_CHOICES = [
		('re_texto', 'Arquivo .RE (texto)'),
		('pdf', 'PDF visual SEFIP'),
	]
	STATUS_CHOICES = [
		('preview', 'Aguardando confirmação'),
		('pending', 'Aguardando'),
		('processing', 'Processando'),
		('done', 'Concluído'),
		('error', 'Erro'),
	]

	usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='importacoes_re')
	empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True)
	arquivo = models.FileField(upload_to='importacoes/re/')
	nome_arquivo = models.CharField(max_length=255)
	tipo_fonte = models.CharField(max_length=20, choices=TIPO_FONTE_CHOICES)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
	linhas_total = models.IntegerField(null=True, blank=True)
	linhas_processadas = models.IntegerField(default=0)
	resultado_json = models.JSONField(null=True, blank=True)
	preview_resultado = models.JSONField(null=True, blank=True)
	mensagem_erro = models.TextField(blank=True)
	criado_em = models.DateTimeField(auto_now_add=True)
	atualizado_em = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-criado_em']
		verbose_name = 'Importação RE/SEFIP'
		verbose_name_plural = 'Importações RE/SEFIP'

	def __str__(self):
		return f"ImportacaoRE #{self.pk} — {self.nome_arquivo}"


class ImportacaoExtratoAnalitico(models.Model):
	"""Rastreia cada importação de Extrato Analítico da CEF para confirmação de pagamentos."""

	STATUS_CHOICES = [
		('preview', 'Aguardando confirmação'),
		('pending', 'Aguardando'),
		('processing', 'Processando'),
		('done', 'Concluído'),
		('error', 'Erro'),
	]

	usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='importacoes_extrato')
	empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True)
	arquivo = models.FileField(upload_to='importacoes/extrato_analitico/')
	nome_arquivo = models.CharField(max_length=255)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
	linhas_total = models.IntegerField(null=True, blank=True)
	linhas_processadas = models.IntegerField(default=0)
	resultado_json = models.JSONField(null=True, blank=True)
	preview_resultado = models.JSONField(null=True, blank=True)
	mensagem_erro = models.TextField(blank=True)
	criado_em = models.DateTimeField(auto_now_add=True)
	atualizado_em = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-criado_em']
		verbose_name = 'Importação Extrato Analítico'
		verbose_name_plural = 'Importações Extrato Analítico'

	def __str__(self):
		return f"ImportacaoExtrato #{self.pk} — {self.nome_arquivo}"

from lancamentos.models_relatorio import RelatorioTask  # noqa: E402,F401
