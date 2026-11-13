"""
Prepara os sprites para o jogo.  Rode UMA vez (ou sempre que trocar um desenho):

    python tools/preparar_assets.py

O que ele faz com cada imagem original:
  1. remove o fundo preto sólido (quando existir);
  2. recorta as bordas transparentes sobrando (para o desenho ficar "justo");
  3. redimensiona para o tamanho usado no jogo;
  4. salva na pasta  sprites/  (as originais não são alteradas).
"""
import os
from PIL import Image, ImageDraw

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, "sprites")
os.makedirs(SAIDA, exist_ok=True)


def abrir(caminho):
    return Image.open(os.path.join(RAIZ, caminho)).convert("RGBA")


def remover_fundo_preto(img, tolerancia=40):
    """Pinta de transparente o fundo escuro que encosta nas bordas da imagem.

    Usamos 'flood fill' (balde de tinta) a partir dos 4 cantos: só some o preto
    que está CONECTADO às bordas, então contornos escuros do desenho ficam.
    """
    if img.getchannel("A").getextrema()[0] != 255:
        return img                      # já tem transparência, nada a fazer
    w, h = img.size
    for canto in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        r, g, b, _ = img.getpixel(canto)
        if r + g + b < 120:             # só pinta se o canto for escuro
            ImageDraw.floodfill(img, canto, (0, 0, 0, 0), thresh=tolerancia)
    return img


def recortar(img):
    caixa = img.getchannel("A").point(lambda a: 255 if a > 20 else 0).getbbox()
    return img.crop(caixa) if caixa else img


def salvar(img, nome, altura=None, largura=None, forcar=None):
    img = recortar(img)
    w, h = img.size
    if forcar:                          # tamanho exato (ignora a proporção)
        largura, altura = forcar
    elif altura:
        largura = round(w * altura / h)
    elif largura:
        altura = round(h * largura / w)
    if (largura, altura) != (w, h):
        img = img.resize((largura, altura), Image.NEAREST)  # NEAREST = pixel art nítida
    img.save(os.path.join(SAIDA, nome))
    print(f"{nome:28s} {img.size}")


# ---------- cenário (preenche a janela do jogo: 1200 x 800) ----------
for nome in ("cenario", "cenario_escuro"):
    fundo = abrir(f"fundo/{nome}.png").resize((1200, 800), Image.LANCZOS)
    fundo.save(os.path.join(SAIDA, f"{nome}.png"))

# ---------- jogador ----------
salvar(abrir("jogador/enfermeira.png"), "jogador_parado.png", altura=110)
salvar(abrir("jogador/enfermeira_lanterna.png"), "jogador_lanterna.png", altura=110)
for i in range(1, 5):
    salvar(abrir(f"jogador/andando/enf_frame{i}.png"), f"jogador_andando_{i}.png", altura=110)

# ---------- entidades ----------
for i in range(1, 5):
    salvar(abrir(f"assets/espreitador/esp_frame{i}.png"), f"espreitador_{i}.png", altura=95)
    salvar(abrir(f"assets/enfermeira_maldita/caminhar_em_frame{i}.png"), f"maldita_{i}.png", altura=120)
salvar(abrir("assets/sombra.png"), "sombra.png", altura=140)

# ---------- cenário interativo ----------
# as janelas são esticadas para cobrir exatamente as janelas desenhadas no cenário
for nome in ("aberta", "fechada", "espreitador"):
    salvar(abrir(f"assets/janela_{nome}.png"), f"janela_{nome}.png", forcar=(248, 118))
# do desenho "paciente na maca" usamos só a parte do paciente (o cenário já tem as camas)
maca = abrir("assets/paciente_maca.png").crop((470, 380, 1135, 655))
salvar(maca, "paciente_deitado.png", largura=150)

# ---------- paciente (retrato usado na interface) ----------
for i in range(1, 5):
    img = remover_fundo_preto(abrir(f"assets/paciente/pc_frame{i}.png"))
    salvar(img, f"paciente_{i}.png", altura=46)
