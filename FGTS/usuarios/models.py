from django.db import models
from django.contrib.auth.models import AbstractUser
from empresas.models import Empresa


class Usuario(AbstractUser):
	manutencao = models.BooleanField(default=False)
	# Controle de verificação de email
	email_confirmed = models.BooleanField(default=False)
	email_confirmed_at = models.DateTimeField(null=True, blank=True)
	# Empresa principal (escopo padrão do usuário)
	empresa = models.ForeignKey(
		Empresa,
		on_delete=models.PROTECT,
		null=True,
		blank=True,
		related_name='usuarios',
		verbose_name='Empresa'
	)
	# Permite atuar em múltiplas empresas (modo gestor multiempresas)
	empresas_permitidas = models.ManyToManyField(
		Empresa,
		blank=True,
		related_name='usuarios_permitidos',
		verbose_name='Empresas permitidas'
	)
	# Flag para indicar que pode operar várias empresas sem trocar login
	is_multi_empresa = models.BooleanField(default=False, verbose_name='Gestor multiempresas')

	def __str__(self):
		return self.username


# Controle de papéis do usuário por empresa
class EmpresaUsuarioRole(models.Model):
	ADMIN = 'admin'
	GESTOR = 'gestor'
	OPERADOR = 'operador'
	ROLE_CHOICES = [
		(ADMIN, 'Administrador'),
		(GESTOR, 'Gestor'),
		(OPERADOR, 'Operador'),
	]
	usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE, related_name='roles_empresas')
	empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='usuarios_roles')
	role = models.CharField(max_length=20, choices=ROLE_CHOICES)
	criado_em = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('usuario', 'empresa')
		verbose_name = 'Permissão de Usuário por Empresa'
		verbose_name_plural = 'Permissões de Usuário por Empresa'

	def __str__(self):
		return f"{self.usuario.username} - {self.empresa.nome} ({self.get_role_display()})"
