"""
Testes para RQ Workers health check.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from django.test import TestCase

from vert_helper.health_checks.rq_workers import check_rq_workers_alive


class RQWorkersHealthCheckTest(TestCase):
    """Testes para check_rq_workers_alive."""

    @patch("vert_helper.health_checks.rq_workers.django_rq")
    def test_all_workers_alive(self, mock_django_rq):
        """Deve retornar OK quando todos os workers estão vivos."""
        mock_connection = MagicMock()
        mock_worker1 = MagicMock()
        mock_worker1.name = "worker1"
        mock_worker2 = MagicMock()
        mock_worker2.name = "worker2"

        mock_django_rq.get_connection.return_value = mock_connection
        mock_django_rq.Worker.all.return_value = [mock_worker1, mock_worker2]

        result = check_rq_workers_alive({"expected_count": 2})

        assert result.status == "OK"
        assert "2/2" in result.message

    @patch("vert_helper.health_checks.rq_workers.django_rq")
    def test_worker_missing(self, mock_django_rq):
        """Deve retornar FAILED quando faltam workers."""
        mock_connection = MagicMock()
        mock_worker = MagicMock()
        mock_worker.name = "worker1"

        mock_django_rq.get_connection.return_value = mock_connection
        mock_django_rq.Worker.all.return_value = [mock_worker]

        result = check_rq_workers_alive({"expected_count": 3})

        assert result.status == "FAILED"
        assert "1/3" in result.message
        assert "2 worker(s) faltando" in result.message

    @patch("vert_helper.health_checks.rq_workers.django_rq")
    def test_no_workers_alive(self, mock_django_rq):
        """Deve retornar FAILED quando nenhum worker está ativo."""
        mock_connection = MagicMock()
        mock_django_rq.get_connection.return_value = mock_connection
        mock_django_rq.Worker.all.return_value = []

        result = check_rq_workers_alive()

        assert result.status == "FAILED"
        assert "Nenhum worker ativo" in result.message

    @patch("vert_helper.health_checks.rq_workers.django_rq")
    def test_workers_no_expected_count(self, mock_django_rq):
        """Deve retornar OK sem expected_count se há workers vivos."""
        mock_connection = MagicMock()
        mock_worker = MagicMock()
        mock_worker.name = "worker1"

        mock_django_rq.get_connection.return_value = mock_connection
        mock_django_rq.Worker.all.return_value = [mock_worker]

        result = check_rq_workers_alive()

        assert result.status == "OK"
        assert "1 worker(s) ativo(s)" in result.message

    def test_django_rq_not_installed(self):
        """Deve retornar UNKNOWN quando django_rq não está instalado."""
        with patch.dict("sys.modules", {"django_rq": None}):
            result = check_rq_workers_alive()
            assert result.status == "UNKNOWN"
            assert "não instalado" in result.message

    @patch("vert_helper.health_checks.rq_workers.django_rq")
    def test_redis_connection_error(self, mock_django_rq):
        """Deve retornar FAILED quando há erro de conexão."""
        mock_django_rq.get_connection.side_effect = Exception(
            "Connection refused"
        )

        result = check_rq_workers_alive()

        assert result.status == "FAILED"
        assert "Erro ao conectar" in result.message

    @patch("vert_helper.health_checks.rq_workers.django_rq")
    def test_one_worker_of_twenty_dead(self, mock_django_rq):
        """Deve retornar FAILED se 1 de 20 workers morrer."""
        mock_connection = MagicMock()
        workers = [MagicMock(name=f"worker{i}") for i in range(19)]

        mock_django_rq.get_connection.return_value = mock_connection
        mock_django_rq.Worker.all.return_value = workers

        result = check_rq_workers_alive({"expected_count": 20})

        assert result.status == "FAILED"
        assert "19/20" in result.message
        assert "1 worker(s) faltando" in result.message
