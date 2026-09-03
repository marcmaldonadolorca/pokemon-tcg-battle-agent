# Mecánica empírica del motor cabt — contrato agente‑motor

Fecha: 2026-08-06. Probes: `research/probe_baraja.py` (resultados en
`research/probe_baraja_resultados.json`), `research/probe_select_tipos.py`
(ejemplos en `research/select_tipos/`), `research/probe_trace.py`
(`research/trace_ejemplo.json`), `research/probe_info_oculta.py`,
`research/probe_finales.py`, `research/probe_acciones.py`.

## 1. Contrato de interfaz

- Agente = `obs -> list[int]`. Primer step: `obs["select"] is None` → devolver la
  baraja (60 card IDs). Después: índices sobre `obs["select"]["option"]`.
- **Longitud de la acción: entre `minCount` y `maxCount`** (verificado: `[]` se
  acepta con min0; con min1 se rechaza). Índices únicos y en rango; si no:
  el motor devuelve error → `battle_select` lanza `IndexError` → el interpreter
  marca INVALID, reward −1, y el rival gana +1. A nivel motor el estado queda
  intacto y se puede reintentar; a nivel Kaggle la primera excepción mata.
- Claves de `obs`: `select`, `logs` (delta desde tu último select, incluye lo del
  turno rival), `current`, `search_begin_input`, `remainingOverageTime` (600 s).
- Config del env (`cabt.json`): episodeSteps 10 M, actTimeout 0, runTimeout 2000.
- Estado de partida **global por proceso** (`Battle.battle_ptr`): 1 partida a la
  vez por proceso; hilos → SIGSEGV (ya verificado antes).
- **RNG interno del motor NO sembrable** (`BattleStart` solo recibe 120 ints):
  misma seed Python → partidas distintas entre procesos. No hay reproducibilidad.
- `search_begin_input`: string ASCII (base64 propio) que crece con el historial
  (82→1454 chars en una partida). Es la entrada de la Search API exportada por
  libcg.so (`SearchBegin/SearchStep/SearchEnd/SearchRelease`, `AgentStart`,
  `AllCard`, `AllAttack`) → simulaciones privadas sin tocar la partida. Detalle
  en `research/search_wrapper.py` (tema aparte).

### Estructura de `select`

Campos SIEMPRE presentes: `type`, `context`, `minCount`, `maxCount`,
`remainDamageCounter`, `remainEnergyCost`, `option`, `deck`, `contextCard`,
`effect`. No hay campo `message`. `effect` = carta que causa el select;
`deck` solo se rellena en búsquedas (lista `{id, serial, playerIndex}` del mazo
PROPIO; tras el efecto hay shuffle — orden no explotable); `contextCard` nunca
se vio non-null.

### Taxonomía de selects observada (type, context)

| (type,ctx) | Qué es | min/max | option.type |
|---|---|---|---|
| (0,0) | Fase principal | 1/1 | 7 jugar carta mano, 8 básico→activo(4)/banca(5), 9 evolucionar/tool sobre inPlay, 12 retirada, 13 atacar (`attackId`), 10 (area 7, ¿estadio?), 14 terminar turno |
| (1,1) | Activo inicial (de mano) | 1/1 | 3 (area 2) |
| (1,2) | Banca inicial | 0/2 | 3 |
| (1,3) | **Cambio forzado con mi activo AÚN EN JUEGO**: mi propio Switch (banca propia) o arrastre de la banca **RIVAL** con Boss's Orders — ver ✏️ 2026-08-11b | 1/1 | 3 (area 5) |
| (1,4) | **Nuevo activo tras KO** (`players[me].active == []`) — ver ✏️ 2026-08-11b | 1/1 | 3 (area 5) |
| (1,21) | Objetivo en banca de un efecto de carta (con mega-lucario: el destino de la energía de Aura Jab) | 1/1 | 3 (area 4 o 5) |
| (1,7) | Búsqueda en mazo (lista `deck`) | 0..1/1 | 3 (area 1) |
| (1,8) | **Descarte de coste: tirar N cartas de la mano** (N variable) | N/N | 3 (area 2) |
| (1,13) | Munkidori: origen de los contadores de daño | 1/1 | 3 (area 4) |
| (1,14) | Dragapult ex: reparto de daño en la banca rival | 1/1 | 3 (area 5) |
| (1,16) | Munkidori: destino de los contadores de daño | 1/1 | 3 (area 4 o 5) |
| (1,17) | Wally's Compassion: Pokémon objetivo | 1/1 | 3 (area 4 o 5) |
| (1,22) | Elegir del descarte (efecto 1163) | 0/1 | 3 (area 3) |
| (4,30) | Descartar energía adjunta (coste; `remainEnergyCost` cuenta atrás) | 1/1 | 6 (`energyIndex`) |
| (5,34) | Elegir cartas reveladas | 2/2 | 15 (`cardId`+`serial`) |
| (8,38) | Robo extra por mulligan rival: elegir número 0..N | 1/1 | 0 (`number`) |
| (9,41) | Elegir primero/segundo | 1/1 | 1=primero, 2=segundo |
| (0,7) | **Confirmación SIN opciones** (búsqueda sin objetivo) | 1/1 | `option=[]` |

⚠️ `(0,7)`: `option` vacío con maxCount 1. El random agent de Kaggle
(`random.sample(range(0),1)`) **casca aquí** y pierde por INVALID; responder
`[0]` funciona (aceptado en trace). Nuestro main.py debe cubrir option vacío.

### ✏️ Corrección 2026-08-11 — `(1,8)` y los contexts «de azar»

La tabla de arriba se escribió el 2026-08-06 con los probes sobre la **baraja de
ejemplo del motor**, y ahí `(1,8)` solo salió con Secret Box (efecto 1092, «elige
3 de tu mano»). Eso resultó ser un artefacto de esa baraja: en el campo real
Secret Box es **1 de 1.123** apariciones (0,1%). Medido sobre 600 episodios de la
ladder (`research/replays/censo_selects_azar.py`, campo `select.effect`):

| (t,c) | carta que lo provoca | quién decide | n | % |
|---|---|---|---|---|
| (1,8) | **Ultra Ball** (1121) | PROPIO | 585 | 52,1% |
| (1,8) | Xerosic's Machinations (1197) | **RIVAL** | 265 | 23,6% |
| (1,8) | Lunatone (675) | PROPIO | 123 | 11,0% |
| (1,8) | Hand Trimmer (1087) | RIVAL 6,0% / PROPIO 3,0% | 101 | 9,0% |
| (1,8) | N's Zoroark ex (293), Morty's Conviction (1187), Secret Box (1092) | PROPIO | 42 | 3,7% |
| (1,13) | Munkidori (112) | PROPIO | 1.852 | 100% |
| (1,16) | Munkidori (112) | PROPIO | 1.852 | 100% |
| (1,14) | Dragapult ex (121) | PROPIO | 1.620 | 100% |
| (1,17) | Wally's Compassion (1229) | PROPIO | 267 | 99,6% |
| (1,3) | *sin efecto* (KO natural) | — | 1.163 | 58,7% |
| (1,3) | Boss's Orders (1182) | PROPIO | 621 | 31,3% |

Lo que cambia respecto a la versión anterior de esta nota:

1. **`(1,8)` NO es «elegir 3 de la mano»**: es el **descarte de coste**, y `N` es
   variable, no 3. Formas observadas (`min=max` SIEMPRE, `area=2`):
   2/2 n=637 (Ultra Ball: «you can use this card only if you discard 2 other
   cards from your hand»), 1/1 n=206, 3/3 n=43, 5/5 n=43, 4/4 n=41, 6/6 n=37
   (Xerosic's Machinations, que baja la mano rival a 3 → N depende de la mano).
   Un agente que asuma `N=3` se rompe en el 96% de los casos.
2. **`(1,3)` mezcla dos cosas distintas** bajo el mismo (type,context) y la misma
   forma (`min=max=1`, `area=5`): un cambio forzado sobre MI banca (`effect`
   **None** o mi propio Switch) y el arrastre desde la banca del **RIVAL** que
   decide quien juega Boss's Orders / Prime Catcher (`effect` no nulo). El «75%
   Boss's Orders» del diagnóstico es el 75% de los casos **con** `effect`
   (621/819), no del total. El signo de la preferencia es **opuesto** en cada
   rama (promuevo lo mejor mío / arrastro lo que más premios me da).
   ⚠️ Lo que NO es: la promoción tras KO. Ver ✏️ 2026-08-11b.
3. `(1,13)`/`(1,14)`/`(1,16)`/`(1,17)` los provoca **siempre el que decide**
   (`effect.playerIndex == current.yourIndex`, 100%). Un select de estos nunca
   llega por una carta del rival: si la carta no está en tu baraja, no lo ves.

Nota general que se deriva de esto: `context` no identifica una mecánica, sino
un **hueco de una carta**. La forma útil de leer un select type 1 es
`(area de option[0], minCount==maxCount, effect.id, effect.playerIndex == yourIndex)`.
Evidencia y consecuencias para la política: `research/notas/descartes-y-selects.md`.

### ✏️ Corrección 2026-08-11b — `(1,3)` y `(1,4)` estaban INTERCAMBIADOS

La tabla decía `(1,3)` = «nuevo activo tras KO» y `(1,4)` = «nuevo activo al
retirar». Es al revés, y el discriminante no es el `effect` sino **el estado de
mi activo**. Evidencia (`research/replays/corpus_promocion.py`, 800 episodios,
6.489 casos con ≥2 opciones; reproducido en local con
`research/probe_promocion.py`):

| (t,c) | `players[me].active` | dueño de las opciones | n | qué es |
|---|---|---|---|---|
| **(1,4)** | **vacío** (100%) | propia (100%) | 3.554 | **promoción tras KO** |
| (1,3) | ocupado (100%) | propia | 1.982 | cambio forzado de MI activo |
| (1,3) | ocupado (100%) | **del rival** | 953 | arrastre (Boss's Orders) |

No hay un solo caso de `(1,4)` con activo vivo ni de `(1,3)` con activo vacío.
Cruce independiente que lo confirma: el acuerdo de v2 medido sobre este corpus
por rama (55,1% en (1,4); 60,2% en (1,3) juntando sus dos mitades) reproduce
exactamente las filas del diagnóstico (55,5% y 59,9%), que también las tenía
etiquetadas al revés — o sea que la **promoción tras KO es la fila de 4.391
casos, no la de 3.691**.

Y hay un tercer inquilino de `area == 5` que la tabla no tenía: **`(1,21)`**, el
objetivo en banca de un efecto de carta. Con mega-lucario es el destino de la
energía de **Aura Jab** y sale **1,36 veces por partida** — más que la propia
promoción tras KO (1,22). Un agente que trate todo `area == 5` como «elige nuevo
activo» está mezclando dos mecánicas distintas. Regla práctica: **despachar por
`players[me].active == []` (KO) y por `playerIndex` de las opciones (mío/suyo),
no por el context**.

- (9,41) lo recibe SIEMPRE el jugador 0 del env (50/50 partidas): elegir ir
  primero/segundo es decisión, no moneda. `current["firstPlayer"]` refleja el
  resultado. Los contexts nuevos pueden aparecer con otras cartas: el agente
  debe ser genérico por `type`+campos, no enumerar contexts.

### Estructura de `current` (real, no la de la doc)

`turn`, `turnActionCount`, `yourIndex`, `firstPlayer`, `supporterPlayed`,
`stadiumPlayed`, `energyAttached`, `retreated` (flags del turno en curso),
`result` (−1 en curso; 0=gana p0, 1=gana p1, otro=empate), `stadium` (lista de
carta), `looking` (siempre null visto), `players[2]`:

- PlayerState: `active[]`, `bench[]`, `benchMax` (5), `deckCount`, `discard[]`
  (contenido completo), `prize` (lista de **null** — ni los propios se ven, solo
  la longitud = restantes), `handCount`, `hand` (cartas propias | **null** para
  el rival), `poisoned/burned/asleep/paralyzed/confused`.
- Pokémon en juego: `id, serial, playerIndex, hp, maxHp, appearThisTurn,
  energies[int], energyCards[carta], tools[], preEvolution[carta]`.
- Cartas: `{id, serial, playerIndex}`; `serial` identifica la copia física
  (0‑59 p0, 60‑119 p1).

## 2. Reglas de baraja verificadas (probe_baraja_resultados.json)

| Caso | errorPlayer/errorType | Nivel env |
|---|---|---|
| baraja ejemplo (33× ID 3) | −1 / 0 (OK) | partida normal |
| 5 copias Pokémon 721 | 0 / **2** | INVALID |
| 4 copias 721 | OK | legal (frontera) |
| 5 copias trainer 1219 | 0 / **2** | INVALID |
| 60 energías sin básico | 0 / **3** | INVALID |
| ID 99999 o 0 | 0 / **1** | INVALID |
| 59 o 61 cartas | ValueError del binding | INVALID («deck does not have 60 cards») |

- **Límite 4 copias por ID** (Pokémon y trainers); **energías básicas exentas**.
- Obligatorio ≥1 Pokémon básico. errorType: 1=ID desconocido, 2=exceso de
  copias, 3=sin básico.
- Con ambos mazos malos, errorPlayer=0 (comprueba p0 primero).
- Bug cosmético del interpreter: el mensaje siempre dice «Player 1's deck
  error.» (usa la `i` del bucle), pero el status INVALID va al jugador correcto.
- **Payoff**: mazo ilegal → infractor INVALID (reward None), rival DONE con
  reward **0** (no gana). Acción ilegal en partida → −1 / **+1**. Es decir: un
  rival con mazo ilegal no te regala victoria; uno que casca en partida, sí.

## 3. Flujo de partida (trace_ejemplo.json, game.py directo)

1. **Setup (turn 0)**: p0 elige primero/segundo (9,41) → cada uno roba 7
   (type 4 propio con cardId / type 5 rival oculto) → chequeo mulligan
   log `{"type":1, hasBasicPokemon}`. **Mulligan**: la mano SE REVELA al rival
   (type 6 mano→mazo con cardId), shuffle (type 0), redraw 7; se repite hasta
   tener básico; el rival recibe (8,38) para robar 0..N extra (N = nº de
   mulligans; visto option 0/1 y robo type 4 tras elegir 1). Con la baraja
   ejemplo (33 energías) hubo 375 mulligans en 50 partidas.
2. Activo inicial (1,1) — colocación **boca abajo** (log type 7 mano→activo,
   sin id para el rival) — banca opcional (1,2) — **6 premios** por jugador
   (6× log type 7 mazo→premios).
3. **Turno**: log 2 (inicio) → robo → selects (0,0) encadenados (cada acción
   devuelve otro (0,0) hasta elegir 14 o atacar 13, que cierran) → log 3 (fin).
   Flags `supporterPlayed/energyAttached/retreated` en `current`.
4. **Monedas**: con la baraja de ejemplo NO aparece ningún log de moneda (el
   primero/segundo es elección, los ataques 1044/1045/1047 no tiran moneda).
   La Search API tiene `manual_coin` → existen en el motor con otras cartas.

### Log types (catálogo completo observado)

0 shuffle · 1 chequeo mulligan (`hasBasicPokemon`) · 2 inicio turno · 3 fin
turno · 4 robo visible (cardId; solo propio) · 5 robo oculto (rival) · 6
movimiento visible (`cardId, fromArea, toArea`) · 7 movimiento oculto (premios,
activo inicial) · 8 retirada (`cardIdActive/cardIdBench`) · 10 trainer jugado ·
11 energía adjuntada (`cardId`+target) · 12 evolución · 15 ataque (`attackId`) ·
16 daño (`value` negativo, `putDamageCounter`) · **23 fin de partida
(`result`, `reason`)**.

Áreas: 1 mazo, 2 mano, 3 descarte, 4 activo, 5 banca, 6 premios, 7 ¿estadio?,
8 energía adjunta, 9 partidario/estadio en juego, 10 bajo la evolución.

## 4. Información oculta (probe_info_oculta.py)

- Del rival se ve: `handCount`, `deckCount`, descarte completo, todo lo en
  juego. NO se ve: mano (`hand: null`), contenido de premios, orden del mazo.
- **Los premios PROPIOS también están ocultos** (`prize: [null,…]`).
- El orden del propio mazo no es observable; en búsquedas se lista el CONTENIDO
  (sin orden explotable: hay shuffle después).
- Logs del rival: sus robos son type 5 sin id; sus jugadas públicas (6, 8, 10,
  11, 12, 15, 16) llevan cardId. Un type 4 con id jamás llega del rival.
  Excepción de información: el mulligan revela la mano entera.

## 5. Condiciones de fin (probe_finales.py — log type 23)

| reason | Condición | Verificado con |
|---|---|---|
| 1 | Premios agotados (el ganador roba su 6º premio) | random (premios_restantes 0) |
| 2 | Deck‑out: el perdedor debe robar con mazo 0 | pasivo vs pasivo (turn ~93) |
| 3 | Sin Pokémon en juego (activo 0 y banca 0) | agresivo vs banquillo |

`result` en el log 23 y en `current["result"]`: 0/1 = índice ganador; el
interpreter mapea cualquier otro valor a empate (0/0). El agente NUNCA ve la
obs final (los estados pasan a DONE y solo quedan rewards); el final se lee en
los logs del último paso si se juega a nivel game.py.

## 6. Implicaciones para main.py

- Cubrir `option == []` → devolver `[0]` (el random agent oficial pierde ahí).
- Devolver entre minCount y maxCount índices únicos válidos; nunca exceptions.
- Genérico por `select.type` + campos de option; los contexts varían por carta.
- Sin reproducibilidad del motor: la consistencia (70 % Model Score) se mide
  contra la varianza real; evaluar con muchas partidas.
- El mulligan filtra información real: barajas con pocos básicos regalan
  información (mano revelada) y robos extra al rival, además del tempo.
