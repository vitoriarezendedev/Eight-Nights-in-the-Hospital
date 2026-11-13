"""
Eight Nights in the Hospital  -  jogo 2D de terror e sobrevivência (Pygame)

Como rodar:   python main.py

Como o código está organizado
-----------------------------
  config.py     -> todos os números do jogo (dificuldade das 8 noites etc.)
  entidades.py  -> classes: Janela, Paciente, Jogador, Sombra, Maldita
  icones.py     -> ícones de acessibilidade desenhados por código
  progresso.py  -> salva estrelas e ranking em progresso.json
  main.py       -> ESTE arquivo: a classe Jogo, que junta tudo

A ideia central de um jogo em pygame é o LAÇO PRINCIPAL (método executar):
repetir ~60 vezes por segundo:   1) ler o teclado   2) atualizar o mundo
3) desenhar na tela.   O jogo tem vários "ESTADOS" (menu, jogando, pausa...) e,
para cada estado, existem métodos com o mesmo nome:
    tecla_<estado>(tecla)   atualizar_<estado>(dt)   desenhar_<estado>()
"""
import math
import os
import random
import sys

import pygame

import config as cfg
import progresso
from entidades import Janela, Paciente, Jogador, Sombra, Maldita
from icones import criar_icones

V = pygame.Vector2
RAIZ = os.path.dirname(os.path.abspath(__file__))
PASTA_SPRITES = os.path.join(RAIZ, "sprites")
PASTA_SONS = os.path.join(RAIZ, "sons")

BRANCO = (235, 235, 235)
VERMELHO = (200, 40, 40)
AMARELO = (255, 214, 64)
CINZA = (130, 130, 140)


# ====================================================================== áudio
class Audio:
    """Trilha sonora (GDD 6) e efeitos sonoros.

    * Músicas: ficam em  sons/  e são listadas em config.MUSICAS. Só UMA música toca
      por vez (pygame.mixer.music); trocar de música troca o arquivo que está tocando.
    * Efeitos: se existir um arquivo com um destes nomes em sons/ ele toca; se não
      existir, simplesmente fica mudo:  cura, gerador, energia_cai, janela_bate,
      janela_fecha, esconder, passos
    """

    def __init__(self):
        self.efeitos = {}
        self.musica_atual = None
        try:
            pygame.mixer.init()
        except pygame.error:
            self.ativo = False                # sem placa de som: o jogo roda mudo
            return
        self.ativo = True
        if os.path.isdir(PASTA_SONS):
            for arquivo in os.listdir(PASTA_SONS):
                nome, ext = os.path.splitext(arquivo)
                if ext.lower() in (".wav", ".ogg") and not nome.startswith("audio"):
                    try:
                        self.efeitos[nome] = pygame.mixer.Sound(os.path.join(PASTA_SONS, arquivo))
                    except pygame.error:
                        pass

    def tocar(self, nome):
        """Toca um efeito sonoro curto (se existir)."""
        efeito = self.efeitos.get(nome)
        if efeito:
            efeito.play()

    def musica(self, nome, repetir=True):
        """Troca a música de fundo. 'nome' é uma chave de config.MUSICAS.
        repetir=False toca uma vez só (vitória e derrota)."""
        if not self.ativo or nome == self.musica_atual:
            return
        self.musica_atual = nome
        arquivo = cfg.MUSICAS.get(nome)
        for ext in (".ogg", ".wav", ".mp3"):
            caminho = os.path.join(PASTA_SONS, str(arquivo) + ext)
            if arquivo and os.path.exists(caminho):
                try:
                    pygame.mixer.music.load(caminho)
                    pygame.mixer.music.play(-1 if repetir else 0, fade_ms=600 if repetir else 0)
                except pygame.error:
                    pass
                return
        pygame.mixer.music.stop()             # música não encontrada: silêncio

    def pausar(self):
        if self.ativo:
            pygame.mixer.music.pause()

    def retomar(self):
        if self.ativo:
            pygame.mixer.music.unpause()


# ====================================================================== jogo
class Jogo:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(cfg.TITULO)
        self.tela = pygame.display.set_mode((cfg.LARGURA, cfg.ALTURA))
        self.relogio = pygame.time.Clock()
        self.fontes = {}
        self.audio = Audio()
        self.carregar_imagens()
        self.icones = criar_icones(44)
        self.dados = progresso.carregar()
        self.obstaculos = [pygame.Rect(o) for o in cfg.OBSTACULOS]
        self.rodando = True
        self.estado = "menu"
        self.item_menu = 0
        self.noite_selecionada = 1
        self.relogio_geral = 0.0              # só para animações de menu
        self.noite = 1
        self.iniciar_noite(1)                 # cria o mundo (para nunca faltar atributo)
        self.estado = "menu"
        self.audio.musica("menu")

    # ------------------------------------------------------------ carregamento
    def carregar_imagens(self):
        def img(nome):
            return pygame.image.load(os.path.join(PASTA_SPRITES, nome)).convert_alpha()

        def espelhar(imagem):
            return pygame.transform.flip(imagem, True, False)

        self.img = {nome: img(nome + ".png") for nome in
                    ("cenario", "cenario_escuro", "janela_aberta", "janela_fechada",
                     "janela_espreitador", "paciente_deitado", "sombra",
                     "jogador_parado", "jogador_lanterna")}
        # os sprites originais olham para a direita; criamos a versão espelhada ("esq")
        self.anim = {}
        for nome in ("jogador_andando", "espreitador", "maldita", "paciente"):
            frames = [img(f"{nome}_{i}.png") for i in range(1, 5)]
            self.anim[nome] = {"dir": frames, "esq": [espelhar(f) for f in frames]}
        for nome in ("jogador_parado", "jogador_lanterna"):
            self.anim[nome] = {"dir": [self.img[nome]], "esq": [espelhar(self.img[nome])]}

    def fonte(self, tamanho):
        if tamanho not in self.fontes:
            self.fontes[tamanho] = pygame.font.Font(None, tamanho)
        return self.fontes[tamanho]

    # ------------------------------------------------------------ nova noite
    def iniciar_noite(self, numero):
        """Zera tudo e prepara a noite 'numero' (1 a 8) a partir do config.py."""
        self.noite = numero
        self.cfg = cfg.NOITES[numero - 1]
        c = self.cfg
        self.tempo = 0.0
        self.duracao = c["duracao"] * 60
        self.n_atendimentos = 0               # pacientes atendidos com sucesso
        self.n_energia = 0                    # vezes que a energia foi restabelecida
        self.jogador = Jogador()
        self.pacientes = [Paciente(i) for i in range(c["pacientes"])]
        self.janelas = [Janela(x) for x in cfg.JANELAS_X]
        # energia: sorteamos QUANDO ela vai cair (espaçado, longe do início e do fim)
        self.energia = True
        self.agenda_quedas = self.sortear_quedas(c["quedas"], self.duracao)
        self.sombra = None
        self.t_sombra = 0.0
        # temporizadores das entidades
        self.t_espreitador = 12.0
        self.maldita = None
        self.t_maldita = c.get("maldita_intervalo", 0) * 0.6
        self.t_musica = 0.0                   # tempo desde a última troca de música
        self.invasao = None                   # animação do Espreitador entrando
        # interação (segurar E)
        self.alvo_atual = None
        self.progresso_acao = 0.0
        self.barulho = False
        self.alertas = {"raio": 0.0, "pegadas": 0.0}   # ícones temporários (segundos restantes)
        self.causa = ""
        self.resultado = {}
        self.t_intro = 4.0
        self.estado = "intro"
        self.audio.musica("calma")

    @property
    def pontos(self):
        """Pontuação da noite (GDD 3.4): atendimentos + energia + tempo de sobrevivência."""
        segundos = min(self.tempo, self.duracao)
        return (self.n_atendimentos * cfg.PONTOS_ATENDIMENTO
                + self.n_energia * cfg.PONTOS_ENERGIA
                + int(segundos * cfg.PONTOS_POR_SEGUNDO))

    @staticmethod
    def sortear_quedas(quantidade, duracao):
        """Sorteia 'quantidade' instantes (em segundos) para a energia cair."""
        inicio, fim = 12.0, max(20.0, duracao - 15.0)
        tempos = []
        for _ in range(quantidade):
            for _tentativa in range(50):      # tenta até achar um instante com folga
                t = random.uniform(inicio, fim)
                if all(abs(t - outro) > 12 for outro in tempos):
                    tempos.append(t)
                    break
        return sorted(tempos)

    # ------------------------------------------------------------ laço principal
    def executar(self):
        while self.rodando:
            dt = min(self.relogio.tick(cfg.FPS) / 1000, 0.05)   # segundos desde o último quadro
            self.relogio_geral += dt
            self.tratar_eventos()
            atualizar = getattr(self, "atualizar_" + self.estado, None)
            if atualizar:
                atualizar(dt)
            getattr(self, "desenhar_" + self.estado)()
            pygame.display.flip()
        pygame.quit()

    def tratar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.rodando = False
            elif evento.type == pygame.KEYDOWN:
                tratar = getattr(self, "tecla_" + self.estado, None)
                if tratar:
                    tratar(evento.key)

    # ============================================================ TECLAS (por estado)
    def tecla_menu(self, tecla):
        if tecla in (pygame.K_UP, pygame.K_w):
            self.item_menu = (self.item_menu - 1) % 4
        elif tecla in (pygame.K_DOWN, pygame.K_s):
            self.item_menu = (self.item_menu + 1) % 4
        elif tecla in (pygame.K_RETURN, pygame.K_SPACE):
            if self.item_menu == 0:
                self.iniciar_noite(1)
            elif self.item_menu == 1:
                self.estado = "selecao"
            elif self.item_menu == 2:
                self.estado = "ranking"
            else:
                self.rodando = False

    def tecla_selecao(self, tecla):
        if tecla == pygame.K_ESCAPE:
            self.estado = "menu"
        elif tecla in (pygame.K_LEFT, pygame.K_a):
            self.noite_selecionada = max(1, self.noite_selecionada - 1)
        elif tecla in (pygame.K_RIGHT, pygame.K_d):
            self.noite_selecionada = min(8, self.noite_selecionada + 1)
        elif tecla in (pygame.K_UP, pygame.K_w):
            self.noite_selecionada = max(1, self.noite_selecionada - 4)
        elif tecla in (pygame.K_DOWN, pygame.K_s):
            self.noite_selecionada = min(8, self.noite_selecionada + 4)
        elif tecla in (pygame.K_RETURN, pygame.K_SPACE):
            if self.noite_selecionada <= self.dados["desbloqueada"]:
                self.iniciar_noite(self.noite_selecionada)

    def tecla_ranking(self, tecla):
        if tecla in (pygame.K_ESCAPE, pygame.K_RETURN):
            self.estado = "menu"

    def tecla_intro(self, tecla):
        if tecla in (pygame.K_RETURN, pygame.K_SPACE):
            self.t_intro = 0

    def tecla_jogando(self, tecla):
        if tecla == pygame.K_ESCAPE:
            self.estado = "pausa"
            self.audio.pausar()
        elif tecla in (pygame.K_LCTRL, pygame.K_RCTRL):
            self.alternar_esconderijo()
        elif tecla == pygame.K_f:
            self.jogador.lanterna = not self.jogador.lanterna
        elif tecla == pygame.K_e:
            self.apertou_e()
        elif tecla == pygame.K_n and cfg.MODO_TESTE:
            self.amanhecer()

    def tecla_pausa(self, tecla):
        if tecla == pygame.K_ESCAPE:
            self.estado = "jogando"
            self.audio.retomar()
        elif tecla == pygame.K_m:
            self.estado = "menu"
            self.audio.retomar()
            self.audio.musica("menu")

    def tecla_amanhecer(self, tecla):
        if tecla == pygame.K_RETURN:
            if self.noite < 8:
                self.iniciar_noite(self.noite + 1)
            else:
                self.estado = "fim"
        elif tecla == pygame.K_ESCAPE:
            self.estado = "menu"
            self.audio.musica("menu")

    def tecla_gameover(self, tecla):
        if tecla == pygame.K_RETURN:
            self.iniciar_noite(self.noite)
        elif tecla == pygame.K_ESCAPE:
            self.estado = "menu"
            self.audio.musica("menu")

    def tecla_fim(self, tecla):
        if tecla in (pygame.K_RETURN, pygame.K_ESCAPE):
            self.estado = "menu"
            self.audio.musica("menu")

    # ============================================================ REGRAS DO JOGO
    def atualizar_intro(self, dt):
        self.t_intro -= dt
        if self.t_intro <= 0:
            self.estado = "jogando"

    def atualizar_jogando(self, dt):
        c = self.cfg
        self.tempo += dt
        teclas = pygame.key.get_pressed()
        j = self.jogador

        # ---- 1) movimento (WASD ou setas)
        direcao = V(0, 0)
        if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
            direcao.x -= 1
        if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
            direcao.x += 1
        if teclas[pygame.K_w] or teclas[pygame.K_UP]:
            direcao.y -= 1
        if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
            direcao.y += 1
        if direcao.length() > 0:
            direcao = direcao.normalize()
        # escondida não se mexe; tentar se mexer (ou mexer em algo) faz BARULHO
        self.barulho = False
        if j.escondido:
            self.barulho = direcao.length() > 0 or teclas[pygame.K_e]
            direcao = V(0, 0)
        j.mover(direcao, dt, self.obstaculos, V(0, 0))
        # para onde ela olha: com lanterna, para o mouse; senão, para onde anda
        if j.lanterna:
            j.direcao = "dir" if self.direcao_mira().x >= 0 else "esq"
        elif direcao.x != 0:
            j.direcao = "dir" if direcao.x > 0 else "esq"

        # ---- 2) segurar E (curar paciente / religar gerador)
        self.atualizar_acao(dt, teclas[pygame.K_e])

        # ---- 3) pacientes perdem vida com o tempo
        for p in self.pacientes:
            p.vida -= c["vida_perde"] * dt
            if p.vida <= 0:
                return self.derrota("Um paciente não resistiu.")

        # ---- 4) entidades e eventos
        for nome in self.alertas:
            self.alertas[nome] = max(0.0, self.alertas[nome] - dt)
        self.atualizar_energia(dt)
        if self.invasao is None:
            self.atualizar_espreitador(dt)
        else:
            self.atualizar_invasao(dt)
            if self.estado != "jogando":
                return
        if "maldita" in c["entidades"]:
            self.atualizar_maldita(dt)
            if self.estado != "jogando":
                return
        self.atualizar_musica(dt)

        # ---- 5) chegou o amanhecer?
        if self.tempo >= self.duracao:
            self.amanhecer()

    # ---------------------------------------------------------- interação
    def alvo_interacao(self):
        """O que está perto o bastante para interagir? Devolve (tipo, objeto) ou None."""
        j = self.jogador
        candidatos = []                                   # (distância, tipo, objeto)
        for p in self.pacientes:
            d = (j.pos - p.centro).length()
            if d <= cfg.DIST_PACIENTE:
                candidatos.append((d, "paciente", p))
        for jan in self.janelas:
            d = (j.pos - jan.centro).length()
            if d <= cfg.DIST_JANELA and jan.estado == "espreitador":   # só se ele estiver lá
                candidatos.append((d, "janela", jan))
        if not self.energia:
            d = (j.pos - V(cfg.GERADOR_POS)).length()
            if d <= cfg.DIST_GERADOR:
                candidatos.append((d, "gerador", None))
        if not candidatos or j.escondido:
            return None
        melhor = min(candidatos, key=lambda item: item[0])   # o mais próximo ganha
        return melhor[1], melhor[2]

    def apertou_e(self):
        """Apertar E uma vez: fecha a janela (as ações longas ficam em atualizar_acao)."""
        alvo = self.alvo_interacao()
        if alvo and alvo[0] == "janela":
            janela = alvo[1]
            janela.estado = "fechada"
            janela.tempo = cfg.TEMPO_JANELA_FECHADA
            self.audio.tocar("janela_fecha")

    def atualizar_acao(self, dt, segurando_e):
        """Segurar E: enche uma barra de progresso. Soltar ou se afastar zera a barra."""
        alvo = self.alvo_interacao()
        valido = segurando_e and alvo is not None and alvo[0] in ("paciente", "gerador")
        if valido and alvo[0] == "paciente" and alvo[1].vida >= 99:
            valido = False                                 # paciente já está bem
        if not valido:
            self.alvo_atual = None
            self.progresso_acao = 0.0
            return
        if self.alvo_atual is None or self.alvo_atual[1] is not alvo[1] or self.alvo_atual[0] != alvo[0]:
            self.alvo_atual = alvo                         # mudou de alvo: recomeça
            self.progresso_acao = 0.0
        tempo_necessario = cfg.TEMPO_CURA if alvo[0] == "paciente" else self.cfg["gerador"]
        self.progresso_acao += dt / tempo_necessario
        if self.progresso_acao >= 1.0:
            if alvo[0] == "paciente":
                if alvo[1].vida <= cfg.LIMITE_ATENDIMENTO:      # só pontua se ele estava mal
                    self.n_atendimentos += 1
                alvo[1].vida = 100.0
                self.audio.tocar("cura")
            else:
                self.restaurar_energia()
            self.progresso_acao = 0.0
            self.alvo_atual = None

    def alternar_esconderijo(self):
        j = self.jogador
        if j.escondido:
            j.escondido = None                             # sair do esconderijo
            return
        for nome, ponto, alcance in cfg.ESCONDERIJOS:
            if (j.pos - V(ponto)).length() <= alcance:
                j.escondido = nome
                j.pos = V(ponto)
                j.lanterna = False
                self.audio.tocar("esconder")
                return

    # ---------------------------------------------------------- lanterna
    def direcao_mira(self):
        """Vetor (tamanho 1) do centro da enfermeira até o mouse."""
        mouse = V(pygame.mouse.get_pos())
        v = mouse - self.jogador.centro
        return v.normalize() if v.length() > 0 else V(1, 0)

    def ponto_iluminado(self, ponto):
        """O ponto está dentro do cone de luz da lanterna?"""
        j = self.jogador
        if not j.lanterna or j.escondido:
            return False
        v = ponto - j.centro
        distancia = v.length()
        if distancia > cfg.ALCANCE_LANTERNA:
            return False
        if distancia < 30:
            return True
        # angle_to dá o ângulo (em graus) entre dois vetores; trazemos para -180..180
        angulo = abs((self.direcao_mira().angle_to(v) + 180) % 360 - 180)
        return angulo <= cfg.ANGULO_LANTERNA

    # ---------------------------------------------------------- energia + Sombra
    def atualizar_energia(self, dt):
        if self.energia:
            if self.agenda_quedas and self.tempo >= self.agenda_quedas[0]:
                self.agenda_quedas.pop(0)
                self.energia = False
                self.sombra = None
                self.t_sombra = cfg.ATRASO_SOMBRA
                self.alertas["raio"] = 4.0
                self.audio.tocar("energia_cai")
            return
        # sem energia: depois de alguns segundos a Sombra aparece
        if self.sombra is None:
            self.t_sombra -= dt
            if self.t_sombra <= 0:
                j = self.jogador
                ponto = max(cfg.PONTOS_SOMBRA, key=lambda p: (V(p) - j.pos).length())  # o mais longe
                self.sombra = Sombra(ponto)
        else:
            luz = self.ponto_iluminado(self.sombra.centro)
            self.sombra.atualizar(dt, self.jogador, self.cfg["sombra_vel"], luz)
            if (not self.jogador.escondido
                    and (self.sombra.pos - self.jogador.pos).length() < cfg.DIST_PEGAR_SOMBRA):
                self.derrota("A Sombra pegou você no escuro.")

    def restaurar_energia(self):
        self.energia = True
        self.sombra = None
        self.n_energia += 1
        self.audio.tocar("gerador")
        # as próximas quedas ficam pelo menos 12 s depois de agora
        self.agenda_quedas = [max(t, self.tempo + 12) for t in self.agenda_quedas]

    # ---------------------------------------------------------- Espreitador
    def atualizar_espreitador(self, dt):
        c = self.cfg
        for jan in self.janelas:
            if jan.estado == "fechada":
                jan.tempo -= dt
                if jan.tempo <= 0:
                    jan.estado = "aberta"
            elif jan.estado == "espreitador":
                jan.tempo -= dt
                if jan.tempo <= 0:                         # não fechou a tempo: ele entra!
                    return self.iniciar_invasao(jan)
        if "espreitador" not in c["entidades"]:
            return
        self.t_espreitador -= dt
        if self.t_espreitador > 0:
            return
        self.t_espreitador = c["esp_intervalo"] * random.uniform(0.8, 1.2)
        abertas = [jan for jan in self.janelas if jan.estado == "aberta"]
        if not abertas:
            return
        escolhidas = abertas if c.get("esp_duplo") else [random.choice(abertas)]
        for jan in escolhidas:
            jan.estado = "espreitador"
            jan.tempo = c["esp_tempo"]
        self.audio.tocar("janela_bate")

    def iniciar_invasao(self, janela):
        j = self.jogador
        if not j.escondido and (j.pos - janela.centro).length() < 200:   # perto e visível: ele ataca a enfermeira
            alvo = j
            ponto = V(j.pos)
        else:                                              # senão, vai atrás do paciente mais próximo
            alvo = min(self.pacientes, key=lambda p: (p.centro - janela.centro).length())
            ponto = V(alvo.centro)
        self.invasao = {"pos": V(janela.centro) + V(0, 60), "alvo": ponto,
                        "tempo": cfg.TEMPO_INVASAO, "alvo_e_jogador": alvo is j,
                        "dir": "dir", "anim": 0.0}
        janela.estado = "aberta"

    def atualizar_invasao(self, dt):
        inv = self.invasao
        inv["tempo"] -= dt
        inv["anim"] += dt
        v = inv["alvo"] - inv["pos"]
        if v.length() > 0:
            inv["pos"] += v.normalize() * (v.length() / max(inv["tempo"], 0.05)) * dt
            inv["dir"] = "dir" if v.x > 0 else "esq"
        if inv["tempo"] <= 0:
            if inv["alvo_e_jogador"]:
                self.derrota("O Espreitador atacou você.")
            else:
                self.derrota("O Espreitador levou um paciente pela janela.")

    # ---------------------------------------------------------- Enfermeira Maldita
    def atualizar_maldita(self, dt):
        c = self.cfg
        if self.maldita is None:
            if self.tempo < 15:
                return
            self.t_maldita -= dt
            if self.t_maldita <= 0:
                self.maldita = Maldita(c["maldita_vel"], c["maldita_presenca"])
                self.alertas["pegadas"] = 4.0
                self.audio.tocar("passos")
            return
        if self.maldita.atualizar(dt, self.jogador, self.barulho):
            return self.derrota("A Enfermeira Maldita encontrou você.")
        if self.maldita.foi_embora:
            self.maldita = None
            self.t_maldita = c["maldita_intervalo"] * random.uniform(0.8, 1.2)

    # ---------------------------------------------------------- trilha sonora
    def escolher_musica(self):
        """Qual música combina com o momento? (GDD 6: calmaria, tensão, perseguição, esconderijo)"""
        j = self.jogador
        if self.invasao:
            return "perseguicao"
        if j.escondido:
            return "esconderijo"
        espreitando = [jan for jan in self.janelas if jan.estado == "espreitador"]
        perigo_iminente = (
            (self.maldita is not None and self.maldita.estado == "perseguindo")
            or (self.sombra is not None and (self.sombra.pos - j.pos).length() < 300)
            or any(jan.tempo < 3 for jan in espreitando)
        )
        if perigo_iminente:
            return "perseguicao"
        if self.sombra or self.maldita or espreitando or not self.energia:
            return "tensao"
        return "calma"

    def atualizar_musica(self, dt):
        """Troca a música, mas no máximo uma vez a cada config.TROCA_MUSICA_MIN segundos
        (senão ela ficaria trocando toda hora quando o perigo aparece e some)."""
        self.t_musica += dt
        desejada = self.escolher_musica()
        if desejada != self.audio.musica_atual and self.t_musica >= cfg.TROCA_MUSICA_MIN:
            self.audio.musica(desejada)
            self.t_musica = 0.0

    # ---------------------------------------------------------- fim da noite
    def derrota(self, causa):
        self.causa = causa
        self.estado = "gameover"
        self.audio.musica("derrota", repetir=False)

    def amanhecer(self):
        """A noite acabou e todos sobreviveram: calcula pontos, estrelas e salva."""
        pontos = self.pontos
        meta2, meta3 = cfg.metas_estrelas(self.noite)
        # 1 estrela: concluir | 2 estrelas: pontuação mínima | 3 estrelas: pontuação máxima
        estrelas = 3 if pontos >= meta3 else 2 if pontos >= meta2 else 1
        self.resultado = {"estrelas": estrelas, "meta2": meta2, "meta3": meta3,
                          "atendimentos": self.n_atendimentos * cfg.PONTOS_ATENDIMENTO,
                          "energia": self.n_energia * cfg.PONTOS_ENERGIA,
                          "tempo": int(min(self.tempo, self.duracao) * cfg.PONTOS_POR_SEGUNDO)}
        self.pontos_final = pontos
        progresso.registrar_noite(self.dados, self.noite, pontos, estrelas)
        self.estado = "amanhecer"
        self.audio.musica("vitoria", repetir=False)

    # ============================================================ DESENHO
    def texto(self, msg, pos, tamanho=30, cor=BRANCO, centro=False, direita=False):
        """Escreve um texto na tela (com uma sombrinha preta para ler melhor)."""
        sombra = self.fonte(tamanho).render(msg, True, (0, 0, 0))
        imagem = self.fonte(tamanho).render(msg, True, cor)
        if centro:
            retangulo = imagem.get_rect(center=pos)
        elif direita:
            retangulo = imagem.get_rect(topright=pos)
        else:
            retangulo = imagem.get_rect(topleft=pos)
        self.tela.blit(sombra, (retangulo.x + 2, retangulo.y + 2))
        self.tela.blit(imagem, retangulo)

    def sprite(self, imagem, pos):
        """Desenha 'imagem' com os PÉS (meio da base) em 'pos'."""
        self.tela.blit(imagem, (pos.x - imagem.get_width() / 2, pos.y - imagem.get_height()))

    def frame(self, nome, direcao, tempo, velocidade=8):
        frames = self.anim[nome][direcao]
        return frames[int(tempo * velocidade) % len(frames)]

    def estrela(self, cx, cy, raio, cor):
        pontos = []
        for i in range(10):
            r = raio if i % 2 == 0 else raio * 0.45
            ang = -math.pi / 2 + i * math.pi / 5
            pontos.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        pygame.draw.polygon(self.tela, cor, pontos)

    def painel(self, rect, alpha=200):
        superficie = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
        superficie.fill((10, 10, 16, alpha))
        self.tela.blit(superficie, (rect[0], rect[1]))
        pygame.draw.rect(self.tela, CINZA, rect, 2)

    # ---------------------------------------------------------- telas simples
    def fundo_escuro(self):
        self.tela.blit(self.img["cenario_escuro"], (0, 0))
        veu = pygame.Surface((cfg.LARGURA, cfg.ALTURA), pygame.SRCALPHA)
        veu.fill((0, 0, 0, 150))
        self.tela.blit(veu, (0, 0))

    def desenhar_menu(self):
        self.fundo_escuro()
        self.texto("EIGHT NIGHTS", (cfg.LARGURA // 2, 150), 110, VERMELHO, True)
        self.texto("IN THE HOSPITAL", (cfg.LARGURA // 2, 235), 80, BRANCO, True)
        itens = ["Jogar", "Selecionar noite", "Ranking", "Sair"]
        for i, nome in enumerate(itens):
            ativo = i == self.item_menu
            self.texto(("> " if ativo else "") + nome, (cfg.LARGURA // 2, 380 + i * 65),
                       52 if ativo else 44, AMARELO if ativo else BRANCO, True)
        self.texto("Setas / W S: escolher     Enter: confirmar", (cfg.LARGURA // 2, 740), 28, CINZA, True)

    def desenhar_selecao(self):
        self.fundo_escuro()
        self.texto("Selecionar noite", (cfg.LARGURA // 2, 90), 70, BRANCO, True)
        for n in range(1, 9):
            col, lin = (n - 1) % 4, (n - 1) // 4
            x, y = 100 + col * 255, 200 + lin * 230
            liberada = n <= self.dados["desbloqueada"]
            self.painel((x, y, 230, 190), 220)
            if n == self.noite_selecionada:
                pygame.draw.rect(self.tela, AMARELO, (x, y, 230, 190), 4)
            self.texto(f"Noite {n}", (x + 115, y + 45), 44, BRANCO if liberada else CINZA, True)
            if liberada:
                ganhas = self.dados["estrelas"].get(str(n), 0)
                for i in range(3):
                    self.estrela(x + 55 + i * 60, y + 120, 24, AMARELO if i < ganhas else (60, 60, 70))
            else:
                self.texto("bloqueada", (x + 115, y + 120), 32, CINZA, True)
        self.texto("Setas: escolher    Enter: jogar    Esc: voltar", (cfg.LARGURA // 2, 740), 28, CINZA, True)

    def desenhar_ranking(self):
        self.fundo_escuro()
        self.texto("Ranking (melhores pontuações)", (cfg.LARGURA // 2, 90), 66, BRANCO, True)
        ranking = self.dados["ranking"]
        if not ranking:
            self.texto("Ainda não há pontuações. Sobreviva a uma noite!", (cfg.LARGURA // 2, 350), 40, CINZA, True)
        for i, r in enumerate(ranking):
            self.texto(f"{i + 1:>2}.   Noite {r['noite']}   -   {r['pontos']} pontos",
                       (cfg.LARGURA // 2, 190 + i * 50), 40, AMARELO if i == 0 else BRANCO, True)
        self.texto("Esc: voltar", (cfg.LARGURA // 2, 740), 28, CINZA, True)

    def desenhar_intro(self):
        self.tela.fill((0, 0, 0))
        self.texto(f"NOITE {self.noite}", (cfg.LARGURA // 2, 300), 120, VERMELHO, True)
        self.texto("12:00 AM", (cfg.LARGURA // 2, 400), 50, BRANCO, True)
        self.texto(self.cfg["dica"], (cfg.LARGURA // 2, 520), 34, AMARELO, True)
        self.texto(f"Pacientes: {self.cfg['pacientes']}     Duração: {self.cfg['duracao']} min",
                   (cfg.LARGURA // 2, 600), 30, CINZA, True)

    def desenhar_pausa(self):
        self.desenhar_jogando()
        veu = pygame.Surface((cfg.LARGURA, cfg.ALTURA), pygame.SRCALPHA)
        veu.fill((0, 0, 0, 170))
        self.tela.blit(veu, (0, 0))
        self.texto("PAUSADO", (cfg.LARGURA // 2, 330), 100, BRANCO, True)
        self.texto("Esc: continuar        M: voltar ao menu", (cfg.LARGURA // 2, 430), 38, AMARELO, True)

    def desenhar_gameover(self):
        self.desenhar_jogando()
        veu = pygame.Surface((cfg.LARGURA, cfg.ALTURA), pygame.SRCALPHA)
        veu.fill((60, 0, 0, 190))
        self.tela.blit(veu, (0, 0))
        self.texto("GAME OVER", (cfg.LARGURA // 2, 290), 120, VERMELHO, True)
        self.texto(self.causa, (cfg.LARGURA // 2, 390), 42, BRANCO, True)
        self.texto(f"Noite {self.noite}  -  {self.pontos} pontos", (cfg.LARGURA // 2, 450), 36, CINZA, True)
        self.texto("Enter: tentar de novo        Esc: menu", (cfg.LARGURA // 2, 540), 38, AMARELO, True)

    def desenhar_amanhecer(self):
        self.desenhar_jogando()
        r = self.resultado
        veu = pygame.Surface((cfg.LARGURA, cfg.ALTURA), pygame.SRCALPHA)
        veu.fill((255, 220, 150, 70))
        self.tela.blit(veu, (0, 0))
        self.painel((280, 130, 640, 540), 230)
        meio = cfg.LARGURA // 2
        self.texto("AMANHECEU!", (meio, 185), 80, AMARELO, True)
        self.texto(f"Você sobreviveu à noite {self.noite}", (meio, 250), 38, BRANCO, True)
        self.texto(f"Pacientes atendidos: +{r['atendimentos']}", (meio, 310), 32, BRANCO, True)
        self.texto(f"Energia restabelecida: +{r['energia']}", (meio, 350), 32, BRANCO, True)
        self.texto(f"Tempo de sobrevivência: +{r['tempo']}", (meio, 390), 32, BRANCO, True)
        self.texto(f"Pontuação: {self.pontos_final}", (meio, 450), 56, AMARELO, True)
        for i in range(3):
            self.estrela(meio - 80 + i * 80, 525, 30, AMARELO if i < r["estrelas"] else (60, 60, 70))
        self.texto(f"2 estrelas: {r['meta2']} pts     3 estrelas: {r['meta3']} pts", (meio, 575), 26, CINZA, True)
        proxima = "Enter: próxima noite" if self.noite < 8 else "Enter: continuar"
        self.texto(f"{proxima}        Esc: menu", (meio, 625), 32, CINZA, True)

    def desenhar_fim(self):
        self.fundo_escuro()
        self.texto("VOCÊ SOBREVIVEU ÀS 8 NOITES!", (cfg.LARGURA // 2, 300), 80, AMARELO, True)
        self.texto("Ophelia deixa o hospital quando o sol nasce.", (cfg.LARGURA // 2, 400), 40, BRANCO, True)
        self.texto("Obrigada por jogar!", (cfg.LARGURA // 2, 470), 40, BRANCO, True)
        self.texto("Enter: voltar ao menu", (cfg.LARGURA // 2, 600), 32, CINZA, True)

    # ---------------------------------------------------------- a cena do jogo
    def desenhar_jogando(self):
        c = self.cfg
        j = self.jogador
        # 1) cenário e janelas
        self.tela.blit(self.img["cenario" if self.energia else "cenario_escuro"], (0, 0))
        for jan in self.janelas:
            self.tela.blit(self.img["janela_" + jan.estado], jan.rect)
        # 2) pacientes nas camas (borda vermelha piscando se a vida está baixa)
        for p in self.pacientes:
            imagem = self.img["paciente_deitado"]
            self.tela.blit(imagem, imagem.get_rect(center=(p.centro.x + 4, p.centro.y)))
            if p.vida < 30 and int(self.relogio_geral * 4) % 2 == 0:
                pygame.draw.rect(self.tela, (220, 30, 30),
                                 (p.centro.x - 98, p.centro.y - 48, 200, 96), 3)
        # 3) personagens, ordenados pelo y (quem está mais embaixo aparece na frente)
        fila = []
        if self.sombra:
            fila.append((self.sombra.pos.y, self.img["sombra"], self.sombra.pos))
        if self.maldita:
            m = self.maldita
            fila.append((m.pos.y, self.frame("maldita", m.direcao, m.anim, 6), m.pos))
        if self.invasao:
            inv = self.invasao
            fila.append((inv["pos"].y, self.frame("espreitador", inv["dir"], inv["anim"], 8), inv["pos"]))
        if not j.escondido:
            fila.append((j.pos.y, self.imagem_jogador(), j.pos))
        for _y, imagem, pos in sorted(fila, key=lambda item: item[0]):
            self.sprite(imagem, pos)
        # 4) escuridão (quando a energia cai)
        if not self.energia:
            self.desenhar_escuridao()
        # 5) interface por cima de tudo
        self.desenhar_hud()

    def imagem_jogador(self):
        j = self.jogador
        if j.lanterna:
            return self.anim["jogador_lanterna"][j.direcao][0]
        if j.andando:
            return self.frame("jogador_andando", j.direcao, j.anim, 9)
        return self.anim["jogador_parado"][j.direcao][0]

    def desenhar_escuridao(self):
        """Cobre a tela de preto e 'fura' buracos de luz: um halo em volta da enfermeira
        e, com a lanterna ligada, um cone na direção do mouse."""
        escuro = pygame.Surface((cfg.LARGURA, cfg.ALTURA), pygame.SRCALPHA)
        escuro.fill((0, 0, 0, cfg.ESCURIDAO_ALPHA))
        luz = pygame.Surface((cfg.LARGURA, cfg.ALTURA), pygame.SRCALPHA)
        j = self.jogador
        centro = j.centro
        if not j.escondido:
            for raio, alfa in ((95, 40), (70, 80), (48, 130)):      # halo (do maior p/ o menor)
                pygame.draw.circle(luz, (255, 255, 255, alfa), (int(centro.x), int(centro.y)), raio)
            if j.lanterna:
                mira = self.direcao_mira()
                for fracao, alfa in ((1.0, 45), (0.85, 85), (0.65, 125), (0.45, 165)):
                    pontos = [(centro.x, centro.y)]
                    for ang in range(-cfg.ANGULO_LANTERNA, cfg.ANGULO_LANTERNA + 1, 8):
                        p = centro + mira.rotate(ang) * cfg.ALCANCE_LANTERNA * fracao
                        pontos.append((p.x, p.y))
                    pygame.draw.polygon(luz, (255, 255, 255, alfa), pontos)
        escuro.blit(luz, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)   # luz "apaga" o escuro
        self.tela.blit(escuro, (0, 0))

    # ---------------------------------------------------------- interface (HUD)
    def desenhar_hud(self):
        c = self.cfg
        j = self.jogador
        # relógio da noite: 12:00 AM -> 6:00 AM
        minutos = min(self.tempo / self.duracao, 1.0) * 360
        hora = int(minutos // 60)
        self.painel((15, 12, 230, 62), 170)
        self.texto(f"Noite {self.noite}", (28, 18), 28, CINZA)
        self.texto(f"{12 if hora == 0 else hora}:{int(minutos % 60):02d} AM", (28, 40), 34, BRANCO)
        # barras de vida dos pacientes
        for i, p in enumerate(self.pacientes):
            y = 90 + i * 56
            self.painel((15, y, 230, 50), 170)
            self.tela.blit(self.frame("paciente", "dir", self.relogio_geral, 3), (22, y + 2))
            cor = (80, 200, 90) if p.vida > 60 else (230, 190, 50) if p.vida > 30 else (220, 50, 50)
            pygame.draw.rect(self.tela, (50, 50, 60), (65, y + 18, 165, 16))
            pygame.draw.rect(self.tela, cor, (65, y + 18, int(165 * max(p.vida, 0) / 100), 16))
            self.texto(f"Leito {i + 1}", (65, y + 2), 20, CINZA)
        self.texto(f"Pontos: {self.pontos}", (cfg.LARGURA - 20, 22), 38, AMARELO, direita=True)
        meta2, meta3 = cfg.metas_estrelas(self.noite)
        self.texto(f"2 estrelas: {meta2}   3 estrelas: {meta3}", (cfg.LARGURA - 20, 62), 24, CINZA, direita=True)
        # ícones de acessibilidade no topo
        ativos = [nome for nome, t in self.alertas.items() if t > 0]
        for jan in self.janelas:
            if c["alerta"] and jan.estado == "espreitador":      # alerta visual (noites 1 e 2)
                piscando = int(self.relogio_geral * 5) % 2 == 0
                if piscando:
                    self.tela.blit(self.icones["mao"], (jan.rect.centerx - 22, jan.rect.bottom + 6))
        for i, nome in enumerate(ativos):
            self.tela.blit(self.icones[nome], (cfg.LARGURA // 2 - 22 + i * 54 - (len(ativos) - 1) * 27, 14))
        if not self.energia:
            if int(self.relogio_geral * 2) % 2 == 0:
                self.texto("SEM ENERGIA! Vá ao gerador (canto superior direito) e segure E",
                           (cfg.LARGURA // 2, 85), 32, (255, 90, 90), True)
        if j.escondido:
            self.texto(f"Escondida ({j.escondido})  -  Ctrl para sair", (cfg.LARGURA // 2, 740), 34, AMARELO, True)
        else:
            self.desenhar_dica_acao()
            self.texto("WASD: andar   E: interagir   F: lanterna (mouse mira)   Ctrl: esconder   Esc: pausa",
                       (cfg.LARGURA // 2, 780), 22, CINZA, True)

    def desenhar_dica_acao(self):
        """Texto e barra de progresso em cima da enfermeira."""
        alvo = self.alvo_interacao()
        j = self.jogador
        x, y = int(j.pos.x), int(j.pos.y - 130)
        if self.progresso_acao > 0:
            pygame.draw.rect(self.tela, (50, 50, 60), (x - 40, y, 80, 10))
            pygame.draw.rect(self.tela, (90, 200, 120), (x - 40, y, int(80 * self.progresso_acao), 10))
        if not alvo:
            return
        tipo, obj = alvo
        if tipo == "paciente":
            msg = "Segure E: curar" if obj.vida < 99 else "Paciente está bem"
        elif tipo == "janela":
            msg = "E: fechar janela"
        else:
            msg = "Segure E: ligar gerador"
        self.texto(msg, (x, y - 14), 26, AMARELO, True)


def main():
    Jogo().executar()


if __name__ == "__main__":
    main()
