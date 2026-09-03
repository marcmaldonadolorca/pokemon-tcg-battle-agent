# heuristico v5 — qué sobrevivió al gate, qué mide la combinación y qué se envía

Fecha: 2026-08-11. Piezas: `research/agentes/heuristico_v5.py` (el candidato, generado por
`scratchpad/v5/gen_v5.py`), `scratchpad/v5/campo.py` + `compara_campo.py` (prueba de
campo), `scratchpad/v5/auditoria.py` (consistencia), `scratchpad/v5/valida_tar.py`
(catálogo dentro del tar). Logs crudos: `scratchpad/v5/*.log|json`.

Encargo: quedarse **solo con lo que gana de verdad**, combinarlo, verificarlo contra el
campo y dejar el envío listo. Nada entró por informe: todo lo que se declaraba ganador se
volvió a medir con **muestra fresca**.

**Resumen: entran TRES reglas; la combinación es aditiva (+10,2 pp en espejo, +4,3 pp
contra el campo real, z=4,6); el paquete está construido y validado.** Y el hallazgo que
más vale de la tanda no es ninguna de las tres, sino por qué dos de ellas estaban
enterradas: **se habían medido con la baraja equivocada.**

| | resultado |
|---|---|
| Candidatas re-medidas por mí con muestra fresca | 4 — las 4 reproducen |
| **Entran en el envío** | **retirada · criterio de búsqueda `(1,7)` · gusting** |
| No entran | FIX_PROMO, descartes `(1,8)`, promoción, secuenciación (×4), banca (×5), cobertura (×4) |
| v5 vs v2 (espejo mega-lucario) | **0,6020 IC95 [0,5844, 0,6194]** n=3.000 |
| v5 vs v2 (campo ponderado real) | **+0,0427 IC95 [+0,0245, +0,0608]** z=4,61 |
| Peor emparejamiento (lo que puntúa la rúbrica) | **0,289 → 0,387** |
| Auditoría | 500/500 DONE, 0 ilegales, 0 fallbacks, margen ×6.893 sobre el banco |
| Paquete | `envios/heuristico-v5-mega-lucario.tar.gz` (0,5 MiB), catálogo completo |

---

## 1. El nulo del banco: 0,5005 con n=8.000

Antes de creerse ninguna diferencia hay que saber cuánto marca la báscula cuando **no** hay
diferencia. Tres espejos independientes, mega-lucario a los dos lados contra
`research/agentes/heuristico.py`:

| control | n | tasa | IC95 |
|---|---:|---:|---|
| `heuristico.py` contra sí mismo (`ruido_suelo`) | 4.000 | 0,5018 | [0,4863, 0,5172] |
| `heuristico_v3.py` con las palancas apagadas | 2.000 | 0,5110 | [0,4891, 0,5329] |
| **`heuristico_v5.py` con las TRES apagadas** | 2.000 | 0,4875 | [0,4656, 0,5094] |
| **agregado** | **8.000** | **0,5005** | **[0,4895, 0,5115]** |

El tercero es el que importa para el envío: **el fichero que se sube, con sus palancas
apagadas, es el v2**. Y no solo medido — también por construcción: el hash del AST de cada
función de `heuristico_v5.py` es idéntico al de `heuristico_v3.py` salvo `_elige_cartas` y
las cuatro funciones nuevas de la búsqueda (que son a su vez idénticas a las de
`heuristico_busq.py`); y `heuristico_v3.py` solo se separa del v2 por llamadas que
devuelven `None` con las palancas apagadas. Los contadores `USOS` salen todos a cero en ese
control, que es la comprobación de que estaban de verdad apagadas.

## 2. Verificación: reportado contra medido por mí

Protocolo idéntico en todas: `mega-lucario` a los dos lados, asientos intercambiados,
`--procs 3`, contra `research/agentes/heuristico.py`, IC de Wilson. **Muestra fresca**: no
se reutilizó ni una partida de las tiradas que produjeron el número reportado.

| candidata | reportado | mi réplica (n=3.000) | ¿reproduce? | agrupado (todas las muestras) |
|---|---|---|---|---|
| `(1,7)` búsqueda **vieja** (`HB_BUSQUEDA`) | 0,538 [0,520, 0,556] n=3.000 | **0,5220 [0,5041, 0,5398]** | sí | 0,5300 [0,5174, 0,5426] n=6.000 |
| `(1,7)` **`BUSQ_CRITERIO`** | 0,532 [0,510, 0,554] n=2.000 | **0,5387 [0,5208, 0,5564]** | sí | 0,5360 [0,5222, 0,5498] n=5.000 |
| **`RETIRADA`** | 0,540 [0,524, 0,555] n=4.000 | **0,5283 [0,5104, 0,5461]** | sí | 0,5306 [0,5196, 0,5417] n=7.800 |
| **`GUSTING`** | 0,514 [**0,4988**, 0,530] n=4.000 → *fallaba* | **0,5267 [0,5088, 0,5445]** | sí, y **pasa** | 0,5241 [0,5130, 0,5352] n=7.800 |

**Las cuatro reproducen.** Tres matices que hay que decir:

1. **Tres de las cuatro réplicas caen por debajo del número reportado.** Es lo que se
   espera de la *maldición del ganador*: el número que se publica es el de la tirada que se
   decidió publicar. Ninguna se cae del gate al replicar, pero la lectura sana es que el
   efecto real de cada palanca está más cerca del agrupado (~+2,5 a +3,5 pp) que del
   titular.
2. **Las dos reglas de `(1,7)` ocupan el MISMO hueco** (la rama `area == 1` de
   `_elige_cartas`): no se suman, se eligen. `BUSQ_CRITERIO` gana en mi réplica (0,5387 vs
   0,5220) y en el agrupado (0,5360 vs 0,5300), pero la diferencia **no es significativa**
   (z ≈ 1,3), así que la decisión no se toma solo con el número: se toma con el mecanismo.
   La vieja suma una lista fija de preferencias; `BUSQ_CRITERIO` calcula la necesidad **del
   estado** (`_necesidades`) — cuánta banca queda, si ya adjunté energía, si la base de la
   evolución está en juego o en la mano. Es la que tiene alguna posibilidad de transferir a
   otra lista. **Entra `BUSQ_CRITERIO`.**
3. **`GUSTING` estaba a 0,0012 de quedar enterrada.** Ver §3, que es la parte de esta nota
   que hay que leer aunque no se lea el resto.

### Lo que NO entra

| candidata | medida | veredicto |
|---|---|---|
| `FIX_PROMO` (bug del `(1,3)`) | 0,4835 [0,4617, 0,5054] n=2.000 | no entra **con esta baraja** — §6 |
| descartes `(1,8)` | 0,484 [0,463, 0,505] n=2.100 | no |
| promoción tras KO | 0,488 [0,463, 0,513] n=1.500 | no |
| secuenciación `B`/`E` | 0,4797 [0,4639, 0,4956] n=3.800 | **peor, significativo** |
| secuenciación `A` (atacar último) | 0,5052 [0,4931, 0,5172] n=6.600 | empate |
| banca (5 configuraciones) | la mejor 0,509 [0,496, 0,521] n=6.000 | no |
| cobertura: `recupera` / `switch` / `tool` / `estadio` | 0,5145 / 0,5080 / 0,5110 / 0,5035, todas n=2.000 | no |

Estas no se re-midieron: se citan de las tandas que las produjeron. La regla aplicada es
asimétrica a propósito — **lo que se declara ganador se replica antes de subirlo; lo que se
declara perdedor se acepta** — porque un falso negativo cuesta una mejora y un falso
positivo cuesta el envío. La excepción fue `GUSTING`, y por eso mismo apareció.

## 3. Lo importante: dos palancas estaban enterradas por la BARAJA, no por el dato

`PKM-009` (2026-08-10) cerró retirada y gusting como «dos negativos medidos»: 0,476 y
0,495. Los números eran correctos. Lo que estaba mal era el **alcance**: se midieron con
`hops-snorlax`, y el mismo día se decidió (PKM-010) que la baraja que va en serio es
`mega-lucario`. Nadie volvió a medirlas.

| palanca | hops-snorlax (PKM-009) | mega-lucario (hoy, n=7.800) |
|---|---|---|
| `RETIRADA` | 0,476 [0,451, 0,501] | **0,5306 [0,5196, 0,5417]** |
| `GUSTING` | 0,495 [0,469, 0,520] | **0,5241 [0,5130, 0,5352]** |

No es una contradicción, es **dependencia de lista**, y las dos direcciones están medidas.
La propia nota del v3 lo explicaba sin saberlo: el gusting no rendía porque «el v2 ya mata
de un golpe con Snorlax» — que es una propiedad de *hops-snorlax*, no de la política.
`mega-lucario` no remata de frente igual, así que arrastrar sí paga. Y la retirada perdía
porque descarta energía; en `mega-lucario` Aura Jab la recarga desde el descarte.

**Y `GUSTING` casi se pierde otra vez, hoy y por lo contrario.** Su confirmatoria de
n=4.000 dio 0,5142 con límite inferior **0,4988**: fallaba el gate por 0,0012. Agrupada con
su piloto de n=800 habría pasado (0,5225), pero ese agrupado está **contaminado por parada
opcional** — la tirada grande se lanzó *porque* la pequeña salió bien — que es exactamente
el error documentado en `descartes-y-selects.md` §6. En vez de elegir el agrupado que
convenía, se tiró una **tercera muestra fresca** de n=3.000: **0,5267 [0,5088, 0,5445]**.
Con las tres muestras independientes, 0,5241 [0,5130, 0,5352] sobre n=7.800.

Las dos lecciones, que valen para todo el histórico de medidas del proyecto:

1. **Un negativo medido con una baraja NO es un negativo de la política.** Antes de
   enterrar una palanca hay que decir con qué lista se midió, y volver a medirla si la
   lista cambia. Aquí eso valía +6,5 pp de winrate en espejo.
2. **Un IC que roza el 0,5 no es un veredicto, es una petición de más muestra.** El corte
   binario sobre una sola tirada convierte ±0,2 pp de azar en «entra / no entra».

## 4. La combinación: aditiva, sin interacción

| | n | tasa | IC95 |
|---|---:|---:|---|
| solo `RETIRADA` | 3.000 | 0,5283 | [0,5104, 0,5461] |
| solo `BUSQ_CRITERIO` | 3.000 | 0,5387 | [0,5208, 0,5564] |
| solo `GUSTING` | 3.000 | 0,5267 | [0,5088, 0,5445] |
| retirada + búsqueda | 3.000 | 0,5637 | [0,5458, 0,5813] |
| **v5 = las tres** | **3.000** | **0,6020** | **[0,5844, 0,6194]** |

Suma esperada si fueran independientes: 0,5 + 0,028 + 0,039 + 0,027 = **0,594**. Medido:
**0,602**. La combinación **no se come a sí misma** — era el riesgo declarado del encargo
(«puede ser menor que la suma, o incluso negativa por interacción») y no se materializa.
Tiene sentido mecánico: las tres viven en selects distintos y no compiten por la misma
ranura del turno. El paso de dos a tres palancas es además **significativo**: los IC de
0,5637 y 0,6020 son disjuntos.

Las tres **disparan de verdad** (contadores `USOS` sobre 3.000 partidas): `busq` = 10.245
aplicaciones (3,4/partida), `gusting` = 1.112 (0,37/partida, 358 de ellas por KO
inmediato), `retirada` = 808 (0,27/partida). Una palanca que no dispara mide 0,5 por
construcción y no por falta de valor; no es el caso de ninguna.

## 5. Prueba de fuego: el campo real, no el espejo

El espejo es el rival más blando posible frente a un cambio de política: se enfrenta a una
copia de uno mismo. La prueba que decide es el **gauntlet ponderado** por el share medido
en la ladder (`gauntlet.md` §1): nuestra lista con el piloto candidato contra cada lista
del campo pilotada por el v2, n=300 por emparejamiento. Línea base del v2: las celdas ya
medidas de `data/gauntlet.json` (n=800 por celda, mismo protocolo, test-retesteadas).

| rival | peso | v2 | v5 | Δ |
|---|---:|---:|---:|---:|
| c1-grimmsnarl | 0,312 | 0,910 | **0,940** | +0,030 |
| c2-alakazam | 0,182 | 0,767 | 0,807 | +0,039 |
| c3-lopunny-froslass | 0,128 | 0,771 | 0,810 | +0,039 |
| c4-dragapult | 0,082 | 0,810 | 0,853 | +0,043 |
| **c5-kangaskhan-crustle** | 0,069 | 0,289 | **0,387** | **+0,098** |
| **c6-ogerpon** | 0,050 | 0,323 | **0,403** | **+0,081** |
| c7-lucario-campo | 0,040 | 0,660 | 0,747 | +0,087 |
| c8-dipplin-grookey | 0,035 | 0,835 | 0,877 | +0,042 |
| x2-hydrapple | 0,025 | 0,626 | 0,607 | **−0,020** |
| x1-slowking | 0,018 | 0,890 | 0,927 | +0,037 |
| x3-cynthia-garchomp | 0,016 | 0,871 | 0,890 | +0,019 |
| x4-ns-zoroark | 0,008 | 0,941 | 0,950 | +0,009 |

| | v2 | v5 |
|---|---|---|
| **POND** (cobertura 96,3%) | 0,7605 [0,7503, 0,7707] | **0,8032 [0,7881, 0,8182]** |
| **Δ POND** | — | **+0,0427 IC95 [+0,0245, +0,0608], z = 4,61** |
| **peor emparejamiento** | c5-kangaskhan **0,289** | c5-kangaskhan **0,387** |
| celdas por debajo del v2 | — | **1 de 12** |
| acciones ilegales | — | **0 en 3.600 partidas** |

Cuatro lecturas:

1. **Gana contra el campo, y donde más gana es donde peor estábamos.** Los dos agujeros
   documentados de `mega-lucario` son los dos mayores incrementos de la tabla:
   Kangaskhan-Crustle +9,8 pp y Ogerpon +8,1 pp. **El peor emparejamiento sube de 0,289 a
   0,387**, que es exactamente la métrica que premia el 70% de la rúbrica (consistencia, no
   media). Los agujeros **siguen siendo agujeros** —0,387 es perder 6 de cada 10— pero se
   han estrechado sin tocar la lista.
2. **No rompe lo que había que no romper.** Grimmsnarl es el 31% del campo y sube
   (0,910 → 0,940). El aviso de `gauntlet.md` §5 («una lista que arregle un agujero y rompa
   Grimmsnarl pierde POND») no se activa.
3. **El espejo exagera**: +10,2 pp en espejo se convierten en **+4,3 pp** ponderados contra
   el campo. No es contradicción — contra el campo ya ganábamos el 76%, y ahí queda menos
   margen que en un 50/50. La báscula que decide es esta, no aquella.
4. **Hay una regresión, y se declara**: x2-hydrapple, −0,020 (no significativa, peso 2,5%).
   Con 12 celdas es lo esperable por azar; no se corrige nada por ella, pero queda escrita
   para no «descubrirla» después.

## 6. `FIX_PROMO`: el que no entra pero no es lo mismo que «no sirve»

Con mega-lucario mide 0,4835 (n=2.000), y tiene explicación mecánica: la rama que arregla
—el arrastre de la banca RIVAL— **se pisa cero veces**, porque en el v2 nuestra política no
sabe jugar Boss's Orders. Con **hops-snorlax** la misma palanca mide **0,6195 [0,5980,
0,6405]**, el efecto más grande medido en el proyecto, porque allí la rama sí se abre
(Defiant Horn de Hop's Dubwool). Es decir: **es una mejora enorme de la otra lista**.

Y hay un cabo suelto que esta tanda deja a propósito: **ahora que `GUSTING` está activo, v5
sí juega Boss's Orders**, así que la rama del `(1,3)` con opciones del rival **ya se abre**
con mega-lucario (contador `objetivo_rival` = 1.112 en 3.000 partidas, antes 0). La mitad
del arrastre que v5 usa es la de `heuristico_v3.py` (`_valor_objetivo`); `FIX_PROMO` es
otra implementación de lo mismo, medida **antes** de que la rama existiera. **Comparar las
dos ahora es la primera medición que habría que hacer en la próxima tanda**, y es barata.

## 7. Auditoría de consistencia (el 70% de la rúbrica)

500 partidas de `heuristico_v5.py` contra el v2, mega-lucario a los dos lados
(`scratchpad/v5/auditoria.py`). La legalidad no se comprueba solo por que el motor no
proteste — se valida **antes de devolver la acción** con el propio `_es_legal`, porque
`_fallback` podría estar tapando una política rota sin que el env se entere.

| prueba | resultado |
|---|---|
| estados del candidato | **500× DONE** — 0 INVALID / ERROR / TIMEOUT |
| estados del rival | 500× DONE |
| acciones ilegales detectadas por nosotros | **0** en 19.664 decisiones |
| `FALLBACKS` (los cuatro) | `politica_ilegal=0 politica_excepcion=0 select_desconocido=0 fase_sin_accion=0` |
| `CASOS_RAROS` | vacío |
| tiempo por decisión | media 0,505 ms · p95 **0,155 ms** · p99 19,5 ms · máx 84,4 ms |
| **tiempo total de agente por partida** | media 0,020 s · p95 0,025 s · **máx 0,087 s** |
| **margen sobre el banco de 600 s** | **×6.893** |

La media (0,505 ms) es **mayor que el p95** (0,155 ms), y no es errata: la cola la produce
la carga del catálogo `AllCard`/`AllAttack`, que aquí se paga **500 veces** porque el arnés
recarga el módulo en cada partida. En el envío se paga una sola vez. La cifra que decide es
la última: el peor caso observado gasta **0,087 s de los 600 s** disponibles.

Sumando la tanda, v5 ha jugado **3.000 + 3.600 + 500 + 15 = 7.115 partidas sin una sola
acción ilegal ni un solo estado anómalo**.

## 8. El paquete

```text
envios/heuristico-v5-mega-lucario.tar.gz   0,5 MiB / límite 197,7 MiB
```

| comprobación | resultado |
|---|---|
| validación con `exec()` y sin `__file__` (la trampa de PKM-005) | 15 partidas, **0 estados anómalos** |
| catálogo cargado **descomprimiendo en directorio limpio** | 1.267 cartas · 1.556 ataques · 1.267 textos de trainer · 1.267 de habilidad — **completo** |
| `deck.csv` | 60 cartas, md5 idéntico a `research/decks/propios/mega-lucario.csv` |
| `agentes/politica.py` | md5 idéntico a `research/agentes/heuristico_v5.py` |

El catálogo se comprueba **dentro del tar** y no en el repo a propósito: el heurístico
degrada en silencio si no encuentra `cards_clean.csv` — jugaría peor sin dar un solo error.

## 9. Límites de todo lo anterior

1. **Es una mejora de `mega-lucario`, no de la política.** Las tres palancas son
   dependientes de la lista y está medido en las dos direcciones (retirada 0,476 y
   `BUSQ_CRITERIO` 0,487 en hops-snorlax). Cambiar de baraja **invalida** este v5 y obliga
   a volver a medir palanca por palanca.
2. **El acuerdo con el experto sigue sin predecir nada.** Ninguna de las tres reglas salió
   de la tabla de co-disponibilidad del diagnóstico; la que más brecha de acuerdo tenía
   (`(1,8)`, 10,8% contra 10,7% de azar) midió 0,484. El gate por winrate ha vuelto a ser lo
   único que separa una hipótesis de una mejora.
3. **La línea base del v2 en §5 viene de celdas medidas en otras sesiones.** Mismo
   protocolo y test-retesteadas, pero no son partidas simultáneas a las de v5.
4. **El agujero de Kangaskhan-Crustle sigue siendo el peor emparejamiento** (0,387) pese a
   la mejora. Ahí lo que toca es la LISTA, no el agente.
5. **Sigue vivo el aviso de la ladder**: dos envíos idénticos han puntuado 940 y 790 μ. Un
   +4,3 pp de POND es real en la báscula y puede no verse en un μ concreto. La práctica
   documentada del top —subir el agente final **dos veces**— sigue siendo la respuesta.
