"""Relatorios e exportacao CSV."""

from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime
from pathlib import Path

from atendimento.models import Cliente, RegistroAtendimento


def filtrar_por_data(
    historico: list[RegistroAtendimento],
    inicio: datetime | None = None,
    fim: datetime | None = None,
) -> list[RegistroAtendimento]:
    resultado = historico
    if inicio is not None:
        resultado = [item for item in resultado if item.data >= inicio]
    if fim is not None:
        resultado = [item for item in resultado if item.data <= fim]
    return resultado


def tempo_medio_atendimento(historico: list[RegistroAtendimento]) -> float:
    if not historico:
        return 0.0
    total = sum(item.duracao_minutos for item in historico)
    return round(total / len(historico), 2)


def top_clientes_mais_atendidos(
    historico: list[RegistroAtendimento], clientes: list[Cliente], limite: int = 5
) -> list[tuple[int, str, int]]:
    nomes = {cliente.id: cliente.nome for cliente in clientes}
    contagem = Counter(item.cliente_id for item in historico)
    itens = [(cliente_id, nomes.get(cliente_id, "Desconhecido"), total) for cliente_id, total in contagem.items()]
    ordenados = merge_sort_por_total(itens)
    return ordenados[:limite]


def alertas_espera_alta(
    historico: list[RegistroAtendimento], limite_minutos: float = 30.0
) -> list[RegistroAtendimento]:
    return [item for item in historico if item.espera_minutos >= limite_minutos]


def ordenar_historico_por_duracao(
    historico: list[RegistroAtendimento],
) -> list[RegistroAtendimento]:
    return quick_sort_registros(historico)


def merge_sort_por_total(
    itens: list[tuple[int, str, int]]
) -> list[tuple[int, str, int]]:
    if len(itens) <= 1:
        return list(itens)
    meio = len(itens) // 2
    esquerda = merge_sort_por_total(itens[:meio])
    direita = merge_sort_por_total(itens[meio:])
    return _intercalar_por_total(esquerda, direita)


def _intercalar_por_total(
    esquerda: list[tuple[int, str, int]], direita: list[tuple[int, str, int]]
) -> list[tuple[int, str, int]]:
    resultado: list[tuple[int, str, int]] = []
    i = 0
    j = 0
    while i < len(esquerda) and j < len(direita):
        if esquerda[i][2] >= direita[j][2]:
            resultado.append(esquerda[i])
            i += 1
        else:
            resultado.append(direita[j])
            j += 1
    resultado.extend(esquerda[i:])
    resultado.extend(direita[j:])
    return resultado


def quick_sort_registros(
    historico: list[RegistroAtendimento],
) -> list[RegistroAtendimento]:
    if len(historico) <= 1:
        return list(historico)
    pivo = historico[0]
    menores = [item for item in historico[1:] if item.duracao_minutos <= pivo.duracao_minutos]
    maiores = [item for item in historico[1:] if item.duracao_minutos > pivo.duracao_minutos]
    return quick_sort_registros(menores) + [pivo] + quick_sort_registros(maiores)


def exportar_csv(
    caminho: str | Path,
    historico: list[RegistroAtendimento],
    clientes: list[Cliente],
) -> Path:
    destino = Path(caminho)
    destino.parent.mkdir(parents=True, exist_ok=True)
    nomes = {cliente.id: cliente.nome for cliente in clientes}
    with destino.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(
            [
                "cliente_id",
                "cliente",
                "atendente_id",
                "data",
                "duracao_minutos",
                "espera_minutos",
                "prioridade",
            ]
        )
        for item in historico:
            escritor.writerow(
                [
                    item.cliente_id,
                    nomes.get(item.cliente_id, "Desconhecido"),
                    item.atendente_id,
                    item.data.strftime("%Y-%m-%d %H:%M:%S"),
                    item.duracao_minutos,
                    item.espera_minutos,
                    "sim" if item.prioridade else "nao",
                ]
            )
    return destino