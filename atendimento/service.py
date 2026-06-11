"""Regras de negocio do sistema de atendimento."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from atendimento.models import (
    Atendente,
    AtendimentoAberto,
    Cliente,
    RegistroAtendimento,
)
from atendimento.repository import JsonRepository
from atendimento.structures import Fila, ListaClientesAtivos, Pilha, VetorClientesOrdenado


class ErroRegraNegocio(ValueError):
    """Erro previsto de regra de negocio ou entrada invalida."""


class AtendimentoService:
    """Coordena dados, estruturas e regras do sistema."""

    def __init__(self, repository: JsonRepository | None = None) -> None:
        self.repository = repository or JsonRepository()
        self.logger = self._criar_logger()
        estado = self.repository.carregar()
        self.clientes_temporarios: list[Cliente] = list(estado["clientes"])
        self.atendentes: list[Atendente] = list(estado["atendentes"])
        self.fila_prioridade = Fila[AtendimentoAberto](estado["fila_prioridade"])
        self.fila_comum = Fila[AtendimentoAberto](estado["fila_comum"])
        self.em_atendimento: list[AtendimentoAberto] = list(estado["em_atendimento"])
        self.historico: list[RegistroAtendimento] = list(estado["historico"])
        self.pilha_desfazer = Pilha[RegistroAtendimento](estado["desfazer"])
        self.vetor_clientes = VetorClientesOrdenado(self.clientes_temporarios)
        self.lista_ativos = ListaClientesAtivos()
        self.lista_ativos.reconstruir(self.clientes_temporarios)

    def cadastrar_cliente(
        self, cliente_id: int, nome: str, telefone: str, prioridade: bool
    ) -> Cliente:
        self._validar_id(cliente_id)
        if self.buscar_cliente(cliente_id) is not None:
            raise ErroRegraNegocio("Ja existe cliente com esse id.")
        if not nome.strip():
            raise ErroRegraNegocio("Nome do cliente nao pode ficar vazio.")
        cliente = Cliente(cliente_id, nome.strip(), telefone.strip(), prioridade)
        self.clientes_temporarios.append(cliente)
        self.vetor_clientes.inserir(cliente)
        self.lista_ativos.adicionar(cliente)
        self.logger.info("Cliente cadastrado: id=%s nome=%s", cliente.id, cliente.nome)
        self.salvar()
        return cliente

    def cadastrar_atendente(self, atendente_id: int, nome: str) -> Atendente:
        self._validar_id(atendente_id)
        if self._buscar_atendente(atendente_id) is not None:
            raise ErroRegraNegocio("Ja existe atendente com esse id.")
        if not nome.strip():
            raise ErroRegraNegocio("Nome do atendente nao pode ficar vazio.")
        atendente = Atendente(atendente_id, nome.strip())
        self.atendentes.append(atendente)
        self.logger.info("Atendente cadastrado: id=%s nome=%s", atendente.id, atendente.nome)
        self.salvar()
        return atendente

    def abrir_atendimento(
        self, cliente_id: int, agora: datetime | None = None
    ) -> AtendimentoAberto:
        cliente = self._obter_cliente(cliente_id)
        if not cliente.ativo:
            raise ErroRegraNegocio("Cliente inativo nao pode entrar na fila.")
        if self._cliente_tem_atendimento_aberto(cliente_id):
            raise ErroRegraNegocio("Cliente ja possui atendimento em aberto.")
        atendimento = AtendimentoAberto(
            cliente_id=cliente.id,
            prioridade=cliente.prioridade,
            entrada_fila=agora or datetime.now(),
        )
        fila = self.fila_prioridade if cliente.prioridade else self.fila_comum
        fila.enfileirar(atendimento)
        self.logger.info("Atendimento aberto: cliente_id=%s", cliente.id)
        self.salvar()
        return atendimento

    def chamar_proximo(
        self, atendente_id: int, agora: datetime | None = None
    ) -> AtendimentoAberto:
        atendente = self._obter_atendente(atendente_id)
        if atendente.ocupado:
            raise ErroRegraNegocio("Atendente ja esta em atendimento.")
        if self.fila_prioridade.vazia() and self.fila_comum.vazia():
            raise ErroRegraNegocio("Nao ha clientes na fila.")
        fila = self.fila_prioridade if not self.fila_prioridade.vazia() else self.fila_comum
        atendimento = fila.desenfileirar()
        inicio = agora or datetime.now()
        atendimento.atendente_id = atendente.id
        atendimento.inicio_atendimento = inicio
        atendente.ocupado = True
        atendente.cliente_atual_id = atendimento.cliente_id
        atendente.inicio_atendimento = inicio
        self.em_atendimento.append(atendimento)
        self.logger.info(
            "Atendimento chamado: cliente_id=%s atendente_id=%s",
            atendimento.cliente_id,
            atendente.id,
        )
        self.salvar()
        return atendimento

    def finalizar_atendimento(
        self, atendente_id: int, agora: datetime | None = None
    ) -> RegistroAtendimento:
        atendente = self._obter_atendente(atendente_id)
        if not atendente.ocupado or atendente.cliente_atual_id is None:
            raise ErroRegraNegocio("Atendente nao possui atendimento em aberto.")
        atendimento = self._remover_em_atendimento(atendente.cliente_atual_id)
        fim = agora or datetime.now()
        inicio = atendimento.inicio_atendimento or atendente.inicio_atendimento or fim
        duracao = max((fim - inicio).total_seconds() / 60, 0)
        espera = max((inicio - atendimento.entrada_fila).total_seconds() / 60, 0)
        registro = RegistroAtendimento(
            cliente_id=atendimento.cliente_id,
            atendente_id=atendente.id,
            data=fim,
            duracao_minutos=round(duracao, 2),
            espera_minutos=round(espera, 2),
            prioridade=atendimento.prioridade,
        )
        self.historico.append(registro)
        self.pilha_desfazer.empilhar(registro)
        atendente.ocupado = False
        atendente.cliente_atual_id = None
        atendente.inicio_atendimento = None
        self.logger.info(
            "Atendimento finalizado: cliente_id=%s atendente_id=%s duracao=%.2f",
            registro.cliente_id,
            registro.atendente_id,
            registro.duracao_minutos,
        )
        self.salvar()
        return registro

    def desfazer_ultima_finalizacao(self) -> RegistroAtendimento:
        if self.pilha_desfazer.vazia():
            raise ErroRegraNegocio("Nao ha finalizacao para desfazer.")
        registro = self.pilha_desfazer.desempilhar()
        for indice in range(len(self.historico) - 1, -1, -1):
            atual = self.historico[indice]
            if atual == registro:
                self.historico.pop(indice)
                break
        self.logger.info(
            "Finalizacao desfeita: cliente_id=%s atendente_id=%s",
            registro.cliente_id,
            registro.atendente_id,
        )
        self.salvar()
        return registro

    def marcar_cliente_inativo(self, cliente_id: int) -> Cliente:
        cliente = self._obter_cliente(cliente_id)
        if self._cliente_tem_atendimento_aberto(cliente_id):
            raise ErroRegraNegocio("Nao e permitido remover cliente com atendimento em aberto.")
        cliente.ativo = False
        self.vetor_clientes.inserir(cliente)
        self.lista_ativos.reconstruir(self.clientes_temporarios)
        self.lista_ativos.remover_inativos()
        self.logger.info("Cliente marcado como inativo: id=%s", cliente.id)
        self.salvar()
        return cliente

    def remover_clientes_inativos(self) -> list[int]:
        removidos: list[int] = []
        ativos: list[Cliente] = []
        for cliente in self.clientes_temporarios:
            if cliente.ativo:
                ativos.append(cliente)
            else:
                if self._cliente_tem_atendimento_aberto(cliente.id):
                    raise ErroRegraNegocio(
                        f"Cliente {cliente.id} possui atendimento em aberto."
                    )
                removidos.append(cliente.id)
                self.vetor_clientes.remover(cliente.id)
        self.clientes_temporarios = ativos
        self.lista_ativos.reconstruir(self.clientes_temporarios)
        self.logger.info("Clientes inativos removidos: %s", removidos)
        self.salvar()
        return removidos

    def historico_por_cliente(self, cliente_id: int) -> list[RegistroAtendimento]:
        self._obter_cliente(cliente_id)
        return [item for item in self.historico if item.cliente_id == cliente_id]

    def buscar_cliente(self, cliente_id: int) -> Cliente | None:
        return self.vetor_clientes.buscar(cliente_id)
    
    def listar_filas(self) -> dict[str, list[AtendimentoAberto]]:
        return {
            "prioridade": self.fila_prioridade.to_list(),
            "comum": self.fila_comum.to_list(),
            "em_atendimento": list(self.em_atendimento),
        }

    def salvar(self) -> None:
        self.repository.salvar(
            {
                "clientes": self.clientes_temporarios,
                "atendentes": self.atendentes,
                "fila_prioridade": self.fila_prioridade.to_list(),
                "fila_comum": self.fila_comum.to_list(),
                "em_atendimento": self.em_atendimento,
                "historico": self.historico,
                "desfazer": self.pilha_desfazer.to_list(),
            }
        )

    def _cliente_tem_atendimento_aberto(self, cliente_id: int) -> bool:
        if self.fila_prioridade.contem_cliente(cliente_id):
            return True
        if self.fila_comum.contem_cliente(cliente_id):
            return True
        return any(item.cliente_id == cliente_id for item in self.em_atendimento)

    def _remover_em_atendimento(self, cliente_id: int) -> AtendimentoAberto:
        for indice, atendimento in enumerate(self.em_atendimento):
            if atendimento.cliente_id == cliente_id:
                return self.em_atendimento.pop(indice)
        raise ErroRegraNegocio("Atendimento em aberto nao encontrado.")

    def _obter_cliente(self, cliente_id: int) -> Cliente:
        cliente = self.buscar_cliente(cliente_id)
        if cliente is None:
            raise ErroRegraNegocio("Cliente nao encontrado.")
        return cliente

    def _buscar_atendente(self, atendente_id: int) -> Atendente | None:
        for atendente in self.atendentes:
            if atendente.id == atendente_id:
                return atendente
        return None

    def _obter_atendente(self, atendente_id: int) -> Atendente:
        atendente = self._buscar_atendente(atendente_id)
        if atendente is None:
            raise ErroRegraNegocio("Atendente nao encontrado.")
        return atendente

    def _validar_id(self, valor: int) -> None:
        if valor <= 0:
            raise ErroRegraNegocio("Id deve ser um numero positivo.")

    def _criar_logger(self) -> logging.Logger:
        Path("logs").mkdir(exist_ok=True)
        logger = logging.getLogger("atendimento")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.FileHandler("logs/operacoes.log", encoding="utf-8")
            formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger