"""
icones.py - desenha, com formas simples do pygame, os ícones de acessibilidade
(GDD 3.3.7): pegadas, mão (batidas) e raio (energia caindo).
Assim não precisamos de arquivos de imagem para eles.
"""
import pygame

AMARELO = (255, 214, 64)
FUNDO = (20, 20, 28, 210)


def _base(tam):
    s = pygame.Surface((tam, tam), pygame.SRCALPHA)
    pygame.draw.circle(s, FUNDO, (tam // 2, tam // 2), tam // 2)
    pygame.draw.circle(s, AMARELO, (tam // 2, tam // 2), tam // 2, 2)
    return s


def _raio(tam):
    s = _base(tam); k = tam / 44
    pts = [(26, 6), (12, 26), (21, 26), (17, 39), (33, 18), (24, 18)]
    pygame.draw.polygon(s, AMARELO, [(x * k, y * k) for x, y in pts])
    return s


def _pegadas(tam):
    s = _base(tam); k = tam / 44
    for dx, dy in ((0, 8), (14, 0)):                     # dois pés
        pygame.draw.ellipse(s, AMARELO, pygame.Rect((10 + dx) * k, (16 + dy) * k, 9 * k, 13 * k))
        pygame.draw.circle(s, AMARELO, (int((14 + dx) * k), int((13 + dy) * k)), max(2, int(2 * k)))
    return s


def _mao(tam):
    s = _base(tam); k = tam / 44
    pygame.draw.rect(s, AMARELO, pygame.Rect(13 * k, 21 * k, 19 * k, 14 * k), border_radius=4)
    for i in range(4):                                   # quatro dedos
        pygame.draw.rect(s, AMARELO, pygame.Rect((13 + i * 5) * k, 9 * k, 4 * k, 15 * k), border_radius=2)
    return s


def criar_icones(tam=44):
    return {"raio": _raio(tam), "pegadas": _pegadas(tam), "mao": _mao(tam)}
