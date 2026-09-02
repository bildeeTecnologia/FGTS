from django.contrib import admin
from .models import Usuario, EmpresaUsuarioRole

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
	list_display = ('username', 'email', 'empresa', 'is_multi_empresa', 'is_staff', 'is_superuser')
	search_fields = ('username', 'email', 'first_name', 'last_name')
	list_filter = ('empresa', 'is_multi_empresa', 'is_staff', 'is_superuser')
	filter_horizontal = ('empresas_permitidas',)

@admin.register(EmpresaUsuarioRole)
class EmpresaUsuarioRoleAdmin(admin.ModelAdmin):
	list_display = ('usuario', 'empresa', 'role', 'criado_em')
	list_filter = ('empresa', 'role')
	search_fields = ('usuario__username', 'empresa__nome')
