# Banca y asiento — dos decisiones que hacíamos sin pensar

Fecha: 2026-08-11 (ampliada la misma tarde con las confirmaciones a n grande, y
**revisada por una segunda pasada de verificación** que reprodujo el dato de campo, cerró el
único hueco de medición que quedaba —`crit` a n grande— y añadió el análisis condicionado del
asiento; ver §8).
Código: `research/agentes/heuristico_banca.py` (copia del v2 con una palanca de banca),
`research/replays/asiento.py` y `research/replays/banca_expertos.py` (extractores de dato
directo sobre los replays). `research/agentes/heuristico.py` (el v2, piloto de los dos envíos
vivos) **no se toca**.

Báscula: `arena.py` (intercambio de asiento + IC de Wilson), `--procs 3`, baraja
`mega-lucario` en los dos lados salvo donde se diga (aísla piloto, no baraja). Las corridas de
esta segunda tanda usan `duelo.py`, un envoltorio de `arena.py` que además cuenta **partidas
ilegales** (`state.status != DONE`) y agrega los contadores `USOS`/`FALLBACKS` del módulo — así
la legalidad y el winrate salen de la MISMA pasada y no de dos experimentos distintos.

> Recordatorio del gate: el acuerdo con los expertos **no** predice ganar (r = −0,028).
> Todo lo de aquí es hipótesis con dirección hasta que `arena.py` diga lo contrario.

**Resumen de una línea**: el asiento estaba bien resuelto por defecto (los expertos eligen
PRIMERO el 99,37% —censo de 9.337 episodios— y nosotros también) y cambiarlo cuesta −8,9 puntos
globales, **−14,3 condicionando al asiento en que de verdad elegimos**; **ninguna política de
banca pasa el gate**, ni por cantidad (recortar es significativamente peor), ni por orden
(0,509 en 6.000 partidas), ni la del enunciado tal cual (`crit`, 0,484 en 2.100), ni la
anti-gusteo medida contra un rival que sí gustea (+0,004 en 4.500 por lado). Lo único que sí se
separa de 0,5 en toda la sesión es un subproducto ajeno a esta tarea: la palanca `GUSTING` de
v3 con `mega-lucario`.

---

## 1. PRIMERO / SEGUNDO — dato directo, cerrado

`research/replays/asiento.py` recorre **los 9.337 episodios completos** de los dos datasets
diarios (2026-08-08 y 2026-08-09), localiza el select `(9,41)` y lee la acción del experto con
el desfase +1. Resultado guardado en `data/replays/asiento.json` (reverificado el 2026-08-11
releyendo el JSON, no reusando el resumen anterior).

> **Es un CENSO, no una muestra.** El zip del 08 trae 4.669 episodios y el del 09 otros 4.668:
> 4.669 + 4.668 = **9.337**, exactamente los que hay en el crudo. O sea que aquí no hay
> semilla ni muestreo que discutir — están **todos** los episodios de los dos días, y el
> `random.Random(2026).shuffle` del extractor es irrelevante porque el corte `[:episodios]`
> no llegó a cortar nada. El IC de la tabla es el de una proporción sobre la población
> completa disponible. (El 99,7% que cita el diagnóstico es su submuestra de 1.000 episodios,
> con 3 discrepancias; el censo da 59/9.337 y es la estimación buena. Misma dirección.)

### Qué eligen los expertos

| elección | n | % | IC95 |
|---|---:|---:|---|
| **PRIMERO** (`option.type == 1`) | **9.278** | **99,37%** | [0,9919, 0,9951] |
| SEGUNDO (`option.type == 2`) | 59 | 0,63% | [0,0049, 0,0081] |

Detalles verificados de paso, todos con n = 9.337:

- El select `(9,41)` lo recibe **siempre el jugador 0** del env (9.337/9.337) y siempre con la
  misma forma: `option = [{"type":1},{"type":2}]`, `min/max = 1/1`.
- **Semántica confirmada contra el estado**, no contra la doc: quien elige `type 1` acaba siendo
  `current["firstPlayer"]` en 9.278/9.278 casos, y quien elige `type 2` **no** lo es en 59/59.
  Es decir, `1 = ir primero` de verdad, y elegir es elegir tu asiento (no el del rival).
- Los 59 que eligen segundo no son un arquetipo: son un puñado de equipos (Seasaw 17,
  suguuuuu & hiehie 7, Shelgon 6…) y ganan 31/59 = 0,525 [0,400, 0,647], indistinguible del
  0,545 [0,535, 0,555] de los que eligen primero. **No hay ninguna baraja que prefiera el
  segundo.**
- **Spot-check a mano del parseo** (2ª pasada, `scratchpad/spot_asiento.py`): se abrieron 7
  episodios crudos del zip —4 de los 59 que eligen segundo y 3 de los que eligen primero— y se
  leyó a ojo el select, la acción cruda, el option al que apunta y el `firstPlayer` posterior.
  Los 7 cuadran: acción `[1]` → `{'type': 2}` → `firstPlayer` = el OTRO jugador. El desfase +1
  y el mapeo tipo→asiento no son una suposición del extractor.

### Qué hacemos nosotros

`heuristico.py` `_politica`, rama `t == 9` (línea 473): devuelve el índice del option con
`type == 1`, o sea **PRIMERO fijo**. Coincide con el campo el 99,4% de las veces. Esto explica
el 99,7% de acuerdo que el diagnóstico reportaba en `(9,41)` sin saber hacia qué lado caía:
**caía a nuestro favor**.

**Veredicto: no hay nada que cambiar.** La decisión estaba bien tomada por defecto.

### Coste medido de elegir lo contrario

Variante idéntica al v2 salvo que en el select type 9 devuelve el option `type 2`
(`scratchpad/wrappers/segundo_mega_lucario.py`), contra `heuristico.py`, `mega-lucario` en los
dos lados:

| variante | n | tasa vs v2 | IC95 | ilegales |
|---|---:|---:|---|---:|
| elegir SEGUNDO — corrida 1 | 1.000 | 0,403 | [0,373, 0,434] | 0 |
| elegir SEGUNDO — corrida 2 | 1.000 | 0,421 | [0,391, 0,452] | 0 |
| elegir SEGUNDO — corrida 3 (2ª pasada) | 1.000 | 0,408 | [0,378, 0,439] | 0 |
| **POOL** | **3.000** | **0,411** | **[0,393, 0,428]** | **0** |

Cambiar la elección cuesta **−8,9 puntos de winrate** en 3.000 partidas, con el IC entero por
debajo de 0,5 y tres corridas independientes que coinciden en signo y magnitud. Es además la
corrida que **valida la sensibilidad de `arena.py`**: la báscula sí detecta un efecto de este
tamaño con n=1.000, así que los empates de la sección 4 son empates de verdad y no falta de
potencia.

#### El número honesto: condicionar al asiento en que sí se elige

Aquí hay una trampa de medición que conviene dejar escrita, porque afecta a **cualquier**
variante que solo cambie el comportamiento del jugador 0. El select `(9,41)` **lo recibe
siempre el jugador 0** (9.337/9.337, §1). `arena.py`/`duelo.py` intercambian asiento, así que
**en la mitad de las partidas nuestra variante es el jugador 1 y NUNCA llega a elegir**: ahí es
el v2, bit a bit. El 0,411 global está por tanto **diluido a la mitad por construcción**.

Separando las dos ramas (`as0` = la variante es jugador 0; `as1` = es jugador 1), y usando como
línea base el espejo v2–v2 con la misma baraja (3 corridas agrupadas, 600+1.500+1.000):

| rama | qué mide | victorias/n | tasa | IC95 |
|---|---|---:|---:|---|
| variante, jugador 0 | **elige SEGUNDO** (aquí sí decide) | 635/1.500 | **0,4233** | [0,3986, 0,4485] |
| espejo, jugador 0 | elige PRIMERO (el v2) | 878/1.550 | **0,5665** | [0,5416, 0,5909] |
| **diferencia** | **coste real de la decisión** | — | **−0,143** | **[−0,178, −0,108]**, z = −7,99 |
| variante, jugador 1 | *placebo*: nunca recibe el select | 597/1.500 | 0,3980 | [0,3735, 0,4230] |
| espejo, jugador 1 | *placebo*: el v2 en el mismo asiento | 649/1.550 | 0,4187 | [0,3944, 0,4434] |
| **diferencia** | **placebo (debe ser 0)** | — | −0,021 | [−0,056, +0,014], z = −1,16 |

Dos lecturas:

1. **La decisión cuesta 14,3 puntos, no 8,9.** Cuando de verdad la tomamos, elegir segundo baja
   el winrate de 0,566 a 0,423. El 8,9 global es ese 14,3 promediado con las partidas en las
   que la variante no podía hacer nada.
2. **El placebo sale limpio** (z = −1,16, IC cruzando el cero): la rama en la que la variante
   no interviene mide lo mismo que el v2. Eso confirma que el wrapper cambió **solo** la
   decisión que creíamos y nada más — sin este control, el −0,143 podría ser un efecto
   colateral del envoltorio y no de la elección.

El método vale para toda la nota: **cuando una palanca solo actúa en un asiento o en un
subconjunto de partidas, la tasa global de `arena.py` subestima su efecto**, y la rama inerte
es un placebo gratis que hay que mirar.

### Cuánto vale el asiento, y por baraja

En el campo real, el que va primero gana el **54,49%** (5.084/9.331 con resultado,
IC95 [0,5347, 0,5549]). En espejo puro dentro del campo (mismo arquetipo a los dos lados, que
aísla el asiento de la fuerza de la baraja) sale **0,528 [0,507, 0,549]** sobre n=2.109
(grimmsnarl 0,537 n=917 · alakazam 0,518 n=326 · dragapult 0,562 n=64 · resto 0,518 n=760).

Con nuestro piloto la ventaja es **mucho mayor** que en el campo, y depende fuerte de la baraja.
Espejo v2 contra v2 en `arena.py`, tasa del que va **primero**:

| baraja | n | gana el que va primero | IC95 |
|---|---:|---:|---|
| **mega-kangaskhan** | 800 | **0,680** | [0,647, 0,711] |
| **mega-lucario** (el envío que va en serio) | **3.100** | **0,574** | **[0,556, 0,591]** |
| hops-snorlax (el otro envío vivo) | 800 | 0,565 | [0,530, 0,599] |
| — campo real, espejo por arquetipo | 2.109 | 0,528 | [0,507, 0,549] |

(El 0,574 de `mega-lucario` agrupa las **tres** corridas de espejo v2–v2 con esa baraja
—600 + 1.500 + 1.000 partidas—. La nota daba antes 0,592 mirando solo la de n=1.500; con el
triple de muestra baja a 0,574 y el IC se estrecha. Sigue muy por encima del campo.)

Lectura: medido como ventaja sobre 0,5, el asiento pesa **entre 2 y 6 veces más para nuestro
piloto que para el campo** (+0,028 el campo; +0,065 hops-snorlax, +0,092 mega-lucario,
+0,180 mega-kangaskhan). Un
piloto que no sabe retirarse ni recuperar tempo depende mucho más de pegar primero. Y
`mega-kangaskhan` es un caso extremo (0,680): esa baraja se juega casi entera en el asiento.
Consecuencia práctica: **cualquier medida de barajas hecha sin intercambiar asiento está
sesgada hasta 18 puntos**; `arena.py` ya lo intercambia, y hay que seguir haciéndolo.

---

## 2. BANCA — qué hace el campo (dato directo)

`research/replays/banca_expertos.py` sobre la **misma muestra que el diagnóstico** (1.000
episodios, 500 de cada día, semilla 2026). Tres medidas. **Reejecutado el 2026-08-11**: sale
idéntico dígito a dígito (la muestra es determinista por semilla), así que las tres tablas están
firmadas por una corrida propia y no heredadas.

### A) Banca inicial `(1,2)` — cuántos básicos baja el experto

| cartas bajadas | n | % |
|---:|---:|---:|
| 0 | 217 | 24,1% |
| **1** | **559** | **62,1%** |
| 2 | 111 | 12,3% |
| 3 | 13 | 1,4% |

Media 0,91. **Nosotros bajamos siempre `maxCount` (2 casi siempre), y los 2 de más `_util`**
(daño bruto). Cuando entre las opciones había un ex, el experto **lo evita 93 veces y lo baja
52** (64% lo evita).

### B) `(0,0)`: cuando SE PUEDE bancar un básico, ¿quién lo hace?

La tabla equivalente a la de co-disponibilidad del diagnóstico, para la banca:

| banca actual | n | EXPERTO baja | NOSOTROS bajamos |
|---:|---:|---:|---:|
| 0 | 1.619 | 56,5% | **100,0%** |
| 1 | 3.080 | 43,6% | **100,0%** |
| 2 | 5.123 | 38,2% | **100,0%** |
| 3 | 7.319 | 31,4% | **100,0%** |
| 4 | 9.740 | 25,5% | **0,0%** (tope duro del v2) |
| **TOTAL** | **26.881** | **33,5%** | **63,8%** |

Elección ex/no-ex cuando había de los dos tipos disponibles:

| | elige no-ex | elige ex |
|---|---:|---:|
| experto | 461 (66,0%) | 237 |
| **nosotros** | 736 (46,6%) | **844** |

### C) Tamaño de la banca por turno (experto)

| turno | banca media (todos) | banca media (el que GANA) |
|---:|---:|---:|
| 1 | 1,73 | 1,79 |
| 3 | 3,06 | 3,21 |
| 5 | 3,65 | 3,83 |
| 7 | 3,72 | 3,95 |
| 9 | 3,71 | 3,98 |
| 12 | 3,61 | 3,85 |
| 20 | 3,51 | 3,48 |

### Lo que este dato dice — y lo que NO dice

Dice: bancamos **el doble de veces que el campo** cuando se puede (63,8% vs 33,5%), llenamos la
banca inicial al máximo cuando el campo baja una sola carta, y preferimos el ex cuando el campo
prefiere el no-ex.

**No dice «hay que tener menos banca».** El campo acaba con banca media **3,7** en el medio
juego y el **ganador la tiene más grande que la media** en todos los turnos del 1 al 17
(3,95 vs 3,72 en el turno 7); el signo solo se invierte a partir del turno 18, donde ya quedan
pocas partidas (n ≤ 525) y la banca la ha vaciado el intercambio de KOs. La diferencia con
nosotros no es el tamaño final: es que ellos
**no gastan las primeras acciones del turno vaciando la mano de básicos** — llegan al mismo
sitio más tarde y eligiendo mejor la pieza. Es la misma fuga de ORDEN que describe
`diagnostico-expertos.md` §2, vista desde la banca.

Esto ya invalida la lectura ingenua de la tarea («cada Pokémon de más es un objetivo gratis
para el gusteo, luego menos banca»). Y hay una razón mecánica además de la estadística: el
gusteo lo **elige el rival**, así que añadir un cuerpo barato a la banca no empeora nada (él
seguiría eligiendo el mejor objetivo que ya estaba). Lo único que empeora de verdad es añadir un
cuerpo que se convierte en **el mejor objetivo**: un ex desnudo, que son 2 premios. La hipótesis
medible no es de **cantidad**, es de **qué bajas**.

---

## 3. La palanca: `research/agentes/heuristico_banca.py`

Copia del v2 con una sola diferencia, tras cuatro globals de módulo que se leen en CADA
decisión (mismo patrón que `heuristico_v3.py`: se fijan por atributo o por entorno):

```python
BANCA_CUPO     = 4   # relleno «no-ex» hasta N en banca         (V4_BANCA_CUPO)
BANCA_EX_MIN   = 2   # un ex solo baja mientras banca < N       (V4_BANCA_EX_MIN)
BANCA_CRITERIO = 1   # 0 = v2 exacto                            (V4_BANCA_CRITERIO)
BANCA_INICIAL  = 2   # 0 = v2; N = reordena y baja ≤N en (1,2)  (V4_BANCA_INICIAL)
```

Con `CUPO=4, CRITERIO=0, INICIAL=0` la política es **idéntica al v2** (control de no-regresión,
medido más abajo).

**Criterio** (`_rango_banca`, menor = mejor):

| rango | qué es | cuándo es elegible |
|---:|---|---|
| 0 | **pieza del plan**: tengo en mano una carta cuyo `evolvesFrom` es su nombre | siempre |
| 2 | relleno barato: no-ex (1 premio si lo noquean) | banca < `BANCA_CUPO` |
| 3 | **frágil y valioso**: `ex`/`megaEx` desnudo = 2 premios gratis al gusteo | banca < `BANCA_EX_MIN` |

Entre los elegibles se baja el de menor rango y, a igualdad, el de más `_util`. **Nunca nos
quedamos sin relevo**: con la banca vacía el rango 3 también entra (`0 < BANCA_EX_MIN`), así que
mientras haya un básico bancable se baja alguno. Esto obliga a `BANCA_EX_MIN >= 1`: con 0 la
garantía se rompe y una mano de solo-ex dejaría la mesa vacía (derrota por `reason 3`).
El mismo orden se aplica al select de banca inicial `(1,2)` cuando `BANCA_INICIAL > 0`, con
tope de `BANCA_INICIAL` cartas.

Por qué esto importa en `mega-lucario` (la baraja del envío que va en serio): sus 8 básicos son
4× **Riolu** (80 hp, evoluciona a Mega Lucario ex — 340 hp) y 4× **Regirock ex** (230 hp,
140 de daño por **4** energías, 2 premios). `_util` = 3,0 + daño/1000 + hp/10000 le da 3,163 a
Regirock ex y 3,038 a Riolu: **el v2 baja siempre el ex antes que la pieza del plan**, en la
banca inicial y en cada turno.

---

## 4. Medición contra nuestro propio piloto (que NO gustea)

Todo `mega-lucario` en los dos lados, `--procs 3`, contra `heuristico.py` (v2).
`as0`/`as1` = tasa de la variante según asiento. **Ilegales = 0 en las dos columnas de todas
las corridas** de la nota entera (0 de **28.600** partidas contando la 2ª pasada, todas con
`status == DONE` en los dos jugadores; el mínimo exigido era 400 por variante y ninguna bajó
de 1.000).

### Controles

| control | n | tasa vs v2 | IC95 |
|---|---:|---:|---|
| espejo v2 vs v2 (ruido puro) | 1.500 | 0,492 | [0,467, 0,517] |
| `ctrl_v2` — palancas en modo v2 (no-regresión) | 1.500 | 0,508 | [0,483, 0,533] |

`ctrl_v2` es literalmente el mismo código de decisión que el v2 y mide 0,508: la copia no es una
regresión y el módulo `heuristico_banca.py` es un drop-in seguro.

### Variantes (rejilla de descubrimiento a n=600, del primer barrido)

| variante | `CUPO` | `EX_MIN` | `CRIT` | `INI` | n | tasa vs v2 | IC95 |
|---|---:|---:|---:|---:|---:|---:|---|
| cupo2 | 2 | 2 | 0 | 0 | 600 | **0,442** | **[0,402, 0,482]** ← peor |
| cupo3 | 3 | 2 | 0 | 0 | 600 | **0,458** | **[0,419, 0,498]** ← peor |
| crit | 4 | 2 | 1 | 0 | 600 | 0,468 | [0,429, 0,508] |
| crit_ini2 | 4 | 2 | 1 | 2 | 600 | 0,462 | [0,422, 0,502] |
| crit_ini1 | 4 | 2 | 1 | 1 | 600 | 0,480 | [0,440, 0,520] |
| crit_ex1 | 4 | 1 | 1 | 2 | 600 | 0,518 | [0,478, 0,558] |
| crit_c3 | 3 | 2 | 1 | 2 | 600 | 0,538 | [0,498, 0,578] |

### Confirmaciones a n grande (lo que decide)

| variante | `CUPO` | `EX_MIN` | `CRIT` | `INI` | n | tasa vs v2 | IC95 | veredicto |
|---|---:|---:|---:|---:|---:|---:|---|---|
| **`crit`** (la del enunciado) | 4 | 2 | 1 | 0 | 1.500 | 0,490 | [0,465, 0,515] | empate |
| **`crit`** pool con el n=600 | — | — | — | — | **2.100** | **0,484** | **[0,463, 0,505]** | **empate/peor** |
| `crit_ex1` | 4 | 1 | 1 | 2 | 1.500 | 0,480 | [0,455, 0,505] | empate/peor |
| `crit_c3` | 3 | 2 | 1 | 2 | 1.500 | 0,493 | [0,468, 0,519] | empate |
| **`orden`** (orden puro) | 4 | 4 | 1 | 0 | 1.500 | 0,518 | [0,493, 0,543] | zona gris |
| **`orden`** confirmación | 4 | 4 | 1 | 0 | 3.000 | 0,503 | [0,485, 0,521] | empate |
| **`orden`** confirmación 2 (2ª pasada) | 4 | 4 | 1 | 0 | 1.500 | 0,509 | [0,484, 0,535] | empate |
| **`orden`** pool | — | — | — | — | **6.000** | **0,509** | **[0,496, 0,521]** | **empate** |
| `orden_ini2` | 4 | 4 | 1 | 2 | 1.500 | 0,479 | [0,454, 0,504] | empate/peor |

Lecturas:

- **`crit` es la traducción literal del enunciado** (bajar lo del plan, no apilar el ex frágil,
  nunca quedarse sin relevo) y era el único hueco de medición que quedaba: solo tenía la
  corrida de descubrimiento a n=600 (0,468 [0,429, 0,508], **zona gris**, IC cruzando 0,5). La
  2ª pasada lo confirmó a n=1.500: **0,490 [0,465, 0,515]**, y el pool de 2.100 partidas da
  **0,484 [0,463, 0,505]**. **No pasa el gate.** Sus contadores dicen que la palanca sí estaba
  actuando —`banca_baja` 3.693 (963 por «pieza del plan», 879 por relevo con la banca vacía) y
  `banca_declina` 7.129, de las cuales 7.045 por «solo quedaban ex»— así que es un negativo
  medido de una política que se ejecutó, no una palanca muerta.
- **Recortar el cupo de banca es malo y es significativo**: `cupo2` 0,442 y `cupo3` 0,458, los
  dos con el IC entero por debajo de 0,5. Coincide exactamente con §2-C (el ganador tiene MÁS
  banca) y con la mecánica del gusteo (el rival elige: un cuerpo barato de más no le regala
  nada). **La lectura «menos banca por el gusteo» queda descartada con dato en las dos
  direcciones.**
- **La variante `orden` era la única bien motivada que faltaba en la rejilla**: `EX_MIN = CUPO`
  deja la CANTIDAD exactamente como el v2 (bancar siempre que se pueda, hasta 4) y solo cambia
  **cuál** se baja (pieza del plan > no-ex > ex). Es la traducción literal de lo que hace el
  campo. Midió 0,518 con n=1.500 y **0,503 [0,485, 0,521] al confirmarla con n=3.000**: el 0,518
  era el máximo de una rejilla, no una señal. Pool 4.500 partidas: **0,508 [0,494, 0,523]**.
  **No pasa el gate.** La 2ª pasada añadió una tercera muestra independiente (n=1.500,
  **0,509**) y el pool sube a **6.000 partidas: 0,509 [0,496, 0,521]**. El límite inferior sigue
  por debajo de 0,5 con 6.000 partidas; si hay algo ahí, es más pequeño que lo que esta báscula
  puede resolver, y desde luego no es el 0,518 del descubrimiento.
- Reordenar además la **banca inicial** empeora (`orden` 0,518 → `orden_ini2` 0,479 con la misma
  n; diferencia −0,039, z ≈ 2,1). Coherente con que en `(1,2)` ya acordamos el 69,8% con el
  campo (diagnóstico): ahí no había fuga que arreglar.
- `crit_ex1` (el ex prácticamente desterrado de la banca) es el más agresivo y el que peor mide
  contra el v2: 0,480. Sus contadores lo explican — `banca_declina` 11.757 veces y 11.745 de
  ellas por «solo quedaban ex»: renuncia a un cuerpo de 230 hp casi siempre.

---

## 5. Por qué el espejo v2–v2 es una báscula CIEGA para el anti-gusteo

Aquí está el hallazgo metodológico de la tarea. La hipótesis «no dejes un ex desnudo en banca
porque el rival lo gustea» solo puede pagar **si el rival gustea**. Y nuestro v2 **no puede
jugar Boss's Orders**. Comprobado en el código, no solo citado: el paso 6 de `_fase_principal`
es la única rama que devuelve un supporter, y su guarda es

```python
if cid is not None and clase(cid) == 3:
    txt = textos.get(cid, "")
    if "draw" in txt or "search" in txt:
```

El texto de Boss's Orders es *«Switch in 1 of your opponent's Benched Pokémon to the Active
Spot»*: no contiene `draw` ni `search`, así que ninguna rama la puede devolver nunca. Es una de
las cartas que el diagnóstico ya listaba como inalcanzables, con 1.170 jugadas del campo
(`diagnostico-expertos.md` §3).

Es decir: **las 9 corridas de la sección 4 miden el COSTE de la política anti-gusteo con el
BENEFICIO puesto a cero por construcción.** No es que la hipótesis esté refutada: es que ese
banco de pruebas no la puede ver.

Banco de pruebas correcto: un rival que sí gustea. `heuristico_v3.py` ya tiene la palanca
`GUSTING` (apagada por defecto); encendida y con `RETIRADA=False`, con `mega-lucario`
(2× Boss's Orders en lista) es un rival que castiga la banca de verdad
(`scratchpad/wrappers/gusteador_mega_lucario.py`).

Primer dato, que además reabre un tema cerrado: **el gusteador le gana al v2**.

| enfrentamiento | n | tasa de A | IC95 |
|---|---:|---:|---|
| A = v2, B = gusteador (1.500 + 3.000, pool) | 4.500 | 0,473 | [0,458, 0,488] |
| ⇒ tasa del **gusteador** | 4.500 | **0,527** | **[0,512, 0,542]** |

`agente-heuristico-v3.md` había medido la palanca de gusting en 0,495 (empate) y por eso está
apagada; con `mega-lucario` mide **0,527 [0,512, 0,542]** en 4.500 partidas, con el IC entero
por encima de 0,5. **Eso es un ticket para el tema de v3, no para éste** (la palanca de gusting
es suya), pero conviene que conste: *la palanca puede valer distinto según la baraja, y se apagó
midiéndola con otra.* Es, de hecho, el único IC que se ha salido de 0,5 hoy.

### La política de banca anti-gusteo, medida contra quien sí gustea

Mismo rival gusteador en los dos casos, misma n, misma baraja:

| A (piloto) | n | tasa vs gusteador | IC95 | ilegales |
|---|---:|---:|---|---:|
| v2 (banca mecánica) — descubrimiento | 1.500 | 0,463 | [0,438, 0,488] | 0 |
| `crit_ex1` (banca anti-gusteo) — descubrimiento | 1.500 | 0,501 | [0,476, 0,527] | 0 |
| diferencia (descubrimiento) | — | +0,039 | [+0,003, +0,074] (z = 2,12) | — |
| v2 — **confirmación** | 3.000 | 0,478 | [0,460, 0,496] | 0 |
| `crit_ex1` — **confirmación** | 3.000 | 0,464 | [0,446, 0,482] | 0 |
| diferencia (confirmación) | — | −0,014 | [−0,039, +0,011] (z = −1,09) | — |
| **v2 — pool** | **4.500** | **0,473** | **[0,458, 0,488]** | 0 |
| **`crit_ex1` — pool** | **4.500** | **0,476** | **[0,462, 0,491]** | 0 |
| **diferencia pool** | — | **+0,004** | **[−0,017, +0,024]** (z = 0,34) | — |

El +0,039 del primer par (z = 2,12, p ≈ 0,03) **no sobrevivió a la confirmación**: con el doble
de n la diferencia cambia de signo, y en el pool de 4.500 partidas por lado queda en
**+0,004 [−0,017, +0,024]**, un cero con un IC de ±2 puntos.

**Veredicto: la política anti-gusteo tampoco paga contra un rival que gustea.** Es un negativo
medido, no un «no lo sabemos»: el banco de pruebas ya era el correcto y la respuesta es que no.
Y es el sexto precedente de mejora «obvia» que mide empate — el primero que llegó a tener un
z > 2 antes de morir, que es justo por lo que existe la regla de confirmar en muestra nueva.

---

## 6. Veredictos

1. **Asiento: cerrado, sin cambio.** Los expertos eligen PRIMERO en 9.278/9.337 (99,37%) —un
   **censo**, no una muestra— y nosotros también. Elegir lo contrario cuesta −8,9 puntos
   globales [0,393–0,428] en 3.000 partidas y, condicionando al asiento en que de verdad
   elegimos, **−14,3 puntos** [−0,178, −0,108], z = −8,0, con el placebo limpio. La ventaja de
   ir primero con nuestro piloto es 0,574 en `mega-lucario` (n=3.100) y 0,680 en
   `mega-kangaskhan`, muy por encima del 0,528 del campo en espejo.
2. **Banca, cantidad: descartado con dato.** Bajar el cupo mide peor de forma significativa
   (0,442 y 0,458) y el campo confirma que el ganador tiene la banca MÁS grande. No tocar.
3. **Banca, orden (qué bajas): empate.** `orden` mide 0,509 [0,496, 0,521] en **6.000**
   partidas contra el v2, y `crit` —la política literal del enunciado— 0,484 [0,463, 0,505] en
   2.100. Ninguna pasa el gate. **No entra.**
4. **Banca, anti-gusteo: negativo medido, ya no con la báscula ciega.** Se construyó el rival
   que sí gustea, se midió el descubrimiento (+0,039, z = 2,12) y se confirmó en muestra nueva:
   el pool de 4.500 partidas por lado da **+0,004 [−0,017, +0,024]**. **No entra, y el tema se
   puede cerrar**: no es que no supiéramos medirlo, es que no está ahí.
5. **Subproducto para otro tema**: la palanca `GUSTING` de v3, apagada por medir 0,495, mide
   **0,527 [0,512, 0,542]** con `mega-lucario` (n=4.500). Es el único IC que se separa de 0,5 en
   toda la sesión. Merece su propia comprobación en el tema de v3 — con `mega-lucario`, que es la
   baraja que va en serio.

### Coste total y disciplina de medición

**28.600 partidas** medidas (23.600 de la primera tanda + 5.000 de la pasada de verificación),
**0 ilegales** en los dos lados de todas las corridas (el mínimo exigido era 400 por variante;
ninguna bajó de 1.000). Las cuatro palancas del módulo de banca se
quedan **apagadas en su configuración v2** y `heuristico.py` sigue intacto.

La lección de método de la sesión: de las tres candidatas que llegaron a superar 0,5 en la
rejilla de descubrimiento (`crit_c3` 0,538, `crit_ex1` 0,518, `orden` 0,518) y del +0,039 con
z = 2,12 del anti-gusteo, **ninguna sobrevivió a la muestra de confirmación**. Con ±0,04 de
anchura y una decena de variantes, el máximo de la rejilla es ruido casi por construcción: la
regla de confirmar el ganador en muestra nueva y a n ≥ 3.000 es lo único que separó las cuatro
señales falsas del cero real.

## 7. La 2ª pasada de verificación (2026-08-11, tarde)

Qué se comprobó sin dar nada por bueno, y qué cambió.

**Integridad del código** (nada que arreglar):

- `research/agentes/heuristico.py` intacto (mtime 2026-08-10 09:48, anterior a toda esta
  tarea). El piloto de los dos envíos vivos no se ha tocado.
- `heuristico_banca.py` con las cuatro palancas en modo v2 y el `assert BANCA_EX_MIN >= 1` en su
  sitio. El `diff` contra el v2 solo toca el paso 1 de `_fase_principal` y el select `(1,2)`.
- La rama `t == 9` del v2 (línea 473) devuelve el option `type 1`: **elegimos PRIMERO**,
  confirmado en el código y no solo en la nota.

**Dato de campo** (reproducido, no heredado):

- Recuento propio sobre `data/replays/asiento.json`: 9.278 / 59 / 0 sin dato → **99,37%**,
  dígito a dígito. Semántica coherente en 9.337/9.337.
- El crudo resultó ser un **censo** (4.669 + 4.668 = 9.337), lo que hace la muestra irrefutable
  por construcción: no hay semilla que pueda cambiarla.
- Spot-check a mano de 7 episodios crudos del zip, 4 de ellos de los que eligen segundo.

**Medición nueva** (5.000 partidas, `--procs 3`, 0 ilegales):

| corrida | por qué | resultado |
|---|---|---|
| `crit` n=1.500 | cerrar el único hueco: la política del enunciado solo tenía n=600 en zona gris | 0,490 [0,465, 0,515] → pool 2.100 = **0,484** |
| `orden` n=1.500 | tercera muestra independiente | 0,509 → pool 6.000 = **0,509 [0,496, 0,521]** |
| `segundo` n=1.000 | tercera muestra del coste del asiento | 0,408 → pool 3.000 = **0,411** |
| espejo v2 n=1.000 | línea base por asiento para el análisis condicionado | 0,484 (as0 0,534 / as1 0,434) |

**Qué cambió respecto a la primera versión de la nota**: (a) `crit` pasa de «medida a n=600 en
zona gris» a **negativo confirmado**; (b) el coste del asiento pasa de −7,9 a −8,9 puntos
globales y aparece el número honesto, **−14,3 condicionado**, con placebo; (c) la ventaja de ir
primero en `mega-lucario` baja de 0,592 (n=1.500) a **0,574** (n=3.100). **Ningún veredicto se
invierte**: lo que era empate sigue siendo empate y lo que estaba cerrado sigue cerrado.

## 8. Ficheros

- `research/agentes/heuristico_banca.py` — la palanca. **Las cuatro vienen apagadas** (=v2
  exacto, no-regresión medida en 1.500 partidas con 0 ilegales) porque ninguna configuración
  pasó el gate. Lleva un `assert BANCA_EX_MIN >= 1` que protege la garantía de relevo.
- `research/duelo.py` — `arena.py` + contador de partidas ilegales (`status != DONE`) +
  agregación de `USOS`/`FALLBACKS`, todo en la misma pasada. Mismo protocolo de asiento e IC.
- `research/agentes/variantes/gen_wrappers.py` — regenera **las once** variantes de esta nota
  (`v2_*`, `ctrl_v2_*`, `orden*`, `crit*`, `gusteador_*`, `segundo_*`) con las palancas fijadas
  por atributo de módulo y la baraja incrustada. Reproducir la nota = ejecutarlo y lanzar
  `research/duelo.py` con las n de las tablas. (La 2ª pasada añadió
  `crit_mega_lucario`, que faltaba: era la única variante de la rejilla sin módulo propio.)
- `research/replays/asiento.py` → `data/replays/asiento.json` (9.337 episodios).
- `research/replays/banca_expertos.py` — las tres tablas de campo de la sección 2.
- `data/banca/*.json` — el crudo de las 18 corridas (victorias, IC, tasa por asiento, ilegales,
  estados finales, contadores de uso). Las cuatro de la 2ª pasada son `crit_n1500.json`,
  `orden_n1500_c.json`, `segundo_n1000_b.json` y `espejo_n1000_b.json`.
- `research/agrega_banca.py` — agrupa las corridas (muestras independientes: el RNG del motor
  no es sembrable) y hace el **análisis condicionado del asiento con su placebo**. Reproduce
  todos los pools de §1 y §4 leyendo `data/banca/*.json`.
- `research/replays/verifica_asiento.py` — recuento propio sobre `data/replays/asiento.json`
  (elección, semántica contra `firstPlayer`, winrate por asiento, espejos). Es la comprobación
  de que el dato de campo no depende del resumen que imprimió el extractor.
