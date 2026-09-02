from django.urls import path
from .views import UsuarioRegisterView, ConfirmEmailView

urlpatterns = [
    path('registrar/', UsuarioRegisterView.as_view(), name='register'),
    path('confirmar-email/<uidb64>/<token>/', ConfirmEmailView.as_view(), name='confirm-email'),
]
