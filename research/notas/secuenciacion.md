# Secuenciación del turno — reordenar la fase principal (0,0) (2026-08-11)

Qué es: el diagnóstico contra expertos (`diagnostico-expertos.md` §2) mide que nuestra fase
principal tiene un **orden de prioridades fijo e invertido** respecto al campo (adjuntamos la
energía antes de jugar cartas, evolucionamos antes que nada, no usamos habilidades cuando
podemos evolucionar). Aquí se implementa la reordenación —cada pieza detrás de su propio
interruptor— y se mide en `arena.py`, que es el único gate que vale.

**Resultado en una línea: el acuerdo con los expertos sube ~1 punto y el winrate baja. No se
activa nada. `heuristico.py` (v2) sigue siendo el piloto.** Es el sexto precedente de mejora
«obvia» que no gana, y el más limpio de todos: el mismo cambio de código sube el acuerdo
(43,61% → 44,55%) y pierde partidas (0,471 con IC95 por debajo de 0,5).

**Reauditado en una segunda pasada independiente (§5-bis): los veredictos se sostienen, y la
replicación añade el dato más útil de toda la tarea — dos políticas que son el v2 exacto
midieron 0,460 y 0,495 a n=600.**

Piezas: `research/agentes/heuristico_seq.py` (v2 + interruptores; `heuristico.py` **intacto**),
`scratchpad/seq_diff.py` y `scratchpad/seq_equiv.py` (diff conductual y clases de equivalencia),
`scratchpad/legalidad_seq.py` (legalidad y tiempos), `scratchpad/acuerdo_variante.py` (acuerdo
con expertos de una variante cualquiera), `scratchpad/seq_porque.py` (mecanismo).
Logs crudos: `scratchpad/bateria2..6.log`, `scratchpad/acuerdos.log`.

---

## 1. Qué hace cada interruptor

`_fase_principal` deja de ser una escalera de `if`s y pasa a ser una **lista de bloques**
(`_ORDEN_V2`) que los interruptores permutan (`_orden_bloques()`, se lee en cada decisión).
Con los cuatro apagados el orden es el del v2 y el código de cada bloque es idéntico.

Orden v2: `banca<4 → evolucionar → habilidad 'robo' → energía → habilidad 'acel' → tool →
item de búsqueda → supporter de robo → estadio → habilidad 'estadio' → atacar → fin`.

| interruptor | qué mueve | hipótesis del diagnóstico |
|---|---|---|
| `SEQ_BUSCAR_ANTES` | `item` y `supporter` **delante** de `energía` | 7 vs 8: experto 41,2/22,2, nosotros 26,0/39,7 |
| `SEQ_ENERGIA_TARDE` | `energía` y `habilidad 'acel'` al final, justo antes de atacar | la misma inversión, versión fuerte |
| `SEQ_HABILIDAD_ANTES` | `habilidad 'robo'` **delante** de `evolucionar` | 9 vs 10: nosotros 87,4% / 0,0% |
| `SEQ_ATACAR_ULTIMO` | bloque nuevo `gratis` antes de `atacar` (5.ª plaza de banca, option 9 y option 8 residuales) | el ataque cierra el turno |

Salvaguardas heredadas: el tope de **12 activaciones de habilidad por turno** es el mismo `_T10`
y la misma `_activa_habilidad` del v2/v3; el bloque `gratis` solo devuelve jugadas que consumen
una carta de la mano, así que se agota solo (sin bucle). `_elige_cartas`, `_politica`,
`_es_legal`, `_fallback` y `agent` son **byte a byte** los del v2.

### Control de identidad (lo primero que hay que probar)

Con los cuatro apagados el módulo tiene que ser el v2 **exacto**, y se comprueba dos veces:

- diff conductual sobre partidas reales: **0 divergencias en 1.322 decisiones (0,0)**;
- acuerdo con expertos sobre 76.359 decisiones: **43,61% / (0,0) 33,88%**, cifra por cifra la
  del v2.

---

## 2. Antes de gastar arena: qué interruptores son de verdad distintos

`seq_equiv.py` juega las 16 combinaciones contra la misma trayectoria y las agrupa por acción.
**Con nuestras barajas varias combinaciones son el MISMO agente**, y medirlas por separado
habría sido gastar arena en ruido:

| baraja | políticas distintas de 16 | detalle |
|---|---|---|
| `mega-lucario` | **4** | `B = E = BE = BH = …` (13,6% de divergencia), `A` (3,8%), `BA` (17,5%), `off = H` (0%) |
| `hops-snorlax` | 8 | `H` sigue siendo nulo: `off = H`, `B = BH`, `E = EH`, `A = HA`… |
| `c2-alakazam` (campo) | 16 | aquí `H` sí muerde (3,8%) |

Dos consecuencias que hay que llevarse:

1. **`SEQ_HABILIDAD_ANTES` es inerte en las dos barajas vivas.** `mega-lucario` no tiene ni una
   habilidad; las dos de `hops-snorlax` (Extra Helpings, Defiant Horn) no son activables como
   option 10. Medirlo ahí habría dado 0,50 **por construcción**, no por falta de valor. La fuga
   9 vs 10 (87,4%/0,0%) es real pero vive en las barajas del CAMPO (Munkidori, Drakloak,
   Dudunsparce), o sea que es un problema de **reconocimiento** de habilidades (§6-R7 del
   diagnóstico: el 58,7% caen en `None`), no de orden.
2. En `mega-lucario`, `BUSCAR_ANTES` y `ENERGIA_TARDE` son **la misma política** (la baraja no
   tiene tool ni estadio, que es lo único que las separa). Un único número vale para las dos.

---

## 3. La báscula: arena contra `heuristico.py`, misma baraja en ambos lados

`--procs 3`, asientos intercambiados. **Se acumulan las repeticiones del mismo emparejamiento.**

### 3.1 El control que hace legible todo lo demás

| A | B | n | tasa | IC95 |
|---|---|---:|---:|---|
| `s_off` (política **idéntica** al v2) | `heuristico.py` | **6.600** | **0,4992** | **[0,4872, 0,5113]** |

Arena está calibrada: un agente idéntico mide 0,50. Pero las tiradas sueltas de ese mismo
control fueron 0,482 (n=600), 0,519 (n=2000) y 0,492 (n=4000): **con n=600 el ruido es ±4 puntos
y con n=2000 sigue siendo ±2,2**. Cualquier lectura entre 0,48 y 0,52 con n≤2.000 no dice nada.

### 3.2 `mega-lucario` (la baraja que va en serio)

| variante | n | tasa | IC95 | veredicto |
|---|---:|---:|---|---|
| `B` buscar antes (= `E` energía tarde) | 2.000 | **0,4710** | [0,4492, 0,4929] | **peor, significativo** |
| `A` atacar último | **6.000** | 0,5040 | [0,4914, 0,5166] | empate |
| `BA` buscar + atacar | 2.000 | 0,5040 | [0,4821, 0,5259] | empate |
| `H` habilidad antes | — | — | — | **inerte con esta baraja** |

Contraste correcto (variante contra el control medido, no contra 0,5):
`A − control = +0,005` (IC95 [−0,013, +0,022], z = 0,53) → nada.
`B − control = −0,028` (IC95 [−0,053, −0,003], z = −2,22) → pérdida real.

### 3.3 `hops-snorlax` (el otro envío vivo) y `c2-alakazam` (para poder medir `H`)

| baraja | variante | n | tasa | IC95 | veredicto |
|---|---|---:|---:|---|---|
| hops-snorlax | `B` buscar antes | 1.200 | **0,4550** | [0,4270, 0,4833] | **peor, significativo** |
| hops-snorlax | `A` atacar último | 2.000 | 0,5020 | [0,4801, 0,5239] | empate |
| hops-snorlax | `BA` | 1.200 | 0,4717 | [0,4436, 0,5000] | peor (al filo) |
| c2-alakazam (espejo) | `H` habilidad antes | 1.200 | 0,5200 | [0,4917, 0,5482] | empate |
| c2-alakazam (espejo) | `B` buscar antes | 1.200 | 0,5083 | [0,4801, 0,5365] | empate |

**`BUSCAR_ANTES` pierde en las dos barajas propias** (0,471 y 0,455) y empata en una baraja del
campo. No es una casualidad de una muestra: son dos negativos independientes en la misma
dirección. `ATACAR_ULTIMO` empata en las dos (0,504 con n=6.000 y 0,502 con n=2.000).

---

## 4. El acuerdo con los expertos SÍ sube — y da igual

`acuerdo_variante.py`, 500 episodios, 76.359 decisiones con elección, mismo protocolo que
`diagnostico_expertos.py` (desfase +1, suelo aleatorio exacto).

| variante | acuerdo global | Δ | acuerdo en (0,0) | Δ |
|---|---:|---:|---:|---:|
| v2 (`heuristico.py`) | 43,61% | — | 33,88% | — |
| `seq` con todo apagado (control) | 43,61% | 0,00 | 33,88% | 0,00 |
| `B` buscar antes | 44,44% | **+0,83** | 35,36% | **+1,48** |
| `BA` buscar + atacar | **44,55%** | **+0,94** | **35,55%** | **+1,67** |
| `BEHA` (los cuatro) | 44,46% | +0,85 | 35,39% | +1,51 |

Reproduce lo que predijo la política sombra del diagnóstico para O1 (+0,89 global / +1,57 en
(0,0)). Y la variante que **más se parece al experto** (`BA`, +0,94) es la que en `hops-snorlax`
mide **0,4717**. Esto es exactamente lo que anunciaba r = −0,028, ahora demostrado sobre el
mismo cambio de código en vez de sobre una correlación.

### Qué le pasa a la tabla de co-disponibilidad

| par | experto | v2 | con `B` | con `BEHA` |
|---|---|---|---|---|
| 7 vs 8 (carta vs energía) | 41,0 / 22,3 | 26,9 / 39,2 | **52,4 / 13,7** | 54,9 / 11,3 |
| 7 vs 10 | 34,1 / 40,4 | 32,4 / 25,1 | 42,1 / 24,9 | 44,0 / 31,9 |
| 9 vs 10 | 37,4 / 33,4 | 86,5 / **0,0** | 86,5 / 0,0 | **58,8 / 27,7** |

La inversión 7 vs 8 no se corrige: **se invierte al otro lado**. Pasamos de adjuntar de más
(39,2% frente al 22,3% del experto) a adjuntar de menos (13,7%), y el acuerdo del propio opt8
cae de 26,4% a 15,0% aunque el global suba. Parecerse «más» en el agregado es compatible con
jugar peor en la jugada concreta. `H` sí arregla el 9 vs 10 (0,0% → 27,7%) en el corpus de
replays, que son barajas del campo — coherente con §2: ahí sí hay habilidades activables.

---

## 5. Por qué pierde `BUSCAR_ANTES` (lo que se descarta, medido)

`seq_porque.py`, 40 partidas por configuración, pilotando de verdad:

| | turnos con energía en mano | energía adjuntada | destino: activo / banca |
|---|---:|---:|---|
| v2 | 270 | 85,6% | 69,8% / 30,2% |
| `B` | 259 | 83,0% | **77,2% / 22,8%** |
| `A` | 296 | 85,8% | 70,7% / 29,3% |

- **No** es que perdamos el adjunte del turno (la hipótesis de que Ultra Ball se lleva la energía
  en el descarte de coste): la tasa es la misma dentro del ruido.
- **No** es que la energía se vaya al banco: con `B` va **más** al activo (77,2% vs 69,8%), que
  es justo el efecto que se buscaba. El cambio hace lo que dice y aun así pierde.

Queda como hipótesis no cerrada (y barata de mirar si alguna vez importa): con `B` jugamos más
Fighting Gong y más búsqueda por turno, y en esta baraja gastar el trainer antes puede estar
quemando recursos que el v2 conservaba para el turno siguiente. **No se persigue**: el gate ya
dijo que no.

---

## 5-bis. Replicación independiente (2026-08-11, segunda pasada)

Se reauditó el trabajo entero sin dar por buena ninguna cifra de la primera pasada.
Log: `scratchpad/repl_verif.log` (`scratchpad/repl_verif.sh`).

**Lo estructural, verificado de nuevo:**

- Todas las funciones de `heuristico_seq.py` son **idénticas por hash MD5** a las de
  `heuristico.py` salvo `_fase_principal` (reescrita como lista de bloques) más
  `_mueve` y `_orden_bloques` (nuevas). `_elige_cartas`, `_politica`, `_es_legal`,
  `_fallback`, `agent`, `_activa_habilidad` y `_t10_registro`: **IGUAL**.
- El tope de 12 activaciones vive en `_activa_habilidad` (línea 272, `reg[1] >= 12`),
  que es byte a byte la del v2. La salvaguarda pedida está y es la heredada.
- `seq_diff.py` rehecho: **0/372 divergencias con todo apagado**. `buscar` y `energia`
  divergen en las mismas 47 decisiones (contador `buscar_vs_energia_difieren` = 0:
  son la MISMA política en esta baraja). `habilidad` = **0 divergencias**. `atacar` = 3,8%.
  La divergencia de `B` es toda `dif_8->7` (energía → jugar carta): el interruptor
  empuja exactamente en la dirección que decía el diagnóstico.
- Las barajas de los wrappers son las 60 cartas de `mega-lucario.csv` en ambos lados.

**Lo que aporta de nuevo: el suelo de ruido de n=600, medido con políticas nulas conocidas.**

Cinco tiradas frescas de n=600, `--procs 3`, contra `heuristico.py`:

| variante | tasa n=600 | IC95 | ¿es política nula? |
|---|---:|---|---|
| `s_off` | 0,495 | [0,455, 0,535] | **sí** (idéntica al v2) |
| `s_buscar` | 0,490 | [0,450, 0,530] | no |
| `s_energia` | **0,518** | [0,478, 0,558] | = `s_buscar`, misma política |
| `s_habilidad` | **0,460** | [0,421, 0,500] | **sí** (inerte en esta baraja) |
| `s_atacar` | 0,517 | [0,477, 0,556] | no |

Dos pares que **por construcción tenían que dar el mismo número** y no lo dan:

1. `s_habilidad` es el v2 exacto (0 divergencias) y midió **0,460**, cuatro puntos por
   debajo de 0,5, rozando el «significativo».
2. `s_energia` y `s_buscar` son la misma política y midieron **0,518 y 0,490**: 2,8
   puntos de separación entre dos agentes que juegan idéntico.

El rango de tiradas nulas o equivalentes a n=600 va de **0,460 a 0,518** (amplitud 5,8
puntos). **Esto liquida n=600 como báscula**: la nota de potencia del encargo se queda
corta, no es que «entre 0,50 y 0,53 haya que subir a n=1500» — es que a n=600 una
política nula puede salir 0,46 o 0,52. Cualquier veredicto de esta tarea basado en una
sola tirada de 600 habría sido ruido con formato de tabla.

**Cifras acumuladas** (se suman todas las repeticiones del mismo emparejamiento):

| variante | n total | tasa | IC95 | veredicto |
|---|---:|---:|---|---|
| nula agregada (`s_off` + `s_habilidad`) | **7.800** | 0,4959 | [0,4848, 0,5070] | el cero del proyecto |
| `s_off` solo | 7.200 | 0,4989 | [0,4873, 0,5104] | arena calibrada |
| `B` = `E` (buscar/energía agrupados) | **3.800** | **0,4797** | **[0,4639, 0,4956]** | **peor, significativo** |
| `A` atacar último | **6.600** | 0,5052 | [0,4931, 0,5172] | empate |
| `B` en hops-snorlax | 1.200 | 0,4550 | [0,4270, 0,4833] | **peor, significativo** |
| `A` en hops-snorlax | 2.000 | 0,5020 | [0,4801, 0,5239] | empate |

Los veredictos de §7 **no cambian**: `B`/`E` siguen por debajo de 0,5 con el IC entero
fuera (y en dos barajas independientes), y `A` sigue sin despegarse del cero medido
(+0,009 sobre la nula agregada, con los IC solapados de par en par).

---

## 6. Legalidad y coste

`legalidad_seq.py`, 400 partidas con **los cuatro interruptores encendidos** (el camino de código
más largo), `mega-lucario` en ambos lados:

- **0 acciones ilegales** en **13.318 decisiones**; 0 estados INVALID; `politica_ilegal`,
  `politica_excepcion`, `select_desconocido`, `fase_sin_accion` = **0**; `CASOS_RAROS` vacío.
- Tiempo por decisión: **mediana 0,046 ms**, p95 0,164 ms. La cola (p99 19,9 ms, máx 88,9 ms) es
  la carga del catálogo `AllCard/AllAttack`, que aquí ocurre 400 veces porque el arnés recarga el
  módulo en cada partida; en el envío se paga una sola vez. Sigue en milisegundos.

---

## 7. Veredicto

| interruptor | qué activar |
|---|---|
| `SEQ_BUSCAR_ANTES` | **NO** — 0,471 (lucario) y 0,455 (hops), ambos con IC95 por debajo de 0,5 |
| `SEQ_ENERGIA_TARDE` | **NO** — misma política que el anterior en lucario; mismo negativo |
| `SEQ_HABILIDAD_ANTES` | **NO** — inerte en las dos barajas vivas; 0,520 [0,492, 0,548] en un espejo de alakazam no es evidencia |
| `SEQ_ATACAR_ULTIMO` | **NO** — 0,504 con n=6.000; +0,005 sobre el control. No empeora, pero no gana, y código que no gana no entra |

`heuristico_seq.py` se queda en el repo **con los cuatro apagados** (= v2 exacto): documenta la
hipótesis, deja el banco de pruebas montado y no toca al piloto.

Lo que este trabajo sí deja para lo siguiente:

1. **La fuga del orden estaba mal atribuida.** El 9 vs 10 (87,4%/0,0%) no se arregla reordenando:
   en nuestras barajas no hay ninguna habilidad activable que reordenar. Lo que hay que arreglar
   es el **reconocimiento** de habilidades (R7) y la **cobertura de items** (R2), que son
   capacidades nuevas, no permutaciones del mismo repertorio.
2. **La nula del proyecto es 0,4959 con n=7.800** (§5-bis), y el rango de una tirada nula a
   n=600 es 0,460–0,518. Los cinco precedentes negativos (ISMCTS 0,529, ISMCTS+valor 0,487,
   retirada 0,476, gusting 0,495, greedy-valor 0,160) deberían releerse contra este número:
   **los que se midieron con n pequeña no distinguen de cero** — «gusting 0,495» y «ISMCTS
   0,529» caen dentro del rango que produce una política que no cambia nada. Antes de volver
   a declarar nada, fijar n por el tamaño de efecto buscado, no por el presupuesto de la tirada.
3. **`seq_equiv.py` antes de cada batería.** Ha ahorrado 9 de 12 mediciones previstas al detectar
   que eran el mismo agente.
