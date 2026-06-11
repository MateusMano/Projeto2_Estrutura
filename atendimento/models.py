"""Modelos de dados do sistema."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


@dataclass
class Cliente:
    id: int
    nome: str
    telefone: str
    prioridade: bool = False
    ativo: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Cliente":
        return cls(
            id=int(data["id"]),
            nome=str(data["nome"]),
            telefone=str(data["telefone"]),
            prioridade=bool(data.get("prioridade", False)),
            ativo=bool(data.get("ativo", True)),
        )


@dataclass
class Atendente:
    id: int
    nome: str
    ocupado: bool = False
    cliente_atual_id: int | None = None
    inicio_atendimento: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "nome": self.nome,
            "ocupado": self.ocupado,
            "cliente_atual_id": self.cliente_atual_id,
            "inicio_atendimento": format_datetime(self.inicio_atendimento),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Atendente":
        return cls(
            id=int(data["id"]),
            nome=str(data["nome"]),
            ocupado=bool(data.get("ocupado", False)),
            cliente_atual_id=data.get("cliente_atual_id"),
            inicio_atendimento=parse_datetime(data.get("inicio_atendimento")),
        )


@dataclass
class AtendimentoAberto:
    cliente_id: int
    prioridade: bool
    entrada_fila: datetime
    atendente_id: int | None = None
    inicio_atendimento: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "cliente_id": self.cliente_id,
            "prioridade": self.prioridade,
            "entrada_fila": format_datetime(self.entrada_fila),
            "atendente_id": self.atendente_id,
            "inicio_atendimento": format_datetime(self.inicio_atendimento),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AtendimentoAberto":
        return cls(
            cliente_id=int(data["cliente_id"]),
            prioridade=bool(data["prioridade"]),
            entrada_fila=parse_datetime(data["entrada_fila"]) or datetime.now(),
            atendente_id=data.get("atendente_id"),
            inicio_atendimento=parse_datetime(data.get("inicio_atendimento")),
        )


@dataclass
class RegistroAtendimento:
    cliente_id: int
    atendente_id: int
    data: datetime
    duracao_minutos: float
    espera_minutos: float
    prioridade: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "cliente_id": self.cliente_id,
            "atendente_id": self.atendente_id,
            "data": format_datetime(self.data),
            "duracao_minutos": self.duracao_minutos,
            "espera_minutos": self.espera_minutos,
            "prioridade": self.prioridade,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RegistroAtendimento":
        return cls(
            cliente_id=int(data["cliente_id"]),
            atendente_id=int(data["atendente_id"]),
            data=parse_datetime(data["data"]) or datetime.now(),
            duracao_minutos=float(data["duracao_minutos"]),
            espera_minutos=float(data.get("espera_minutos", 0)),
            prioridade=bool(data.get("prioridade", False)),
        )


def format_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.strftime(DATE_FORMAT)


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.strptime(value, DATE_FORMAT)