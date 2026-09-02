from django.urls import path
from . import views

urlpatterns = [
    path('', views.FuncionarioListView.as_view(), name='funcionario-list'),
    path('novo/', views.FuncionarioCreateView.as_view(), name='funcionario-create'),
    path('<int:pk>/editar/', views.FuncionarioUpdateView.as_view(), name='funcionario-update'),
    path('<int:pk>/excluir/', views.FuncionarioDeleteView.as_view(), name='funcionario-delete'),
    path('baixar-modelo/', views.FuncionarioDownloadTemplateView.as_view(), name='funcionario-download-template'),
    path('importar/', views.FuncionarioUploadImportView.as_view(), name='funcionario-import'),
    path('json/', views.funcionarios_json, name='funcionarios-json'),
    path('autocomplete/', views.funcionarios_autocomplete, name='funcionarios-autocomplete'),
    path('vinculos/json/', views.vinculos_json, name='vinculos-json'),
    path('<int:pk>/', views.FuncionarioDetailView.as_view(), name='funcionario-detail'),
    path('vinculos/atualizar/', views.VinculoUploadUpdateView.as_view(), name='vinculo-bulk-update'),
    path('vinculos/baixar-modelo-atualizacao/', views.VinculoDownloadUpdateTemplateView.as_view(), name='vinculo-download-update-template'),
    path('<int:pk>/vinculos/novo/', views.FuncionarioVinculoCreateView.as_view(), name='funcionario-vinculo-create'),
    path('<int:pk>/transferir/', views.FuncionarioTransferenciaView.as_view(), name='funcionario-transferir'),
    path('<int:pk>/vinculos/<int:vid>/recalcular/', views.VinculoRecalcularView.as_view(), name='vinculo-recalcular'),
]
