# Auto-juego sobre el clon: las dos vías fallan, y el control que hubo que montar para demostrarlo encuentra +0,20

Fecha: 2026-08-12. Piezas nuevas:

| fichero | qué es |
|---|---|
| `research/clon/autojuego.py` | el clon genera su propio corpus (espejo + campo), con exploración Gumbel y filtrado por resultado |
| `research/clon/entrenar_sp.py` | entrenador con corpus mixto experto+auto-juego, pesos por resultado y arranque en caliente |
| `research/clon/campo_sp.py` | báscula ANTI-COLAPSO: candidato contra los 12 arquetipos pilotados por OTRO agente |
| `research/agentes/clon_sp.py` | agente = clon con los pesos de auto-juego |
| `research/agentes/clon_busq.py` | **vía 3**: la red propone las k mejores, la simulación desempata |
| `research/agentes/variantes/gen_sp.py`, `gen_bq.py` | wrappers (pesos × baraja) |

Corpus en `data/clon/sp_r1.npz` y `sp_r2.npz` (1,0 GB cada uno, gitignorados).
Medidas en `data/campo_sp.json`. Todas las cifras de esta nota son frescas, con
`arena.py --procs 3`, asientos intercambiados e IC de Wilson.

---

## Resumen

1. **Las vías 1 y 2 (filtrar por ganador / pesar por resultado) NO mejoran al clon: lo
   empeoran de forma significativa.** Con el control bien puesto —mismo entrenamiento,
   con y sin el corpus de auto-juego— el auto-juego mide **0,454 [0,432, 0,475]** (vía 1)
   y **0,443 [0,421, 0,464]** (vía 2) contra su propio control, n=2.000 cada una, IC95
   enteros por debajo de 0,5.
2. **La vía 3 SÍ funciona, y mucho**: la red propone 3 candidatas y una simulación corta
   desempata → **0,705 [0,685, 0,725]** (n=2.000, muestra independiente; 0,659
   [0,629, 0,688] en la primera de n=1.000) contra el clon de la ladder, y **0,672
   [0,652, 0,693]** sobre la red ya bien entrenada (o sea: **aditiva**, no una muleta),
   con **0 ilegales** y 3,4 s de reloj por partida en UN núcleo (×176 sobre los 600 s).
3. **El hallazgo que se lleva la tanda es del experimento de control**: la red de la
   ladder está entrenada **2 épocas**, y `research/clon/politica_e20.npz` —20 épocas,
   **ya estaba en el repo, medida y descartada**— gana **0,699 [0,679, 0,719]** con
   c2-alakazam. El «+3,4 pp de top-1 no compran ni una partida» de `clon-politica.md`
   se replica exactamente… **pero solo con mega-lucario** (0,475). Es la inversión del
   ADR PKM-012 otra vez, ahora entre RED y BARAJA.

---

## 1. Cómo se genera el corpus propio (`autojuego.py`)

4.000 partidas por ronda, 3 procesos, ~4 partidas/s. Las barajas de los dos lados se
sortean independientes: 25% c2-alakazam + 25% mega-lucario (las dos que se miden) y el
50% restante repartido por el share real del campo. Así el corpus cubre el estado que
de verdad se visita sin dejar de ver barajas raras, y salen espejos y cruces solos.

**Exploración por Gumbel.** `z + tau·Gumbel(0,1)` aplicado a la ORDENACIÓN es
Gumbel-top-k = muestreo sin reemplazo de `softmax(z/tau)`, así que vale igual para los
selects de multi-selección. `tau=0` reproduce el argmax de `clon.py`.

**Calibración de tau (n=600 cada una, c2-alakazam espejo, contra el argmax):**

| tau | tasa contra el argmax |
|---|---|
| 0,3 | 0,487 [0,447, 0,527] |
| **0,5** | **0,502 [0,462, 0,542]** |
| 0,7 | 0,410 [0,371, 0,450] |
| 1,0 | 0,402 [0,363, 0,441] |

(la fracción de decisiones que el ruido cambia solo está medida en tau=0,5: **33,2%**
en la ronda 1 y 30,2% en la ronda 2, contadas dentro del generador)

Hay un escalón entre 0,5 y 0,7. Se usa **tau=0,5**: la exploración máxima que **no
cuesta absolutamente nada**. Ese número es además el diagnóstico de todo lo que sigue:
el clon es **indiferente** entre su argmax y su top-k. Si cambiar un tercio de las
decisiones no mueve el marcador, el margen que queda en la ordenación de la red es
pequeño, y filtrar por resultado solo puede recuperar una fracción de él.

Ronda 1 (corpus del clon de la ladder): 512.714 decisiones, 3,89 M opciones, 50,8%
ganadoras, 33,2% exploradas, **0 fallbacks heurísticos y 0 acciones ilegales**.
Ronda 2 (corpus de la red de control): 503.149 decisiones, 51,0% ganadoras.

## 2. Cómo se entrena (`entrenar_sp.py`)

Misma red y misma pérdida que `entrenar.py`. El corpus experto se parte 70/15/15 por
episodio **con la misma semilla**, así que el test es el mismo fichero de decisiones y
los top-1 son comparables número a número. El auto-juego entra **entero en train** y
nunca en val/test.

Detalle que resultó importante: **la época NO se puede elegir por top-1 de imitación**.
El primer intento seleccionó por un holdout de auto-juego ganador y eligió la época 2 de
6 — porque ese criterio lo maximiza la red que GENERÓ los datos, es decir, «no aprendas
nada». Esa red midió 0,479. La misma receta guardando la ÚLTIMA época midió 0,523. Todas
las cifras de abajo usan la última época.

## 3. Vía 1 — filtrado de expertos (quedarse con el bando ganador)

**Ronda 1**, arranque en caliente desde `politica.npz`, 6 épocas, lr 0,006:

| variante | baraja | n | tasa vs el clon de la ladder | IC95 |
|---|---|---:|---:|---|
| sp1 (época por holdout de auto-juego) | c2-alakazam | 2.000 | 0,479 | [0,458, 0,501] |
| **sp1u** (última época) | c2-alakazam | 800 | 0,539 | [0,504, 0,573] |
| **sp1u** (confirmación) | c2-alakazam | **2.000** | **0,523** | [0,502, 0,545] |
| **sp1u** | mega-lucario | **2.000** | **0,572** | [0,550, 0,594] |
| sp1f (auto-juego con peso doble) | c2-alakazam | 800 | 0,496 | [0,462, 0,531] |

Visto solo, parece que el auto-juego compra +0,02/+0,07. **No compra nada**: lo compran
las épocas extra, y el auto-juego se come parte de la ganancia. La prueba es el control.

### El control que hacía falta

`politica.npz` es de **2 épocas**. Cualquier variante de auto-juego entrena épocas
extra, así que hay dos cosas cambiando a la vez. El control aísla una: mismas 6 épocas,
mismo arranque, mismo lr, **corpus experto solo, sin una sola partida propia**.

| red | qué es | baraja | n | tasa vs el clon de la ladder | IC95 |
|---|---|---|---:|---:|---|
| sp1u | 6 épocas, experto + auto-juego ganador | c2-alakazam | 2.000 | 0,523 | [0,502, 0,545] |
| **ctl** | **6 épocas, SOLO experto** | c2-alakazam | 800 | **0,601** | [0,567, 0,635] |
| **ctl** (confirmación) | ídem | c2-alakazam | **2.000** | **0,620** | [0,598, 0,641] |
| ctl | ídem | mega-lucario | 2.000 | 0,510 | [0,488, 0,532] |

El corpus propio no solo no aporta: **resta ~0,10 de winrate** frente a no usarlo.

### Ronda 2: el mismo experimento con una red base que ya juega bien

Objeción legítima a la ronda 1: el corpus lo generó una red floja (2 épocas), así que
filtrar por ganador solo re-imita a una red floja. La ronda 2 la elimina: el corpus lo
genera **`ctl`**, y se comparan dos redes que salen del MISMO punto con el MISMO
entrenamiento (6 épocas más, lr 0,006), lo único que cambia es si el auto-juego entra:

| | n | tasa | IC95 | veredicto |
|---|---:|---:|---|---|
| **sp2 (con auto-juego) vs ctl2 (sin él)** | **2.000** | **0,454** | **[0,432, 0,475]** | **el auto-juego PIERDE, significativo** |

## 4. Vía 2 — pesar por resultado en vez de filtrar

| variante | ronda | rival | n | tasa | IC95 |
|---|---|---|---:|---:|---|
| sp1p (peso 1±0,5 según ganó/perdió) | 1 | clon de la ladder | 800 | 0,539 | [0,504, 0,573] |
| **sp2p** (ídem, desde `ctl`) | 2 | **ctl2 (su control)** | **2.000** | **0,443** | **[0,421, 0,464]** |

**Vía 2 = vía 1.** En la ronda 1 dan el mismo número hasta el tercer decimal (0,539 las
dos) y en la ronda 2 las dos pierden contra su control con IC disjuntos de 0,5. Pesar en
vez de filtrar no cambia nada, lo que era de esperar: son la misma reponderación del
corpus con distinta dureza.

### Dos variantes propias, fuera del guion

- **Peso CON SIGNO (REINFORCE con línea base 0,5)**: las perdedoras empujan la
  probabilidad en sentido contrario. **Diverge**: la entropía cruzada no tiene máximo,
  el log-loss se va a 3,0 (alpha 0,3) y 12,4 (alpha 1,0) y el top-1 cae a 0,52 y 0,39.
  No llegó a arena. Queda escrito para que nadie lo repita.
- **Objetivo negativo ACOTADO** (`--filtro neg`): en una decisión perdida el objetivo
  pasa a ser «cualquier opción menos la que jugué», uniforme, con peso 0,3. Es estable
  y mide **0,540 [0,505, 0,574]** (n=800, ronda 1) — es decir, exactamente lo mismo que
  las otras dos, y por debajo del control.

## 5. Contra el campo: no hay colapso, hay peor juego

`campo_sp.py`, candidato con c2-alakazam contra los **12 arquetipos pilotados por el
clon**, n=200 por emparejamiento (2.400 partidas por fila), ponderado por el share real:

| candidato | POND | IC95 | PEOR | cobertura |
|---|---:|---|---|---|
| **ctl2** (sin auto-juego) | **0,5302** | [0,5026, 0,5578] | c5-kangaskhan **0,335** | 96,3% |
| sp2 (con auto-juego) | 0,5124 | [0,4843, 0,5405] | c5-kangaskhan **0,295** | 96,3% |

**No hay colapso** en el sentido clásico: la red de auto-juego no se hunde contra
terceros mientras sube en el espejo. Simplemente es **peor en casi todas las casillas**
(10 de 12) y peor en el peor emparejamiento, que es lo que puntúa el 70% del rubric. El
agujero histórico de `c5-kangaskhan` sigue siendo el agujero.

## 6. Por qué no funciona (la explicación cuadra con los números)

El crédito por decisión es diminuto. Una partida tiene ~76 decisiones por bando y el
único dato es ganó/perdió, así que la reponderación por resultado que ve cada decisión
es del orden de `P(gana|a)/P(gana)` ≈ 1,02-1,04: un desplazamiento de ~0,03 en el
logit, contra separaciones típicas de 1-3 entre opciones. Solo puede cambiar el argmax
en los casi-empates, y los casi-empates son justo donde ya sabemos que **da igual lo
que se elija** (tau=0,5 cambia el 33% de las decisiones y mide 0,502). El auto-juego
gasta la mitad de cada lote de entrenamiento en mover la red por un eje donde no hay
premio, y lo que pierde es lo que ese mismo gradiente habría hecho sobre el corpus
experto, que sí tiene señal por decisión.

## 7. El hallazgo colateral: la red de la ladder está a medio entrenar

El control obligó a medir la escalera de épocas, y ahí está el premio gordo. Todas
contra **el clon de la ladder**, espejo, n=2.000:

| red | épocas | top-1 test | c2-alakazam | mega-lucario |
|---|---|---:|---:|---:|
| `politica.npz` (LA QUE ESTÁ EN LA LADDER) | 2 | 0,5839 | — | — |
| `politica_ctl.npz` (caliente, 6) | 2+6 | 0,6041 | **0,620** [0,598, 0,641] | 0,510 [0,488, 0,532] |
| `politica_ctl2.npz` (caliente, 12) | 2+12 | 0,6095 | 0,594 vs `ctl` [0,572, 0,615] | — |
| **`politica_e20.npz`** (desde cero, **ya estaba en el repo**) | 20 | 0,6178 | **0,699** [0,679, 0,719] | 0,475 [0,454, 0,497] |

`clon-politica.md` cerró este eje con «**+3,4 pp de top-1 no compran ni una partida**:
el modelo que peor predice es el que mejor juega». Ese resultado **se replica aquí sin
un rasguño… con mega-lucario** (0,475: la red de 20 épocas efectivamente no gana). Con
**c2-alakazam, que es la lista recomendada para el envío**, la misma red gana **+0,199**.

Es exactamente la estructura del **ADR PKM-012** (la báscula de barajas se invierte
según el piloto), un piso más arriba: **la báscula de REDES también se invierte según
la baraja**. Y el corolario operativo es incómodo: el eje «entrenar más» se dio por
muerto midiéndolo con la lista equivocada, y los pesos que lo desmienten llevaban
horas en `research/clon/` sin que nadie los volviera a medir.

## 8. Vía 3 — la red propone, la simulación desempata (`clon_busq.py`)

Lo que el ISMCTS (`mcts.py`, 0,529 sin significación) no tenía: una política decente.
Aquí la búsqueda no busca la jugada, solo rompe empates.

- Candidatas: las `C=3` mejores acciones DISTINTAS de la red. Se construyen forzando
  cada opción del top a ir primera y dejando que la regla de selección de `clon.py`
  arme la acción entera, así que vale igual para los selects de multi-selección.
- Se busca **solo si están cerca** (`MARGEN=1,5` en puntuación) y `rival_bocabajo_n == 0`.
- Cada candidata: `K=8` determinizaciones (`InfoTracker.sample` + `search_begin`) × un
  rollout truncado a `R=16` selects **con la propia red pilotando los dos lados dentro
  de la búsqueda**, y evaluación de material de `mcts._evalua` al final (mucha menos
  varianza que un resultado binario con tan pocas muestras).
- `search_end()` en `finally`, toda acción por `heuristico._es_legal`, fallback al clon
  y luego al heurístico.

| medida | valor |
|---|---|
| **busq vs el clon de la ladder** (c2-alakazam, espejo) | **0,659 [0,629, 0,688]** n=1.000 |
| **ídem, muestra de CONFIRMACIÓN independiente** | **0,705 [0,685, 0,725]** n=2.000 |
| **búsqueda sobre la red BUENA**: busq(ctl2) vs ctl2 | **0,672 [0,652, 0,693]** n=2.000 |
| **control: el MISMO agente con la búsqueda apagada** (`CB_MARGEN=-1`) | 0,525 [0,485, 0,565] n=600 — **sin diferencia** |
| decisiones que se buscan | 51,1% |
| de esas, cuántas cambian la jugada | 51,0% (→ 26% del total) |
| auditoría en **1 núcleo** (`taskset -c 0`, 30 partidas) | **60/60 DONE**, 0 ilegales, 0 excepciones, 0 determinizaciones fallidas, 0 errores de step |
| reloj | 3,4 s/partida (2,91 s de búsqueda), 77 ms por decisión buscada |
| margen sobre los 600 s de producción | **×176** |

**La búsqueda NO es una muleta de una red floja: es aditiva.** Sobre `ctl2` —que ya
gana 0,594 a `ctl` y 0,620 al clon de la ladder— la misma búsqueda vuelve a ganar
**0,672 [0,652, 0,693]**. Los dos ejes (entrenar más la red / desempatar con
simulación) se suman en vez de solaparse, que es lo que había que comprobar antes de
recomendar los dos a la vez.

El **control que cierra la atribución**: el mismo módulo con la puerta de búsqueda
cerrada (`CB_MARGEN=-1`, nunca busca) mide **0,525 [0,485, 0,565]** contra `clon.py`,
sin diferencia significativa — es decir, sin búsqueda **es** el clon, y los +0,20 son
de la búsqueda y no de alguna diferencia accidental en cómo construye la acción.

Un bug que costó un rato y conviene recordar: el `InfoTracker` es **estado que se
acumula partida a partida**. En `arena.py` cada partida re-importa el agente y no se
nota, pero en un proceso que juega varias seguidas el tracker de la partida anterior lo
rompe (medido: **138 excepciones de 348 decisiones**), y un módulo que pilota los DOS
bandos mezcla las dos perspectivas en el mismo objeto (13 excepciones y 8
determinizaciones fallidas en 3 partidas). `clon_busq.py` lleva **un tracker por asiento
(`yourIndex`) y reinicio cuando el turno retrocede**; tras el arreglo, 4 partidas
espejo en un solo proceso dan 229 decisiones con **0 excepciones, 0 ilegales, 0
determinizaciones fallidas**. `mcts.py` tiene el patrón viejo y la misma trampa.

### Que se puede empaquetar: verificado, no supuesto

Probado con la disposición REAL del envío (`main.py` ejecutado con `compile`+`exec`
**sin `__file__`**, el agente como `agentes/politica.py`, el repo fuera de `sys.path`):
carga y juega 4 partidas, 8/8 DONE, 0 ilegales. Ficheros de apoyo que hay que pasar con
`--extra`, y son los del clon **más tres**: `rasgos.py`, `features_v2.py`, `features.py`,
`politica*.npz` + **`mcts.py`, `tracker.py`, `search_wrapper.py`**. Nada de terceros.
Un defecto encontrado y corregido en el camino: `clon_busq.py` resolvía los pesos con
una ruta fija `../clon/politica.npz` que en el paquete plano no existe; ahora usa el
mismo `_busca()` tolerante a las dos disposiciones que `clon.py`.

## 9. Veredicto

- **Vía 1 (filtrado por ganador): NO.** 0,454 [0,432, 0,475] contra su propio control.
- **Vía 2 (pesado por resultado): NO,** y es indistinguible de la vía 1. 0,443 [0,421, 0,464].
- **No hacer ronda 3.** Las dos rondas apuntan igual, la explicación mecánica cuadra
  con la calibración de tau, y la vía 2 —que es la misma idea con otra dureza— cae en
  el mismo sitio. Más partidas propias escalan como √n una señal que ya se midió nula.
- **Vía 3: SÍ, y es el cambio más grande medido en el proyecto.** 0,705 [0,685, 0,725]
  contra la red que está en la ladder (confirmado en dos muestras independientes) y
  0,672 [0,652, 0,693] sobre la red bien entrenada, con el reloj y la legalidad
  auditados y el empaquetado probado.
- **Los dos ejes que SÍ pagan se suman**: entrenar más la red (+0,199 con `e20`) y
  desempatar con simulación (+0,172 sobre una red ya entrenada). El candidato obvio
  para el envío es **la búsqueda sobre la mejor red disponible, con c2-alakazam**.
- **Y antes que nada, medir `politica_e20.npz` con la lista del envío.** Es gratis:
  los pesos ya existen, no hay que entrenar nada.

---

## 10. Medidas todavía en vuelo al cerrar la nota

Lanzadas y desatendidas; los resultados aparecen solos en estos ficheros:

| log | qué mide |
|---|---|
| `scratchpad/ronda3e.log` | busq vs clon con **mega-lucario** n=2.000 · busq(ctl2) vs el clon de la ladder n=2.000 |
| `scratchpad/ronda4g.log` | **busq(e20) vs e20** y vs el clon de la ladder (n=2.000) · campo de `e20` y de `busq(e20)` |

Lo que falta para poder enviar la vía 3, en orden:

1. `busq(e20)` con c2-alakazam contra el campo (`campo_sp.py`): el **peor emparejamiento**
   es el 70% del rubric y todavía no está medido para este agente.
2. Auditoría de reloj con la red final y `remainingOverageTime` real de producción
   (aquí: 3,4 s/partida en un núcleo, ×176 de margen — sobra, pero se re-mide con los
   pesos que se envíen).
3. `empaquetar.py --politica research/agentes/clon_busq.py --extra` con los SIETE
   ficheros de apoyo (§8) y `--validar`.
