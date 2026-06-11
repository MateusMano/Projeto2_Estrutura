"""Testes da camada de regras."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from atendimento.reports import (
    alertas_espera_alta,
    tempo_medio_atendimento,
    top_clientes_mais_atendidos,
)
from atendimento.repository import JsonRepository
from atendimento.service import AtendimentoService, ErroRegraNegocio


class AtendimentoServiceTest(unittest.TestCase):
    def criar_service(self) -> AtendimentoService:
        self.tmpdir = tempfile.TemporaryDirectory()
        caminho = Path(self.tmpdir.name) / "db.json"
        return AtendimentoService(JsonRepository(caminho))

    def tearDown(self) -> None:
        tmpdir = getattr(self, "tmpdir", None)
        if tmpdir is not None:
            tmpdir.cleanup()

    def test_busca_binaria_encontra_cliente_por_id(self) -> None:
        service = self.criar_service()
        service.cadastrar_cliente(20, "Bruno", "2222", False)
        service.cadastrar_cliente(10, "Ana", "1111", True)

        cliente = service.buscar_cliente(10)

        self.assertIsNotNone(cliente)
        self.assertEqual(cliente.nome, "Ana")
        self.assertIsNone(service.buscar_cliente(99))

    def test_prioridade_fica_na_frente_mantendo_ordem_de_chegada(self) -> None:
        service = self.criar_service()
        service.cadastrar_cliente(1, "Comum", "1", False)
        service.cadastrar_cliente(2, "Prioridade A", "2", True)
        service.cadastrar_cliente(3, "Prioridade B", "3", True)
        service.cadastrar_atendente(1, "Atendente")

        service.abrir_atendimento(1, datetime(2026, 6, 11, 8, 0, 0))
        service.abrir_atendimento(2, datetime(2026, 6, 11, 8, 1, 0))
        service.abrir_atendimento(3, datetime(2026, 6, 11, 8, 2, 0))

        primeiro = service.chamar_proximo(1, datetime(2026, 6, 11, 8, 3, 0))
        service.finalizar_atendimento(1, datetime(2026, 6, 11, 8, 8, 0))
        segundo = service.chamar_proximo(1, datetime(2026, 6, 11, 8, 9, 0))

        self.assertEqual(primeiro.cliente_id, 2)
        self.assertEqual(segundo.cliente_id, 3)

    def test_finalizar_registra_historico_e_desfazer_remove(self) -> None:
        service = self.criar_service()
        entrada = datetime(2026, 6, 11, 9, 0, 0)
        inicio = entrada + timedelta(minutes=10)
        fim = inicio + timedelta(minutes=25)
        service.cadastrar_cliente(1, "Ana", "1", False)
        service.cadastrar_atendente(1, "Marina")
        service.abrir_atendimento(1, entrada)
        service.chamar_proximo(1, inicio)

        registro = service.finalizar_atendimento(1, fim)
        desfeito = service.desfazer_ultima_finalizacao()

        self.assertEqual(registro.duracao_minutos, 25)
        self.assertEqual(registro.espera_minutos, 10)
        self.assertEqual(desfeito, registro)
        self.assertEqual(service.historico, [])

    def test_nao_remove_cliente_com_atendimento_aberto(self) -> None:
        service = self.criar_service()
        service.cadastrar_cliente(1, "Ana", "1", False)
        service.abrir_atendimento(1)

        with self.assertRaises(ErroRegraNegocio):
            service.marcar_cliente_inativo(1)

    def test_relatorios_calculam_media_top_e_alertas(self) -> None:
        service = self.criar_service()
        service.cadastrar_cliente(1, "Ana", "1", False)
        service.cadastrar_cliente(2, "Bruno", "2", False)
        service.cadastrar_atendente(1, "Marina")

        self._finalizar(service, 1, 10, 35)
        self._finalizar(service, 1, 20, 5)
        self._finalizar(service, 2, 30, 40)

        self.assertEqual(tempo_medio_atendimento(service.historico), 20)
        self.assertEqual(top_clientes_mais_atendidos(service.historico, service.clientes_temporarios)[0][0], 1)
        self.assertEqual(len(alertas_espera_alta(service.historico)), 2)

    def _finalizar(
        self, service: AtendimentoService, cliente_id: int, duracao: int, espera: int
    ) -> None:
        base = datetime(2026, 6, 11, 10, 0, 0) + timedelta(hours=len(service.historico))
        service.abrir_atendimento(cliente_id, base)
        service.chamar_proximo(1, base + timedelta(minutes=espera))
        service.finalizar_atendimento(1, base + timedelta(minutes=espera + duracao))


if __name__ == "__main__":
    unittest.main()