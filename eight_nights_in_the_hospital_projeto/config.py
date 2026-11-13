"""
config.py - TODOS os números do jogo ficam aqui.

Quer deixar o jogo mais fácil ou mais difícil? Mexa nos valores deste arquivo,
sem precisar mexer no resto do código.
"""

TITULO = "Eight Nights in the Hospital"
LARGURA, ALTURA = 1200, 800
FPS = 60

# True = ativa atalhos para testar (tecla N pula direto para o amanhecer)
MODO_TESTE = False

# ---------------------------------------------------------------- jogador
VELOCIDADE_JOGADOR = 220          # pixels por segundo
POS_INICIAL = (520, 620)          # onde a Ophelia começa (pés)
# limites por onde ela pode andar: (x_min, y_min, x_max, y_max)
LIMITES = (310, 195, 1110, 770)
# obstáculos retangulares (x, y, largura, altura): o balcão no meio da sala
# (a parte de cima do balcão fica livre para dar passagem)
OBSTACULOS = [(630, 290, 40, 230)]

# ---------------------------------------------------------------- cenário
# centro de cada cama (x, y). Os pacientes ficam nas primeiras camas.
CAMAS = [(205, 175), (205, 300), (200, 428), (195, 560)]
# janelas: x do canto esquerdo (o retângulo é 248 x 118 e começa em y = 3)
JANELAS_X = [265, 678]
GERADOR_POS = (1075, 175)         # onde ficar para mexer no gerador
PORTA = (1135, 470)               # por onde entram a Enfermeira Maldita
# esconderijos: (nome, ponto onde a Ophelia fica escondida, alcance para entrar)
ESCONDERIJOS = [
    ("armário", (594, 200), 120),
    ("balcão", (650, 545), 110),
    ("atrás da cama", (325, 365), 105),      # perto dos pacientes
    ("atrás da cama", (325, 640), 105),
]
# pontos por onde a Enfermeira Maldita passeia
PONTOS_PATRULHA = [(450, 300), (900, 300), (480, 650), (950, 650),
                   (760, 700), (820, 450), (420, 480)]
# de onde a Sombra pode surgir (escolhemos o ponto mais longe da Ophelia)
PONTOS_SOMBRA = [(330, 730), (1090, 740), (1100, 230), (700, 740)]

# ---------------------------------------------------------------- interação
DIST_PACIENTE = 150
DIST_JANELA = 170
DIST_GERADOR = 140
TEMPO_CURA = 3.0                  # segundos segurando E (GDD: 3 s)
# ---------------------------------------------------------------- pontuação (GDD 3.4)
PONTOS_ATENDIMENTO = 500          # paciente atendido com sucesso
LIMITE_ATENDIMENTO = 70           # só conta se a vida dele estava em 70% ou menos
PONTOS_ENERGIA = 200              # restabelecimento de energia (blackout)
PONTOS_POR_SEGUNDO = 10           # tempo total de sobrevivência
TEMPO_JANELA_FECHADA = 7.0        # a janela fechada reabre depois disso

# ---------------------------------------------------------------- lanterna
ALCANCE_LANTERNA = 380
ANGULO_LANTERNA = 32              # meio-ângulo do cone de luz, em graus
ESCURIDAO_ALPHA = 238             # 0 = nada escuro, 255 = breu total

# ---------------------------------------------------------------- entidades
ATRASO_SOMBRA = 3.0               # segundos entre a energia cair e a Sombra surgir
DIST_PEGAR_SOMBRA = 38
VISAO_MALDITA = 300               # a que distância a Maldita enxerga a Ophelia
VEL_MALDITA_PATRULHA = 70
TEMPO_INVASAO = 1.6               # animação do Espreitador entrando

# ---------------------------------------------------------------- as 8 noites (GDD 3.4)
# duracao em MINUTOS (tempo real).   vida_perde = pontos de vida perdidos por
# segundo por paciente.   quedas = quantas vezes a energia cai.
# sombra_vel = velocidade da Sombra (px/s): lenta, "média", "rápida", "alta velocidade".
NOITES = [
    dict(pacientes=1, duracao=1, entidades=["sombra"], quedas=1, alerta=True,
         vida_perde=0.7, sombra_vel=70, gerador=5,
         dica="Segure E perto da cama para curar. Se a energia cair, ligue o gerador e use a lanterna (F)."),
    dict(pacientes=2, duracao=2.5, entidades=["sombra"], quedas=1, alerta=True,
         vida_perde=0.9, sombra_vel=75, gerador=5,
         dica="Agora são 2 pacientes. Divida bem o seu tempo."),
    dict(pacientes=2, duracao=3, entidades=["sombra", "espreitador"], quedas=2, alerta=True,
         vida_perde=1.1, sombra_vel=80, gerador=5, esp_intervalo=20, esp_tempo=9,
         dica="Novo: Espreitador. Quando ele aparecer numa janela, feche-a apertando E perto dela."),
    dict(pacientes=3, duracao=3.5, entidades=["sombra", "espreitador"], quedas=2, alerta=False,
         vida_perde=1.3, sombra_vel=100, gerador=5, esp_intervalo=18, esp_tempo=8.5,
         dica="O alerta visual sumiu: observe as janelas! A Sombra está mais rápida."),
    dict(pacientes=3, duracao=4, entidades=["sombra", "maldita"], quedas=2, alerta=False,
         vida_perde=1.4, sombra_vel=105, gerador=5,
         maldita_intervalo=40, maldita_presenca=24, maldita_vel=125,
         dica="Nova: Enfermeira Maldita. Esconda-se (Ctrl) no armário ou atrás do balcão."),
    dict(pacientes=4, duracao=4.5, entidades=["sombra", "maldita"], quedas=3, alerta=False,
         vida_perde=1.5, sombra_vel=125, gerador=5,
         maldita_intervalo=34, maldita_presenca=26, maldita_vel=140,
         dica="4 pacientes e a Sombra bem mais rápida."),
    dict(pacientes=4, duracao=5, entidades=["sombra", "espreitador", "maldita"], quedas=3,
         alerta=False, vida_perde=1.6, sombra_vel=130, gerador=5, esp_intervalo=16, esp_tempo=8.5,
         maldita_intervalo=32, maldita_presenca=28, maldita_vel=150,
         dica="O Espreitador volta, agora junto com a Enfermeira Maldita."),
    dict(pacientes=4, duracao=6, entidades=["sombra", "espreitador", "maldita"], quedas=4,
         alerta=False, vida_perde=1.8, sombra_vel=150, gerador=5, esp_intervalo=14, esp_tempo=8,
         maldita_intervalo=28, maldita_presenca=30, maldita_vel=165,
         dica="Última noite: tudo está na velocidade máxima. Boa sorte!"),
]

# ---------------------------------------------------------------- trilha sonora (GDD 6)
# nome usado no código -> arquivo dentro da pasta sons/ (.ogg, .wav ou .mp3)
MUSICAS = {
    "menu": "audioMenu",              # tela de início
    "calma": "audioCalma",            # sem ameaças
    "tensao": "audioTensao",          # entidade presente
    "perseguicao": "audioPerseguicao",  # perigo iminente
    "esconderijo": "audioEsconderijo",  # silêncio tenso
    "vitoria": "audioVencer",         # amanhecer
    "derrota": "audioDerrota",        # game over
}
TROCA_MUSICA_MIN = 1.5                # segundos mínimos entre trocas de música


def pontos_ideais(noite):
    """Pontuação de uma noite "muito boa" (usada para calcular as metas das estrelas)."""
    c = NOITES[noite - 1]
    segundos = c["duracao"] * 60
    # uma cura devolve em média uns 45 pontos de vida
    atendimentos = c["pacientes"] * max(1, round(segundos * c["vida_perde"] / 45))
    return segundos * PONTOS_POR_SEGUNDO + atendimentos * PONTOS_ATENDIMENTO + c["quedas"] * PONTOS_ENERGIA


# (pontuação para 2 estrelas, pontuação para 3 estrelas) de cada noite
METAS = [
    (400, 750),     # Noite 1
    (600, 900),    # Noite 2
    (1000, 1300),    # Noite 3
    (1300, 1700),   # Noite 4
    (1500, 2000),   # Noite 5
    (1900, 2500),  # Noite 6
    (2600, 3500),  # Noite 7
    (3500, 4500),  # Noite 8
]


def metas_estrelas(noite):
    """(2 estrelas, 3 estrelas) = pontuação mínima e pontuação máxima da noite."""
    return METAS[noite - 1]
