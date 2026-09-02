from django.urls import path

from .views import (
    EmpresaCreateView,
    EmpresaListView,
    EmpresaUpdateView,
    PainelAdminEmpresaView,
)

# Rotas do app de empresas
urlpatterns = [
    path('cadastrar/', EmpresaCreateView.as_view(), name='empresa-cadastrar'),
    path('listar/', EmpresaListView.as_view(), name='empresa-list'),
    path('editar/<int:pk>/', EmpresaUpdateView.as_view(), name='empresa-editar'),
    path('painel/<int:empresa_id>/', PainelAdminEmpresaView.as_view(), name='painel-admin-empresa'),
]
