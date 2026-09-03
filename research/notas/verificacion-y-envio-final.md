# Verificación independiente, candidato final y empaquetado

Fecha: 2026-08-12 (tarde). Corte de la Simulation: **2026-08-16 23:59 UTC**.
Encargo: verificar los tres informes del día (CLON CON MÁS DATOS · AUTO-JUEGO ·
LISTA PROPIA), elegir el candidato, rehacer la elección de lista con el piloto
que se envía y dejar los paquetes construidos y validados.

Instrumentación de esta tanda en `scratchpad/final/` (`mk.py` genera los
envoltorios, `c1..c5.sh` las cadenas, `auditar2.py` la auditoría).
Resultados de campo en `data/campo_sp.json`.

**Todo lo de esta nota se midió con `OMP_NUM_THREADS=1`.** No es un detalle de
higiene: con BLAS multihilo la misma arena de 120 partidas tarda 30,8 s y quema
~11 núcleos; con un hilo tarda **21,4 s** y quema 3. Las matrices del clon son
diminutas y el hilado solo añade sincronización. Mide igual y cuesta 3× menos.

---

## 1. Verificación: reportado contra re-medido

Muestras frescas e independientes, arena, misma lista a los dos lados, asientos
intercambiados, `--procs 3`. **Los dos lados son envoltorios que fijan sus
propios pesos DESPUÉS del `exec_module`** (`_m._RUTA = ...`), que es la única
forma inmune al fallo de herencia de `CLON_PESOS` documentado en
`clon-escalado.md` §0 — no basta con fijar la variable de entorno antes de cada
carga, porque el orden de carga vuelve a importar en cuanto alguien mete un
agente pelado.

| afirmación del informe | reportado | re-medido (n=2.000) | veredicto |
|---|---|---|---|
| `politica_7d_h192_mejorval` (clon_v2) vs clon de la ladder, c2-alakazam | 0,6778 (n=4.000) | **0,696 [0,675, 0,715]** | **CONFIRMADO** |
| `politica_7d_h384_mejorval` vs clon de la ladder, c2-alakazam | 0,7190 | **0,724 [0,704, 0,743]** | **CONFIRMADO** |
| `politica_e20` vs clon de la ladder, c2-alakazam | 0,699 | **0,680 [0,659, 0,700]** | **CONFIRMADO** (−1,9 pp, maldición del ganador) |
| `clon_busq.py` (vía 3) vs clon de la ladder, c2-alakazam | 0,705 | **0,709 [0,688, 0,728]** | **CONFIRMADO** |
| vía 1 y vía 2 del auto-juego (filtrado / pesado por resultado) | 0,454 y 0,443 contra su control | no se re-mide | **descartadas por el propio informe** |

Ninguna de las cuatro afirmaciones vivas se cae. La única que baja al re-medirla
es `e20`, y sigue muy por encima de 0,5.

## 2. Qué red: `politica_7d_h384_mejorval`, y en las dos listas

La báscula de redes se invierte con la baraja (`clon-escalado.md` §7), así que el
torneo se corrió en las dos listas candidatas. n=2.000 por celda.

| duelo | c2-alakazam | c1-grimmsnarl |
|---|---|---|
| `d7h384` vs `e20` | **0,584 [0,562, 0,605]** | — |
| `d7h384` vs `d7h192` | **0,589 [0,567, 0,610]** | **0,529 [0,508, 0,551]** |
| `e20` vs `d7h192` | 0,489 [0,467, 0,511] — empate | — |
| `d7h384` vs la red de la ladder | 0,724 [0,704, 0,743] | **0,735 [0,715, 0,754]** |

`d7h384` gana a las otras dos en las dos listas (en c1-grimmsnarl por poco, pero
con el IC entero por encima de 0,5), y `e20` y `d7h192` empatan entre sí. **La
red que se envía es `research/clon/politica_7d_h384_mejorval.npz`** (7 días de
replays, H1=384, checkpoint de mejor validación).

## 3. La combinación: los dos ejes se suman, y se suman en log-odds

| agente (c2-alakazam, contra el clon de la ladder) | n | tasa | IC95 |
|---|---:|---:|---|
| solo red nueva: `d7h384` | 2.000 | 0,724 | [0,704, 0,743] |
| solo búsqueda: `busq(politica.npz)` | 2.000 | 0,709 | [0,688, 0,728] |
| **las dos: `busq(d7h384)`** | **2.000** | **0,859** | **[0,843, 0,873]** |

En log-odds: 0,964 (red) + 0,891 (búsqueda) = **1,855 predicho** contra **1,807
observado** (0,865 predicho contra 0,859 medido). **No hay interferencia
medible**: cada eje aporta lo suyo sobre el otro. Es la misma conclusión que el
informe de auto-juego apuntaba con `ctl2` (`busq(ctl2)` vs el clon de la ladder,
n=2.000: **0,803 [0,785, 0,820]**), con una red mejor y el punto ya cerrado.

Y la comprobación directa, con la búsqueda encendida en los DOS lados —el duelo
más caro de la tanda, 1.200 partidas a ~7 s cada una— **`busq(d7h384)` vs
`busq(politica.npz)`: 0,731 [0,705, 0,755]**, contra el 0,714 que predecía la
aditividad en log-odds. Es decir: cambiar la red debajo de la búsqueda sigue
comprando +0,23 aunque la búsqueda ya esté puesta. Los dos ejes son de verdad
independientes; no es que la búsqueda estuviera tapando los errores de la red
vieja.

## 4. La elección de lista, rehecha con el piloto que se envía

Instrumento: `research/clon/campo_sp.py` — nuestro agente con NUESTRA lista
contra los 12 arquetipos del campo (96,3% de cobertura) **pilotados por el clon
de la ladder**. Es la báscula honesta para esto: el gauntlet clásico pone el
mismo piloto a los dos lados y mide la lista, pero lo que se envía es el par
agente+lista. Comprobación de que los dos instrumentos hablan el mismo idioma:
`campo_sp` con el clon de la ladder a los dos lados da c2-alakazam **0,4634**
frente al **0,4543** del gauntlet — la misma casilla.

### 4.1 Con el piloto de la ladder (n=200/emparejamiento, 2.400 partidas)

| lista | POND | IC95 | PEOR |
|---|---:|---|---|
| c1-grimmsnarl | 0,5505 | [0,5226, 0,5785] | c6-ogerpon 0,070 |
| mia-crustle-tijeras | 0,5240 | [0,4983, 0,5497] | c2-alakazam 0,175 |
| c2-alakazam | 0,4634 | [0,4358, 0,4909] | c1-grimmsnarl 0,315 |

### 4.2 Con la red nueva sin búsqueda (n=200/emparejamiento)

| lista | POND | IC95 | PEOR | peor con peso ≥5% |
|---|---:|---|---|---|
| c1-grimmsnarl | **0,7356** | [0,7127, 0,7585] | c6-ogerpon 0,195 | c5-kangaskhan 0,305 |
| mia-crustle-tijeras | 0,6044 | [0,5802, 0,6286] | c2-alakazam 0,190 | 0,190 |
| c2-alakazam | 0,5785 | [0,5508, 0,6062] | c1-grimmsnarl 0,405 | 0,405 |

### 4.3 Con el piloto que se envía, `busq(d7h384)` (n=150/emparejamiento, 1.800 partidas)

| lista | POND | IC95 | PEOR | peor con peso ≥5% |
|---|---:|---|---|---|
| c1-grimmsnarl | **0,7378** | [0,7091, 0,7665] | c6-ogerpon **0,147** | c5-kangaskhan 0,520 |
| c2-alakazam | 0,7067 | [0,6761, 0,7373] | **c1-grimmsnarl 0,547** | 0,547 |
| mia-crustle-tijeras (propia) | 0,6685 | [0,6420, 0,6951] | c2-alakazam 0,287 | 0,287 |

Casilla a casilla con el piloto final:

| lista | grimm 31% | alak 18% | lopu 13% | drag 8% | kanga 7% | oger 5% | luca 4% | dipp 3,5% | hydr | slow | cynt | zoro |
|---|--|--|--|--|--|--|--|--|--|--|--|--|
| c1-grimmsnarl | 0,700 | 0,833 | 0,833 | 0,913 | 0,520 | **0,147** | 0,873 | 0,847 | 0,540 | 0,973 | 0,860 | 0,960 |
| c2-alakazam | **0,547** | 0,900 | 0,587 | 0,833 | 0,627 | 0,787 | 0,860 | 0,840 | 0,833 | 0,987 | 0,740 | 0,920 |
| mia-crustle-tijeras | 0,847 | **0,287** | 0,373 | 0,900 | 0,680 | 0,947 | 0,873 | 0,460 | 0,933 | 0,940 | 0,833 | 0,933 |

### 4.4 La lista propia, con el piloto final: qué cuesta exactamente

`mia-crustle-tijeras` sube con la búsqueda igual que las demás (0,6044 → 0,6685) y su
agujero estructural sigue donde el informe de la lista propia dijo que estaría: los dos
arquetipos del campo cuya condición de victoria **no** lleva Rule Box, contra los que
*Mysterious Rock Inn* no aplica por definición — Alakazam (18,25% del campo) **0,287** y
Dipplin (3,5%) 0,460. A cambio bate a los tres pilares del campo con ex: Grimmsnarl
0,847, Ogerpon 0,947, Hydrapple 0,933.

El coste medido de jugarla en vez de `c2-alakazam`, con el piloto que se envía:
**−0,038 de POND** (IC solapados, por debajo de la resolución declarada de la báscula)
y **−0,260 de suelo** (0,547 → 0,287). Es decir: la lista propia no cuesta media, cuesta
consistencia — que es justo el 70% del Model Score. **Es una decisión del propietario**,
porque lo que compra es el 20% de Deck Score (concepto propio, 34-37 cartas de distancia
a cualquier lista del censo, 0 Pokémon de dos premios, 0 cartas muertas) y eso no lo
puede arbitrar una báscula de winrate.

**Lo que decide:** con el piloto final las dos listas empatan en media (0,7378
contra 0,7067, IC solapados) y se separan en el suelo. **`c2-alakazam` no tiene
un solo emparejamiento por debajo de 0,50** — su peor casilla de las doce es
0,547. `c1-grimmsnarl` tiene media un pelo mejor y un agujero de 0,147 contra
Ogerpon (5,0% del campo) más dos casillas en 0,52-0,54.

Y un aviso que hay que anotar: **el orden entre listas NO se invierte al cambiar
de piloto esta vez** (c1-grimmsnarl ≥ tijeras ≥ c2-alakazam con los tres
pilotos), pero **las distancias sí cambian mucho**. Con la red sola,
c1-grimmsnarl saca +0,157 a c2-alakazam; con la búsqueda encima, +0,031 y sin
significación. La búsqueda le compra a `c2-alakazam` casi todo lo que le faltaba
(+0,128 de POND, y su peor casilla sube 0,405 → 0,547). PKM-012 sigue vigente
como advertencia metodológica: **hay que re-medir la lista con el piloto que se
envía**, aunque en este salto concreto el ganador por media no cambie.

## 5. Auditoría del candidato final

`scratchpad/final/auditar2.py`, 500 partidas repartidas por los 12 arquetipos
(rival = clon de la ladder con la lista del arquetipo), un proceso, BLAS a 1
hilo, asientos intercambiados.

| | `busq(d7h384)` + c2-alakazam | `busq(d7h384)` + c1-grimmsnarl |
|---|---|---|
| estados | **1.000/1.000 DONE** | **1.000/1.000 DONE** |
| anomalías (INVALID/ERROR/TIMEOUT/excepción) | **0** | **0** |
| acciones ilegales · fallbacks · determinizaciones fallidas · errores de step | **0 · 0 · 0 · 0** | **0 · 0 · 0 · 0** |
| decisiones | 25.468 | 38.166 |
| decisiones que se buscan | 39,9% | 40,1% |
| de las buscadas, cuántas cambian la jugada | 54,0% | 54,3% |
| ms por decisión: media / p95 / p99 / máx | 32,0 / 100,7 / 115,9 / **193,3** | 31,3 / 92,3 / 100,0 / **147,8** |
| reloj de la PEOR partida | **3,88 s** | **5,23 s** |
| margen sobre el banco de 600 s | **×155** | **×115** |
| tasa de victoria (media sin ponderar de los 12) | 0,944 | 0,906 |

El banco de producción es de 600 s por agente y partida y en producción hay ~1,6
vCPU; aquí la medida es de **un solo hilo** compitiendo con otros seis procesos
en la máquina, o sea el escenario malo. La decisión más lenta de 38.166 tardó
0,193 s.

## 6. Empaquetado

`empaquetar.py --politica research/agentes/clon_busq.py` con los OCHO ficheros de
apoyo: `rasgos.py`, `features_v2.py`, `features.py`, `heuristico.py`, `mcts.py`,
`tracker.py`, `search_wrapper.py` y `politica.npz`. **Los pesos hay que copiarlos
con el nombre `politica.npz`**: en el paquete no hay variables de entorno y tanto
`clon.py` como `clon_busq.py` resuelven el fichero por nombre con `_busca()`.

| paquete | tamaño |
|---|---|
| `envios/busq-d7h384-c2-alakazam.tar.gz` | 1,14 MiB (límite 197,7) |
| `envios/busq-d7h384-c1-grimmsnarl.tar.gz` | 1,14 MiB |

Verificación de los dos en un directorio limpio (`scratchpad/verifica_tar.py`),
descomprimiendo el tar y ejecutando `main.py` con `compile`+`exec` **sin
`__file__`** y el repo fuera de `sys.path`:

- 21 entradas, **0 código de terceros**;
- catálogo **completo**: 1.267 cartas · 1.556 ataques · 1.267 textos de trainer ·
  1.267 de habilidad (y 1.267/1.556 también por la vía de `features_v2`);
- pesos dentro y con la forma correcta: `W1s (114, 384)`, `W2 (384, 192)` — es
  decir, viaja la red H1=384 y no otra;
- **15 partidas, 0 estados anómalos** en cada paquete.

Y la comprobación que faltaba: **que la búsqueda de verdad se ejecute dentro del
paquete**. Seis partidas cargadas con `exec` sin `__file__` desde el tar
descomprimido: 353 decisiones, **123 buscadas (34,8%)**, 62 cambian la jugada,
`det_fallida 0 · err_step 0 · excepcion 0 · ilegal 0`. La vía 3 no se degrada en
silencio al empaquetarla.
