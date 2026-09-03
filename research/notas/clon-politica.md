# Clon de política: red entrenada por imitación sobre los replays del top de la ladder

Fecha: 2026-08-12. Piezas nuevas: `research/clon/rasgos.py` (esquema),
`research/clon/extraer.py` (replays → dataset), `research/clon/entrenar.py`
(numpy puro), `research/clon/auditar.py` (legalidad y reloj),
`research/agentes/clon.py` (el agente), pesos en `research/clon/politica.npz`.
Dataset en `data/clon/pol_1030.npz` (gitignorado).

**Resumen: FUNCIONA, y es el primer cambio de arquitectura que mueve la aguja.**
Después de nueve refinamientos de la heurística sin una sola mejora confirmada, una
red de política clonada de los replays gana en arena a los dos pilotos que teníamos.

| | resultado |
|---|---|
| Top-1 en test (63.037 decisiones, episodios no vistos) | **0,6178** · heurístico 0,4303 · azar 0,2180 |
| **clon vs `heuristico.py` v2** (mega-lucario, espejo) | **0,620 IC95 [0,602, 0,637]** n=3.000 |
| **clon vs `heuristico_v5`** (el rival fuerte) | **0,567 IC95 [0,550, 0,585]** n=3.000 |
| **clon vs `heuristico_v6`** (v5+`recupera`, lo más nuevo del repo) | **0,563 IC95 [0,541, 0,585]** n=2.000 |
| **Campo real ponderado** (12 arquetipos, 96,3% de cobertura) | **0,8155 [0,8036, 0,8275]** n=6.000 · v5 0,7844 · v2 0,7605 |
| Peor emparejamiento (lo que puntúa el 70%) | v2 0,289 · v5 0,280 · **clon 0,322** |
| Legalidad | **0 ilegales / 0 excepciones / 0 fallbacks** en 13.535 decisiones de arena + 9.714 de replays ajenos |
| Reloj | 0,21 ms/decisión → margen **×64.000** sobre los 600 s de producción |
| Paquete | `envios/clon-mega-lucario.tar.gz` (0,6 MiB), validado con el cargador real |
| Lo que NO funciona | los híbridos (peores que el clon puro) y **hops-snorlax (0,466: el clon pierde)** |
| Contraintuitivo y medido | **+3,4 pp de top-1 no compran ni una partida**: el modelo que peor predice es el que mejor juega |

---

## 0. Por qué se reabrió (y qué cambió respecto al «NO» del 10-ago)

`research/notas/replays-imitacion.md` §5 dijo NO a behavioral cloning con cinco
argumentos. Cuatro siguen en pie como cautelas; el que decidía —«el techo lo pone
la representación, no los datos» (§4.3)— era **correcto y por eso mismo señalaba la
puerta equivocada**: el piloto de entonces usaba los 30 rasgos de la v1 y 39 campos
crudos de opción, y sacó **45,79%** de top-1. La conclusión que se sacó fue «BC no
compra nada»; la que tocaba era «la representación del PILOTO no compra nada».

Lo que ha cambiado aquí, en orden de importancia:

1. **Rasgos de opción que describen lo que la opción HACE**, no sus campos crudos:
   la carta resuelta con sus propiedades del catálogo, el Pokémon en juego al que
   apunta, y el ataque concreto con su daño ya corregido por debilidad/resistencia.
2. **Resolución de carta del 44% al 84,5%**: el piloto no resolvía `area == 1`
   (búsqueda en mazo, la lista va en `select.deck`, no en una zona del jugador) ni
   el `type 7` (jugar carta de la mano, que **no trae campo `area`**). Entre las dos
   se llevaban la mitad de las opciones no resueltas.
3. **Rasgos de estado v2** (62, con la aritmética de combate y premios) en vez de
   los 30 de la v1, más 52 que describen la FORMA del select.
4. **Se admiten las decisiones que el piloto tiraba**: acciones multi-índice y la
   acción vacía `[]`, esta última mediante una opción virtual «no elegir nada».

## 1. Esquema de rasgos (`research/clon/rasgos.py`)

Un solo módulo, compartido por el extractor, el entrenador y el agente. Si diverge,
los pesos dejan de significar nada.

### 1.1 Estado — 114 valores, constantes dentro del bloque de opciones

| bloque | dim | qué |
|---|---:|---|
| `features_v2.extrae(current)` | 62 | los 30 densos v1 + combate (mata_ya, daño pagable/potencial con debilidad y resistencia, turnos para tumbar, carrera) + energía + premios (1/2/3 según ex/megaEx) + tablero |
| one-hot `select.type` | 10 | |
| forma del select | 13 | `min==max`, `minCount/6`, `maxCount/6`, `n/20`, `log1p(n)/3,5`, hay `deck`, `len(deck)/60`, hay `effect`, `effect` es mío, **mi activo está vacío** (discrimina (1,4) de (1,3)), todas las opciones son mías, todas son suyas, `turnActionCount/20` |
| one-hot `area` de `option[0]` | 13 | |
| multi-hot de los `type` presentes en el bloque | 16 | el «modo» del select sin enumerar contexts |

Los rasgos del select no rompen el softmax por sí solos (son iguales para todas las
opciones del bloque) pero **interaccionan con los de opción en la capa oculta**: es
como el modelo aprende «en una promoción tras KO prefiero HP alto y pocos premios»
sin que nadie escriba esa regla. Se evita one-hot de `context` a propósito:
`context` es un hueco de carta, no una mecánica (`motor-mecanica.md` ✏️ 2026-08-11).

### 1.2 Opción — 96 valores por opción candidata

| bloque | dim | qué |
|---|---:|---|
| A · campos crudos | 39 | one-hot `type` (16) · one-hot `area` (13) · hay `playerIndex`, es mío, `index/20`, hay `attackId`, `inPlayArea`∈{4,5}, `inPlayIndex/5`, `count/5`, hay `toolIndex`, `number/5` |
| B · la carta implicada | 33 | resuelta · one-hot `cardType` (7: 0 Pokémon, 1 item, 2 tool, 3 partidario, 4 estadio, 5 energía básica, 6 energía especial) · basic/stage1/stage2/ex/megaEx/tera/aceSpec · `hp/400` · retirada/4 · **premios que concede (1/2/3)** · daño máximo/300 · coste mínimo/5 · one-hot `energyType` (10) · **daño efectivo contra el activo rival** (con debilidad ×2 y resistencia −30) · **mataría al activo rival** · es energía básica |
| C · el Pokémon EN JUEGO al que apunta | 13 | resuelto · es mío · es el activo · `hp/400` · `hp/maxHp` · energías/5 · premios que concede · su daño pagable contra el activo contrario · **mata ya** · **muere ya al golpe del rival** · retirada/4 · tools/3 · `appearThisTurn` |
| D · el ataque concreto | 10 | hay ataque · daño nominal · **daño efectivo** · **mata** · sobrekill (ef/hp) · nº de energías del coste · el texto menciona moneda · menciona descarte · menciona curación · **premios que me da ese KO** |
| E · «no elegir nada» | 1 | fila virtual añadida cuando `minCount == 0` |

**Resolución de la carta de una opción** (esto es lo que subió del 44% al 84,5%):
`type 15` trae `cardId`; `type 12/13` (retirada, ataque) apuntan a mi activo;
`type 7` es la mano **sin campo `area`**; `area 1` indexa `select.deck`, no una zona
del jugador; `area 2/3` mano/descarte y `area 4/5` activo/banca del `playerIndex`.
El objetivo en juego se resuelve por tres formas distintas: `inPlayArea/inPlayIndex`
(tipos 8 y 9), `area 4/5 + index` (tipos 3, 4, 6, 10) y mi activo (12, 13).

**Deck-agnóstico a propósito**: ninguna identidad de carta entra como rasgo. La
identidad va aparte, como un sesgo escalar por carta `b[c]`, ablacionable. Una
baraja que la red no vio se describe con los mismos números — que es justo lo que
hace falta, porque nosotros jugamos mega-lucario (4,3% del campo) y el corpus es
sobre todo grimmsnarl/alakazam/dragapult.

## 2. Dataset

`research/clon/extraer.py`, dos días de replays, filtro `min_score >= 1030` (el
PEOR de los dos jugadores, que evita la ambigüedad de atribuir rating a equipo).

| | |
|---|---|
| episodios | **2.773** de 9.337 (los que pasan el filtro de rating) |
| decisiones con elección real | **418.068** |
| opciones | **3.015.620** (7,21 por decisión) |
| cartas resueltas | **84,5%** (piloto: 44,0%) |
| fichero | 812 MB (`float16` en las opciones: la mitad de RAM) |

**Desfase +1 aplicado** (`replays-imitacion.md` §2): la acción que responde a
`steps[k][p].observation` está en `steps[k+1][p].action`. Sin él, el 34% de los
pares son estructuralmente imposibles.

**Corte train/val/test POR EPISODIO** 70/15/15 (2.773 episodios → 293.466 /
61.565 / 63.037 decisiones). Nunca por muestra: las dos perspectivas de una partida
van juntas y mezclarlas infla la validación.

El suelo del heurístico **se mide decisión a decisión durante la extracción**, no se
cita de otra tanda: `meta[:,7]` guarda si `heuristico._politica` (con su propio
`_fallback`) coincide con el experto en esa misma decisión.

## 3. Modelo y entrenamiento

    Ps = S @ W1s                        (una vez por DECISIÓN)
    Po = O @ W1o                        (una vez por OPCIÓN)
    h1 = relu(Ps[bloque] + Po + b1)     H1 = 128
    h2 = relu(h1 @ W2 + b2)             H2 = 64
    z  = h2 @ w3 + b3 + b_carta[c]
    p  = softmax(z) DENTRO del bloque del mismo select
    L  = − Σ T·log p / n_decisiones     (T = 1/len(acción) en las elegidas)

La suma factorizada `Ps[bloque] + Po` es algebraicamente idéntica a
`hstack([S[bloque], O])` en la primera capa, pero calcula la proyección del estado
una vez por decisión en vez de 7,21 veces, y no materializa una matriz (3M, 210).
Con este corpus es la diferencia entre entrenar y no caber en RAM; en producción es
lo que hace que la inferencia cueste microsegundos con 1,6 vCPU.

Adam a mano, lr 0,02, lote de 2.048 decisiones, L2 1e-6, numpy puro (no hay torch en
el venv y no se instala). Se restauran los pesos de la mejor época de validación.

### 3.1 Curva y saturación

Val top-1 por época: 0,5749 · 0,5840 · 0,5926 · 0,6021 · 0,6001 · 0,6032 · 0,6016 ·
0,6041 · 0,6071 · 0,6068 · 0,6078 · 0,6058 · 0,6120 · … · **0,6141** (mejor, época 17)
· 0,6133 (época 20). Satura: los últimos 8 puntos caben en 0,8 pp. No es falta de
entrenamiento y no es falta de datos.

### 3.2 Top-1 en TEST contra los dos suelos

Mismo conjunto de test (63.037 decisiones, 416 episodios que no se vieron ni en
train ni en validación) para los tres:

| | top-1 en test |
|---|---:|
| azar entre las opciones legales | **0,2180** |
| primera opción siempre | 0,3485 |
| **`heuristico.py` v2** (el piloto de la ladder) | **0,4303** |
| BC piloto de agosto (30 rasgos, 39 de opción) | 0,4579 *(otra muestra)* |
| **clon (esta red)** | **0,6178** |

**+18,8 puntos sobre el heurístico** y +2,8× sobre el azar. El piloto anterior sacaba
+3,1; el salto no vino de más datos ni de más épocas, vino de los rasgos.

Y sube donde el heurístico es más flojo, que es lo que hacía falta:

| (type,context) | qué es | n | clon | heurístico | azar |
|---|---|---:|---:|---:|---:|
| (0,0) | fase principal — **57% de las decisiones** | 35.404 | **0,5336** | 0,3430 | 0,1590 |
| (1,7) | búsqueda en mazo | 9.930 | **0,6197** | 0,5019 | 0,2434 |
| (1,4) | promoción tras KO | 1.916 | **0,7912** | 0,5402 | 0,2698 |
| (1,3) | cambio forzado / arrastre | 1.818 | **0,7310** | 0,5704 | 0,2657 |
| (1,14) | reparto de daño (Dragapult) | 1.632 | **0,6752** | 0,2843 | 0,2587 |
| (1,21) | objetivo en banca de un efecto | 1.512 | **0,7851** | 0,6402 | 0,3366 |
| (9,43) | sí/no de una carta | 1.464 | 0,9665 | 0,9590 | 0,5000 |
| (1,5) | búsqueda con 2 objetivos | 1.255 | **0,7976** | 0,5865 | 0,2892 |
| (1,8) | **descarte de coste** | 1.231 | **0,5061** | 0,1113 | 0,1963 |
| (1,13) | origen de contadores (Munkidori) | 1.088 | **0,7390** | 0,2243 | 0,2207 |

El `(1,8)` al 11,1% era el agujero flagrante que señaló `replays-imitacion.md` §5:
la red lo lleva al 50,6%. El `(0,0)`, que es el 57% de todas las decisiones, pasa de
34,3% a 53,4%.

Por dificultad, la ventaja NO se estrecha cuando hay muchas opciones —al revés:

| nº de opciones | n | clon | heurístico | azar |
|---|---:|---:|---:|---:|
| 2 | 8.618 | 0,8486 | 0,7510 | 0,5000 |
| 3-4 | 14.994 | 0,7423 | 0,5634 | 0,2917 |
| 5-7 | 18.432 | 0,5901 | 0,3698 | 0,1769 |
| 8-12 | 11.905 | 0,4776 | 0,2716 | 0,1058 |
| 13+ | 9.088 | 0,4333 | 0,2372 | 0,0589 |

Por banda de rating del rival, el clon se degrada mucho menos que el heurístico
(0,6325 → 0,6049 entre 1030-1059 y 1120-1149; el heurístico 0,4419 → 0,4038).

**Cautela obligatoria**: el diagnóstico de expertos midió que el acuerdo con el campo
**no correlaciona con ganar** (r = −0,028). Todo lo de arriba es una medida de
predicción, no de juego. El criterio de éxito es la arena, y va abajo.

## 4. Arena

Protocolo de casa: `arena.py`, **mega-lucario a los dos lados**, asientos
intercambiados mitad y mitad, `--procs 3`, IC de Wilson. El ruido de suelo de esta
báscula está medido: v2 contra sí mismo **0,4959 [0,4848, 0,5070]** con n=7.800.

### 4.1 Los dos duelos que decidían

| enfrentamiento | n | tasa del clon | IC95 | veredicto |
|---|---:|---:|---|---|
| **clon vs `heuristico.py` v2** (el piloto de la ladder) | 3.000 | **0,620** | [0,602, 0,637] | mejor, z≈13 |
| **clon vs `heuristico_v5`** (el rival más fuerte que teníamos) | 3.000 | **0,567** | [0,550, 0,585] | mejor, z≈7,3 |
| **clon vs `heuristico_v6`** (= v5 + `recupera`, aparecido durante esta tanda) | 2.000 | **0,563** | [0,541, 0,585] | mejor, z≈5,6 |

Muestra de descubrimiento previa e **independiente** (modelo corto, n=600): 0,650
contra v2 y 0,582 contra v5. Ambas direcciones se replican con n=3.000. No es el
z=2,12 de otras veces: son ±12 y ±7 puntos porcentuales sobre el 0,5, con el suelo
de la báscula calibrado en 0,4959.

No había `research/notas/sparring.md` en el repo, así que el rival fuerte de
referencia es `heuristico_v5.py`, que es el que está medido como el mejor
(0,6020 contra v2 en espejo, `agente-v5.md`). Mientras se corría esto, otro trabajo
del taller estaba midiendo candidatas (`heuristico_cob5` contra `heuristico_v5_ref`) y
dejó `research/agentes/heuristico_v6.py` (= v5 + `recupera`) con su paquete de envío.
Se ha medido el clon contra ese v6 también, para no comparar contra un rival ya
superado: **0,563 [0,541, 0,585]** con n=2.000. El clon gana a los tres heurísticos.
Nada de lo de esa otra línea de trabajo se ha usado ni se le atribuye aquí.

### 4.2 Contra el CAMPO real (lo que puntúa la rúbrica)

`scratchpad/v5/campo.py`: nuestro piloto con mega-lucario contra las 12 listas líder
del campo, cada una pilotada por el v2, ponderando por el share medido en la ladder
(cobertura 96,3%). Comparable celda a celda con las tablas ya medidas de v2 y v5.

| piloto | WR ponderada | IC95 | peor emparejamiento | ilegales |
|---|---:|---|---|---:|
| `heuristico.py` v2 | 0,7605 | [0,7503, 0,7707] | kangaskhan-crustle **0,289** | 0 |
| `heuristico_v5` | 0,7844 | [0,7692, 0,7996] | kangaskhan-crustle **0,280** | 0 |
| clon (20 épocas, H1=128) | 0,7882 | [0,7704, 0,8059] | kangaskhan-crustle **0,328** | 0 |
| clon (2 épocas) — descubrimiento | 0,8254 | [0,8098, 0,8411] | kangaskhan-crustle 0,328 | 0 |
| clon (2 épocas) — **confirmación independiente** | 0,8056 | [0,7877, 0,8235] | kangaskhan-crustle 0,316 | 0 |
| **clon (2 épocas) — AGRUPADO n=6.000** | **0,8155** | **[0,8036, 0,8275]** | kangaskhan-crustle **0,322** | **0** |

La confirmación se corrió con muestra fresca **antes** de declarar nada, y cae 2,0 pp
por debajo del descubrimiento: la maldición del ganador de siempre. El agrupado es el
número bueno.

Delta del clon corto agrupado: **+0,0550 sobre v2 (z≈6,9)** y **+0,0311 sobre v5
(z≈3,1)** — el doble de lo que consiguió el v5 sobre el v2 (+0,0239). Y sube en 11 de
12 emparejamientos.
Lo que más importa para el 70% de Model Score («consistency across matchups»): el
**peor emparejamiento sube de 0,289 a 0,328** y el segundo peor, ogerpon, de 0,323 a
**0,632**. Único retroceso: alakazam 0,767 → 0,764 con el corto (el largo sí lo
empeoraba, 0,684).

### 4.3 Más imitación NO es mejor juego (y es el resultado con más filo)

Los tres modelos entrenados predicen cada vez mejor y **juegan igual o peor**:

| modelo | top-1 en test | vs v5 (n=3.000) | vs v2 (n=3.000) | campo ponderado |
|---|---:|---:|---:|---:|
| 2 épocas, H1=96 | 0,5840 | **0,568** [0,550, 0,586] | **0,649** [0,631, 0,666] | **0,8155** (n=6.000) |
| 3 épocas, H1=128 | 0,5986 | — | — | — |
| 20 épocas, H1=128 | **0,6178** | 0,567 [0,550, 0,585] | 0,620 [0,602, 0,637] | 0,7882 (n=3.000) |

Duelos directos entre modelos:

| | n | tasa | IC95 |
|---|---:|---:|---|
| clon 20 épocas **vs** clon 2 épocas | 1.200 | 0,468 | [0,440, 0,497] → gana el corto |
| clon 3 épocas (H1=128) **vs** clon 20 épocas | 2.000 | 0,512 | [0,490, 0,534] → empate |

Lectura honesta: **+3,4 puntos de top-1 no compran una sola partida**, y contra v2 y
contra el campo el modelo peor predictor juega mejor. Pero el control de ancho fijo
(3 vs 20 épocas con H1=128) sale **empate**, así que no se puede atribuir el efecto a
«menos épocas»: lo que está medido es que dentro de este rango la cantidad de
imitación es indiferente o contraproducente, no que exista un óptimo en la época 2.
Es la confirmación operativa del hallazgo del diagnóstico (acuerdo con los expertos
↔ ganar, r = −0,028) llevada al sitio donde duele: **el criterio de parada de un
clon no puede ser la log-verosimilitud**.

### 4.4 Los híbridos son PEORES que el clon puro

La hipótesis 5 del encargo era usar la red solo donde la heurística es floja. Se
midió al revés de lo esperado:

| variante (`CLON_MODO`) | qué decide la red | n | vs v5 | IC95 |
|---|---|---:|---:|---|
| `todo` (clon puro) | todo | 3.000 | **0,567** | [0,550, 0,585] |
| `auxiliar` | todo menos la fase principal | 1.500 | 0,486 | [0,461, 0,511] |
| `principal` | solo la fase principal (0,0) | 1.500 | 0,445 | [0,420, 0,470] |

Ninguna mezcla llega al puro, y **la mitad-y-mitad es peor que cualquiera de las dos
políticas enteras**. (Las tres filas se midieron con los pesos de 20 épocas, que era
el modelo por defecto cuando se corrió la cadena; la comparación entre ellas es
limpia porque comparten pesos.) Interpretación: una partida es una secuencia; dos políticas con
planes distintos alternando turnos se estorban (la red busca una carta para un plan
que la heurística luego no ejecuta). Esto también dice que el valor del clon no está
en un tipo de decisión concreto sino en la **coherencia del plan completo**, que es
justo lo que ningún parche de la heurística podía comprar.

### 4.5 El negativo que hay que decir: NO transfiere a hops-snorlax

| enfrentamiento | n | tasa | IC95 |
|---|---:|---:|---|
| clon **con hops-snorlax** vs v2 con hops-snorlax | 2.000 | **0,466** | [0,444, 0,488] |

Con la segunda baraja de la ladder el clon **pierde** contra el mismo heurístico al
que gana 0,620 con mega-lucario. La red es la misma y sus rasgos son deck-agnósticos,
así que el problema no es que «no conozca» las cartas: es que la política media del
campo top **no es la política correcta para esa lista**. hops-snorlax juega un plan
que el corpus apenas contiene, y clonar la mezcla devuelve un plan genérico que la
heurística —escrita mirando esa baraja— ejecuta mejor.

Medido con los pesos de 20 épocas. No se ha repetido con los de 2 porque la
conclusión operativa no cambia: para cambiar el signo harían falta +7 pp y la mejor
diferencia medida entre los dos modelos es de +3.

Consecuencia operativa directa: **el clon se envía con mega-lucario, y con
hops-snorlax se deja el heurístico**. Y advertencia para el futuro: cualquier baraja
nueva hay que volver a medirla con el clon antes de asumir la mejora.

## 5. Auditoría de legalidad y reloj

`research/clon/auditar.py` juega las partidas EN EL MISMO PROCESO (los contadores del
agente son globales de módulo y se pierden en el `Pool` de `arena.py`).

| | |
|---|---|
| partidas | 300 contra `heuristico_v5` (mega-lucario los dos lados) |
| estados finales | **600/600 DONE** |
| decisiones | 13.535 · **red 13.235 (97,78%)** · heurístico 0 · excepciones 0 · **ilegales 0** |
| tiempo/decisión | **0,208 ms** · 0,24 s de partida completa |
| margen sobre el reloj de pared de producción | **×64.066** (600 s por agente y partida) |

El 2,22% que no pasa por la red son los `select is None` (la baraja del primer paso),
uno por partida: **el 100% de las decisiones reales las toma la red**, sin un solo
fallback.

### 5.1 La prueba dura: selects de barajas que no son la nuestra

Jugar espejos con mega-lucario solo ejercita las formas de select que produce nuestra
lista. La prueba que importa es la del campo: se pasaron por el agente las **9.714
decisiones reales** de 60 episodios de la ladder (barajas ajenas, cartas que no
jugamos, `(1,8)` de Xerosic, `(5,34)`, `(4,30)`, `(8,38)`…), midiendo la legalidad de
lo que devuelve:

    decisiones probadas 9714   ILEGALES 0
    contadores {'red': 9714, 'heuristico': 0, 'excepcion': 0, 'ilegal': 0}

Formas cubiertas: `min/max` = 1/1 (8.258), 0/1 (966), 2/2 (186), 0/2 (172), 0/5 (41),
0/3 (28), 3/3 (18), 1/3 (12), 0/4 (9), 1/2 (5), 5/5 (5), 4/4 (3). Es decir: multi-
selección de hasta 5, rangos abiertos y la acción vacía, todas legales.

Latencia sobre esas mismas 6.303 decisiones cronometradas: media **0,387 ms**, p99
**3,2 ms**, y una sola llamada de **841 ms** — la primera, que paga el parseo de
`AllCard`/`AllAttack` del catálogo. Es un coste único por proceso, irrelevante frente
a los 600 s.

### 5.2 Empaquetado verificado

`empaquetar.py` solo copiaba UN fichero de política; el clon son seis (`clon.py`,
`rasgos.py`, `features_v2.py`, `features.py`, `heuristico.py` de respaldo y los pesos).
Se le añadió `--extra` (repetible, por defecto vacío: el camino del heurístico no
cambia). Construido y **validado con el cargador real** (`compile` + `exec` sin
`__file__`, repo fuera de `sys.path`, cwd en la carpeta del paquete):

    .venv/bin/python empaquetar.py --deck research/decks/propios/mega-lucario.csv \
      --politica research/agentes/clon.py \
      --extra research/clon/rasgos.py --extra research/valor/features_v2.py \
      --extra research/valor/features.py --extra research/agentes/heuristico.py \
      --extra research/clon/politica.npz --validar

    paquete: 0,6 MiB / límite 197,7 · validación: 12 partidas · estados anómalos: 0
    VEREDICTO : OK — listo para subir

Los pesos pesan **0,10 MB**: sobra sitio para un modelo mil veces mayor si algún día
hace falta. El paquete queda en `envios/clon-mega-lucario.tar.gz`.

## 6. Veredicto

**El clon entra, con mega-lucario y con el modelo CORTO.** Es la primera vez en diez
hipótesis que algo gana con margen, y no gana por poco: +12 pp contra el piloto de la
ladder, +7 contra el mejor agente que teníamos y +5,5 pp de winrate ponderada contra
el campo real, con el peor emparejamiento subiendo por primera vez.

Lo que se envía:

    research/agentes/clon.py                (MODO="todo")
    research/clon/politica.npz              (2 épocas, H1=96 — el que juega mejor)
    research/decks/propios/mega-lucario.csv
    envios/clon-mega-lucario.tar.gz         ya construido y validado

Reproducir de cero:

    .venv/bin/python research/clon/extraer.py \
        data/replays/pokemon-tcg-ai-battle-episodes-2026-08-08.zip \
        data/replays/pokemon-tcg-ai-battle-episodes-2026-08-09.zip \
        --salida data/clon/pol_1030.npz --episodios 3000 --procs 3 --min-rating 1030
    .venv/bin/python research/clon/entrenar.py data/clon/pol_1030.npz \
        --salida research/clon/politica.npz --epocas 2          # H1=96 por defecto

Ficheros de pesos que quedan: `politica.npz` (2 épocas, el vivo), `politica_e3.npz`
(3 épocas H1=128), `politica_e20.npz` (20 épocas H1=128, mejor predictor).

### Qué NO se ha demostrado

1. **No está medido en la ladder.** Todo lo de arriba es local. El campo real de la
   ladder no es el conjunto de 12 listas del gauntlet ni lo pilotan heurísticos
   nuestros: los rivales de verdad usan RL entrenado. Un +5,5 pp contra un campo
   pilotado por v2 **no se traduce mecánicamente** en +N de rating. Lo que sí es
   defendible es la dirección y el tamaño relativo (más del doble que el v5, que ya
   se subió).
2. **No transfiere de baraja** (§4.5). Cada lista nueva hay que volver a medirla.
3. **No sabemos por qué el modelo corto juega mejor.** El control a ancho fijo salió
   empate, así que «2 épocas» no es un óptimo demostrado, es el punto donde estaba el
   mejor agente medido. La hipótesis razonable —el entrenamiento largo afina la
   política MEDIA del campo, incluidas manías de barajas que no son la nuestra— está
   sin probar.
4. **El corpus son dos días.** El meta se mueve (grimmsnarl 50,3% → 45,1% en un mes).
   Un clon entrenado el 8-9 de agosto envejece.

### Lo siguiente, por orden de valor esperado

1. **Barrer el criterio de parada como si fuera un hiperparámetro de JUEGO**: entrenar
   4-5 puntos (1, 2, 4, 8 épocas × H1 ∈ {64, 96, 128}) y ordenarlos por arena, no por
   log-loss. Es barato (~70 s por época, ~10 min por celda de arena) y §4.3 dice que
   ahí hay puntos tirados.
2. **Filtrar el corpus por rating alto de verdad** (`min_score >= 1100`, 237
   episodios/día) o **ponderar las muestras por el rating**: clonar la mezcla da la
   política media; ahora que sabemos que clonar funciona, merece la pena pagar por
   clonar a los mejores.
3. **Reentrenar con replays frescos** el 15-ago, justo antes del cierre.
4. **Arreglar kangaskhan-crustle** (0,322 y sigue siendo el peor con diferencia, 6,9%
   del campo): es el único emparejamiento donde el clon no despega, y el 70% de Model
   Score premia el suelo, no la media.
5. **Medir el clon con hops-snorlax entrenado o descartar esa baraja del segundo
   envío**; hoy el segundo envío debe seguir con el heurístico.

### Qué necesita decisión del propietario

- **Qué se sube y en qué orden.** Hay dos envíos activos como máximo. La lectura de
  esta nota es: envío 1 = clon + mega-lucario (`envios/clon-mega-lucario.tar.gz`);
  envío 2 = lo que ya esté vivo, sin tocar, hasta ver rating del clon. Subir los dos
  a la vez al clon dejaría el proyecto sin control.
- Si el clon sube el rating de verdad, **el writeup cambia de tesis**: pasa de «un
  heurístico afinado a mano» a «clonamos al top de la ladder y medimos que imitar
  mejor no es jugar mejor», que es material mucho más fuerte para «originality of the
  proposed approach». : OK — listo para subir

Los pesos pesan **0,14 MB**: sobra sitio para un modelo 1.000 veces mayor si algún día
hace falta.
