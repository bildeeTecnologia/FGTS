from django.urls import path
from .views import CoefJamListView
from .views_upload import CoefJamUploadView

urlpatterns = [
    path('', CoefJamListView.as_view(), name='coefjam-list'),
    path('importar/', CoefJamUploadView.as_view(), name='coefjam-upload'),
]
