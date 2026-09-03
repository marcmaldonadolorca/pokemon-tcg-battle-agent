# El bug de la promoción (1,3) y el criterio de búsqueda (1,7)

Fecha: 2026-08-11. Piezas: `research/replays/confirma_bug13.py` (evidencia del bug),
`research/agentes/heuristico_busq.py` (las dos palancas),
`research/agentes/variantes/gen_wrappers_busq.py` (los módulos que mide `duelo.py`),
`research/duelo.py` (la báscula + contador de ilegales + contador de USOS).

Dos encargos en una tanda: un **bug real** en el select `(1,3)` (promoción del activo) y
la **segunda fuga por volumen**, `(1,7)` (búsqueda en mazo, 23.509 decisiones = 15,6% del
total). Los dos van en el mismo módulo con **interruptores independientes**
(`FIX_PROMO`, `BUSQ_CRITERIO`), apagados los dos → v2 exacto (control verificado).

**Resumen por delante:**

| resultado | medida |
|---|---|
| 🐛 El bug de `(1,3)` es real, y peor de lo descrito | v2 acierta el Pokémon **0 de 1.317 veces** en la rama del rival |
| ❗ El discriminante `effect is None` es **incorrecto** | 125 de 483 selects CON efecto listan MI banca (Switch, Kieran, TR Giovanni) |
| ⚪ Arreglarlo es **invisible en mega-lucario** | 0,4835 [0,4617, 0,5054] — toca el 1,5% de las decisiones |
| ✅ **Y vale +11,7 pp en hops-snorlax** | **0,6165 IC95 [0,5950, 0,6376]** en muestra de confirmación (n=2.000) |
| ✅ Contra un rival que gustea (hops-snorlax) | **+14,1 pp** sobre el control, z=9,02 |
| ✅ `BUSQ_CRITERIO` en mega-lucario | 0,5230 [0,5011, 0,5448] en confirmación — pasa… |
| ⚠️ …pero no mejora la regla que ya estaba validada | 0,5075 [0,4856, 0,5294] contra `heuristico_busqueda.py` |
| ✅ Legalidad | **0 ilegales y 0 fallbacks en 27.000 partidas** (54.000 estados) |

---

## 1. El bug de `(1,3)`, confirmado y ampliado

### 1.1 Lo que dice el código

`heuristico._elige_cartas`, rama `area == 5` (líneas 420-429 de `heuristico.py`):

```python
if area == 5:  # nuevo activo tras KO/retirada: el más cargado/peligroso
    def puntua(o):
        pkm = _pokemon_en(5, o.get("index"), yo)      # <-- `yo` SIEMPRE
        ...
        return (10 * len(pkm.get("energies") or []) + ...)
    mejores = sorted(range(len(ops)), key=lambda i: -puntua(ops[i]))
    return mejores[:max(sel["minCount"], 1)]
```

`yo = cur["players"][me]`. No hay ninguna lectura de `option[i]["playerIndex"]`, que es
el campo que dice **de quién es la banca** que el motor está listando. Un `(1,3)` abierto
por Boss's Orders lista la banca del **RIVAL**, y su `index` es un índice sobre esa banca.

O sea que el diagnóstico original se quedaba corto: no es que v2 aplique «el mejor» donde
tocaba «el peor». Es que v2 **puntúa Pokémon de mi banca y devuelve ese índice sobre la
banca del rival**. Con la banca propia más corta que la del rival, `_pokemon_en` devuelve
`None` → puntuación 0,0 para todos → el orden lo rompe el índice, que es arbitrario.

### 1.2 Lo que dicen los replays

`research/replays/confirma_bug13.py`, 300 episodios de la ladder (semilla independiente
de la que usó `promocion_expertos.py`, para no reciclar la misma muestra):

**Quién es el dueño de la banca listada, cruzado con `effect`:**

| `effect` | banca listada | n |
|---|---|---|
| `None` | **MIA** | 646 |
| no nulo | **MIA** | **125** |
| no nulo | RIVAL | 358 |

Desglose de esos 125: Switch (1123) 45, Abra (741) 50, Dunsparce (305) 9, Buneary (848) 9,
TR Giovanni (1218) 5, Prime Catcher (1088) 4, Kieran (1191) 2, Bayleef (709) 1.

> **Corrección a la nota `descartes-y-selects.md` §5.3 y a `motor-mecanica.md`:** el
> discriminante **no es `effect is None`**. El 25,9% de los selects con efecto siguen
> siendo mi propia banca (todas las cartas «cambia tu activo por uno de tu banca»).
> Separar por `effect` invertiría el signo en esos 125 casos, que es exactamente el error
> que se pretende arreglar. El discriminante robusto es **`option[*].playerIndex == yourIndex`**
> — que es, además, la regla general que ya enunciaba `motor-mecanica.md`: un select type 1
> se lee por `(area, min==max, effect.id, playerIndex)`, nunca por el `context`.

**El bug, medido opción a opción** (`_pokemon_en(5, idx, yo)` vs. el Pokémon que el motor
realmente referencia):

| banca listada | v2 resuelve el correcto | v2 devuelve `None` | v2 resuelve **otro** Pokémon |
|---|---|---|---|
| MIA | **2.935** | 0 | 0 |
| RIVAL | **0** | 328 | 989 |

**Cero de 1.317.** En la rama propia v2 es correcto siempre; en la del rival no acierta
jamás el objeto que puntúa.

**Acuerdo con el experto y signo** (solo casos con ≥2 opciones y con variación del rasgo):

| banca | n | acuerdo v2 | experto elige MÁX energías | experto elige MÍN energías |
|---|---|---|---|---|
| MIA | 723 | **72,3%** | **81,0%** | 16,2% |
| RIVAL | 318 | **31,8%** | 33,3% | **57,2%** |

El signo es opuesto, como se sospechaba, y además la rama del rival está por debajo de lo
que daría elegir al azar informado. Ejemplo real (episodio 91151819, paso 95, turno 9,
Boss's Orders): banca rival = [848 1e 70hp, 66 0e 140hp, 848 0e 70hp, 66 0e 140hp,
860 0e 70hp]; el experto arrastra el índice 4 (860, sin energía, 70 hp) y v2 el índice 1.

### 1.3 Qué dice el experto que hay que hacer en cada rama

Sobre la muestra grande (`data/replays/promocion_expertos.pkl`, 1.884 decisiones):

| rama | señal | el experto la maximiza |
|---|---|---|
| **MIA** | **puede atacar YA** | **91,7%** (n=775) — elegido 65,3% vs. disponible 24,0% |
| MIA | energías | 79,1% |
| MIA | es *ex* | 82,2% — elegido 60,3% vs. disponible 29,7% |
| **RIVAL** | es *ex* | **66,6%** (2 premios) — elegido 35,7% vs. disponible 20,6% |
| RIVAL | puede atacar ya | lo **minimiza** 60,8% |
| RIVAL | energías | lo minimiza 51,9% |

Traducción: en mi banca promuevo **al que ya puede atacar** (señal dominante, y v2 solo la
aproxima por «lleva más energías»); en la del rival arrastro **la pieza gorda que todavía
no puede atacar**, que se queda clavada en el puesto activo perdiendo turnos.

---

## 2. Qué hace cada interruptor

`research/agentes/heuristico_busq.py` = copia de `heuristico.py` (que NO se toca) con dos
palancas. Se leen en cada decisión, así que un wrapper puede fijarlas como atributo de
módulo (patrón de `gen_wrappers.py`). Con las dos apagadas el módulo es v2 exacto:
control `bq_ctrl_mega_lucario` vs `v2_mega_lucario` = **0,500 con USOS todos a cero**.

### `FIX_PROMO`

1. Despacha por `option[*].playerIndex`, no por `effect`.
2. Banca propia (`_promo_propia`): dominante **«puede pagar YA algún ataque»** — con
   `_pagable`, el casamiento real de coste por tipo que v2 no tiene y `heuristico_v3.py`
   sí — y entre los que pueden, el que más pega **con lo que lleva puesto**; entre los que
   no, el que menos energías le faltan.
3. Banca del rival (`_promo_rival`): KO este turno ponderado por premios (×2 si es *ex*),
   si no la pieza que aún **no** puede atacar, y de desempate la más herida.
4. Si los índices no caen en la banca esperada, no inventa: devuelve la respuesta de v2 y
   lo cuenta en `USOS["promo_no_resuelve"]` (0 en todas las tiradas).

**Limitación conocida, y su arreglo exacto.** Cuatro selects distintos comparten la forma
literal `(min=1, max=1, area=5, option.type=3)` — censo `censo_selects_azar.pkl`, campo
`forma`: `(1,3)` n=1.982, `(1,14)` Dragapult ex n=1.620, `(1,16)` Munkidori n=705,
`(1,17)` Wally's Compassion n=71. Los tres últimos también listan banca del rival, pero
NO son «a quién arrastro» sino «dónde pongo contadores de daño». El discriminante genérico
que los separa **sin usar el `context`** es `remainDamageCounter`, que en los de daño
cuenta atrás y en `(1,3)` es 0. Ninguna de nuestras dos listas lleva Munkidori, Dragapult
ex ni Wally's Compassion (`descartes-y-selects.md` §2: son 100% PROPIO, no se ven si la
carta no es tuya), así que la rama no se puede pisar en estas medidas — pero si una lista
futura los incluye, la rama del rival necesita el guardia
`sel.get("remainDamageCounter", 0) == 0` antes de aplicarse.

### `BUSQ_CRITERIO`

Reutiliza el término de jugabilidad de `heuristico_busqueda.py` —que ya pasó el gate con
0,538 IC95 [0,520, 0,556] sobre 3.000 partidas— y lo convierte en un criterio de
**necesidad calculada del estado** en vez de una lista fija de preferencias
(`_necesidades` se calcula una vez por select, `_util_busq` una vez por opción):

| término | peso | condición medida en el estado |
|---|---|---|
| evolución | **+3,5** / +0,8 / −2,5 | su base está en juego / en la mano / huérfana |
| básico | +2,5 / +1,5 / +0,6 / −2,5 | banca con 0-1 / 2 / 3-4 Pokémon / llena |
| energía | +2,5 (+1,0) / −1,5 | no adjunté aún y mi mejor atacante no llega (y es su tipo) / no |
| buscador | +1,2 / 0,0 | el setup NO está hecho / ya pego |
| robo | +0,8 / 0,0 | mano ≤3 / mano larga |
| no jugable | −2,5 | nuestra política no tiene rama que juegue esa carta |
| duplicada | −0,8 por copia | ya la llevo en la mano |

El defecto que corrige es el mismo que ya identificó la tanda anterior y sigue vivo en v2:
`_util` es codicioso de estadísticas y con mega-lucario saca **siempre Mega Lucario ex**
aunque no haya un Riolu en juego que evolucionar — una carta muerta en la mano.

---

## 3. Antes de medir: ¿la medición mide?

Lección propia (`verificar-que-la-verificacion-mide`): el módulo lleva contadores `USOS`
que `duelo.py` agrega, y se miraron **antes** de gastar las tiradas grandes. Sonda de
60 partidas por configuración:

| configuración | `promo_mia` | cambia | `promo_rival` | cambia | `busq` | cambia |
|---|---|---|---|---|---|---|
| ambas, mega-lucario vs v2 | 116 | **2 (1,7%)** | **0** | 0 | 171 | **58 (33,9%)** |
| promo, mega-lucario vs gusteador | 130 | **4 (3,1%)** | **0** | 0 | — | — |
| promo, **hops-snorlax** vs v2 | 171 | **67 (39,2%)** | **89** | **54 (60,7%)** | — | — |

Tres hechos que cambian el diseño de la medición:

1. **La rama del rival no se puede pisar con mega-lucario.** Se abre solo cuando el
   agente **juega él** una carta de arrastre, y las dos Boss's Orders de la lista están
   entre las 10 cartas que la política de v2 **no sabe jugar nunca**
   (`descartes-y-selects.md` §3). Que el rival gustee **no** la abre: el `(1,3)` de
   Boss's Orders lo recibe **quien la juega**, no la víctima (100% PROPIO en el censo).
   Por eso medir contra `gusteador_mega_lucario` deja el contador igual de a cero: es el
   mismo tipo de espejo ciego que se detectó con la banca, pero el ciego aquí no es el
   rival, es **nuestra propia lista**.
2. **Sí se pisa con hops-snorlax**, y mucho: 89 usos por cada 60 partidas. No por Boss's
   Orders (tampoco la juega) sino por **Hop's Dubwool (310)**, cuya habilidad *Defiant
   Horn* se dispara al evolucionar — y evolucionar sí lo hace la política. Es decir: la
   rama vive o muere según la LISTA, no según el rival.
3. **En mega-lucario, `FIX_PROMO` toca 2 decisiones de cada 116.** Su banca es
   Riolu / Mega Lucario ex / Regirock ex, y ahí «el que lleva más energías» y «el que
   puede atacar ya» casi siempre son el mismo Pokémon. Una tirada de n=2.000 sobre
   ~67 decisiones cambiadas no puede distinguir nada: se mide igual, pero el resultado
   esperado es empate **por construcción**, y así hay que leerlo.

---

## 4. Medición

`research/duelo.py` (arena + ilegales + USOS), misma lista a los dos lados, asientos
intercambiados, 3 procesos, **n=2.000** por celda. Rival por defecto = `heuristico.py` (v2),
el piloto de los dos envíos vivos.

### 4.1 Espejo contra v2

| tirada | baraja | n | tasa | IC95 | ilegales | decisiones cambiadas |
|---|---|---|---|---|---|---|
| `BUSQ_CRITERIO` | mega-lucario | 2.000 | **0,5320** | **[0,5101, 0,5538]** | 0 | 2.040 de 6.550 (31,1%) |
| `FIX_PROMO` | mega-lucario | 2.000 | 0,4835 | [0,4617, 0,5054] | 0 | **59 de 4.056 (1,5%)** |
| las dos | mega-lucario | 2.000 | **0,5455** | **[0,5236, 0,5672]** | 0 | 81 + 2.203 |
| **`FIX_PROMO`** | **hops-snorlax** | 2.000 | **0,6195** | **[0,5980, 0,6405]** | 0 | **3.559 de 8.322 (42,8%)** |
| `BUSQ_CRITERIO` | hops-snorlax | 2.000 | 0,4870 | [0,4651, 0,5089] | 0 | 1.509 de 6.702 (22,5%) |

### 4.2 Contra un rival que SÍ gustea (`heuristico_v3` con `GUSTING=True`)

Contra un rival fijo, «A vs gusteador» no es un A/B: hace falta el **control** «v2 vs
gusteador» y contrastar las dos proporciones (Wald sobre p₁−p₂, `scratchpad/bq/contraste.py`).

| baraja | `FIX_PROMO` vs gusteador | v2 vs gusteador | diferencia | veredicto |
|---|---|---|---|---|
| mega-lucario | 0,4555 [0,4338, 0,4774] | 0,4855 [0,4636, 0,5074] | **−0,0300** [−0,0609, +0,0009] z=−1,90 | **NO significativa** |
| **hops-snorlax** | **0,6175** [0,5960, 0,6386] | 0,4770 [0,4552, 0,4989] | **+0,1405** [+0,1100, +0,1710] **z=9,02** | **significativa** |

Lo que hay que leer aquí, y no es lo que la tarea anticipaba: el rival que gustea **no**
es lo que hace visible el arreglo. Lo que lo hace visible es que **nuestra propia lista
sepa abrir la rama** (§3). Con mega-lucario el contador de `promo_rival` sigue a cero
contra el gusteador y el resultado es un empate estadístico (con la puntual por debajo:
z=−1,90 en muestra de descubrimiento, que por nuestra propia regla **no es un hallazgo**).
Con hops-snorlax el arreglo vale +14,1 pp contra un rival que gustea — algo **más** que
los +11,95 pp contra el v2 pasivo, lo cual es coherente: un rival que arrastra tu banca
provoca más KO y por tanto más promociones que decidir.

### 4.3 ¿Aporta algo el criterio de necesidad sobre la regla ya validada?

`BUSQ_CRITERIO` (nuevo) contra `heuristico_busqueda.py` (el término de jugabilidad binario
que ya pasó el gate con 0,538 [0,520, 0,556] sobre 3.000 partidas), mega-lucario:

```
n=2.000   tasa 0,5075   IC95 [0,4856, 0,5294]   -> sin diferencia significativa
```

**No aporta.** Las dos reglas miden lo mismo contra v2 (0,532 vs 0,538, IC solapados) y
empatan entre sí. Todo el valor de `(1,7)` estaba ya capturado por el término binario
«¿puedo jugar esta carta YA?»; los siete términos ponderados por necesidad (tipo de
energía, banca escalada, buscador según setup, robo según mano) **no añaden nada medible**.
Por `codigo-minimo`, la que debería sobrevivir es la simple, que ya está validada con más
muestra.

### 4.4 Muestras de confirmación independientes

Regla de decisión fijada antes de tirarlas: IC95 con límite inferior > 0,5 sobre la
muestra **nueva**, y nada más.

| tirada | n | tasa | IC95 | veredicto |
|---|---|---|---|---|
| `BUSQ_CRITERIO` vs v2, mega-lucario (confirmación) | 2.000 | **0,5230** | **[0,5011, 0,5448]** | **PASA** |
| `FIX_PROMO` vs v2, hops-snorlax (confirmación) | 2.000 | **0,6165** | **[0,5950, 0,6376]** | **PASA** |

Las dos reproducen su muestra de descubrimiento (0,5320 y 0,6195). El agregado
descubrimiento+confirmación de la búsqueda es 0,5275 [0,5120, 0,5429] sobre 4.000
partidas, pero **está contaminado por parada opcional** (la confirmación se lanzó *porque*
la primera salió bien): el número que vale es el de la confirmación sola, 0,5230.

### 4.5 Legalidad

Requisito: cero ilegales en 500 partidas de la mejor variante. Se cumple con margen —
`bq_ambas` con las dos palancas puestas, 500 partidas por baraja:

| tirada | partidas | estados | `INVALID`/`ERROR` | `FALLBACKS` |
|---|---|---|---|---|
| `bq_ambas` mega-lucario | 500 | 1.000 DONE | **0** | **0** |
| `bq_ambas` hops-snorlax | 500 | 1.000 DONE | **0** | **0** |

Y sobre **las 27.000 partidas de toda la tanda** (13 celdas, 54.000 estados de jugador):
**0 estados distintos de DONE y 0 fallbacks de ningún tipo** — ni excepción, ni acción
ilegal, ni select desconocido, ni fase sin acción. `USOS["promo_no_resuelve"]` también a 0,
o sea que el despacho por `playerIndex` resolvió el 100% de los índices.

---

## 5. Veredicto

| interruptor | baraja | veredicto |
|---|---|---|
| **`FIX_PROMO`** | **hops-snorlax** | ✅ **ENTRA. 0,6165 IC95 [0,5950, 0,6376]** en muestra de confirmación (+11,7 pp). Contra un rival que gustea, **+14,1 pp** (z=9,02) |
| `FIX_PROMO` | mega-lucario | ⚪ **NULO por construcción**: solo toca 1,5% de las decisiones. 0,4835 [0,4617, 0,5054]. Ni gana ni rompe |
| **`BUSQ_CRITERIO`** | **mega-lucario** | ✅ **PASA. 0,5230 IC95 [0,5011, 0,5448]** en confirmación (+2,3 pp)… |
| `BUSQ_CRITERIO` | vs regla ya validada | ⚠️ …pero **empata con `heuristico_busqueda.py`** (0,5075 [0,4856, 0,5294]): no aporta nada sobre el término binario de jugabilidad que ya estaba medido |
| `BUSQ_CRITERIO` | hops-snorlax | ⚪ 0,4870 [0,4651, 0,5089]: nulo, como predecía el mecanismo (baraja sin línea de evolución) |

**El titular es `FIX_PROMO` en hops-snorlax: +11,7 pp confirmados, el efecto más grande
medido en el proyecto** — casi el triple que la regla de búsqueda (+3,8 pp), que hasta hoy
era la única candidata que había pasado el gate. Y no es una heurística nueva: es **un bug
arreglado**. v2 no acertaba el Pokémon que puntuaba ni una sola vez de 1.317 en esa rama.

### Lo que rompe el patrón de los seis negativos

Las seis candidatas anteriores (ISMCTS, ISMCTS+valor, retirada, gusting, greedy sobre la
red, banca, descartes) eran **política nueva**: apuestas sobre cómo jugar mejor. Esta es
**un defecto de lectura del contrato del motor**. La lección que deja no es «prueba más
heurísticas» sino: **antes de inventar política, comprueba que la que hay lee bien la
observación**. El diagnóstico contra expertos señalaba `(1,3)` como una fuga menor
(2,4% de las decisiones, 59,9% de acuerdo) y resultó ser el mayor rendimiento por línea
de código de toda la tanda, porque el 31,8% de acuerdo de una de sus dos ramas estaba
escondido dentro de un promedio con la otra, que acuerda 72,3%.

### Lo que NO se recomienda, y por qué

1. **No subir nada todavía.** Falta pasarlo por el **gauntlet ponderado de campo**
   (`research/gauntlet.py`), que es la báscula que ordena igual que la ladder; el espejo
   solo dice que le gana a una copia de sí mismo. La decisión de tocar un envío es del
   propietario.
2. **No meter `BUSQ_CRITERIO` en su forma actual.** Pasa el gate, pero empata con
   `heuristico_busqueda.py`, que es más simple y tiene más muestra detrás (3.000 partidas).
   Si entra la búsqueda, que entre la versión simple.
3. **No reabrir «que el agente juegue Boss's Orders» pensando que ahora sí.** Es la
   combinación que ya mide `heuristico_v3` con `GUSTING=True`, que **incluye** el mismo
   arreglo del objetivo (líneas 691-703 de `heuristico_v3.py`) y midió 0,495 (n=1.500).
   Dato lateral de esta tanda, con más muestra: el gusteador contra v2 gana 0,5145
   IC95 [0,4926, 0,5364] sobre 2.000 partidas — sigue **sin** ser significativo. No es
   un hallazgo.
4. **Ojo con `promo_vs_gust_ML` = −3,0 pp (z=−1,90).** Es muestra de descubrimiento y por
   nuestra propia regla **no es un hallazgo**; además es mecánicamente imposible que el
   arreglo haga daño ahí (toca 91 decisiones de 3.811 y ninguna de la rama del rival).
   Si alguien quiere tratarlo como regresión, hace falta una muestra de confirmación.

### Lo que queda como valor permanente

1. **`descartes-y-selects.md` §5.3 y `motor-mecanica.md` quedan corregidas**: el
   discriminante de `(1,3)` **no es `effect is None`** (falla en el 25,9% de los selects
   con efecto), es `option[*].playerIndex`.
2. **La rama vive o muere según TU lista, no según el rival.** Un `(1,3)` de banca rival
   solo lo recibe quien juega la carta de arrastre. Medir contra un rival que gustea no
   hace visible el arreglo; lo hace visible llevar una carta de arrastre **que la política
   sepa jugar** — en hops-snorlax es Hop's Dubwool (310), que arrastra al **evolucionar**,
   y evolucionar sí lo hace la política.
3. **`research/replays/confirma_bug13.py`**: reutilizable para cualquier select type 1
   sobre `area 5` — dice si la política resuelve el Pokémon que el motor referencia o
   simplemente devuelve un índice con sentido para otra zona.
4. Cuatro selects distintos comparten la forma `(1,1,area 5,type 3)`; separarlos exige
   `remainDamageCounter` (§2, limitación conocida).
