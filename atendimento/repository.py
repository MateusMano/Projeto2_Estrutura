"""Persistencia em arquivos JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atendimento.models import (
    Atendente,
    AtendimentoAberto,
    Cliente,
    RegistroAtendimento,
)


class JsonRepository:
    """Repositorio simples em JSON para persistencia local."""

    def __init__(self, caminho: str | Path = "data/atendimentos.json") -> None:
        self.caminho = Path(caminho)

    def carregar(self) -> dict[str, Any]:
        if not self.caminho.exists():
            return self._estado_vazio()
        with self.caminho.open("r", encoding="utf-8") as arquivo:
            bruto = json.load(arquivo)
        return {
            "clientes": [Cliente.from_dict(item) for item in bruto.get("clientes", [])],
            "atendentes": [
                Atendente.from_dict(item) for item in bruto.get("atendentes", [])
            ],
            "fila_prioridade": [
                AtendimentoAberto.from_dict(item)
                for item in bruto.get("fila_prioridade", [])
            ],
            "fila_comum": [
                AtendimentoAberto.from_dict(item) for item in bruto.get("fila_comum", [])
            ],
            "em_atendimento": [
                AtendimentoAberto.from_dict(item)
                for item in bruto.get("em_atendimento", [])
            ],
            "historico": [
                RegistroAtendimento.from_dict(item)
                for item in bruto.get("historico", [])
            ],
            "desfazer": [
                RegistroAtendimento.from_dict(item) for item in bruto.get("desfazer", [])
            ],
        }

    def salvar(self, estado: dict[str, Any]) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        bruto = {
            "clientes": [item.to_dict() for item in estado["clientes"]],
            "atendentes": [item.to_dict() for item in estado["atendentes"]],
            "fila_prioridade": [
                item.to_dict() for item in estado["fila_prioridade"]
            ],
            "fila_comum": [item.to_dict() for item in estado["fila_comum"]],
            "em_atendimento": [item.to_dict() for item in estado["em_atendimento"]],
            "historico": [item.to_dict() for item in estado["historico"]],
            "desfazer": [item.to_dict() for item in estado["desfazer"]],
        }
        with self.caminho.open("w", encoding="utf-8") as arquivo:
            json.dump(bruto, arquivo, ensure_ascii=False, indent=2)

    def _estado_vazio(self) -> dict[str, list[Any]]:
        return {
            "clientes": [],
            "atendentes": [],
            "fila_prioridade": [],
            "fila_comum": [],
            "em_atendimento": [],
            "historico": [],
            "desfazer": [],
        }