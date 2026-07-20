"""
Testes para Django-Q2 health check.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from django.test import TestCase

from vert_helper.health_checks.django_q2 import check_django_q2_queue


class DjangoQ2HealthCheckTest(TestCase):
    """Testes para check_django_q2_queue."""

    @patch("vert_helper.health_checks.django_q2.Task")
    @patch("vert_helper.health_checks.django_q2.Stat")
    def test_cluster_healthy_with_recent_tasks(self, mock_stat, mock_task):
        """Deve retornar OK quando cluster está respondendo e processando tasks."""
        mock_stat.get_all.return_value = {"workers": 2, "tasks": 5}
        
        mock_recent = MagicMock()
        mock_recent.exists.return_value = True
        mock_task.objects.filter.return_value = mock_recent

        result = check_django_q2_queue({"queue_name": "default"})

        assert result.status == "OK"
        assert "respondendo" in result.message

    @patch("vert_helper.health_checks.django_q2.OrmQ")
    @patch("vert_helper.health_checks.django_q2.Task")
    @patch("vert_helper.health_checks.django_q2.Stat")
    def test_cluster_stalled_tasks_pending(self, mock_stat, mock_task, mock_orm_q):
        """Deve retornar FAILED quando cluster está travado (tasks aguardando)."""
        mock_stat.get_all.return_value = {"workers": 2}
        
        # Sem tasks recentes
        mock_recent = MagicMock()
        mock_recent.exists.return_value = False
        
        # Mas há tasks aguardando
        mock_pending = MagicMock()
        mock_pending.count.return_value = 10
        
        mock_task.objects.filter.return_value = mock_recent
        mock_orm_q.objects.filter.return_value = mock_pending

        result = check_django_q2_queue({"queue_name": "default"})

        assert result.status == "FAILED"
        assert "travado" in result.message
        assert "10" in result.message

    @patch("vert_helper.health_checks.django_q2.Task")
    @patch("vert_helper.health_checks.django_q2.Stat")
    def test_cluster_not_responding_no_stats(self, mock_stat, mock_task):
        """Deve retornar FAILED quando cluster não está respondendo (sem stats)."""
        mock_stat.get_all.return_value = None

        result = check_django_q2_queue({"queue_name": "default"})

        assert result.status == "FAILED"
        assert "não respondendo" in result.message

    @patch("vert_helper.health_checks.django_q2.OrmQ")
    @patch("vert_helper.health_checks.django_q2.Task")
    @patch("vert_helper.health_checks.django_q2.Stat")
    def test_cluster_healthy_no_pending_tasks(self, mock_stat, mock_task, mock_orm_q):
        """Deve retornar OK quando cluster respondendo e sem tasks (vazio é OK)."""
        mock_stat.get_all.return_value = {"workers": 2}
        
        # Sem tasks recentes
        mock_recent = MagicMock()
        mock_recent.exists.return_value = False
        
        # Sem tasks aguardando
        mock_pending = MagicMock()
        mock_pending.count.return_value = 0
        
        mock_task.objects.filter.return_value = mock_recent
        mock_orm_q.objects.filter.return_value = mock_pending

        result = check_django_q2_queue({"queue_name": "default"})

        assert result.status == "OK"
        assert "sem tasks" in result.message

    def test_django_q_not_installed(self):
        """Deve retornar UNKNOWN quando django_q não está instalado."""
        with patch.dict("sys.modules", {"django_q": None}):
            result = check_django_q2_queue({"queue_name": "default"})
            assert result.status == "UNKNOWN"
            assert "não instalado" in result.message

    @patch("vert_helper.health_checks.django_q2.Task")
    @patch("vert_helper.health_checks.django_q2.Stat")
    def test_queue_name_parameter(self, mock_stat, mock_task):
        """Deve usar queue_name correto no filtro."""
        mock_stat.get_all.return_value = {"workers": 2}
        mock_recent = MagicMock()
        mock_recent.exists.return_value = True
        mock_task.objects.filter.return_value = mock_recent

        check_django_q2_queue({"queue_name": "long"})

        # Verificar que o filtro foi chamado com queue_name="long"
        calls = mock_task.objects.filter.call_args_list
        assert any("long" in str(call) for call in calls)

    @patch("vert_helper.health_checks.django_q2.Task")
    @patch("vert_helper.health_checks.django_q2.Stat")
    def test_connection_error(self, mock_stat, mock_task):
        """Deve retornar FAILED quando há erro de conexão."""
        mock_stat.get_all.side_effect = Exception("Database connection failed")

        result = check_django_q2_queue({"queue_name": "default"})

        assert result.status == "FAILED"
        assert "Erro ao verificar" in result.message

    @patch("vert_helper.health_checks.django_q2.OrmQ")
    @patch("vert_helper.health_checks.django_q2.Task")
    @patch("vert_helper.health_checks.django_q2.Stat")
    def test_multiple_clusters_expected(self, mock_stat, mock_task, mock_orm_q):
        """Deve retornar OK mesmo com expected_count (não valida quantidade exata)."""
        mock_stat.get_all.return_value = {"workers": 4}
        
        mock_recent = MagicMock()
        mock_recent.exists.return_value = True
        mock_task.objects.filter.return_value = mock_recent

        result = check_django_q2_queue({
            "queue_name": "default",
            "expected_count": 3,  # Esperamos 3, mas não validamos
        })

        assert result.status == "OK"
        assert "1+ clusters" in result.message
