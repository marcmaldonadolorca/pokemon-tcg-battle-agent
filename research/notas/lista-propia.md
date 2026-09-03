# Lista propia medida con el clon: el muro que los Pokémon ex no pueden tocar

Fecha: 2026-08-12. Encargo: cerrar el hueco entre lo que puntúa el rating (las dos listas
vivas son **copias exactas** del líder de su arquetipo, sacadas del censo de replays) y lo
que puntúa el **20% de Deck Score** («concepto de baraja claramente articulado, cartas
clave bien elegidas»). Todo lo de esta nota está medido **con el clon pilotando los dos
lados** (PKM-012: con piloto bueno la báscula de barajas se invierte, así que nada de lo
medido con el heurístico vale aquí).

Ficheros: `research/decks/propios/mia-*.csv` · resultados en `data/gauntlet.json`
(rama `pilotos.clon.gauntlet`) · sondas en `scratchpad/lista_propia/`.

---

## 1. El hallazgo: Crustle 345 y su habilidad *Mysterious Rock Inn*

Buscando en el pool con `scratchpad/lista_propia/scan.py` aparece una carta que **ninguna
de las 21 listas rivales del corpus juega** y que está hecha contra este campo concreto:

> **Crustle 345** — Stage 1 {G}, 150 HP, **un solo premio**, evoluciona de Dwebble 344.
> *[Habilidad] Mysterious Rock Inn: **Prevent all damage done to this Pokémon by attacks
> from your opponent's Pokémon ex.***
> *Superb Scissors [{G}●●] 120 :: This attack's damage isn't affected by any effects on
> your opponent's Active Pokémon.*

Por qué es una carta contra ESTE campo: **la condición de victoria del 84,5% del campo es
un Pokémon ex** (Grimmsnarl ex 31,2% · Lopunny/Froslass ex 12,8% · Dragapult ex 8,2% ·
Kangaskhan ex 6,9% · Ogerpon ex 5,0% · Lucario ex 4,0% · Hydrapple ex, Slowking+Kangaskhan,
Zoroark ex…). Contra todos ellos Crustle es literalmente **inmune** mientras el rival no
cambie de atacante. Y `Superb Scissors` ignora los efectos sobre el activo rival, que es lo
que sostienen Mist Energy (c3) y Battle Cage (c3).

### 1bis. Verificado en el motor, no deducido del texto

Sonda `scratchpad/lista_propia/probe_dano.py` (agrupa cada `log 15` = ataque con los
`log 16` = daño que provoca), clon en los dos lados, 24 partidas por pareja:

| evento | n | valor observado | lectura |
|---|---:|---|---|
| **Marnie's Grimmsnarl ex → Crustle** (Shadow Bullet, 180) | 459 | **0** | la habilidad **FUNCIONA** |
| Marnie's Morgrem (NO es ex) → Crustle | 34 | **−60** | el daño de un no-ex sí pasa: experimento natural |
| Crustle → Marnie's Grimmsnarl ex | 125 | **−240** | 120 × 2 por debilidad {G} |
| Crustle → Froslass / Snorunt | 12 | −120 | sin debilidad |
| Meowscarada → Mega Lopunny ex / Mega Froslass ex | 51 | **−180** | el «+90 si el activo rival es ex» está implementado |
| Meowscarada → Fan Rotom / Snorunt (no ex) | 17 | −90 | ídem, la condición discrimina |
| **Meowscarada → Marnie's Grimmsnarl ex** | 6 | **−360** | 180 × 2: **KO de un golpe a un Stage 2 de 320 HP** |
| Grimmsnarl ex → Shaymin 343 / Dunsparce en banca | 74 | **0** | *Flower Curtain* protege la banca sin Rule Box |

Ninguna carta muerta: `scratchpad/lista_propia/probe_uso.py` sobre 18 partidas registra uso
de **las 19 cartas distintas** de la lista (`SIN USO REGISTRADO: []`). El clon activa las
habilidades (option type 10) que el heurístico ignoraba, así que el «Tramo B» que
`estrategia-deckbuilding.md` §9bis daba por bloqueado **está abierto con este piloto**.

---

## 2. Las cuatro listas propias y su tesis

Las cuatro son legales (`battle_start` errorPlayer −1), 60 exactas, ≤4 copias, ≥1 básico,
**1 sola ACE SPEC**, y **0 Pokémon de dos premios** (el campo va del 5% de `c2-alakazam` al
27,9% de media; nuestras listas viejas, 32,8%). La distancia mínima a cualquier lista de
`research/decks/campo/` es de **34 a 37 cartas** de las 60: no son copias de nada.

| lista | tesis | núcleo | Pk/bás/Tr/En | mulligan | ACE SPEC |
|---|---|---|---|---|---|
| **`mia-crustle-muro`** | **el muro**: el 84,5% del campo gana con un ex y no puede hacerle daño a nuestro atacante | 4 Dwebble 344 + 4 Crustle 345 | 16/10/33/11 | 0,259 | Neutralization Zone 1247 |
| `mia-seis-kos` | **un solo premio**: el rival necesita 6 KO y nosotros 3; Rising Bloom mata a Grimmsnarl ex de un golpe | 4-2-4 Sprigatito/Floragato/Meowscarada 924 | 17/9/33/10 | 0,300 | Neutralization Zone 1247 |
| `mia-viento` | **control de mano**: el recurso que el campo necesita es la mano (Alakazam escala con la suya, Mega Froslass con la nuestra) | 4-3-4 Scatterbug/Spewpa/Vivillon 1019 + Xerosic + Judge | 18/9/32/10 | 0,300 | Unfair Stamp 1080 |
| `mia-doble-filo` | **los dos agujeros**: el muro contra el 31% + el rematador contra el 13% | Crustle 345 + Meowscarada 924 | 18/11/31/11 | 0,222 | Neutralization Zone 1247 |

Elecciones que hay que justificar una a una (esto es lo que puntúa el Deck Score):

- **Dwebble 344 y no Dwebble 532**: el 344 es {G} (pega en la debilidad del 31,2% del campo)
  y trae *Ascension*, que busca su propia evolución sin gastar carta.
- **Forest of Vitality 1261**: «cada Pokémon {G} puede evolucionar el turno en que se juega».
  En este campo es **asimétrico**: el único rival {G} que evoluciona es `c8` (3,5%).
  Convierte a Dwebble→Crustle en un turno.
- **Neutralization Zone 1247 como ACE SPEC**: es el único ACE SPEC del pool cuyo efecto
  «ninguna otra carta da» **y que además solo puede jugar una lista como la nuestra**: impide
  todo el daño de los ex a los Pokémon **sin Rule Box**, y los 16 Pokémon de la lista lo son.
  Es la misma habilidad de Crustle extendida a toda la mesa. (Master Ball, que llevábamos en
  7 de 9 listas viejas, no la juega **nadie** en las 21 listas rivales.)
- **Poké Pad 1152 ×4**: los 16 Pokémon son objetivo legal. Era el agujero más caro del
  diagnóstico (48 copias en 13 de 15 listas del campo, 0 en las nuestras).
- **Hilda 1225 ×4**: busca evolución **y** energía con una carta; es lo que permite bajar a
  11 energías con un ataque de coste 3.
- **Shaymin 343 ×2**: *Flower Curtain* anula el 30 de banca de Shadow Bullet (31% del campo)
  y el reparto de Dragapult (8%) — verificado, 0 daño en 46 eventos.
- **Enhanced Hammer 1081**: el 42,9% del campo depende de energía especial.
- **0 Master Ball, 0 supporters de robo por encima de 3**: `estrategia-deckbuilding.md` §5bis.

---

## 3. Resultado: la báscula del campo con el clon pilotando

`research/gauntlet.py --politica research/agentes/clon.py --rivales ampliado --n 150`,
12 arquetipos, **96,3% de cobertura**, 1.800 partidas por fila, asientos intercambiados.
Las dos primeras filas son la referencia (medidas antes, n=200/celda).

| lista (piloto = clon en los dos lados) | grimm 31% | alak 18% | lopu 13% | drag 8% | kanga 7% | oger 5% | luca 4% | dipp 3,5% | hydr | slow | cynt | zoro | **POND** | IC95 | **PEOR** |
|---|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|
| **`mia-crustle-tijeras`** (propia, final) | **0,760** | 0,180 | 0,320 | 0,807 | 0,560 | 0,820 | 0,773 | 0,227 | 0,860 | 0,847 | 0,740 | 0,947 | **0,571** | [0,543, 0,600] | 0,180 |
| `c1-grimmsnarl` (ladder, copiada) | 0,510 | 0,695 | 0,605 | 0,790 | 0,130 | 0,125 | 0,695 | 0,735 | 0,345 | 0,915 | 0,580 | 0,930 | 0,558 | [0,530, 0,586] | 0,125 |
| `mia-crustle-muro` (propia, v1) | 0,667 | 0,027 | 0,207 | 0,813 | 0,407 | 0,887 | 0,680 | 0,167 | 0,840 | 0,893 | 0,747 | 0,940 | 0,484 | [0,456, 0,512] | 0,027 |
| `c2-alakazam` (ladder, copiada) | 0,320 | 0,470 | 0,335 | 0,730 | 0,445 | 0,455 | 0,715 | 0,655 | 0,605 | 0,895 | 0,450 | 0,880 | 0,454 | [0,427, 0,482] | **0,320** |
| `mega-lucario` (la vieja) | 0,290 | 0,105 | 0,780 | 0,575 | 0,110 | 0,210 | 0,350 | 0,650 | 0,405 | 0,885 | 0,355 | 0,770 | 0,362 | [0,337, 0,386] | 0,105 |
| `mia-doble-filo` (propia, parcial) | 0,487 | 0,073 | 0,160 | — | — | — | — | 0,160 | — | — | — | — | 0,291 | [0,250, 0,332] | 0,073 |
| `mia-seis-kos` (propia) | 0,087 | 0,107 | 0,140 | 0,120 | 0,120 | 0,047 | 0,200 | 0,260 | 0,040 | 0,473 | 0,160 | 0,640 | **0,123** | [0,103, 0,144] | 0,040 |
| `mia-viento` (propia, parcial) | 0,080 | 0,073 | 0,073 | 0,060 | — | — | — | — | — | — | — | — | **0,075** | [0,051, 0,098] | 0,060 |

⚠️ Las filas con `—` son parciales y su POND se renormaliza sobre menos rivales: se cortaron
en cuanto quedó claro el veredicto (`mia-viento` iba a 0,08 en los cuatro rivales más
jugados; `mia-seis-kos` sí se midió entera). Comparar una fila al 66% con otra al 96% es
comparar dos mezclas distintas — pero a 0,08 la mezcla no cambia el signo.

### Lo que enseña la tabla, en tres frases

1. **Las dos tesis de Stage 2 son un fracaso limpio y grande**: `mia-seis-kos` (0,123) y
   `mia-viento` (0,075) pierden contra TODO, incluso contra los emparejamientos donde su
   carta clave hace lo que promete (Meowscarada mata a Grimmsnarl ex de un golpe, medido,
   y aun así 0,087 contra él). La razón es de tempo: una línea 4-2-4 con un básico de 60 HP
   no llega viva al turno en que la carta buena importa. **La tesis correcta no era «un solo
   premio», era «un solo premio Y Stage 1»**.
2. **La tesis del muro sí funciona y funciona en todo el campo con ex**: 0,807 Dragapult,
   0,820 Ogerpon, 0,773 Lucario, 0,860 Hydrapple, 0,947 Zoroark, y **0,760 contra el 31%
   más jugado**, que es exactamente donde `c2-alakazam` se hunde (0,320).
3. **El agujero del muro es el campo SIN ex**: Alakazam 18% (0,180) y Dipplin 3,5% (0,227),
   los dos únicos arquetipos del top-8 cuya condición de victoria no tiene Rule Box. Es un
   agujero *estructural*, no un accidente de muestreo: la habilidad no aplica, por
   definición.

---

## 4. Iteración sobre la mejor: qué compró cada cambio

Todas las variantes son de 2-4 cartas sobre la lista anterior y se midieron contra los
**cuatro rivales que marcan el veredicto** (los dos más jugados y los dos agujeros:
grimmsnarl 31% + alakazam 18% + lopunny 13% + dipplin 3,5% = 65,7% del campo), n=150 por
emparejamiento, antes de gastar el gauntlet entero.

| variante | cambio (respecto a la anterior) | grimm | alak | lopu | dipp | POND(65,7%) | veredicto |
|---|---|--|--|--|--|--|---|
| `mia-crustle-muro` | — (base) | 0,667 | 0,027 | 0,207 | 0,167 | 0,373 | base |
| `mia-crustle-gravedad` | −2 Forest, −1 Judge, **+3 Gravity Mountain** | 0,633 | 0,033 | 0,300 | 0,240 | 0,381 | **NO** (no arregla el agujero) |
| `mia-crustle-mano` | −2 Judge, −1 Bug Set, **+3 Xerosic 1197** | 0,720 | 0,100 | 0,280 | 0,300 | 0,440 | **SÍ** (+0,067) |
| `mia-crustle-total` | −2 Forest, −2 Judge, **+2 Gravity +2 Xerosic** | 0,713 | 0,127 | 0,300 | 0,280 | 0,447 | **SÍ**, mejor suelo |
| `mia-crustle-luna` | −2 Dunsparce, −1 Dudunsparce, −3 {G}, **+3 Roaring Moon 61 +3 {D}** | 0,647 | 0,067 | 0,253 | 0,227 | 0,387 | **NO** (−0,060) |
| **`mia-crustle-tijeras`** | −2 Bug Set, −1 Switch, **+3 Hand Trimmer 1087** | **0,760** | **0,180** | **0,320** | 0,227 | **0,485** | **SÍ** (+0,038) |
| `mia-crustle-tenaza` | −1 Poffin, −1 Hammer, +1 Trimmer, +1 Xerosic | 0,587 | 0,113 | 0,247 | — | 0,378 | **NO** (−0,107) |

Tres lecciones que se pueden defender:

- **La palanca del agujero no era el daño, era la mano.** Alakazam pone 2 contadores de
  daño por cada carta de SU mano; el tech que lo arregla no es un atacante que le pegue en
  la debilidad (**Roaring Moon 61 mide PEOR**: 70×2 = 140 = HP exacto de Alakazam y aun así
  cae de 0,127 a 0,067, porque partir la energía en dos colores rompe la lista), sino
  quitarle cartas de la mano. 0,027 → 0,100 (Xerosic) → **0,180** (Hand Trimmer).
- **Item > Supporter, otra vez.** Xerosic's Machinations es Supporter (1 por turno) y Hand
  Trimmer es Item (varios por turno). Contra un rival cuyo reloj es su propia mano, esa
  diferencia vale **+8 puntos** en el emparejamiento y +5 en el ponderado. Es la regla de
  `estrategia-deckbuilding.md` §8.3 medida por primera vez en este proyecto.
- **La disrupción tiene techo, y está cerca.** `tenaza` (4 Trimmer + 3 Xerosic) pagando con
  1 Poffin y 1 Enhanced Hammer **pierde 0,107**: la 8ª carta de disrupción vale menos que el
  buscador que quita. Es literalmente la advertencia de sobre-consistencia del §5.

---

## 5. El duelo directo contra la lista viva, y por qué NO manda

`research/gauntlet.py --h2h`, clon en los dos lados, muestra independiente de las celdas:

| duelo | n | tasa | IC95 |
|---|---:|---:|---|
| **`mia-crustle-tijeras` vs `c2-alakazam`** | **2.000** | **0,147** | [0,132, 0,163] |

Es decir: **la lista propia pierde 6 de cada 7 duelos directos contra la lista que está en
la ladder, y aun así la bate por 0,117 de POND contra el campo real, con IC95 disjuntos.**
No es una contradicción, es la intransitividad que `gauntlet.md` §4[D] ya dejó medida y
la razón por la que la báscula vieja (una lista contra UNA rival) elegía mal:

- `c2-alakazam` es, por construcción, **el peor emparejamiento posible para esta lista**:
  su condición de victoria no tiene Rule Box, así que ni Crustle ni Neutralization Zone
  aplican. Ganar ese duelo no es lo que puntúa la ladder; ese arquetipo es el 18,25% de las
  partidas y en el otro 81,75% la lista propia va muy por delante.
- El precedente está en la propia nota de selección: `abomasnow-plus` perdía en POND contra
  `mega-lucario` (0,693 vs 0,769) y le ganaba el duelo directo 0,670.
- La regla de uso de la báscula (`gauntlet.md` §5) es explícita: **resuelve diferencias de
  POND ≥ 0,10**. La nuestra es 0,117 con IC95 disjuntos ([0,543, 0,600] vs [0,427, 0,482]).

**Lo honesto que hay que decir en el informe**: la lista propia gana en media contra el
campo y pierde el duelo contra la lista viva; el criterio que decide cuál va a la ladder
es cuál de los dos números creemos, y la báscula está validada para el primero (espejos
0,4975, test-retest sd(z)=0,82, orden correcto de los dos envíos vivos), no para el segundo.

## 6. Veredicto

**`research/decks/propios/mia-crustle-tijeras.csv` es la mejor lista propia medida y la
mejor lista del banco entero con este piloto** (POND 0,571 [0,543, 0,600] sobre el 96,3%
del campo; n=1.800 por fila). Supera:

| | POND | vs tijeras | PEOR |
|---|---|---|---|
| **`mia-crustle-tijeras`** (propia) | **0,571** [0,543, 0,600] | — | 0,180 alakazam |
| `c1-grimmsnarl` (ladder) | 0,558 [0,530, 0,586] | +0,013 · **por debajo de la resolución de la báscula (0,10): empate** | 0,125 |
| `c2-alakazam` (ladder) | 0,454 [0,427, 0,482] | **+0,117, IC95 disjuntos** | **0,320** |
| `mega-lucario` (la vieja) | 0,362 [0,337, 0,386] | +0,209 | 0,105 |

Lo que **no** consigue: subir el suelo. El peor emparejamiento de `c2-alakazam` (0,320)
sigue siendo mejor que el nuestro (0,180), y el 70% del Model Score premia justo eso. La
lista propia gana por media y por cobertura (9 de 12 emparejamientos por encima de 0,56),
no por consistencia.

**Recomendación (decisión del propietario, no mía)**: es una lista propia, articulable en
lenguaje de jugador, con 34-37 cartas de diferencia respecto a cualquier lista del censo,
0 cartas muertas medidas y 0 Pokémon de dos premios — es decir, cubre el 20% de Deck Score
sin regalar el 70% de Model Score, y además mide por encima de las dos listas copiadas en
la báscula que este proyecto tiene validada. Lo que hay que decidir es si se acepta perder
el duelo directo contra la lista viva a cambio de +0,117 de POND.

### 6bis. La lista final, entera

`research/decks/propios/mia-crustle-tijeras.csv` — 16 Pokémon / 33 Trainers / 11 Energía ·
10 básicos (mulligan **0,259**) · **0 Pokémon de dos premios** · 1 ACE SPEC · 0 cartas muertas.

```
Pokémon (16)                      Trainer (33)                       Energy (11)
4 Dwebble        344 {G} 70 HP    4 Poké Pad          1152           11 Basic {G} Energy
4 Crustle        345 {G} 150 HP   4 Buddy-Buddy Poffin 1086
4 Dunsparce      305              4 Hilda             1225
2 Dudunsparce     66              3 Lillie's Determination 1227
2 Shaymin        343              3 Boss's Orders     1182
                                  3 Hand Trimmer      1087
                                  2 Xerosic's Machinations 1197
                                  2 Enhanced Hammer   1081
                                  2 Night Stretcher   1097
                                  2 Ultra Ball        1121
                                  2 Gravity Mountain  1252
                                  1 Switch            1123
                                  1 Neutralization Zone 1247  ← ACE SPEC
```

Dos cartas que sobrevivieron a un intento explícito de sacarlas:
- **Gravity Mountain 1252** entra por el §7(b) del diagnóstico (el 57,6% del campo gana con
  un Stage 2 y **nosotros no tenemos ni uno**: es un estadio de un solo filo) y se quedó
  porque `mia-crustle-bosque` (cambiarlo por 2 Forest of Vitality, cambio de 2 cartas)
  **mide PEOR**: 0,412 vs 0,485 sobre los mismos 4 rivales.
- **Enhanced Hammer 1081 ×2**: quitar una para meter más disrupción (`tenaza`) cuesta 0,107.

## 7. Párrafo de defensa para el writeup (inglés)

> **Rock Inn Crustle — the wall the format cannot punch through.**
> We censused 18,674 decklists from public ladder replays and asked one question: what does
> this format actually win with? The answer is Pokémon ex — Marnie's Grimmsnarl ex (31% of
> the field), Mega Lopunny / Mega Froslass ex (13%), Dragapult ex (8%), Mega Kangaskhan ex
> (7%), Teal Mask Ogerpon ex (5%), Mega Lucario ex (4%). So we built the deck around the one
> card in the pool that reads like a rule against them: **Crustle**, whose *Mysterious Rock
> Inn* prevents **all** damage done to it by attacks from your opponent's Pokémon ex. Against
> most of the room our attacker simply cannot be Knocked Out by the card the opponent built
> their deck around — Grimmsnarl ex swings Shadow Bullet for 180 and does nothing. Meanwhile
> Superb Scissors hits for 120 and its damage "isn't affected by any effects on the
> opponent's Active", which is how we get through the Mist Energy in the Lopunny/Froslass
> deck. Grimmsnarl ex is Grass Weak, so that 120 becomes 240: we two-shot a 320 HP Stage 2
> that cannot answer us. **Dwebble**'s Ascension fetches its own evolution, so the wall is a
> Stage 1 that assembles itself.
>
> **We chose not to play a single Pokémon with a Rule Box, and that choice pays three
> different bills.** It turns the opponent's prize map from three Knock Outs into six. It
> makes **Poké Pad** — a free search card the field runs 48 copies of — able to find *every*
> Pokémon in our deck. And it is what makes our ACE SPEC, **Neutralization Zone**, a
> one-sided card instead of a dead one: it prevents all damage done to Pokémon without a
> Rule Box by attacks from Pokémon ex, so while it is out, Crustle's personal lock applies to
> our whole board. No top deck in this format could play that card; we can only play it
> because we gave up ex attackers. For the same reason **Gravity Mountain** is free for us:
> 58% of the field wins with a Stage 2 and we do not run one, so −30 HP is a cost only the
> opponent pays — it puts Alakazam at 110 HP, inside one Superb Scissors.
>
> **The decks that beat us are the ones that don't attack with an ex**, and we build for that
> instead of pretending otherwise. Alakazam (18% of the field) attacks with Powerful Hand,
> which places 2 damage counters for each card in *its* hand, so we attack the resource, not
> the Pokémon: three **Hand Trimmer** — an Item, so we can play more than one in a turn, which
> matters against a clock made of cards — plus two **Xerosic's Machinations** roughly halve
> that damage. Two **Enhanced Hammer** answer the 43% of the field whose Energy is special.
> The rest is the consistency the format already agreed on: 4 Poké Pad, 4 Buddy-Buddy Poffin,
> 4 **Hilda** (an Evolution *and* an Energy on one card — the reason eleven Energy is enough
> for a three-Energy attack), 3 Boss's Orders to drag the ex we want to hit, 2 Night
> Stretcher, and 2 **Shaymin**, whose Flower Curtain blanks Shadow Bullet's 30 to the Bench
> and Dragapult's spread, because every Pokémon we bench is Rule Box-free. Ten Basics, a
> 25.9% mulligan rate, and zero cards in the list that our agent never plays.

## 8. Lo que queda abierto

- **El suelo.** 0,180 contra Alakazam (n=150; confirmado en muestra independiente de n=2.000
  en el duelo directo: **0,147 [0,132, 0,163]**; agrupado 0,149 sobre 2.150 partidas). Con el
  valor confirmado la POND baja de 0,571 a ≈0,565, sin cambiar ningún veredicto. Subir ese
  suelo es la única línea de trabajo que queda en la lista.
- **No probado**: cambiar el atacante secundario (hoy no hay: la lista ataca solo con
  Crustle) por algo que castigue a los arquetipos sin ex sin partir la energía — Roaring
  Moon con {D} ya se midió y es peor.
- **`mia-crustle-tijeras` no está empaquetada ni enviada**: eso lo decide el propietario.
