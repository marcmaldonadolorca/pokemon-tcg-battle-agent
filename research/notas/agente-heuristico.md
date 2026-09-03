# Agente heurístico greedy — baseline y política de rollout

Fecha: 2026-08-07. Código: `research/agentes/heuristico.py`. Verificación con
`arena.py` (procs 4) y un verificador de estados de 1.000 partidas (scratchpad,
desechable). Fuentes: `motor-mecanica.md`, `research/select_tipos/`,
`research/cards_clean.csv` y el catálogo del propio motor.

## API

- `agent(obs) -> list[int]`; con `obs["select"] is None` devuelve `DECK`.
- `DECK` = baraja de ejemplo del motor (Mega Abomasnow aggro, 60 IDs) — la
  sustituirá el laboratorio de barajas.
- Sin estado entre llamadas (la única «memoria» es la caché idempotente del
  catálogo de cartas). Importable como módulo por `arena.py`.
- Consultables a nivel módulo: `FALLBACKS` (dict de contadores:
  `politica_excepcion`, `politica_ilegal`, `select_desconocido`,
  `fase_sin_accion`) y `CASOS_RAROS` (set de formas no contempladas).

## Blindaje (gotcha 2)

Toda acción de la política pasa por `_es_legal` (lista de ints únicos, longitud
en [minCount, maxCount], índices en rango; con `option==[]` acepta exactamente
`[0]`/`[]` — el `[0]` está verificado contra el motor). Si la política lanza
excepción o propone algo ilegal, cae a `_fallback` (primeros `minCount`
índices; `[0]` si option vacío con min≥1; `[]` si min 0) y se incrementa el
contador. La política nunca puede tumbar la partida.

## Datos de cartas: catálogo del motor, no solo el CSV

`libcg.so` exporta `AllCard`/`AllAttack` (JSON) — **solo devuelven datos con
una partida iniciada**, por eso la carga es perezosa en el primer select real.
Semántica verificada:

- `cardType`: 0 Pokémon (1.056), 1 Item (77), 2 Tool (27), 3 Supporter (61),
  4 Stadium (26), 5 energía básica (8), 6 especial (12) — cuadra con el censo
  de `cartas-pool.md`.
- `energyType` = tipo elemental del Pokémon/energía y **misma escala que
  `weakness`** (1..8 = G R W L P F D M) → debilidad ×2 si
  `weakness(defensor) == energyType(atacante)`. `pokemonType` es la clase de
  rule box (1 normal, 4 Mega…), NO el elemento.
- `attacks` de la carta = lista de `attackId` → `AllAttack[id]` da `damage`,
  `energies` (lista de tipos por hueco, 0 = incoloro) y `text`.
- ⚠️ Los ataques «hace N daño por cada X» llevan `damage=0` (Riptide,
  Hammer-lanche): se estiman con regex `(\d+) damage (?:for each|times)` × 3
  (naíf deliberado; mejora futura: rollouts con la Search API).
- Textos de trainers: `cards_clean.csv` (`trainer_effect`), clasificación por
  substring `draw`/`search`. Todo degrada con gracia si falta el CSV.

## Correcciones a la taxonomía de `motor-mecanica.md` (verificadas con sonda)

- En (0,0) el option **7** juega CUALQUIER carta de mano por `index`: básicos a
  banca, items, supporters y estadios (la tabla decía «8 básico→activo/banca»).
- El option **8** es adjuntar de mano a un Pokémon en juego
  (`inPlayArea` 4/5 + `inPlayIndex`): energías **y tools**; el 9 es evolucionar.
- El option **10** (area 7) es usar el efecto del estadio en juego, no jugarlo.
- Nuevo select visto: **type 1 con options de area 6 (premios)** al cobrar
  premio — cartas boca abajo, cualquier índice vale.

## Política greedy (deck-agnóstica, despacho por `select.type` + forma)

- **(0,0)** un action por select, orden: bancar básicos hasta 4 (mejor por
  utilidad) → evolucionar (activo primero) → energía del turno al necesitado
  (activo primero, luego el de más daño potencial) → tool (activo primero) →
  item con «search» → supporter con «draw»/«search» si las cartas no-energía
  de la mano son ≤4 (una mano atascada de energías es mano vacía a efectos de
  robo; medible: +7 pts de tasa vs first) → estadio → atacar: kill con
  debilidad ×2 contra el hp actual del activo rival, si no el de más daño
  estimado → terminar turno.
- **type 1** por `area` del option: 5 (nuevo activo) = el más cargado
  (10·energías + daño/10 + hp/100); 2 con `effect` = coste de descarte → las
  `minCount` peores ([] si opcional); 1/2/3/6 = ganancia/setup → las mejores
  hasta `maxCount`.
- **Utilidad de carta**: Pokémon 3,0+daño/1000 > energía 2,5 si a algún propio
  le faltan / 1,0 > supporter robo 2,0 > «search» 1,5 > resto 0,5.
- **type 4** (descartar energía como coste, encadenado): `[0]`. **type 5**
  (reveladas): mejores `maxCount`. **type 8** (número): el máximo. **type 9**
  (primero/segundo): primero. **option vacío** (p. ej. (0,7)): `[0]`.
- Recortes deliberados: nunca retirada (12); el option 10 (habilidades) era
  recorte del baseline y lo cubre el apéndice v2 de abajo.

## Resultados (2026-08-07, torre, procs 4)

| Prueba | n | Resultado |
|---|---|---|
| Estados propios vs random | 1.000 | **1.000× DONE — 0 INVALID/ERROR/TIMEOUT** |
| Fallbacks/casos raros en las 1.000 | — | **todos los contadores a 0, set vacío** |
| Tasa vs random (verificador) | 1.000 | 0,938 IC95 [0,921, 0,951] |
| Tasa vs random (arena) | 400 | 0,938 IC95 [0,909, 0,957] (1º 0,955 / 2º 0,920) |
| Tasa vs first (arena) | 400 | **0,595 IC95 [0,546, 0,642]** (1º 0,700 / 2º 0,490) |
| Tiempo/decisión | 490 dec. | media 0,086 ms, máx 30,1 ms (carga de catálogo) — presupuesto 1,0 s/dec con margen ×10⁴ |

- `first` es un rival serio aquí: nunca casca en (0,7) y el orden de options de
  (0,0) le hace jugar mecánicamente razonable. Antes de los dos afinados
  (umbral de supporter por no-energía y energía al de más daño) estábamos en
  0,525 [0,476, 0,573] — no significativo.
- El split 1º/2º vs first (0,700/0,490) es tempo del mirror aggro (ambos eligen
  ir primero cuando les toca (9,41)), no un bug: mismo patrón atenuado vs
  random.
- ~9 derrotas/100 vs random: varianza real del mazo tragaperras (mulligans de
  33 energías, Hammer-lanche del rival).

## Mejoras futuras (fuera del baseline)

Retirada táctica; valoración real de ataques × (Search API / conteo de
descarte); Boss's Orders y gusting dirigido; elección segundo si el meta lo
premia; usar `remainingOverageTime` (hoy sobra todo el banco).

## Apéndice v2: habilidades (2026-08-10)

Cierra el recorte del baseline: el option **type 10** en (0,0) = activar una
habilidad de un Pokémon en juego (`{"type":10,"area":4|5,"index":i}`) o el
efecto del estadio (`area:7`) — hallazgo de `lab-barajas.md` §3. v1 guardada en
`research/agentes/heuristico_v1_sin_type10.py`.

### Qué activa y con qué regla (`_habilidad_activable`, por texto de habilidad)

Clasificación por `ability_text` del CSV (nueva 4ª componente `habil` del
catálogo; los option 10 de Pokémon sin texto clasificable NO se activan):

- **robo** — «draw» en el texto; entra en (0,0) tras evolucionar y antes de
  gastar recursos. Gates: mazo propio >6 (anti deck-out); Trade («discard a
  card from your hand») solo si el peor descarte no duele (utilidad mínima de
  mano ≤1,0 — energía sobrante/relleno); Flashing Draw («discard…from this
  pokémon») solo con mano ≤4 y sin desnudar al atacante activo (energías >
  coste del mejor ataque si area 4); Run Away Draw («shuffle this pokémon»)
  nunca con el activo sin banca (derrota por mesa vacía); «until you have N»
  solo con mano ≤4. Run Errand pasa sin gate extra. «search your deck» sin
  «draw» (Bonded by the Journey, 353) → mismo escalón, gratis.
- **acel** — «attach»+«energy»; entra tras la energía del turno. Desde mano
  (Electric Streamer, Golden Flame): solo si hay esa energía básica en mano
  (letra parseada de «basic {X} energy») **y** a algún propio le falta energía
  para su mejor ataque — la propia activación consume ambas condiciones, no
  hay bucle. Desde descarte (Charging Up, 401): si hay energía básica que coger.
- **estadio** (area 7) — entra justo antes de atacar. Solo patrón Levincia
  («discard pile into their hand» + «basic {X} energy») y con esa energía en el
  descarte propio. Surfing Beach (switch) NO se activa.
- Tope duro anti-bucle: **12 activaciones type 10 por turno** (`_T10`, única
  memoria entre llamadas; se resetea sola al cambiar turn/partida).

### Selects posteriores nuevos (resueltos, ya no caen a fallback)

- (1,21) objetivo de adjuntar y (1,22)/mano: si el `effect` es carta PROPIA con
  «attach»+«energy» (habilidad o trainer Janine/PP Up; se excluye «switch» para
  no tocar la promoción de activo) → objetivo = el que necesita energía, luego
  el que más pega, hasta maxCount; energías de mano = maxCount (ganancia, no
  coste).
- **type 2** (energías adjuntas, option type 5 con `energyIndex`): coste
  forzoso (min≥1, Flashing Draw) → primeras minCount; opcional (min 0, Erasure
  Ball) → declinar. Idéntico al fallback previo, ahora política deliberada.
- **type 6** con options type 13 (`attackId`, «usa uno de sus ataques», TR
  Murkrow 463): el de más daño estimado.

### Verificación (corrida 2026-08-10, torre, procs 4)

| Prueba | n | Resultado |
|---|---|---|
| Estados propios vs random (150 c/u bellibolt, kangaskhan, zekrom, hooh) | 600 | **600× DONE — 0 INVALID/ERROR/TIMEOUT propios**; rival 600× DONE |
| FALLBACKS / CASOS_RAROS en las 600 | — | **todos a 0, set vacío** |
| v2 vs first (arena, baraja sample) | 400 | 0,620 IC95 [0,572, 0,666] (1º 0,715 / 2º 0,525) — v1 era 0,595 [0,546, 0,642] |
| v2 vs v1 (arena, baraja sample) | 400 | 0,525 IC95 [0,476, 0,573] — sin diferencia (sin regresión: la sample no tiene habilidades) |
| **v2 vs v1 (arena, iono-bellibolt)** | 400 | **0,790 IC95 [0,747, 0,827]** (1º 0,820 / 2º 0,760) — el motor de habilidades vale +29 pts en mirror |
| Tiempo/decisión (espejo bellibolt) | 877 dec. | media 0,083 ms, p99 0,124 ms, máx 45,9 ms (carga de catálogo) — sin cambio vs v1 |

- En las 600 vs random las 8 cartas de habilidad del pool propio se activaron
  (sondeo de 30 espejos: Run Errand ×65, Electric Streamer ×61, Run Away Draw
  ×30+, Levincia ×42, Golden Flame, Trade, Bonded, Flashing Draw) sin un solo
  bucle ni fallback.
- Tasas vs random (sample) por baraja: bellibolt 0,773, kangaskhan 0,827,
  zekrom 0,533, hooh 0,400 — dato de fuerza de BARAJA contra la sample aggro,
  no de legalidad; alimenta el §5 del laboratorio.
- API intacta: `agent(obs)`, `DECK`, `FALLBACKS` (mismas 4 claves),
  `CASOS_RAROS`; blindaje `_es_legal` + `_fallback` sin tocar.
