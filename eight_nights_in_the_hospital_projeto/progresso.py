"""
progresso.py - guarda no computador o progresso do jogador (arquivo progresso.json):
noites desbloqueadas, estrelas conquistadas e o ranking local.
"""
import json
import os

ARQUIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "progresso.json")


def carregar():
    dados = {"desbloqueada": 1, "estrelas": {}, "ranking": []}
    try:
        with open(ARQUIVO, encoding="utf-8") as f:
            dados.update(json.load(f))
    except (OSError, ValueError):
        pass                      # arquivo não existe ou está quebrado: começa do zero
    return dados


def salvar(dados):
    try:
        with open(ARQUIVO, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
    except OSError:
        pass                      # se não der para salvar, o jogo continua normalmente


def registrar_noite(dados, noite, pontos, estrelas):
    """Chamado quando o jogador sobrevive a uma noite."""
    chave = str(noite)
    dados["estrelas"][chave] = max(estrelas, dados["estrelas"].get(chave, 0))
    dados["desbloqueada"] = max(dados["desbloqueada"], min(noite + 1, 8))
    dados["ranking"].append({"noite": noite, "pontos": pontos})
    dados["ranking"].sort(key=lambda r: r["pontos"], reverse=True)
    dados["ranking"] = dados["ranking"][:10]       # só os 10 melhores
    salvar(dados)
