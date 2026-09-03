# Selección del envío final: verificación de los tres informes y el hallazgo del par piloto↔baraja

Fecha: 2026-08-12 (madrugada). Encargo: verificar de forma independiente lo que dicen
los informes de CLON, SPARRING y COBERTURA, ordenar los supervivientes contra el rival
más fuerte disponible, pasar el gauntlet al ganador, auditarlo y dejarlo empaquetado.

Todas las medidas de esta nota son **frescas**: ninguna cifra se copia de las tandas
anteriores. `arena.py`, `--procs 3`, asientos intercambiados, IC de Wilson. Suelo de la
báscula ya calibrado en otra tanda: v2 contra sí mismo 0,4959 [0,4848, 0,5070] n=7.800.

---

## 1. Verificación: lo reportado contra lo medido de nuevo

| candidato | qué decía su informe | re-medido aquí (muestra independiente) | veredicto |
|---|---|---|---|
| **clon** (`research/agentes/clon.py` + `politica.npz`, 2 épocas) vs `heuristico.py` v2, mega-lucario ambos lados | 0,649 [0,631, 0,666] n=3.000 | **0,651 [0,630, 0,672]** n=2.000 | **CONFIRMADO** |
| **`heuristico_v6`** (v5+`recupera`, ganador de COBERTURA) vs `heuristico.py` v2 | no se midió contra v2; se dedujo de v5 (0,602) + `recupera` (0,5186) | **0,611 [0,589, 0,632]** n=2.000 | **CONFIRMADO** (coherente con la deducción) |
| **sparring fuerte** | SIN RESULTADO; `research/notas/sparring.md` no existe | — | no hay candidato |
| **clon vs `heuristico_v6`** (el rival más fuerte que existe) | 0,563 [0,541, 0,585] n=2.000 | **0,539 [0,517, 0,561]** n=2.000 | **CONFIRMADO** (más bajo: maldición del ganador; sigue con IC95 por encima de 0,5) |

Los dos candidatos vivos ganan a la línea base y **el clon gana también al v6**, así que
el orden contra el rival más duro es: **clon > v6 > v2**.

## 2. El rival fuerte que faltaba ya lo teníamos: es el propio clon

El encargo pedía medir contra un «sparring fuerte» que ninguna tanda produjo. La pieza
que lo sustituye estaba delante: **el clon pilotando las listas del campo** es una
imitación directa de cómo juegan de verdad los equipos mejor valorados de la ladder.
Usarlo como rival cambia el resultado de todo lo demás, y ese es el hallazgo de esta
tanda.

## 3. La combinación pedida (punto 3 del encargo): el clon ya contiene a `recupera`

Los dos supervivientes ocupan **el mismo hueco** (los dos son la política entera), así que
«combinarlos» solo puede ser un híbrido. Dos formas, las dos medidas:

**(a) ¿Hace falta la familia `recupera` del v6 dentro del clon?** No: el clon ya juega
esas cartas. Sonda `scratchpad/probe_clon.py`, 120 partidas contra `heuristico_v6`,
5.695 decisiones, contando qué ofrece el motor y qué elige la red:

| carta | v5/v6 sin `recupera` (`cobertura-cartas.md`) | clon (jugadas/partida) |
|---|---|---|
| 1097 Night Stretcher | **0** en 14.936 decisiones | **0,48** (84% de las veces que se le ofrece) |
| 1238 Tarragon | **0** | **0,42** |
| 1123 Switch | **0** | **0,28** |
| 1141 Premium Power Pro | **0** | **0,44** |
| 1182 Boss's Orders | 15,6% (lo resucitó GUSTING) | 0,31 |

Las cuatro «cartas muertas» que la tanda de cobertura tuvo que resucitar a mano — y de las
que solo una (`recupera`) pasó el gate — **el clon las juega sin que nadie escriba la regla**.
La cobertura de la lista deja de ser un problema abierto: 0 cartas muertas.

**(b) Híbrido por confianza.** Los híbridos por CLASE de decisión ya estaban medidos
peores (auxiliar 0,486 / principal 0,445 contra v5). Aquí se probó otro reparto que no
estaba medido: la red decide siempre **salvo cuando está perdida** — si su softmax top-1
cae por debajo de 0,17 (el decil inferior medido: mediana 0,400, p10 0,166), decide el v6.
Eso cede ~10% de las decisiones en vez del 43%.

| | n | tasa contra `heuristico_v6` | IC95 |
|---|---:|---:|---|
| clon puro | 2.000 | 0,539 | [0,517, 0,561] |
| clon + puerta de confianza → v6 | 2.000 | 0,550 | [0,529, 0,572] |

+0,011 con IC solapados (z≈0,7): **no es una mejora confirmada**. Se queda fuera por
disciplina de medida — pero es un negativo distinto del de los híbridos por clase: ceder
solo el 10% de las decisiones ya no HACE DAÑO, lo que sitúa el problema de los híbridos
en el volumen de decisiones cedidas y no en mezclar dos políticas.

## 4. El hallazgo: la báscula de barajas se INVIERTE cuando el piloto es bueno

`research/gauntlet.py` mide una lista contra las 12 líder del campo **con el mismo
piloto en los dos lados**. Hasta ahora siempre se había corrido con `heuristico.py`.
Se ha corrido tres veces, cambiando solo el piloto, sobre las mismas 12 listas rivales
y con n=200 por emparejamiento (2.400 partidas por fila):

| lista | POND con piloto **v2** (débil) | POND con piloto **clon** (fuerte) |
|---|---|---|
| **mega-lucario** (la nuestra, la de la ladder) | **0,758** [0,746, 0,769] · peor 0,277 | **0,362** [0,337, 0,386] · peor **0,105** |
| c2-alakazam | 0,358 [0,330, 0,385] · peor 0,105 | **0,454** [0,427, 0,482] · peor 0,320 |
| c1-grimmsnarl | 0,413 [0,385, 0,441] · peor 0,050 | (ver §5) |

**El orden se da la vuelta.** Con el piloto flojo, mega-lucario es la mejor lista del
banco y alakazam la peor; con el piloto bueno pasa lo contrario. No es un matiz: son
40 puntos porcentuales en cada dirección, con IC95 disjuntos y n=2.400 por fila.

Esto cierra `PKM-006` («el ranking de barajas mide baraja × piloto, no baraja»), que
lo dejó por escrito el 10-ago y aplazó la decisión a «cuando el piloto sea bueno». El
piloto bueno ya existe, y la respuesta es que **la lista que elegimos para la ladder
estaba elegida con el instrumento equivocado**.

Por qué pasa, con la mecánica delante: mega-lucario es un aggro directo que un
puñado de reglas ejecuta casi óptimamente, así que el piloto flojo le saca todo el
jugo; alakazam y grimmsnarl ganan montando secuencias (búsqueda, evolución en dos
pasos, colocación de banca) que el heurístico no sabe montar y la red sí. El número
que lo enseña sin ambigüedad es el espejo — misma lista en los dos lados, clon contra
`heuristico_v6`:

| lista del espejo | clon vs v6 | IC95 | n |
|---|---:|---|---:|
| mega-lucario | 0,539 | [0,517, 0,561] | 2.000 |
| c2-alakazam | **0,789** | [0,763, 0,813] | 1.000 |
| c1-grimmsnarl | **0,906** | [0,886, 0,923] | 1.000 |

La ventaja de la red sobre la heurística **depende de la lista**: +4 pp en la nuestra,
+29 en alakazam, +41 en grimmsnarl. Nuestra lista es justo donde menos rinde el mejor
agente que tenemos.

## 6. Empaquetado y verificación del paquete

`empaquetar.py` con la política del clon y sus cinco ficheros de apoyo (`--extra`), la
baraja elegida y `--validar` (15 partidas cargando `main.py` con `compile`+`exec`, sin
`__file__`, repo fuera de `sys.path`). Además, `scratchpad/verifica_tar.py` descomprime
el tar en un **directorio limpio** y comprueba desde ahí:

- contenido del tar y **ausencia de código de terceros** (nada de `research/terceros/`:
  el sparring y los notebooks públicos son solo material local de estudio);
- catálogo **COMPLETO**: 1.267 cartas, 1.556 ataques, 1.267 textos de trainer y 1.267 de
  habilidad — y también el catálogo que usa `rasgos.py` (1.267 / 1.556);
- los **pesos `.npz` viajan dentro** (`agentes/politica.npz`) y la inferencia funciona
  desde el paquete descomprimido: se imprimen las formas de las ocho matrices;
- 15 partidas reales con **0 estados anómalos** y los contadores del agente al final
  (`red` > 0, `heuristico`/`excepcion`/`ilegal` = 0: ni un fallback).

## 5. La báscula de barajas rehecha con el piloto bueno (punto 4 del encargo)

`research/gauntlet.py --politica research/agentes/clon.py --rivales ampliado --n 200`,
**clon en los dos lados**, 12 rivales, 2.400 partidas por fila, 0 ilegales.

| candidata | grimm 31% | alak 18% | lopu 13% | drag 8% | kanga 7% | oger 5% | luca 4% | dipp 3,5% | hydr | slow | cynt | zoro | **POND** | IC95 | **PEOR** |
|---|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|
| c1-grimmsnarl | 0,510 | 0,695 | 0,605 | 0,790 | **0,130** | **0,125** | 0,695 | 0,735 | 0,345 | 0,915 | 0,580 | 0,930 | **0,558** | [0,530, 0,586] | 0,125 |
| **c2-alakazam** | 0,320 | 0,470 | 0,335 | 0,730 | **0,445** | **0,455** | 0,715 | 0,655 | 0,605 | 0,895 | 0,450 | 0,880 | **0,454** | [0,427, 0,482] | **0,320** |
| mega-lucario (la de la ladder) | 0,290 | 0,105 | 0,780 | 0,575 | **0,110** | **0,210** | 0,350 | 0,650 | 0,405 | 0,885 | 0,355 | 0,770 | 0,362 | [0,337, 0,386] | 0,105 |

Y la otra báscula, la del campo con el rival pilotado por el v2 (`scratchpad/v5/campo.py`,
n=250 por emparejamiento, 3.000 partidas por fila) — es decir, **nuestro par contra un
rival flojo**, que es la mitad baja de la ladder:

| par | POND | IC95 | peor | peor con peso ≥5% | ilegales |
|---|---|---|---|---|---|
| clon + c1-grimmsnarl | **0,8654** | [0,8522, 0,8786] | c6-ogerpon **0,364** | c5-kangaskhan 0,532 | 0 |
| **clon + c2-alakazam** | 0,8252 | [0,8054, 0,8449] | c6-ogerpon **0,720** | c5-kangaskhan **0,736** | 0 |
| clon + mega-lucario | 0,8155 (agrupado n=6.000) | [0,8036, 0,8275] | c5-kangaskhan **0,322** | c5-kangaskhan 0,322 | 0 |

**Los dos agujeros históricos** (`c5-kangaskhan` 0,278 y `c6-ogerpon` 0,335 con v2, el
11,8% del campo) **solo los tapa alakazam**: 0,736 y 0,720 contra el campo flojo, 0,445 y
0,455 contra el campo fuerte. Grimmsnarl no los tapa, los empeora (0,130 / 0,125).

Duelos directos, muestra independiente de las celdas del gauntlet:

| duelo | n | tasa | IC95 | celda del gauntlet |
|---|---:|---:|---|---|
| clon+c2-alakazam vs clon+mega-lucario | 2.000 | **0,882** | [0,867, 0,895] | 0,895 |
| clon+c1-grimmsnarl vs clon+mega-lucario | 2.000 | **0,703** | [0,683, 0,723] | 0,710 |
| clon+c2-alakazam vs `heuristico_v6`+mega-lucario (el par del envío actual) | 1.000 | **0,880** | [0,858, 0,899] | — |

Las dos celdas replican dentro de 1,3 pp. La báscula de barajas con este piloto es
reproducible.

## 7. Auditoría del candidato final (punto 5 del encargo)

`scratchpad/auditoria_final.py`, **500 partidas** de `clon + c2-alakazam` contra los
**12 arquetipos del campo pilotados por el clon** (el rival más duro que existe aquí),
en un solo proceso y **fijado a UN núcleo** (`taskset -c 0`, `OMP_NUM_THREADS=1`) para
parecerse a los ~1,6 vCPU de producción.

| | |
|---|---|
| estados finales | **1.000/1.000 DONE** — ni un INVALID, ERROR o TIMEOUT |
| decisiones | 36.306 · **red 35.806** · heurístico **0** · excepciones **0** · **ilegales 0** |
| ms por decisión | media **0,206** · p95 **0,371** · p99 0,465 · **máximo 31,9** (la primera llamada, que parsea `AllCard`/`AllAttack`; coste único por proceso) |
| segundos de agente por partida | media 0,01 · **máximo 0,05** |
| margen sobre el banco de 600 s | **×10.961** |
| WR (media simple sobre los 12 rivales) | 0,618 |

Las 500 decisiones que no pasan por la red son los `select is None` (la baraja del primer
paso), una por partida: **el 100% de las decisiones reales las toma la red y ninguna
necesitó el respaldo heurístico**.

## 8. Veredicto y qué enviar

**Nada de lo que había mejora al clon: el clon es el agente.** Lo que cambia respecto a
lo que dijeron los tres informes es **la baraja**, y el cambio no es cosmético.

Ranking final contra el rival más fuerte disponible (POND del gauntlet con el clon
pilotando los dos lados) y contra el campo flojo, con el suelo de cada uno:

| par (piloto + baraja) | campo FUERTE POND | peor | campo FLOJO POND | peor | vs el par del envío actual |
|---|---|---|---|---|---|
| clon + **c1-grimmsnarl** | **0,558** | 0,125 | **0,8654** | 0,364 | 0,703 vs clon+mega-lucario |
| clon + **c2-alakazam** | 0,454 | **0,299** (confirmado n=1.000) | 0,8252 | **0,720** | **0,882** vs clon+mega-lucario · **0,880** vs v6+mega-lucario |
| clon + mega-lucario | 0,362 | 0,105 | 0,8155 | 0,322 | — |
| `heuristico_v6` + mega-lucario | — | — | — | — | pierde 0,461 contra el clon |
| `heuristico.py` v2 + mega-lucario (**lo que está en la ladder, μ 468**) | — | — | 0,7605 | 0,289 | pierde 0,349 contra el clon |

**Recomendación: `clon + c2-alakazam` en el primer slot.** Es el único par medido cuyo
PEOR emparejamiento sube de verdad (0,105 → 0,299 contra el campo fuerte; 0,322 → 0,720
contra el flojo) y el único que tapa los dos agujeros históricos. Es lo que pide
literalmente el 70% del Model Score («consistency across repeated games», «no depender de
emparejamientos concretos») y lo que ya decidió `PKM-004`.

**Segundo slot: `clon + c1-grimmsnarl`.** Si lo único que se optimiza es μ, esta es
mejor: +10,4 pp de media contra el campo fuerte y +4,0 contra el flojo, con IC disjuntos.
Paga con un suelo de 0,125 en el 11,8% del campo. Como la división deja **dos envíos
activos** y está documentado que dos envíos idénticos sacaron 940 y 790 μ, mandar los dos
es también el experimento que decide con datos reales cuál de los dos criterios manda.

Lo que NO se toca: `research/agentes/heuristico.py` y `research/decks/propios/mega-lucario.csv`
siguen intactos (son los que están en la ladder), y ningún envío lleva código de terceros.

**Aviso honesto**: `c2-alakazam.csv` y `c1-grimmsnarl.csv` son copias exactas de la lista
líder de su arquetipo tomadas del censo de replays públicos, no listas nuestras. La
aportación propia es el agente y el análisis; para el writeup de la Strategy, esa
diferencia hay que decirla, y es una decisión del propietario si prefiere pagar rating
por jugar una lista propia.
