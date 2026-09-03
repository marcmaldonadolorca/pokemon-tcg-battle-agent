# Potencia de la báscula, re-medición de los «empates» y proxies de alta señal

Fecha: 2026-08-11. Código: `research/proxies.py` (nuevo), `research/duelo.py`, `arena.py`.
Wrappers: `research/agentes/variantes/*_mega_lucario.py` (generados con el patrón de
`gen_wrappers.py`: agente base cargado por ruta + palancas como atributos + baraja incrustada).
JSON crudos: `scratchpad/potencia/*.json`. Cálculo de potencia: `scratchpad/potencia/potencia.py`.

Motivo: `estrategia-plan.md` §2.3 avisa de que varios de los seis negativos del proyecto se
declararon con `n` que no medía nada. Antes de congelar el envío hay que saber si enterramos una
mejora real. Todo lo de aquí es espejo con `mega-lucario` (la lista viva) a los dos lados,
`--procs 3`, intercambio de asiento e IC de Wilson.

---

## 1. La corrección estadística previa: la fórmula que usábamos es la de dos muestras

`estrategia-plan.md` §2.3 usa `n ≈ 16·p(1−p)/d²`. Esa es la fórmula de **dos proporciones
independientes**. Nuestra báscula no es eso: `arena.py`/`duelo.py` juegan `n` partidas entre A y
B y cuentan las que gana A, o sea **una sola proporción contrastada contra 0,5**. La fórmula
correcta es `n = (z_{α/2}+z_β)²·p(1−p)/d²`, que da `d = 1,40/√n` en vez de `d = 2/√n`.

Consecuencia práctica: **la báscula es un √2 más sensible de lo que creíamos**, y las `n` que
pedía el plan estaban infladas un 100 %. Para resolver ±1 pp no hacen falta 9.604 partidas sino
4.802 (o 9.604 si se quiere ese semiancho de IC, que es otra cosa distinta del MDE).

| n | semiancho IC95 | MDE 80 % pot. | pot. si el efecto real es +2 pp | +3 pp | +5 pp | +10 pp |
|---:|---:|---:|---:|---:|---:|---:|
| 240 | ±6,33 pp | 9,04 pp | 9 % | 15 % | 34 % | 87 % |
| 400 | ±4,90 pp | 7,00 pp | 12 % | 22 % | 52 % | 98 % |
| 800 | ±3,46 pp | 4,95 pp | 20 % | 40 % | 81 % | 100 % |
| 1.000 | ±3,10 pp | 4,43 pp | 24 % | 48 % | 89 % | 100 % |
| 1.500 | ±2,53 pp | 3,62 pp | 34 % | 64 % | 97 % | 100 % |
| 2.000 | ±2,19 pp | 3,13 pp | 43 % | 77 % | 99 % | 100 % |
| **4.000** | **±1,55 pp** | **2,21 pp** | **72 %** | **97 %** | 100 % | 100 % |
| 4.500 | ±1,46 pp | 2,09 pp | 77 % | 98 % | 100 % | 100 % |

Lectura de la tabla, que es el punto de toda esta tarea: **con n=240 teníamos un 15 % de
probabilidad de ver un +3 pp real, y un 34 % de ver un +5 pp.** Enterrar una hipótesis con esa
muestra no es un negativo, es no haber mirado. Con n=1.500 la cosa mejora (64 % para +3 pp) pero
sigue dejando escapar dos de cada tres mejoras pequeñas. Con n=4.000 el +3 pp se ve el 97 % de
las veces: **eso ya es un negativo de verdad.**

---

## 2. El ruido de suelo de la báscula (el número que faltaba)

`heuristico.py` contra sí mismo, misma baraja `mega-lucario`, n=4.000:

| medida | valor |
|---|---|
| tasa de A | **0,50175** |
| IC95 | **[0,4863, 0,5172]** (semiancho 1,55 pp, exactamente el teórico) |
| acciones ilegales | **0** en 8.000 lados |
| pasos medios | 68,5 |

La báscula es **insesgada**: el espejo perfecto cae en 0,502 con el 0,5 dentro del IC. Ese
±1,55 pp es la resolución real del instrumento a n=4.000, y ninguna afirmación por debajo de
esa cifra es defendible sin más partidas. Sirve además de control de sanidad del arnés: si un
brazo A/B espejo diera 0,53 «sin cambiar nada», el problema sería el arnés y no la política.

### Hallazgo lateral que no buscaba: el asiento vale 18 puntos

En ese mismo espejo, con las dos mitades de asiento separadas (n=2.000 cada una):

| | tasa |
|---|---|
| A yendo **primero** | **0,5915** |
| A yendo **segundo** | 0,4120 |
| **swing** | **+17,95 pp** (ee 1,58 pp → **IC95 [+14,9, +21,1]**, z = 11,4) |

Es decir: con `mega-lucario` y este piloto, **el que va primero gana el 59 %**. Es el efecto más
grande medido en el proyecto y estaba escondido a plena vista dentro del espejo. `estrategia-plan.md`
§5.4 pedía exactamente esta corrida («medirlo una vez, con potencia») y su predicción era
«primero»: **confirmada, y con margen**. `heuristico.py:473` (`if t == 9` → primero) no se toca.
Corolario metodológico: cualquier medición que no intercambie asiento a partes iguales está
contaminada por un efecto de 18 pp, mucho mayor que cualquier palanca que estemos midiendo.

---

## 4. Proxies de alta potencia (`research/proxies.py`)

La idea de `estrategia-plan.md` §2.3/§3-R3: ganar o perder es **un bit por partida**; hay
métricas intermedias que dan varias observaciones por partida y por tanto detectan diferencias
con muchas menos partidas. Se implementan tres, medidas **por lado y en la misma pasada que el
winrate**, con el mismo protocolo (intercambio de asiento, procesos, nunca hilos):

| proxy | definición | dirección esperada en el bueno |
|---|---|---|
| `energia_enterrada` | energías que murieron adjuntas ÷ energías invertidas | **baja** |
| `premios_t7` | premios robados por ese lado hasta el turno 7 incluido | **alta** |
| `turno_primer_ko` | turno en que ese lado roba su primer premio | **baja** (antes) |

**Cómo se observa.** Se envuelve el `agent()` de los dos lados y se lee `obs["current"]` en cada
decisión (~34 muestras por partida). Todo lo que está en juego de los DOS jugadores es visible
(`motor-mecanica.md` §4), así que cada lado se mide con su propia obs y no hace falta tocar el
motor ni instrumentar `env`.

**Dos trampas que costaron dos bugs, y que hay que dejar escritas:**

1. **La evolución no es un entierro.** El seguimiento es por `serial` (la copia física). Al
   evolucionar, el serial del pre-evolutivo desaparece de `active`/`bench` y baja a
   `preEvolution` del que lo cubre: **sigue en juego**. Sin contar los `serial` de
   `preEvolution` como vivos, toda evolución cuenta como energía enterrada y la métrica queda
   inservible en una baraja de evolución como `mega-lucario`.
2. **En el setup los premios aún no están repartidos.** En `turn 0` llega `prize: []`, de modo
   que `6 − len(prize)` da **6 premios robados** en la primera observación. Sin el guardián
   «solo cuento desde que he visto la pila de 6», `premios_t7` sale 6,0 para los dos lados y
   `turno_primer_ko` sale 0. Es exactamente el tipo de error que produce un proxy que
   «correlaciona perfectamente» y no mide nada.

Detalle menor pero declarado: si un lado nunca roba premio, `turno_primer_ko` se **censura** al
último turno visto + 1 en vez de descartarse; tirar esos casos borraría de la media justo el
peor resultado posible.

**Aviso de causalidad, obligatorio (ya estaba en `estrategia-errores.md` y sigue vigente).**
La energía enterrada está confundida con el resultado: perder implica que te maten cosas. No se
puede leer como «bajar la métrica X da +Y % de winrate». Sirve como **función objetivo
intermedia** y como instrumento de cribado rápido, no como estimador de winrate.

---

## 3. Re-medición de los «empates» con n=4.000

Todo espejo `mega-lucario`, `--procs 3`, `duelo.py` (mismo protocolo que `arena.py` más el
recuento de acciones ilegales y de disparos de la palanca). **A = variante, B = `heuristico.py`.**

| brazo | n antes | tasa antes | **n ahora** | **tasa ahora** | **IC95** | z | ilegales |
|---|---:|---:|---:|---:|---|---:|---:|
| ruido de suelo (v2 vs v2) | — | — | **4.000** | **0,5018** | [0,4863, 0,5172] | +0,22 | 0 |
| control v3 con palancas apagadas | — | — | 4.000 | *(§3.3)* | | | |
| **retirada** | 1.500 | 0,476 | **4.000** | **0,5397** | **[0,5241, 0,5553]** | **+5,03** | 0 |
| **gusting** | 1.500 | 0,495 | **4.000** | **0,5142** | [0,4986, 0,5298] | +1,80 | 0 |
| gusting vs rival que gustea | — | — | 2.000 | 0,4930 | [0,4710, 0,5150] | −0,63 | 0 |
| **v3 completo (retirada+gusting)** | 1.200 | 0,501 | **4.000** | **0,5598** | **[0,5443, 0,5752]** | **+7,56** | 0 |

Cero acciones ilegales en 36.000 lados de partida, y cero fallbacks de política en todos los
brazos: lo que se mide es política, no excepciones.

### 3.1 La retirada no era un negativo: es la mayor palanca medida del proyecto

`agente-heuristico-v3.md` la enterró en **0,476 con n=1.500** y la dejó apagada. Con n=4.000 y
la baraja del envío mide **0,5397 [0,5241, 0,5553]**: el IC entero por encima de 0,5, z = +5,03.
Disparó **967 veces en 4.000 partidas** (0,24 por partida) y aun así mueve 4 puntos.

Dos avisos honestos sobre esta cifra, porque los dos importan:

1. **No es la misma corrida repetida.** El 0,476 se midió con `hops-snorlax`; esto es
   `mega-lucario`. Es el mismo patrón que ya documentó `banca-y-asiento.md` §5 con el gusting:
   *la palanca vale distinto según la baraja, y se apagó midiéndola con otra*. Es decir, no basta
   con decir «lo medimos con poca n»: además lo medimos con la lista equivocada.
2. **Hay una muestra que discrepa.** La corrida de proxies (§4) es una muestra independiente de
   n=800 del mismo brazo y dio **0,494**. Contra el 0,5397 de n=4.000, la diferencia da z = 2,4:
   incómodo. Por eso hay una **muestra de confirmación** de n=4.000 corriendo (§3.4). Es
   exactamente la regla que sacamos del falso positivo z=2,12 de `banca-y-asiento.md`.

### 3.2 Gusting: la tercera muestra baja el efecto pero no lo mata

Historia completa de esta palanca, que es un caso de libro de regresión a la media:

| muestra | n | tasa del gusteador | IC95 |
|---|---:|---:|---|
| descubrimiento (`agente-heuristico-v3.md`, hops-snorlax) | 1.500 | 0,495 | — |
| `banca-y-asiento.md` §5 (mega-lucario, 1.500+3.000) | 4.500 | 0,527 | [0,512, 0,542] |
| **esta nota** (mega-lucario, muestra nueva) | **4.000** | **0,5142** | [0,4986, 0,5298] |
| **acumulado mega-lucario** | **8.500** | **≈0,521** | **[0,510, 0,531]** |

La tercera muestra queda por debajo de la segunda y su IC roza el 0,5, pero el acumulado de
8.500 partidas sigue por encima. Veredicto: **efecto real pero pequeño, del orden de +2 pp**, no
los +2,7 pp del descubrimiento. Hay una tercera confirmación corriendo (§3.4).

**Contra un rival que también gustea**: 0,4930 [0,4710, 0,5150] con n=2.000, es decir 0,5 como
manda la simetría. Ese brazo no mide la palanca (dos agentes idénticos siempre empatan): es el
**control de que el wrapper no tiene sesgo de asiento ni bug asimétrico**, y lo pasa. El valor
de la palanca *contra alguien que gustea* ya se deduce por simetría del espejo y es el mismo
+2 pp: en un A/B espejo, «A gustea y B no» y «B gustea y A no» son el mismo experimento visto
del revés.

### 3.3 Lo que de verdad hay que llevarse: el v3 completo

Con las dos palancas encendidas a la vez: **0,5598 [0,5443, 0,5752], n=4.000, z = +7,56**.
`agente-heuristico-v3.md` lo había medido en **0,501 con n=1.200** y `hops-snorlax`. Los efectos
son aproximadamente aditivos (+4,0 y +1,4 → +6,0 medido). **Es la mayor ganancia de política
medida en el proyecto**, y estaba apagada por defecto desde el 10 de agosto.

### 3.3-bis Control obligatorio: el v3 con las palancas apagadas ES el v2

Antes de atribuirle nada a las palancas hay que descartar que el módulo v3 difiera del v2 por
otra vía. `agente-heuristico-v3.md` afirmaba la equivalencia **leyendo el código**; aquí está
medida:

| control | n | tasa | IC95 |
|---|---:|---:|---|
| v3 (`RETIRADA=False`, `GUSTING=False`) vs v2 | 4.000 | **0,5040** | [0,4885, 0,5195] |

Indistinguible de 0,5. Por tanto **lo que miden los brazos de §3 es la palanca, no la base**.

### 3.4 Muestra de confirmación: la retirada sobrevive

La regla de casa (un z alto en la muestra de descubrimiento no es un hallazgo hasta que
sobrevive a una muestra independiente) aplicada a los dos brazos vivos:

| brazo | muestra | n | victorias | tasa |
|---|---|---:|---:|---:|
| retirada | descubrimiento | 4.000 | 2.159 | 0,5397 |
| retirada | **confirmación** | 4.000 | 2.161 | **0,5403** |
| **retirada** | **acumulado** | **8.000** | **4.320** | **0,5400 [0,5291, 0,5509]**, z = **+7,16** |

Dos muestras independientes de 4.000 partidas dan 2.159 y 2.161 victorias. **La retirada es un
resultado, no un candidato**: +4,0 pp [+2,9, +5,1] sobre el piloto de los envíos vivos. Y
disparó 967 y 941 veces respectivamente, o sea ~0,24 retiradas por partida: la palanca es
quirúrgica, no un cambio de estilo.

Esto invierte uno de los seis negativos del proyecto. El texto de `estrategia-plan.md` §2.3 tenía
razón en el diagnóstico general y se queda corto en el caso concreto: **la corrida de n=1.500 que
enterró la retirada no solo tenía poca potencia (64 % para un +3 pp), es que además la midió con
la baraja que no era.**

### 3.5 Gusting: tres muestras, efecto real de ~+2 pp

| muestra | baraja | n | tasa del gusteador |
|---|---|---:|---:|
| descubrimiento (`agente-heuristico-v3.md`) | hops-snorlax | 1.500 | 0,495 |
| `banca-y-asiento.md` §5 | mega-lucario | 4.500 | 0,527 |
| esta nota, descubrimiento | mega-lucario | 4.000 | 0,5142 |
| esta nota, **confirmación** | mega-lucario | 4.000 | **0,5240** |
| **acumulado mega-lucario** | | **12.500** | **0,5219 [0,5132, 0,5307]**, z = **+4,90** |

Confirmado también, con un efecto la mitad de grande que el de la retirada: **+2,2 pp**. Disparó
1.398 veces por 4.000 partidas, 443 de ellas asegurando un KO.

### 4.1 ¿Ordenan igual que el winrate? Sí, en los tres casos con respuesta conocida

n=800 por caso, espejo salvo el de barajas. `dif` es A−B con IC95 pareado por partida.

| caso | winrate A | `energia_enterrada` A / B (z) | `premios_t7` A / B (z) | `turno_primer_ko` A / B (z) |
|---|---:|---|---|---|
| v2 **vs random** | 0,951 | 0,127 / 0,800 (**−36,9**) | 0,47 / 0,08 (**+9,9**) | 9,9 / 13,5 (**−16,2**) |
| v2 **vs first** | 0,849 | 0,254 / 0,834 (**−25,8**) | 0,53 / 0,30 (**+4,6**) | 9,4 / 11,7 (**−9,6**) |
| **mega-lucario vs hops-snorlax** (v2 los dos) | 0,855 | 0,246 / 0,898 (**−34,0**) | 1,07 / 0,69 (**+7,5**) | 6,7 / 11,5 (**−20,5**) |
| **espejo v2 vs v2** (control de nulo) | 0,496 | 0,571 / 0,559 (+0,50) | 0,78 / 0,71 (+1,22) | 8,72 / 8,79 (−0,31) |

Los tres proxies **ordenan igual que el winrate en los tres casos conocidos y en la dirección
predicha**, y —lo que más importa— **el espejo da cero en los tres**: un instrumento que
«detectara» algo entre dos copias del mismo agente no serviría para nada. Como cifra de contexto:
nuestro piloto entierra el **57 %** de la energía que adjunta, entre el ganador (0,448) y el
perdedor (0,718) del campo.

### 4.2 Pero NO dan 10-100× más potencia: dan entre 0,8× y 1,7×

Aquí hay que corregir a `estrategia-plan.md`. Comparando, **a la misma n**, el z del proxy con
el z del winrate:

| caso | z winrate | z mejor proxy | multiplicador en z | en partidas equivalentes |
|---|---:|---:|---:|---:|
| v2 vs random | 25,5 | 36,9 | ×1,45 | ×2,1 |
| v2 vs first | 19,7 | 25,8 | ×1,31 | ×1,7 |
| mega-lucario vs hops | 20,1 | 34,0 | ×1,69 | ×2,9 |
| retirada (n=800) | −0,34 | −0,36 | ×1,06 | ×1,1 |
| gusting (n=800) | +3,62 | −2,90 | ×0,80 | ×0,6 |

**El multiplicador real está entre 0,6× y 2,9× en partidas, no entre 10× y 100×.** La razón es
estructural y conviene dejarla escrita: el «10-100×» del plan sale de contar **decisiones**
(150.000 en el corpus), y eso vale para las métricas de *acuerdo offline* del Nivel 1. La energía
enterrada, en cambio, se agrega a **un número por partida y por lado** — es una observación
continua en lugar de un bit, que es mejor, pero sigue siendo **una** observación por partida. Su
varianza resulta ser del mismo orden que la de ganar/perder.

### 4.3 Veredicto sobre los proxies

**Sirven, pero no como se esperaba.** No son un atajo para medir palancas con 40 partidas en vez
de 4.000: para eso el winrate a n=4.000 es igual de bueno y responde a la pregunta que importa.
Su valor real es otro y es doble:

1. **Instrumento de diagnóstico**: dicen *por qué* un agente gana (entierra menos energía, KO
   antes, va por delante en premios en el turno 7), no solo *si* gana. Para el writeup (10 %
   Report) y para dirigir la siguiente palanca, eso vale más que otro winrate.
2. **Se miden gratis**: van en la misma pasada que el winrate y no cuestan una sola partida
   extra. Está bien dejarlos puestos en toda medición futura por si un cambio sube el winrate
   empeorando la disciplina de energía (señal de que gana por azar de la muestra).

Lo que **no** hay que hacer es sustituir el A/B de n=4.000 por un proxy de n=200 y creerse el
resultado. Ese atajo no existe.

### 4.4 Los proxies sobre los dos brazos vivos (n=800, muestra pequeña a propósito)

| brazo | winrate A | `energia_enterrada` A/B (z) | `premios_t7` (z) | `turno_primer_ko` (z) |
|---|---:|---|---|---|
| retirada | 0,494 | 0,545 / 0,555 (−0,36) | (−0,20) | (−0,60) |
| gusting | 0,564 | 0,523 / 0,597 (**−2,90**) | (+1,72) | (−1,86) |

Estas dos filas son la prueba honesta del instrumento en el régimen que importa (efectos de 2-4
pp), y **el resultado es incómodo**: con n=800 el brazo de la retirada dio 0,494 y proxies planos,
cuando el mismo brazo con n=8.000 da 0,540. No es un fallo del proxy: es que n=800 no basta **ni
para el winrate ni para el proxy**. Refuerza la conclusión de §4.2: aquí no hay atajo.

En el brazo del gusting los tres proxies apuntan en la dirección correcta (entierra menos
energía, roba más premios pronto, mata antes) y coinciden con el signo del acumulado de 12.500
partidas. Vale como corroboración cualitativa, no como sustituto.

---

## 6. Veredictos y qué hacer con esto

1. **La báscula está sana**: ruido de suelo 0,5018 [0,4863, 0,5172], 0 ilegales, resolución
   ±1,55 pp a n=4.000. Lo que estaba roto era la **n**, no el instrumento.
2. **Dos de los seis negativos del proyecto se caen.** `retirada` es **+4,0 pp**
   (0,5400 [0,5291, 0,5509] sobre 8.000 partidas, con confirmación independiente) y `gusting`
   es **+2,2 pp** (0,5219 sobre 12.500). Los dos se habían apagado midiéndolos con n pequeña
   **y con la baraja que no era**.
3. **El v3 completo mide 0,5598 [0,5443, 0,5752] contra el piloto de los envíos vivos.** Es la
   mayor ganancia de política del proyecto y hoy está apagada por defecto.
4. **Ir primero es correcto y no se toca**: swing +17,95 pp [+14,9, +21,1] medido en el espejo
   con la baraja del envío. `estrategia-plan.md` §5.4 pedía esta corrida; queda hecha.
5. **Los proxies sirven de diagnóstico, no de atajo** (§4.3). El «10-100×» del plan no existe
   para métricas agregadas por partida: el multiplicador real es ×0,6 a ×2,9.
6. **Regla que hay que fijar para lo que queda**: ningún A/B por debajo de n=4.000, y todo z>2
   pasa por muestra de confirmación independiente antes de tocar el envío. Las dos palancas de
   aquí la han pasado; el falso positivo z=2,12 de `banca-y-asiento.md` no la pasó. La regla
   distingue bien.

### Lo que NO está medido y hace falta antes de cambiar el envío

El +6 pp del v3 completo es **espejo contra nuestro propio v2**. El Model Score (70 %) premia
**consistencia contra el campo real**, y `estrategia-plan.md` §2.3 exige un Nivel 3 antes de
promocionar nada: `research/gauntlet.py --n 500 --procs 3` con `v3full_mega_lucario.py` contra
`c1..c8`, mirando **la WR ponderada por share Y el peor emparejamiento**. Un cambio que suba la
media y hunda el peor emparejamiento no entra. **Esa corrida es el siguiente paso obligatorio y
no está hecha** (la máquina estaba ocupada con el ISMCTS).
