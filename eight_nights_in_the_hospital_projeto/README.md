# Eight Nights in the Hospital

Jogo 2D de terror e sobrevivência em Python/Pygame. Você é Ophelia, enfermeira de plantão
numa enfermaria assombrada: mantenha os pacientes vivos por 8 noites.

## Como rodar
```
pip install -r requirements.txt
python main.py
```
(Se trocar algum desenho em `assets/`, rode `python tools/preparar_assets.py` para regerar `sprites/`.)

## Controles
| Ação | Tecla |
|---|---|
| Andar | WASD ou setas |
| Curar paciente / ligar gerador | segurar **E** perto |
| Fechar janela | **E** perto da janela (com o Espreitador nela) |
| Lanterna | **F** liga/desliga, o mouse mira |
| Esconder / sair | **Ctrl** perto do armário, do balcão ou das camas |
| Pausa | Esc |

## Estrutura
- `main.py` - classe `Jogo`: laço principal, estados (menu, jogando, pausa...), regras e desenho
- `entidades.py` - classes Janela, Paciente, Jogador, Sombra, Maldita, Sussurro
- `config.py` - todos os números (dificuldade das 8 noites, velocidades, distâncias)
- `icones.py` - ícones de acessibilidade (pegadas, mão, raio) desenhados por código
- `progresso.py` - salva estrelas e ranking em `progresso.json`
- `tools/preparar_assets.py` - remove fundos, recorta e redimensiona os sprites
- `sons/` - trilha sonora (.ogg) e, opcionalmente, efeitos
- `sprites/` - sprites prontos para o jogo; `assets/`, `fundo/`, `jogador/` - originais

## Pontuação e estrelas (GDD 3.4)
- Paciente atendido com sucesso (curado com 70% de vida ou menos): **+500**
- Energia restabelecida: **+200**
- Tempo de sobrevivência: **+10 por segundo**
- 1 estrela: concluir a noite. 2 estrelas: pontuação mínima da noite. 3 estrelas: pontuação máxima.
  As metas de cada noite são calculadas em `config.py` (`metas_estrelas`) e aparecem na tela.
- Estrelas e ranking ficam salvos em `progresso.json`.

## Trilha sonora
A música muda conforme a situação: calmaria, tensão, perseguição e esconderijo (ver `sons/LEIAME.txt`).

## Dificuldade
Os números das 8 noites estão em `config.py` (lista `NOITES`). Se alguma noite ficar difícil
ou fácil demais, mexa em `vida_perde`, `sombra_vel`, `esp_tempo`, `maldita_vel`...
