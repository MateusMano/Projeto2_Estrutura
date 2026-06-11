"""Estruturas de dados estudadas no projeto."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Generic, Iterable, Iterator, TypeVar

from atendimento.models import Cliente

T = TypeVar("T")


class Fila(Generic[T]):
    """Fila FIFO baseada em deque, com enfileirar O(1) e desenfileirar O(1)."""

    def __init__(self, itens: Iterable[T] | None = None) -> None:
        self._dados: deque[T] = deque(itens or [])

    def enfileirar(self, item: T) -> None:
        self._dados.append(item)

    def desenfileirar(self) -> T:
        if self.vazia():
            raise IndexError("fila vazia")
        return self._dados.popleft()

    def vazia(self) -> bool:
        return not self._dados

    def tamanho(self) -> int:
        return len(self._dados)

    def remover_por_cliente(self, cliente_id: int) -> T | None:
        for item in list(self._dados):
            if getattr(item, "cliente_id", None) == cliente_id:
                self._dados.remove(item)
                return item
        return None

    def contem_cliente(self, cliente_id: int) -> bool:
        return any(getattr(item, "cliente_id", None) == cliente_id for item in self._dados)

    def to_list(self) -> list[T]:
        return list(self._dados)

    def __iter__(self) -> Iterator[T]:
        return iter(self._dados)


class Pilha(Generic[T]):
    """Pilha LIFO para desfazer a ultima finalizacao."""

    def __init__(self, itens: Iterable[T] | None = None) -> None:
        self._dados: list[T] = list(itens or [])

    def empilhar(self, item: T) -> None:
        self._dados.append(item)

    def desempilhar(self) -> T:
        if self.vazia():
            raise IndexError("pilha vazia")
        return self._dados.pop()

    def vazia(self) -> bool:
        return not self._dados

    def to_list(self) -> list[T]:
        return list(self._dados)


@dataclass
class NoCliente:
    cliente: Cliente
    proximo: NoCliente | None = None


class ListaClientesAtivos:
    """Lista encadeada usada para controlar clientes ativos."""

    def __init__(self) -> None:
        self.inicio: NoCliente | None = None

    def reconstruir(self, clientes: Iterable[Cliente]) -> None:
        self.inicio = None
        for cliente in clientes:
            if cliente.ativo:
                self.adicionar(cliente)

    def adicionar(self, cliente: Cliente) -> None:
        novo = NoCliente(cliente=cliente)
        if self.inicio is None:
            self.inicio = novo
            return
        atual = self.inicio
        while atual.proximo is not None:
            atual = atual.proximo
        atual.proximo = novo

    def remover_inativos(self) -> list[int]:
        removidos: list[int] = []
        anterior: NoCliente | None = None
        atual = self.inicio
        while atual is not None:
            if not atual.cliente.ativo:
                removidos.append(atual.cliente.id)
                if anterior is None:
                    self.inicio = atual.proximo
                else:
                    anterior.proximo = atual.proximo
            else:
                anterior = atual
            atual = atual.proximo
        return removidos

    def ids(self) -> list[int]:
        resultado: list[int] = []
        atual = self.inicio
        while atual is not None:
            resultado.append(atual.cliente.id)
            atual = atual.proximo
        return resultado


class VetorClientesOrdenado:
    """Vetor ordenado por id com busca binaria recursiva."""

    def __init__(self, clientes: Iterable[Cliente] | None = None) -> None:
        self._clientes: list[Cliente] = []
        for cliente in clientes or []:
            self.inserir(cliente)

    def inserir(self, cliente: Cliente) -> None:
        existente = self.buscar(cliente.id)
        if existente is not None:
            self._clientes = [
                cliente if atual.id == cliente.id else atual for atual in self._clientes
            ]
            return
        posicao = 0
        while posicao < len(self._clientes) and self._clientes[posicao].id < cliente.id:
            posicao += 1
        self._clientes.insert(posicao, cliente)

    def remover(self, cliente_id: int) -> None:
        self._clientes = [cliente for cliente in self._clientes if cliente.id != cliente_id]

    def buscar(self, cliente_id: int) -> Cliente | None:
        return self._buscar_recursivo(cliente_id, 0, len(self._clientes) - 1)

    def _buscar_recursivo(
        self, cliente_id: int, inicio: int, fim: int
    ) -> Cliente | None:
        if inicio > fim:
            return None
        meio = (inicio + fim) // 2
        cliente = self._clientes[meio]
        if cliente.id == cliente_id:
            return cliente
        if cliente_id < cliente.id:
            return self._buscar_recursivo(cliente_id, inicio, meio - 1)
        return self._buscar_recursivo(cliente_id, meio + 1, fim)

    def to_list(self) -> list[Cliente]:
        return list(self._clientes)
        