# Cobertura de cartas del piloto — medida, ampliada y medida otra vez

> **AVISO (2026-08-12)**: las §1-§6 miden contra `heuristico.py` (v2). La segunda pasada,
> a partir de la §7, repite TODO contra `heuristico_v5.py` (el agente del envío) y es la
> que manda. Resumen: sobrevive una sola familia, `recupera`, +1,9 pp [+0,8, +2,9] con
> n=9.000 sobre `mega-lucario`; y −1,7 pp sobre `hops-snorlax`.

Fecha: 2026-08-11. Scripts: `research/cobertura.py` (instrumentación),
`research/agentes/heuristico_cob.py` (política ampliada, interruptores por familia),
`research/agentes/heuristico_ref.py` (envoltorio que solo cambia el `DECK` de
`heuristico.py` para poder medir espejo sin tocarlo), `research/duelo.py` (arena +
contador de ilegales + agregación de `USOS`). `heuristico.py` y `mega-lucario.csv`
**intactos**. Sin commits.

Regla de la nota: cada número lleva su n y su IC95 de Wilson. Un negativo medido es un
resultado. Y nada se acepta con una sola muestra: lo que sale entre 0,50 y 0,53 se vuelve
a tirar con una muestra independiente antes de creérselo.

---

## 1. La medida: qué se le ofrece al piloto y qué juega

`research/cobertura.py` envuelve al agente sin modificarlo. En cada select `(0,0)` resuelve,
para cada `option`, el `card_id` al que se refiere (índice en la mano para los option type
7/8/9; Pokémon en juego para 10/12/13), cuenta en cuántos **puntos de decisión** apareció
cada carta como jugable y cuántas veces la política **la eligió**. Las dos partidas del
espejo cuentan (mismo piloto, misma baraja).

Ofrecida > 0 y jugada = 0 ⇒ **papel**: la carta está en la baraja, el motor la ofrece, y la
política no tiene ninguna rama que la devuelva jamás.

### Cartas muertas — `mega-lucario` (la lista de la ladder), heuristico.py, n=300, 12.405 decisiones

| id | copias | carta | ofrecida (veces/partida) | en mano (veces/partida) | jugada |
|---|---|---|---|---|---|
| 1141 | 2 | Premium Power Pro | 3.084 (**10,28**) | 3.084 (10,28) | **0** |
| 1123 | 2 | Switch | 2.646 (**8,82**) | 3.273 (10,91) | **0** |
| 1182 | 2 | Boss's Orders | 2.035 (**6,78**) | 3.212 (10,71) | **0** |
| 1097 | 2 | Night Stretcher | 1.436 (**4,79**) | 3.108 (10,36) | **0** |
| 1238 | 2 | Tarragon | 1.227 (**4,09**) | 3.125 (10,42) | **0** |

**Cobertura = 50/60 = 0,833.** Diez copias, cinco IDs. Coincide exactamente con la
aritmética de `estrategia-plan.md` §R2 («10/60 con v2»), ahora medida contra el motor.

### Cartas muertas — `hops-snorlax` (el envío vivo 55407312), n=300, 19.779 decisiones

| id | copias | carta | ofrecida (veces/partida) | jugada |
|---|---|---|---|---|
| 1123 | 2 | Switch | 5.385 (**17,95**) | **0** |
| 1097 | 2 | Night Stretcher | 4.685 (**15,62**) | **0** |
| 1182 | 2 | Boss's Orders | 4.301 (**14,34**) | **0** |

**Cobertura = 54/60 = 0,900** (las «6/60» del plan, confirmadas).

Dato lateral que corrige una sospecha: **las herramientas NO están muertas**. Hop's Choice
Band 1171 se juega el 61,2 % de las veces que se ofrece y el estadio Postwick 1255 el
27,5 %. El paso 4 de `_fase_principal` (que busca `option type 8` con `cardType 2`) sí
dispara. Lo que le falta a las herramientas no es cobertura, es **elección de portador**.

### Por qué no se juegan (cruce con el catálogo)

El paso 5 de `_fase_principal` exige `clase(cid) == 1 and "search" in textos[cid]` y el
paso 6 exige `clase(cid) == 3 and ("draw" or "search")` **y** mano no-energía ≤ 4. Los
textos reales:

| carta | cardType | texto | ¿casa con «draw»/«search»? |
|---|---|---|---|
| 1097 Night Stretcher | 1 (Item) | *put a Pokémon or a Basic Energy card from your discard pile into your hand* | **no** |
| 1123 Switch | 1 (Item) | *switch your Active Pokémon with 1 of your Benched Pokémon* | **no** |
| 1141 Premium Power Pro | 1 (Item) | *during this turn, attacks used by your {F} Pokémon do 30 more damage* | **no** |
| 1238 Tarragon | **3 (Supporter)** | *put up to 4 … {F} Pokémon and Basic {F} Energy … from your discard pile into your hand* | **no** |
| 1182 Boss's Orders | 3 (Supporter) | *switch in 1 of your opponent's Benched Pokémon to the Active Spot* | **no** |

No hay bug: hay un filtro por texto que solo reconoce dos verbos. Todo lo demás es
invisible para la política.

### Sonda obligatoria: qué select abre cada carta muerta

Antes de activarlas (`scratchpad/probe_selects_nuevas.py`, 60 partidas forzando el clic):

| carta | select que abre | ¿lo cubre `_elige_cartas`? |
|---|---|---|
| 1097 Night Stretcher | `(1,7)` min1 **max1** area 3 | sí (rama de ganancia area 3) |
| 1238 Tarragon | `(1,7)` min1 **max4** area 3 | sí (misma rama, coge las 4 mejores) |
| 1141 Premium Power Pro | ninguno: vuelve a `(0,0)` | — |
| 1123 Switch | `(1,3)` min1 max1 **area 5, `playerIndex` = mío** | sí (promoción propia) |
| 1182 Boss's Orders | `(1,3)` min1 max1 **area 5, `playerIndex` = del RIVAL** | **NO** |

El último es el aviso de `motor-mecanica.md` (corrección 2026-08-11) hecho carne: el mismo
`(1,3)` con la misma forma indexa **la banca del rival**, y `_elige_cartas` lo resolvería
contra `yo["bench"]` con el signo invertido («el más cargado»), que para gustear es
exactamente lo contrario de lo que se quiere. Por eso la familia `gusting` lleva su propia
rama (`_peor_de_la_banca_rival`).

---

## 2. La ampliación: `research/agentes/heuristico_cob.py`

Copia de `heuristico.py` con siete familias, **cada una detrás de su interruptor**
(variable de entorno `COB_FAMILIAS`, coma-separada, `todas` las enciende). Con los
interruptores apagados el módulo es la política v2 sin cambios — comprobado abajo. La
baraja se toma de `COB_DECK` para poder medir espejo con listas reales.

| familia | qué añade | dónde |
|---|---|---|
| `recupera` | recursión del descarte: Night Stretcher 1097, Tarragon 1238, Sacred Ash 1129 y cualquier texto `discard pile into your hand/deck`. Puerta: ≥1 objetivo si pesca 1 (y si es energía, solo con la mano sin energía); ≥3 si es multipesca; para Supporter exige ≥3 (compite con «roba 3») | pasos 5b (Item) y 6b (Supporter) |
| `switch` | Switch 1123 y equivalentes. Puerta: **tempo** (el activo no puede atacar y en la banca hay quien sí) o **salvamento** (el activo es ex/megaEx, muere a la amenaza estimada del turno siguiente y hay relevo igual de cargado). Se juega **antes** de la energía del turno para que la energía vaya al que se queda | paso 2c |
| `tool` | elige **portador**: globo (`retreat cost … less`) al de retirada más cara; modificador de daño al atacante que cumple la restricción (nombre «Hop's», `rule box`, `{ex}` rival), no «el activo y ya» | paso 4b (antes del 4 original) |
| `estadio` | juega el estadio propio solo si conviene: nunca sustituye a uno propio ya en juego, siempre tira el del rival, y si el texto dice *both yours and your opponent's* cuenta beneficiarios y exige que ganemos nosotros más (o, si es castigo `-N HP`, que pierdan ellos más) | paso 7 |
| `energia` | trainers que **adjuntan** energía sin decir «draw»/«search» (PP Up, Janine…), solo si falta energía | paso 3c |
| `buff` | modificador de daño (Premium Power Pro 1141) **solo si cruza el umbral de KO** del activo rival, con debilidad aplicada | paso 7c, antes de atacar |
| `gusting` | Boss's Orders 1182 con puerta estrecha N5/P12 (arrastra un KO, o un objetivo que no puede retirarse ni atacar) **+ la corrección del `(1,3)` de banca rival** | paso 6a y `_elige_cartas` |

Contadores `USOS` por familia (los agrega `duelo.py`), para no medir nunca un interruptor
que en realidad no dispara.

---

## 3. Las medidas — espejo, `duelo.py`, n=2.000, procs 3

`A = heuristico_cob.py` (familia encendida) vs `B = heuristico_ref.py` (= `heuristico.py`),
**la misma baraja en los dos lados**, asiento intercambiado. Cero acciones ilegales
(`status` = DONE) y cero `FALLBACKS` en **todas** las corridas.

### Control (interruptores apagados)

| corrida | n | tasa | IC95 | veredicto |
|---|---|---|---|---|
| control | 2.000 | 0,4920 | [0,4701, 0,5139] | la copia es la v2: la báscula no tiene sesgo |

### Familias, una a una

| familia | baraja | usos | n | tasa | IC95 | veredicto |
|---|---|---|---|---|---|---|
| `recupera` | mega-lucario | 1.394 (0,70/partida) | 2.000 | **0,5145** | [0,4926, 0,5364] | no significativa |
| `gusting` | mega-lucario | 793 (0,40/partida) | 2.000 | **0,5140** | [0,4921, 0,5359] | no significativa |
| `tool` | hops-snorlax | 4.663 (2,33/partida) | 2.000 | **0,5110** | [0,4891, 0,5329] | no significativa |
| `switch` | mega-lucario | 304 (0,15/partida) | 2.000 | **0,5080** | [0,4861, 0,5299] | no significativa |
| `estadio` | hops-snorlax | 571 (0,29/partida) | 2.000 | **0,5035** | [0,4816, 0,5254] | no significativa |
| `buff` | mega-lucario | **1 uso en 200 partidas** | — | — | — | **no medible**: ver §5 |
| `energia` | — | 0 | — | — | — | **no aplicable**: ninguna de las dos listas vivas lleva energía especial ni acelerador de trainer |

Ninguna familia suelta mueve la aguja al nivel de resolución de n=2.000 (±2,2 pp). Todas
pasan el gate de «no empeora» (límite inferior ≥ 0,482 en el peor caso).

### La combinación, y el negativo que salió de ella

| combinación | baraja | n | tasa | IC95 | z |
|---|---|---|---|---|---|
| `recupera+switch+gusting` (descubrimiento) | mega-lucario | 2.000 | 0,5320 | [0,5101, 0,5538] | +2,86 |
| `recupera+switch+gusting` (confirmación 1) | mega-lucario | 2.000 | 0,5125 | [0,4906, 0,5344] | +1,12 |
| `recupera+switch+gusting` (confirmación 2) | mega-lucario | 2.000 | 0,5375 | [0,5156, 0,5593] | +3,35 |
| **agregado** | mega-lucario | **6.000** | **0,5273** | **[0,5147, 0,5399]** | **+4,23** |
| **misma combinación** | **hops-snorlax** | 2.000 | **0,4305** | **[0,4090, 0,4523]** | **−6,21** |
| `recupera+switch+tool+estadio+gusting` | hops-snorlax | 2.000 | 0,4370 | [0,4154, 0,4588] | −5,63 |

Sobre `mega-lucario` la combinación gana +2,7 pp con n=6.000. **Sobre `hops-snorlax` la
misma combinación pierde 7 pp.** Ese contraste es el hallazgo de la pasada, y obliga a
aislar. La culpable es una sola familia:

| aislamiento | baraja | n | tasa | IC95 |
|---|---|---|---|---|
| `gusting` solo | hops-snorlax | 2.000 | **0,4265** | [0,4050, 0,4483] |
| todo **menos** `gusting` (`recupera+switch+tool+estadio`) | hops-snorlax | 2.000 | **0,5050** | [0,4831, 0,5269] |

`gusting` explica el hundimiento entero: −7,4 pp él solo sobre `hops-snorlax`, y quitarlo
devuelve la combinación a la neutralidad. Es coherente con lo ya sabido (gusting general
0,495 con n=1.500) y añade el *por qué*: Boss's Orders **gasta la ranura de Supporter**, y
`hops-snorlax` es una lista que vive del robo (16 Supporters). Su puerta estrecha no
compensa el turno de robo que se come. Sobre `mega-lucario` sale 0,514 — no significativo —
así que **no hay ninguna baraja donde `gusting` esté demostrado que ayude, y hay una donde
está demostrado que hace daño. Fuera.**

### La combinación aceptada

| combinación | baraja | n | tasa | IC95 |
|---|---|---|---|---|
| `recupera+switch` (descubrimiento) | mega-lucario | 2.000 | 0,5230 | [0,5011, 0,5448] |
| `recupera+switch` (confirmación independiente) | mega-lucario | 2.000 | 0,5175 | [0,4956, 0,5393] |
| **agregado** | mega-lucario | **4.000** | **0,5202** | **[0,5048, 0,5357]** |
| `recupera+switch+tool+estadio` | hops-snorlax | 2.000 | 0,5050 | [0,4831, 0,5269] |

Lectura honesta: la muestra de confirmación **por sí sola no es significativa** (z=+1,57);
lo que sostiene el resultado es que las dos muestras apuntan en la misma dirección y el
agregado de n=4.000 sí lo es (z=+2,56). Es un **+2,0 pp [+0,5, +3,6]**, no un +5. Y sobre
la otra baraja viva es neutro (no daña). Ese es el tamaño real del techo de cobertura sobre
estas dos listas.

---

## 4. Verificación de la variante aceptada (`recupera+switch`, mega-lucario)

`scratchpad/legalidad_tiempo.py`, 500 partidas, procs 3:

- **Acciones ilegales: 0.** `status` = DONE en los 500 episodios, en los dos lados.
- `FALLBACKS` = `{politica_excepcion: 0, politica_ilegal: 0, select_desconocido: 0, fase_sin_accion: 0}`.
  Ningún select nuevo cayó al fallback: los `(1,7)` de Night Stretcher/Tarragon y el
  `(1,3)` de Switch los resuelve `_elige_cartas` tal cual.
- **Tiempo: 18.354 decisiones en 9,47 s ⇒ 0,52 ms/decisión** (~0,02 s de reloj por partida
  frente a los 600 s de banco: margen ×30.000). Sigue en milisegundos.

---

## 5. Cobertura antes / después

Con la configuración **aceptada** (`recupera+switch`; en `hops-snorlax` además
`tool+estadio`, que ahí sí aplican), n=300 por medida:

| baraja | cobertura antes | cobertura después | copias que reviven |
|---|---|---|---|
| `mega-lucario` | **50/60 = 0,833** | **56/60 = 0,933** | 2× Night Stretcher, 2× Tarragon, 2× Switch |
| `hops-snorlax` | **54/60 = 0,900** | **58/60 = 0,967** | 2× Night Stretcher, 2× Switch |

Y se juegan de verdad, no es cobertura de papel:

| carta | baraja | % de veces jugada cuando se ofrece (antes → después) |
|---|---|---|
| 1097 Night Stretcher | mega-lucario | 0,0 % → **33,7 %** (204 usos en 300 partidas) |
| 1238 Tarragon | mega-lucario | 0,0 % → **21,4 %** (181) |
| 1123 Switch | mega-lucario | 0,0 % → **2,9 %** (93) |
| 1097 Night Stretcher | hops-snorlax | 0,0 % → **43,6 %** (514) |
| 1123 Switch | hops-snorlax | 0,0 % → **1,1 %** (58) |
| 1255 Postwick (estadio) | hops-snorlax | 27,5 % → **9,5 %** |

Postwick **baja** a propósito: su texto es *Attacks used by Hop's Pokémon (**both yours and
your opponent's**) do 30 more damage*, y en el espejo el rival tiene tantos Pokémon «Hop's»
como nosotros, así que la puerta lo declina. Eso es exactamente el «no cuando ayuda más al
rival» del encargo; contra el campo, donde casi nadie juega Hop's, la misma puerta lo
jugaría. La familia `estadio` midió 0,5035 [0,4816, 0,5254]: no cuesta nada.

Con **todas** las familias encendidas la cobertura de `mega-lucario` llega a **60/60**,
pero dos de las que cierran el hueco no se aceptan:

- **1182 Boss's Orders (2 copias, ofrecida 8,88 veces/partida)** sigue en papel: la única
  familia que la juega mide −7,4 pp en `hops-snorlax`. **Es una decisión de baraja, no de
  piloto**: o se sustituyen las 2 copias por cartas que sí jugamos, o se queda el papel.
- **1141 Premium Power Pro (2 copias, ofrecida 12,79 veces/partida)** sigue en papel, y la
  puerta es correcta: en el espejo Mega Lucario (340 PS) contra Aura Jab (130), +30 nunca
  cruza un umbral de KO — disparó **1 vez en 200 partidas**. La carta no es injugable, es
  **inútil en este emparejamiento**; su valor hay que medirlo contra el campo (gauntlet),
  no en espejo. Otra decisión de baraja disfrazada de cobertura.

---

## 6. Qué se lleva el proyecto

1. La cobertura era real y ahora está medida, no calculada: 50/60 y 54/60 sobre las dos
   listas vivas, con las frecuencias de aparición de cada carta muerta.
2. Ampliarla vale **+2,0 pp [+0,5, +3,6]** con n=4.000 en `mega-lucario` y **0** en
   `hops-snorlax`. Es una mejora pequeña y honesta, del tamaño que predijo la báscula, no
   la palanca que da la vuelta a un piloto que va 100 puntos por debajo de μ0.
3. El techo que queda **no es de piloto**: 4 de las 60 cartas de `mega-lucario` siguen
   muertas porque son cartas que esta baraja no debería llevar (Boss's Orders y Premium
   Power Pro). Eso es §6 de `estrategia-plan.md`, y es del propietario.
4. Séptimo negativo medido del proyecto: **`gusting` con puerta estrecha, 0,4265
   [0,4050, 0,4483] con n=2.000 sobre `hops-snorlax`.** No solo «no ayuda»: hace daño, y
   se sabe por qué (se come la ranura de Supporter de una lista que vive del robo).
5. Método que conviene conservar: **medir una palanca sobre las DOS barajas vivas**. Con
   una sola (`mega-lucario`) la combinación con `gusting` habría entrado con +2,7 pp y
   z=+4,23 tras confirmación, y habría hundido el otro envío.

---

# Segunda pasada (2026-08-12): la cobertura contra un rival FUERTE

Todo lo de arriba se midió contra `heuristico.py` (v2), que es tan flojo como el
candidato. Entre medias, otra tanda dejó **`heuristico_v5.py`** (v2 + RETIRADA +
BUSQ_CRITERIO + GUSTING; 0,6020 contra el v2 en espejo, n=3.000; es el agente del envío).
Eso cambia dos cosas y por eso se repite la medida entera:

1. **Hay báscula fuerte.** Medir la cobertura contra el v5 dice si aporta algo *encima de
   lo mejor que tenemos*, no si dos flojos empatan.
2. **El v5 sabe RETIRAR**, y la retirada era la capacidad que faltaba para que las
   herramientas sirvieran de algo (`lucario-v2.md`: Air Balloon se pegaba ~1 vez por
   partida y era inerte porque el piloto nunca retiraba, 975 option 12 ofrecidos y 0 usados).
   La regla del encargo —una familia que depende de otra capacidad se implementa y se mide
   **con** ella— aquí se cumple sola: el par globo+retirada ya es medible.

Piezas nuevas: `research/agentes/heuristico_cob5.py` (= v5 + familias, generado por
`scratchpad/gen_cob5.py`), `research/agentes/heuristico_v5_ref.py` (v5 con la baraja por
`COB_DECK`, la referencia), `scratchpad/probe_globo.py` y `scratchpad/probe_recupera.py`
(zombis), `scratchpad/gen_v6.py` → **`research/agentes/heuristico_v6.py`** (el candidato
sin variables de entorno). `heuristico.py`, `heuristico_v5.py` y `mega-lucario.csv`
intactos; sin commits; sin subir nada.

**Prueba de que la copia no cambia nada por sí sola**: el hash del AST de las 30 funciones
del v5 es idéntico en `heuristico_cob5.py` salvo las dos que llevan gancho
(`_fase_principal`, `_decide_retirada`), y el control con todas las familias apagadas mide
**0,4935 IC95 [0,4716, 0,5154] n=2.000** con los seis contadores `USOS` de cobertura a cero.

## 7. Cobertura medida del v5 (no del v2)

`research/cobertura.py`, `mega-lucario` a los dos lados, n=300 · 14.936 puntos de decisión,
0 fallbacks:

| id | copias | carta | ofrecida (veces/partida) | jugada | %jug |
|---|---|---|---|---|---|
| 1141 | 2 | Premium Power Pro | 3.950 (**13,17**) | **0** | 0,0 % |
| 1123 | 2 | Switch | 3.427 (**11,42**) | **0** | 0,0 % |
| 1097 | 2 | Night Stretcher | 1.667 (5,56) | **0** | 0,0 % |
| 1238 | 2 | Tarragon | 1.535 (5,12) | **0** | 0,0 % |
| 1182 | 2 | Boss's Orders | 1.525 (5,08) | 238 | **15,6 %** |

**Cobertura del v5 = 52/60 = 0,867** (el v2 daba 50/60). La diferencia es exactamente
Boss's Orders: la palanca GUSTING del v5 resucitó las 2 copias que la §5 de esta nota daba
por papel mojado. Las otras cuatro cartas muertas son las mismas, con las mismas
frecuencias.

## 8. Zombis: cartas que se juegan y no se aprovechan

Zombi = la carta sí se juega, pero el efecto muere porque el piloto no tiene la capacidad
que lo explota. El caso canónico es **Air Balloon 1174** (no está en `mega-lucario`; está
en la variante `lucario-v2-balloon` = −2 Urbain +2 Air Balloon). `scratchpad/probe_globo.py`,
200 partidas, los dos asientos:

| medida | v2 (`lucario-v2.md`) | **v5** | v5 + familia `tool` |
|---|---|---|---|
| globo ofrecido | 306 | 1.787 (8,94/partida) | 1.641 |
| globo pegado | 58 (0,19/partida) | 333 (**1,67**/partida) | 329 |
| retiradas (option 12) | **0 de 975** | 150 (0,75/partida) | 147 |
| retiradas del que LLEVA el globo | **0** | **67** (0,34/partida) | 60 |
| …más baratas gracias al globo | 0 | **61** | 50 |
| …imposibles sin el globo | 0 | **6** | 10 |
| portador | — | Regirock 166 · Lucario 122 · Riolu 45 | Regirock 187 · Lucario 93 · Riolu 49 |

Lectura: **el zombi lo mató la RETIRADA del v5, no la cobertura.** Con el v2 el globo era
100 % inerte; con el v5, 0,34 retiradas por partida van montadas en él y 6 de cada 200
partidas contienen una retirada que sin globo era ilegal. Elegir mejor el **portador**
(familia `tool`, que además hace que `_decide_retirada` cuente el coste **efectivo**: 370
retiradas abaratadas en 2.000 partidas) no añade nada: **0,4985 IC95 [0,4766, 0,5204]
n=2.000**.

Y la pregunta que dejó abierta `lucario-v2.md` («si alguna vez se implementa la retirada,
esta lista es la primera que hay que volver a medir») ya tiene respuesta, con las dos listas
pilotadas por el v5:

| comparación de BARAJAS | n | tasa | IC95 |
|---|---|---|---|
| `lucario-v2-balloon` **contra** `mega-lucario` | 2.000 | **0,4690** | [0,4472, 0,4909] |

**No.** Aun con la retirada implementada y el globo de verdad en uso, cambiar 2 Urbain por
2 Air Balloon **pierde 3,1 pp**. Queda cerrado: el globo no es una carta muerta por falta de
piloto, es una carta que **no compensa las 2 cartas de robo que desplaza**.

Los otros dos candidatos a zombi resultaron no serlo: las herramientas de `hops-snorlax` ya
se jugaban el 61,2 % de las veces (§1) y elegirles portador mide 0,4935; el estadio Postwick
se juega y su puerta mide 0,4895.

## 9. Las familias, una a una, contra el v5

`research/duelo.py`, A = `heuristico_cob5.py` (familia encendida), B = `heuristico_v5_ref.py`,
misma baraja a los dos lados, asientos intercambiados, `--procs 3`, IC de Wilson.
**Cero acciones ilegales y cero fallbacks en las 25.000 partidas de la tanda.**

| familia | baraja | usos | n | tasa | IC95 | veredicto |
|---|---|---|---|---|---|---|
| control (todas apagadas) | mega-lucario | 0 | 2.000 | 0,4935 | [0,4716, 0,5154] | la copia es el v5 |
| **`recupera`** | mega-lucario | 1.379 (0,69/partida) | 2.000 | **0,5280** | [0,5061, 0,5498] | descubrimiento |
| **`recupera`** (confirmación) | mega-lucario | 1.468 | 2.000 | 0,5100 | [0,4881, 0,5319] | no significativa sola |
| **`recupera`** (3ª muestra) | mega-lucario | 2.252 | 3.000 | 0,5213 | [0,5034, 0,5392] | reproduce |
| `switch` | mega-lucario | 360 (0,18/partida) | 2.000 | **0,5000** | [0,4781, 0,5219] | **nada, y exacto** |
| `recupera+switch` | mega-lucario | 1.411 / 389 | 2.000 | 0,5250 | [0,5031, 0,5468] | = `recupera` sola |
| `tool` | hops-snorlax | 4.664 (2,33/partida) | 2.000 | 0,4935 | [0,4716, 0,5154] | no |
| `tool` (globos) | lucario-v2-balloon | 1.644 | 2.000 | 0,4985 | [0,4766, 0,5204] | no |
| `estadio` | hops-snorlax | 589 | 2.000 | 0,4895 | [0,4676, 0,5114] | no |
| `buff` | mega-lucario | **1 uso / 30 partidas** | — | — | — | no medible (igual que en §5) |
| `energia` | — | 0 | — | — | — | no aplicable (ninguna lista la lleva) |

### La única que sobrevive: `recupera`

| muestra | n | victorias | tasa |
|---|---|---|---|
| descubrimiento | 2.000 | 1.056 | 0,5280 |
| confirmación independiente | 2.000 | 1.020 | 0,5100 |
| tercera muestra independiente | 3.000 | 1.564 | 0,5213 |
| **agregado** | **7.000** | **3.640** | **0,5200 IC95 [0,5083, 0,5317] · z = +3,35** |
| + el fichero de envío `heuristico_v6.py` punta a punta | 2.000 | 1.027 | 0,5135 |
| **agregado con las cuatro** | **9.000** | **4.667** | **0,5186 IC95 [0,5082, 0,5289] · z = +3,52** |

Tres muestras independientes apuntando al mismo sitio y ninguna parada opcional: la tercera
se tiró **antes** de mirar si hacía falta, precisamente por el error que documenta
`agente-v5.md` §3. **+1,9 pp [+0,8, +2,9] encima del v5**, que es el agente del envío.

### Y el negativo que la acota: `recupera` es DE ESTA BARAJA

| baraja | n | tasa | IC95 |
|---|---|---|---|
| `mega-lucario` | 9.000 | **0,5186** | [0,5082, 0,5289] |
| `hops-snorlax` (2 muestras: 0,4780 y 0,4880) | 4.000 | **0,4830** | [0,4675, 0,4985] |

Sobre `hops-snorlax` **cuesta 1,7 pp** y el IC no toca el 0,5. Tiene mecánica: en
`mega-lucario` el descarte es el depósito de combustible (Aura Jab adjunta hasta 3 energías
{F} **del descarte**, Regi Charge hasta 2), así que devolver Pokémon a la mano encaja con un
motor que ya vive del descarte; `hops-snorlax` no tiene nada de eso y la carta solo gasta
ranura. Es la lección de `agente-v5.md` §3 otra vez, ahora en la dirección contraria: **una
palanca medida con una lista no es una palanca de la política.**

Refinamiento que NO hace falta (medido antes de escribirlo, `scratchpad/probe_recupera.py`,
200 partidas): la sospecha era que recuperar **energía** le roba combustible a Aura Jab. De
281 disparos, **254 tienen Pokémon que recuperar y solo 27 (9,6 %) son de energía sola**.
Una variante «solo Pokémon» cambiaría menos del 10 % de las decisiones: no es medible con
n=2.000 y no se construye.

## 10. Verificación de la variante aceptada

`scratchpad/legalidad_cob5.py`, `recupera` sobre `mega-lucario`, 500 partidas, procs 3:

- **0 acciones ilegales**: `status` = DONE en los 500 episodios y en los dos lados.
- `FALLBACKS` = `{politica_excepcion: 0, politica_ilegal: 0, select_desconocido: 0, fase_sin_accion: 0}`.
- **21.672 decisiones en 7,71 s ⇒ 0,356 ms/decisión** (~0,015 s de agente por partida frente
  a los 600 s de banco).
- Paquete construido y validado con la trampa de PKM-005 (`exec()` sin `__file__`):
  `envios/heuristico-v6-mega-lucario.tar.gz`, 0,5 MiB, 15 partidas, 0 estados anómalos.
  **No se ha subido nada** (los envíos los hace el orquestador).

### Cobertura antes / después (n=300 cada una)

| | v5 | v5 + `recupera` (= v6) |
|---|---|---|
| cobertura | **52/60 = 0,867** | **56/60 = 0,933** |
| 1097 Night Stretcher | 0,0 % de 1.667 ofertas | **34,5 %** (276 usos) |
| 1238 Tarragon | 0,0 % de 1.535 ofertas | **18,6 %** (187 usos) |
| copias que siguen muertas | 8 | **4**: 2× Switch 1123, 2× Premium Power Pro 1141 |

Las 4 copias que quedan podrían cubrirse —con `recupera+switch` la cobertura sube a **58/60 = 0,967**, medido, n=200—
pero `switch` mide **0,5000 exacto** con n=2.000. Es la moraleja de la tanda:
**la cobertura no es el objetivo, es el diagnóstico.** Cubrir una carta que no paga sube el
numerador y no sube el winrate. Las 2 copias de Premium Power Pro siguen siendo decisión de
BARAJA, no de piloto (con Mega Lucario de 340 PS contra Aura Jab de 130, +30 no cruza un
umbral de KO casi nunca: 1 disparo cada 30 partidas).

## 11. Qué se lleva el proyecto de esta segunda pasada

1. **`recupera` es la primera palanca de cobertura que sobrevive a un rival fuerte**:
   +1,9 pp [+0,8, +2,9] sobre el v5 con n=9.000 y cuatro muestras independientes. Candidato
   listo: `research/agentes/heuristico_v6.py` + `envios/heuristico-v6-mega-lucario.tar.gz`.
2. **Está atada a `mega-lucario`**: sobre `hops-snorlax` mide 0,4830 [0,4675, 0,4985], que es
   daño medido. No mandar el v6 con otra lista sin repetir la medida.
3. **El zombi Air Balloon ya no lo es, y aun así la lista con globos pierde** (0,4690
   [0,4472, 0,4909] contra `mega-lucario`). Pregunta cerrada de `lucario-v2.md`.
4. **Cuatro negativos medidos más**: `switch` 0,5000 (n=2.000), `tool` 0,4935 (hops) y
   0,4985 (globos), `estadio` 0,4895, y la baraja de globos 0,4690.
5. La primera pasada (§1-§6, contra el v2) **no estaba equivocada, estaba mal referenciada**:
   `recupera` medía 0,5145 contra el v2 y 0,5186 contra el v5 — el efecto era real y del
   mismo tamaño; lo que era ruido eran `switch`, `tool` y `estadio`, que contra un rival
   fuerte se caen a 0,50 limpiamente.
