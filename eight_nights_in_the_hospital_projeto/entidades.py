"""
entidades.py - as "coisas" do jogo: cada uma é uma CLASSE (um molde) com seus
dados (posição, vida...) e seu comportamento (métodos).

Todas as posições são Vector2 (pygame.Vector2): um par (x, y) que sabe somar,
subtrair e calcular distância. Ex.:  (b - a).length()  é a distância entre a e b.
"""
import random
import pygame
import config as cfg

V = pygame.Vector2


def limitar(valor, minimo, maximo):
    """Mantém 'valor' entre minimo e maximo."""
    return max(minimo, min(maximo, valor))


class Janela:
    """Uma das duas janelas. Estados: 'aberta', 'espreitador' ou 'fechada'."""

    def __init__(self, x):
        self.rect = pygame.Rect(x, 3, 248, 118)
        self.centro = V(self.rect.centerx, 150)   # ponto usado para medir a distância
        self.estado = "aberta"
        self.tempo = 0.0                          # contagem regressiva do estado atual


class Paciente:
    """Um paciente deitado numa cama. Se a vida chegar a 0, é fim de jogo."""

    def __init__(self, indice):
        self.indice = indice
        self.centro = V(cfg.CAMAS[indice])
        self.vida = 100.0


class Jogador:
    """A enfermeira Ophelia."""

    def __init__(self):
        self.pos = V(cfg.POS_INICIAL)     # posição dos PÉS
        self.direcao = "dir"              # para onde está olhando: "dir" ou "esq"
        self.anim = 0.0                   # relógio da animação de andar
        self.andando = False
        self.lanterna = False
        self.escondido = None             # nome do esconderijo, ou None

    @property
    def centro(self):
        """Ponto no meio do corpo (de onde sai a luz da lanterna)."""
        return self.pos - V(0, 55)

    def mover(self, direcao, dt, obstaculos, puxao):
        """Anda na 'direcao' (vetor de tamanho 0 ou 1) respeitando paredes e obstáculos.

        Movemos um eixo de cada vez (x, depois y): assim, ao bater numa parede,
        ela ainda desliza pelo outro eixo em vez de "grudar".
        """
        deslocamento = direcao * cfg.VELOCIDADE_JOGADOR * dt + puxao * dt
        x_min, y_min, x_max, y_max = cfg.LIMITES
        for eixo in (0, 1):
            nova = V(self.pos)
            if eixo == 0:
                nova.x = limitar(nova.x + deslocamento.x, x_min, x_max)
            else:
                nova.y = limitar(nova.y + deslocamento.y, y_min, y_max)
            pes = pygame.Rect(nova.x - 15, nova.y - 14, 30, 14)
            if not any(pes.colliderect(o) for o in obstaculos):
                self.pos = nova
        self.andando = direcao.length() > 0
        if self.andando:
            self.anim += dt


class Sombra:
    """Persegue a enfermeira no escuro e foge quando a lanterna aponta para ela."""

    def __init__(self, pos):
        self.pos = V(pos)

    @property
    def centro(self):
        return self.pos - V(0, 70)

    def atualizar(self, dt, jogador, velocidade, iluminada):
        if jogador.escondido:             # esconderijo = invisível: a Sombra fica parada
            return
        para_jogador = jogador.pos - self.pos
        distancia = para_jogador.length()
        if distancia == 0:
            return
        direcao = para_jogador / distancia
        if iluminada:
            self.pos -= direcao * velocidade * 1.3 * dt      # foge da luz (mais rápido)
        else:
            self.pos += direcao * velocidade * dt            # persegue
        x_min, y_min, x_max, y_max = cfg.LIMITES
        self.pos.x = limitar(self.pos.x, x_min - 60, x_max + 40)
        self.pos.y = limitar(self.pos.y, y_min, y_max + 20)


class Maldita:
    """A Enfermeira Maldita. Estados:
       entrando -> patrulha -> perseguindo -> procurando -> patrulha ... -> saindo
    """

    def __init__(self, vel_perseguir, presenca):
        self.pos = V(cfg.PORTA)
        self.estado = "entrando"
        self.tempo_estado = 2.0
        self.presenca = presenca          # quantos segundos ela fica na enfermaria
        self.vel_perseguir = vel_perseguir
        self.destino = V(1000, 470)
        self.ultimo_visto = V(0, 0)
        self.direcao = "esq"
        self.anim = 0.0
        self.foi_embora = False
        self.tempo_longe = 0.0            # há quanto tempo a enfermeira está longe dela

    def _ir_para(self, alvo, velocidade, dt):
        """Anda em direção a 'alvo'. Devolve True se chegou."""
        v = alvo - self.pos
        distancia = v.length()
        if distancia <= velocidade * dt or distancia == 0:
            self.pos = V(alvo)
            return True
        self.pos += v / distancia * velocidade * dt
        self.direcao = "dir" if v.x > 0 else "esq"
        self.anim += dt
        return False

    def _novo_destino(self):
        self.destino = V(random.choice(cfg.PONTOS_PATRULHA))

    def atualizar(self, dt, jogador, barulho):
        """Devolve True se ela pegou a enfermeira."""
        distancia = (jogador.pos - self.pos).length()
        escondida = jogador.escondido is not None
        ve_jogador = (not escondida) and distancia < cfg.VISAO_MALDITA

        # fez barulho escondida perto dela? Foi encontrada.
        if barulho and distancia < 300 and self.estado != "entrando":
            return True
        # encostou na enfermeira (e ela não está escondida)
        if not escondida and distancia < 40 and self.estado != "entrando":
            return True

        if self.estado == "entrando":
            self._ir_para(V(1000, 470), 60, dt)
            self.tempo_estado -= dt
            if self.tempo_estado <= 0:
                self.estado = "patrulha"
                self._novo_destino()

        elif self.estado == "patrulha":
            self.presenca -= dt
            if ve_jogador:
                self.estado = "perseguindo"
            elif self.presenca <= 0:
                self.estado = "saindo"
            elif self._ir_para(self.destino, cfg.VEL_MALDITA_PATRULHA, dt):
                self._novo_destino()

        elif self.estado == "perseguindo":
            # se a enfermeira conseguir fugir (ficar longe por 2,5 s), ela desiste
            self.tempo_longe = self.tempo_longe + dt if distancia > cfg.VISAO_MALDITA * 1.3 else 0.0
            if self.tempo_longe > 2.5:
                self.estado = "patrulha"
                self.tempo_longe = 0.0
                self._novo_destino()
            elif escondida:                        # perdeu a enfermeira de vista
                self.estado = "procurando"
                self.tempo_estado = 3.0
                self.ultimo_visto = V(jogador.pos)
            else:
                self._ir_para(jogador.pos, self.vel_perseguir, dt)

        elif self.estado == "procurando":
            self._ir_para(self.ultimo_visto, 90, dt)
            self.tempo_estado -= dt
            if ve_jogador:
                self.estado = "perseguindo"
            elif self.tempo_estado <= 0:
                self.estado = "patrulha"
                self._novo_destino()

        elif self.estado == "saindo":
            if self._ir_para(V(cfg.PORTA), 90, dt):
                self.foi_embora = True
        return False
