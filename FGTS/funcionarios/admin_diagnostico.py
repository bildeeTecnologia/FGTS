from django.contrib import admin
from django.db import connection, transaction
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse

from .models import DiagnosticoOrfaos, Funcionario

# ── Queries de diagnóstico (todas SELECT) ────────────────────────────────────

_SQL_FUNCIONARIOS_SEM_VINCULO = """
    SELECT f.id, f.nome, f.cpf, f.pis
    FROM funcionarios_funcionario f
    WHERE NOT EXISTS (
        SELECT 1 FROM empresas_funcionariovinculo v WHERE v.funcionario_id = f.id
    )
    ORDER BY f.nome;
"""

# Sem vínculo MAS com lançamentos — PERIGOSO deletar.
_SQL_FUNC_SEM_VINCULO_COM_LANCAMENTO = """
    SELECT
        f.id,
        f.nome,
        f.cpf,
        e.nome AS empresa,
        COUNT(l.id) AS qtd_lancamentos,
        MIN(l.competencia) AS primeira_competencia,
        MAX(l.competencia) AS ultima_competencia
    FROM funcionarios_funcionario f
    JOIN lancamentos_lancamento l ON l.funcionario_id = f.id
    JOIN empresas_empresa e ON l.empresa_id = e.id
    WHERE NOT EXISTS (
        SELECT 1 FROM empresas_funcionariovinculo v WHERE v.funcionario_id = f.id
    )
    GROUP BY f.id, f.nome, f.cpf, e.id, e.nome
    ORDER BY f.nome, e.nome;
"""

# Sem vínculo E sem lançamentos — candidatos seguros.
_SQL_FUNC_SEM_VINCULO_SEM_LANCAMENTO = """
    SELECT f.id, f.nome, f.cpf, f.pis
    FROM funcionarios_funcionario f
    WHERE NOT EXISTS (
        SELECT 1 FROM empresas_funcionariovinculo v WHERE v.funcionario_id = f.id
    )
    AND NOT EXISTS (
        SELECT 1 FROM lancamentos_lancamento l WHERE l.funcionario_id = f.id
    )
    ORDER BY f.nome;
"""

# IDs seguros para deletar (usado na limpeza).
_SQL_IDS_SEGUROS = """
    SELECT f.id
    FROM funcionarios_funcionario f
    WHERE NOT EXISTS (
        SELECT 1 FROM empresas_funcionariovinculo v WHERE v.funcionario_id = f.id
    )
    AND NOT EXISTS (
        SELECT 1 FROM lancamentos_lancamento l WHERE l.funcionario_id = f.id
    );
"""

_SQL_VINCULOS_EMPRESA_INEXISTENTE = """
    SELECT v.id, v.funcionario_id, f.nome AS funcionario, v.empresa_id, v.status
    FROM empresas_funcionariovinculo v
    JOIN funcionarios_funcionario f ON v.funcionario_id = f.id
    LEFT JOIN empresas_empresa e ON v.empresa_id = e.id
    WHERE e.id IS NULL
    ORDER BY f.nome;
"""

_SQL_LANCAMENTOS_EMPRESA_INEXISTENTE = """
    SELECT l.id, l.funcionario_id, f.nome AS funcionario, l.empresa_id, l.competencia
    FROM lancamentos_lancamento l
    JOIN funcionarios_funcionario f ON l.funcionario_id = f.id
    LEFT JOIN empresas_empresa e ON l.empresa_id = e.id
    WHERE e.id IS NULL
    ORDER BY f.nome, l.competencia;
"""

_SQL_LANCAMENTOS_FUNCIONARIO_INEXISTENTE = """
    SELECT l.id, l.funcionario_id, l.empresa_id, l.competencia
    FROM lancamentos_lancamento l
    LEFT JOIN funcionarios_funcionario f ON l.funcionario_id = f.id
    WHERE f.id IS NULL
    ORDER BY l.empresa_id, l.competencia;
"""


def _executar_query(sql):
    """Executa SELECT e devolve (colunas, linhas) onde linhas são listas."""
    with connection.cursor() as cursor:
        cursor.execute(sql)
        colunas = [col[0] for col in cursor.description]
        linhas = [list(row) for row in cursor.fetchall()]
    return colunas, linhas


@admin.register(DiagnosticoOrfaos)
class DiagnosticoOrfaosAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # ── URLs customizadas ────────────────────────────────────────────────────

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'limpar-orfaos/',
                self.admin_site.admin_view(self.limpar_orfaos_view),
                name='funcionarios_limpar_orfaos',
            ),
        ]
        return custom + urls

    # ── View de confirmação + execução da limpeza ────────────────────────────

    def limpar_orfaos_view(self, request):
        cols, candidatos = _executar_query(_SQL_FUNC_SEM_VINCULO_SEM_LANCAMENTO)

        if request.method == 'POST' and request.POST.get('confirmar') == 'sim':
            # Re-executa a query para pegar IDs no momento exato da exclusão,
            # garantindo que nada mudou entre a confirmação e o clique.
            with connection.cursor() as cursor:
                cursor.execute(_SQL_IDS_SEGUROS)
                ids_seguros = [row[0] for row in cursor.fetchall()]

            if ids_seguros:
                with transaction.atomic():
                    deletados, _ = Funcionario.objects.filter(
                        pk__in=ids_seguros,
                        # Dupla verificação via ORM: recusa qualquer um com vínculo ou lançamento
                        vinculos__isnull=True,
                        lancamentos__isnull=True,
                    ).delete()
            else:
                deletados = 0

            diag_url = reverse('admin:funcionarios_diagnosticoorfaos_changelist')
            self.message_user(
                request,
                f'✔ {deletados} funcionário(s) órfão(s) excluído(s) com segurança.',
            )
            return HttpResponseRedirect(diag_url)

        context = {
            **self.admin_site.each_context(request),
            'title': 'Confirmar limpeza de funcionários órfãos',
            'opts': self.model._meta,
            'candidatos_cols': cols,
            'candidatos': candidatos,
        }
        return TemplateResponse(
            request,
            'admin/funcionarios/confirmar_limpeza.html',
            context,
        )

    # ── View principal do diagnóstico ────────────────────────────────────────

    def changelist_view(self, request, extra_context=None):
        cols1, func_sem_vinculo = _executar_query(_SQL_FUNCIONARIOS_SEM_VINCULO)
        cols1b, func_sem_vinculo_com_lanc = _executar_query(_SQL_FUNC_SEM_VINCULO_COM_LANCAMENTO)
        cols1c, func_sem_vinculo_sem_lanc = _executar_query(_SQL_FUNC_SEM_VINCULO_SEM_LANCAMENTO)
        cols2, vinculos_orfaos = _executar_query(_SQL_VINCULOS_EMPRESA_INEXISTENTE)
        cols3, lanc_empresa_orfa = _executar_query(_SQL_LANCAMENTOS_EMPRESA_INEXISTENTE)
        cols4, lanc_func_orfao = _executar_query(_SQL_LANCAMENTOS_FUNCIONARIO_INEXISTENTE)

        summaries = [
            ('Funcionários sem vínculo (total)', len(func_sem_vinculo), 'sec1', False),
            ('  ↳ com lançamentos — NÃO deletar', len(func_sem_vinculo_com_lanc), 'sec1b', True),
            ('  ↳ sem lançamentos — seguros para limpeza', len(func_sem_vinculo_sem_lanc), 'sec1c', False),
            ('Vínculos com empresa inexistente', len(vinculos_orfaos), 'sec2', True),
            ('Lançamentos com empresa inexistente', len(lanc_empresa_orfa), 'sec3', True),
            ('Lançamentos com funcionário inexistente', len(lanc_func_orfao), 'sec4', True),
        ]

        limpar_url = reverse('admin:funcionarios_limpar_orfaos')

        context = {
            **self.admin_site.each_context(request),
            'title': 'Diagnóstico de Dados Órfãos',
            'opts': self.model._meta,
            'summaries': summaries,
            'limpar_url': limpar_url,
            'func_sem_vinculo_cols': cols1,
            'func_sem_vinculo': func_sem_vinculo,
            'func_sem_vinculo_com_lanc_cols': cols1b,
            'func_sem_vinculo_com_lanc': func_sem_vinculo_com_lanc,
            'func_sem_vinculo_sem_lanc_cols': cols1c,
            'func_sem_vinculo_sem_lanc': func_sem_vinculo_sem_lanc,
            'vinculos_orfaos_cols': cols2,
            'vinculos_orfaos': vinculos_orfaos,
            'lanc_empresa_orfa_cols': cols3,
            'lanc_empresa_orfa': lanc_empresa_orfa,
            'lanc_func_orfao_cols': cols4,
            'lanc_func_orfao': lanc_func_orfao,
        }
        return TemplateResponse(
            request,
            'admin/funcionarios/diagnostico.html',
            context,
        )
