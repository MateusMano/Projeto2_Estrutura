"""Interface de terminal."""

from __future__ import annotations

from datetime import datetime, time
from pathlib import Path

from atendimento.models import DATE_FORMAT
from atendimento.reports import (
    alertas_espera_alta,
    exportar_csv,
    filtrar_por_data,
    ordenar_historico_por_duracao,
    tempo_medio_atendimento,
    top_clientes_mais_atendidos,
)
from atendimento.service import AtendimentoService, ErroRegraNegocio


def main() -> None:
    service = AtendimentoService()
    print("Sistema Completo de Atendimento")
    while True:
        mostrar_menu()
        opcao = input("Opcao: ").strip()
        try:
            if opcao == "1":
                cadastrar_cliente(service)
            elif opcao == "2":
                cadastrar_atendente(service)
            elif opcao == "3":
                abrir_atendimento(service)
            elif opcao == "4":
                chamar_proximo(service)
            elif opcao == "5":
                finalizar_atendimento(service)
            elif opcao == "6":
                mostrar_historico_cliente(service)
            elif opcao == "7":
                desfazer_finalizacao(service)
            elif opcao == "8":
                remover_inativos(service)
            elif opcao == "9":
                mostrar_relatorios(service)
            elif opcao == "10":
                exportar_relatorio(service)
            elif opcao == "11":
                buscar_cliente(service)
            elif opcao == "12":
                listar_filas(service)
            elif opcao == "0":
                print("Encerrando.")
                break
            else:
                print("Opcao invalida.")
        except ErroRegraNegocio as erro:
            print(f"Erro: {erro}")
        except ValueError:
            print("Entrada invalida. Digite os dados no formato solicitado.")


def mostrar_menu() -> None:
    print()
    print("1 - Cadastrar cliente")
    print("2 - Cadastrar atendente")
    print("3 - Abrir atendimento")
    print("4 - Chamar proximo")
    print("5 - Finalizar atendimento")
    print("6 - Historico por cliente")
    print("7 - Desfazer ultima finalizacao")
    print("8 - Remover clientes inativos")
    print("9 - Relatorios")
    print("10 - Exportar historico CSV")
    print("11 - Buscar cliente por id")
    print("12 - Listar filas")
    print("0 - Sair")


def cadastrar_cliente(service: AtendimentoService) -> None:
    cliente_id = ler_int("Id do cliente: ")
    nome = input("Nome: ")
    telefone = input("Telefone: ")
    prioridade = ler_bool("Prioridade? (s/n): ")
    cliente = service.cadastrar_cliente(cliente_id, nome, telefone, prioridade)
    print(f"Cliente cadastrado: {cliente.id} - {cliente.nome}")


def cadastrar_atendente(service: AtendimentoService) -> None:
    atendente_id = ler_int("Id do atendente: ")
    nome = input("Nome: ")
    atendente = service.cadastrar_atendente(atendente_id, nome)
    print(f"Atendente cadastrado: {atendente.id} - {atendente.nome}")


def abrir_atendimento(service: AtendimentoService) -> None:
    cliente_id = ler_int("Id do cliente: ")
    atendimento = service.abrir_atendimento(cliente_id)
    tipo = "prioridade" if atendimento.prioridade else "comum"
    print(f"Cliente {cliente_id} entrou na fila {tipo}.")


def chamar_proximo(service: AtendimentoService) -> None:
    atendente_id = ler_int("Id do atendente: ")
    atendimento = service.chamar_proximo(atendente_id)
    print(
        f"Chamado cliente {atendimento.cliente_id} para atendente {atendente_id}."
    )


def finalizar_atendimento(service: AtendimentoService) -> None:
    atendente_id = ler_int("Id do atendente: ")
    registro = service.finalizar_atendimento(atendente_id)
    print(
        "Atendimento finalizado: "
        f"{registro.duracao_minutos:.2f} min, espera {registro.espera_minutos:.2f} min."
    )


def mostrar_historico_cliente(service: AtendimentoService) -> None:
    cliente_id = ler_int("Id do cliente: ")
    historico = service.historico_por_cliente(cliente_id)
    if not historico:
        print("Cliente sem atendimentos finalizados.")
        return
    for item in historico:
        print(
            f"{item.data.strftime('%d/%m/%Y %H:%M')} | "
            f"atendente {item.atendente_id} | {item.duracao_minutos:.2f} min"
        )


def desfazer_finalizacao(service: AtendimentoService) -> None:
    registro = service.desfazer_ultima_finalizacao()
    print(
        f"Finalizacao removida do historico: cliente {registro.cliente_id}, "
        f"atendente {registro.atendente_id}."
    )


def remover_inativos(service: AtendimentoService) -> None:
    cliente_id = ler_int("Id do cliente a marcar como inativo: ")
    service.marcar_cliente_inativo(cliente_id)
    removidos = service.remover_clientes_inativos()
    print(f"Clientes removidos: {removidos if removidos else 'nenhum'}.")


def mostrar_relatorios(service: AtendimentoService) -> None:
    inicio = ler_data_opcional("Data inicial (AAAA-MM-DD ou vazio): ", inicio=True)
    fim = ler_data_opcional("Data final (AAAA-MM-DD ou vazio): ", inicio=False)
    historico = filtrar_por_data(service.historico, inicio, fim)
    print(f"Tempo medio: {tempo_medio_atendimento(historico):.2f} min")
    print("Top clientes:")
    for cliente_id, nome, total in top_clientes_mais_atendidos(
        historico, service.clientes_temporarios
    ):
        print(f"{cliente_id} - {nome}: {total}")
    alertas = alertas_espera_alta(historico)
    print(f"Alertas de espera alta (>=30 min): {len(alertas)}")
    print("Atendimentos ordenados por duracao:")
    for item in ordenar_historico_por_duracao(historico):
        print(f"Cliente {item.cliente_id}: {item.duracao_minutos:.2f} min")


def exportar_relatorio(service: AtendimentoService) -> None:
    destino = input("Arquivo destino (padrao data/relatorio.csv): ").strip()
    if not destino:
        destino = "data/relatorio.csv"
    caminho = exportar_csv(destino, service.historico, service.clientes_temporarios)
    print(f"CSV exportado para {caminho}")


def buscar_cliente(service: AtendimentoService) -> None:
    cliente_id = ler_int("Id do cliente: ")
    cliente = service.buscar_cliente(cliente_id)
    if cliente is None:
        print("Cliente nao encontrado.")
        return
    status = "ativo" if cliente.ativo else "inativo"
    prioridade = "prioridade" if cliente.prioridade else "comum"
    print(f"{cliente.id} - {cliente.nome} | {cliente.telefone} | {prioridade} | {status}")


def listar_filas(service: AtendimentoService) -> None:
    filas = service.listar_filas()
    for nome, itens in filas.items():
        print(f"{nome}: {[item.cliente_id for item in itens]}")


def ler_int(mensagem: str) -> int:
    valor = input(mensagem).strip()
    return int(valor)


def ler_bool(mensagem: str) -> bool:
    valor = input(mensagem).strip().lower()
    if valor in {"s", "sim", "y", "yes"}:
        return True
    if valor in {"n", "nao", "não", "no"}:
        return False
    raise ValueError("booleano invalido")


def ler_data_opcional(mensagem: str, inicio: bool) -> datetime | None:
    valor = input(mensagem).strip()
    if not valor:
        return None
    data = datetime.strptime(valor, "%Y-%m-%d").date()
    horario = time.min if inicio else time.max
    return datetime.combine(data, horario).replace(microsecond=0)


def carregar_exemplo() -> None:
    origem = Path("data/exemplo_atendimentos.json")
    destino = Path("data/atendimentos.json")
    destino.write_text(origem.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Base de exemplo carregada em {destino}")


__all__ = ["main", "carregar_exemplo", "DATE_FORMAT"]