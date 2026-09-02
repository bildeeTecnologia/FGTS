from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import AuditLog


class AuditLogModelTest(TestCase):
    """Testes para o modelo AuditLog"""
    
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    def test_create_audit_log(self):
        """Testa criação de um log de auditoria"""
        log = AuditLog.objects.create(
            user=self.user,
            action='LOGIN',
            ip_address='127.0.0.1',
            object_repr='Login: testuser'
        )
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, 'LOGIN')
        self.assertEqual(log.ip_address, '127.0.0.1')
    
    def test_audit_log_str(self):
        """Testa representação em string do log"""
        log = AuditLog.objects.create(
            user=self.user,
            action='LOGIN',
            object_repr='Login: testuser'
        )
        self.assertIn('testuser', str(log))
        self.assertIn('Login', str(log))
