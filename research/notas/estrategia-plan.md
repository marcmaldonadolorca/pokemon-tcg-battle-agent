# Plan ejecutable: de la teoría del papel al piloto que tenemos

Fecha: 2026-08-11. Esta nota **no aporta teoría nueva**: es el filtro. Toma lo que produjeron
las cuatro pasadas de investigación (`estrategia-principios.md`, `estrategia-errores.md`,
`estrategia-arquetipos.md`, `estrategia-deckbuilding.md`) y el diagnóstico empírico
(`diagnostico-expertos.md`), tira lo que no se puede implementar o medir en **este** motor, y
deja cinco reglas con especificación y plan de medición, más la decisión de asiento y el
material de writeup.

Reglas de la pasada: 0 partidas jugadas, 1 proceso, sin commits, `research/agentes/heuristico.py`
intacto. Todo lo numérico nuevo de esta nota sale de `research/cards_clean.csv` y de los CSV de
`research/decks/` (aritmética, no simulación); lo demás está citado a la nota que lo midió.

---

## 0. Resumen ejecutivo

Tres frases:

1. **La báscula está rota antes que la política.** Cuatro palancas algorítmicas se declararon
   «empate» con n=240–1.500. Con n=240 el IC95 es ±6,2 pp: un efecto real de +3 pp es invisible.
   El motor da ~6 partidas/s con `--procs 3`; **n=4.000 cuesta ~11 minutos**. Antes de escribir
   una línea de política nueva hay que subir la n y adoptar métricas intermedias con 10–100× más
   potencia estadística por partida (§2.3).
2. **El piloto no puede jugar el 45,4 % de los ítems del campo, y 6 de las 60 cartas del envío
   vivo son papel.** El techo de cualquier heurística fina está por debajo de eso. Reglas 1–4 son
   de acceso y secuenciación; son baratas y ya están medidas en política sombra (+3,00 pp de
   acuerdo, `diagnostico-expertos.md` §6).
3. **La decisión con más impacto y coste cero no es de código: es de baraja.** Contra
   `propios/mega-lucario` el campo gana con **2 KOs**; contra `propios/hops-snorlax` necesita
   **6**. Nosotros necesitamos ~4,8 contra el campo medio (§6). Esa asimetría es, en un número,
   «perdemos de forma consistente sin depender del emparejamiento».

Orden de trabajo recomendado: **§2.3 (báscula) → R1 → R2 → R4 → R3 → R5**, con la decisión de
baraja del §6 en paralelo (es del propietario, no mía).

---

# 1. FILTRO DE REALIDAD — qué se descarta y por qué

El criterio no es «esto es falso», es **«esto no se puede ejecutar ni medir aquí»**. Cinco
motivos distintos, y conviene no mezclarlos porque cada uno tiene una salida diferente.

## 1.1 No existe en el pool (motivo: pool cerrado de 1.267 cartas)

Verificado por nombre contra `research/cards_clean.csv`. **Citar cualquiera de estas en el
writeup delante de tres jueces de The Pokémon Company sería el error más caro posible**, porque
lo detectan en un segundo.

| Carta que citan las guías | Estado | Equivalente real en nuestro pool |
|---|---|---|
| Iono, Professor's Research, Marnie, Arven, Carmine (como robo genérico) | **no existe** | Cheren 1224 / Urbain 1236 (roba 3), Lillie's Determination 1227 (baraja mano + roba 6), Judge 1213 (4/4) |
| Nest Ball, Quick Ball, Battle VIP Pass, Artazon | **no existe** | Poké Pad 1152 (Item, busca Pokémon sin Rule Box), Buddy-Buddy Poffin 1086, Ultra Ball 1121, Brock's Scouting 1210 |
| **Counter Catcher** | **no existe** | La *mecánica* sí: Counter Gain 1168 y Rosa's Encouragement 1240 (condicionadas a ir perdiendo). **Gusting condicionado al marcador: no hay.** Gusting incondicional: Boss's Orders 1182, Prime Catcher 1088, Pokémon Catcher 1124, Lisia's Appeal 1204, TR Giovanni 1218 |
| Super Rod, Earthen Vessel, Lost Vacuum | **no existe** | Night Stretcher 1097, Sacred Ash 1129 (**no es ACE SPEC**, corrige `lab-barajas.md` §1) |
| Forest Seal Stone, Lumineon V, Dedenne-GX, Radiant X | **no existe** | — (la regla «1 Radiant por baraja» sobra) |
| Bravery Charm, Defiance Band, Technical Machine | **no existe** | Hop's Choice Band 1171, Maximum Belt 1158, Brave Bangle 1175, Air Balloon 1174 |
| «baby Lucario» SVI 114 (atacante de 1 premio del arquetipo) | **no existe**: `prev_stage=='Riolu'` devuelve un único resultado, **678 Mega Lucario ex** | Solrock 676 / Hariyama 674 / Terrakion 607 hacen ese papel |

## 1.2 No es este juego (motivo: homónimos)

- **Todo Pokémon TCG Pocket** (game8, cardgamer, sportskeeda y buena parte de lo que devuelven
  los buscadores en 2026): 20 cartas, 3 premios, banca de 3, **energy zone automática**. Sus
  conclusiones están **invertidas** respecto a las nuestras y ya estuvieron a punto de hacernos
  cambiar la decisión de asiento en contra de nuestros propios 9.331 datos.
- **trainertower.com** hoy es un sitio de **VGC** (videojuego), no de TCG.
- **Listas de formatos rotados** (SixPrizes 2011/2013, ejemplos de JustInBasil con Welder o
  Charizard-VMAX): los **principios** valen, los **counts de carta concretos** no.
- **Matchups de Limitless** (<https://play.limitlesstcg.com/decks/mega-lucario-ex/matchups>):
  sirven para el *porqué* mecánico, **no** para predecir nuestra ladder — allí existen Gardevoir
  y Charizard, aquí no. Ejemplo concreto: en papel Alakazam gana a Lucario 67,7 % apoyándose en
  la debilidad {P}; **aquí el daño de Alakazam son contadores, que no aplican debilidad**, y la
  ladder mide 52 %. *La frase «Lucario es malo porque es débil a {P}» no debe ir al writeup.*

## 1.3 La observación no lo da (motivo: información no observable)

Este es el filtro que más candidatas mata. Contrastado campo a campo con `motor-mecanica.md` §1 y §4.

| Principio del papel | Qué haría falta | ¿Está en la obs? | Veredicto |
|---|---|---|---|
| «Cuenta tus premios para saber qué te falta» | contenido de `prize` propio | **NO** (`prize: [null,…]`) — solo la **longitud** | **Parcial**: la *carrera* de premios (cuántos quedan a cada lado) sí es implementable; el *prize checking* (qué pieza está premiada) solo por eliminación: `4 − (mano + juego + descarte)` repartido entre mazo y premios. Caro, valor medio |
| «Juega alrededor de la carta que tiene en la mano» | `hand` del rival | **NO** (`hand: null`; solo `handCount`) | **Descartado** como regla determinista. Único sustituto: `discard[]` del rival es **completo y visible** → «ya gastó sus 2 Boss's Orders» sí es deducible |
| «Apila el mazo / cuenta el orden» | orden del mazo | **NO**, y hay shuffle tras cada búsqueda | **Descartado** |
| «Guarda el gusting para cuando vayas perdiendo» | marcador + gusting condicionado | marcador sí; carta **no existe** (§1.1) | **Descartado como carta**; sobrevive como *puerta* de 3 líneas sobre Boss's Orders |
| «Gestiona el reloj de torneo» | reloj | `actTimeout 0`, 600 s de banco, ~0,03 ms/decisión | **Descartado** (presupuesto ×34.000) |
| «Baraja y corta bien» | — | lo hace el motor | **Descartado** |
| «Lee al rival / gestiona el tilt» | humano | no hay | **Descartado**. Lo que sí queda: **el mulligan revela la mano entera del rival** (log type 6 con `cardId`) — información real y gratis que hoy no usamos |
| «Prize checking entre partidas del match» | best-of-3 | en Kaggle cada episodio es una partida suelta | **Descartado** |
| Aritmética de veneno/quemadura | estados especiales | el campo **no los usa** (0 estados en 200 partidas) | **Congelado** |
| «Gana la moneda y elige» | moneda | **no hay moneda para el asiento**: el jugador 0 elige siempre, select (9,41) | **Se invierte**: es una decisión gratis en ~50 % de las partidas, no azar (§5) |

Dos notas de precisión que hay que llevarse:

- **`current["looking"]` SÍ viene poblado** en partidas reales (`area 12` en los options). Las
  sondas antiguas lo vieron siempre `null` porque la baraja de ejemplo no tiene cartas de «mira
  las N primeras». Esto convierte a R4 de «inimplementable» en «dos líneas».
- **El agente nunca ve la observación final** (log 23 no llega): cualquier detector de fin de
  partida hay que leerlo de `ep["rewards"]`, no de `current["result"]`.

## 1.4 Lo hemos medido nosotros y salió en contra (motivo: evidencia propia)

Este bloque es el más valioso del filtro porque descarta cosas **que las cuatro notas
recomendaban**. Es material de writeup por sí solo.

| Recomendación | Medida que la mata | Estado |
|---|---|---|
| «Probar ir segundo» (E13/N9 v1) | el asiento que elige gana **54,5 %** (n=9.331) y elige primero el **99,4 %**; consistente en 7/7 arquetipos | **Invertida**. La línea `if t == 9: primero` es correcta. Ver §5 |
| «Banca menos / no llenes la banca» (E6/N8) | el **ganador** tiene la banca más llena (3,45 vs 3,07 cuerpos) y expone **más** premios (4,33 vs 3,74), z=+5,6 | **Congelado.** Solo sobrevive la versión estrecha: *no bajar un multi-premio hasta el turno en que se usa* (que no reduce cuerpos, sustituye) |
| «Rama de retirada» | 0,476 IC95 [0,451, 0,501] con n=1.500; y el campo se retira solo el **5,0 %** de las veces que puede — ninguna condición simple sube de ahí | **Descartada como regla.** El caso que sí importa («salvar al ex herido») exige evaluar riesgo de KO, no una heurística de texto |
| «Rama de gusting general» | 0,495 IC95 [0,469, 0,520] con n=1.500 | **Descartada en su forma general.** Sobreviven **dos** puertas estrechas nunca medidas: *gustear solo si cierra la partida* (P2) y *gustear al que no puede retirarse*, `retreat > len(energies)` (N5/P12) |
| «Copiar el shell del campo» (Lunatone/Hariyama/Dudunsparce) | su motor vive en **habilidades (option type 10)** que este piloto clasifica como `None` | **Bloqueado** hasta R6. Meterlas hoy mediría **peor** que lo que tenemos |
| «Neutralization Zone 1247 blinda nuestro paquete de 1 premio» | es **simétrica**: apagaría a nuestro propio Mega Lucario ex contra Alakazam/Dipplin/Froslass/Munkidori/Slowking = el 24 % del campo que ya nos cuesta | **Es una carta contra nosotros** |
| «Regirock ex es nuestro acelerador» | 4 copias de 2 premios; con 4 Mega Lucario ex la lista da **2,00 premios por cuerpo** → el rival gana con 2 KOs (§6) | **Como mínimo bajar a 1 copia** |

## 1.5 Sobrevive, pero requalificado

- **«El daño que sobra no existe» (P7/N3)**: válido, pero aquí casi todo es 2HKO contra Megas de
  300–380 PS, así que la forma útil de la regla no es «no sobrepases», es **«cruza el umbral»**:
  jugar el modificador de daño solo cuando cambia un KO. En el pool eso son 184 ataques (11,8 %
  de 1.558) con «+N more damage» condicional y 26 con «this attack does nothing».
- **«Ordena el turno por reversibilidad» (P5)**: la fuente en desacuerdo
  (<https://levelsptcg.com/pokemon-tcg-turns/>, «suelta los ítems pronto porque no tienen límite
  por turno») no contradice: el orden correcto no es por *tipo de carta* sino por
  *reversibilidad*, con dos excepciones duras (refresco de mano y buscador con descarte).
- **«Cuenta el mazo» (P8/E12)**: real (derrota por `reason 2` verificada, cola hasta 93 turnos),
  pero con mediana de 12 turnos el deck-out es **marginal**. Vale como veto (`deckCount ≤ 6` →
  no encadenar robo), no como plan.
- **Monedas**: 100 cartas del pool llevan `flip a coin`. No es una regla de piloto, es un
  **filtro de construcción**: varianza, mala compañera del 70 % de Model Score.

---

# 2. PRIORIZACIÓN — dónde coinciden la teoría y el diagnóstico empírico

## 2.1 La tabla de cruce

`vol` = decisiones por partida en el corpus de expertos; `brecha` = acuerdo nuestro − suelo
aleatorio en esa clase (`diagnostico-expertos.md` §1–§2); `medido` = efecto ya cuantificado en
política sombra o en `arena.py`.

| Principio (teoría) | Clase de decisión (empírico) | vol/partida | nuestro acuerdo | medido | Veredicto |
|---|---|---|---|---|---|
| **P5/N7/E5 secuenciación** | (0,0) opt7 vs opt8 — 20,7 co-disponibilidades/partida; el experto juega carta 41,2 % / adjunta 22,2 %, **nosotros al revés** (26,0 / 39,7) | 20,7 | 29,0 % (opt7) | **+1,57 pp** en (0,0) | **R1 — oro**: teoría y dato coinciden y el cambio es mover un bloque |
| **E16 cobertura de trainers** | (0,0) opt7 Item: **45,4 % inalcanzables**; Supporter: 29,0 % | 15,3 + 8,5 | — | **+1,06 pp** con R1 | **R2 — oro** |
| **P6/E4/N11 dónde va la energía** | (0,0) opt8 adjuntar, acuerdo 26,0 % vs azar 10,4 % | 10,1 | 26,0 % | proxy **z = −14,6** (energía enterrada 0,448 ganador / 0,718 perdedor) | **R3 — oro**: es la correlación más fuerte del proyecto *y* la métrica que da señal sin ganar partidas |
| **P8 buscar con criterio** | (1,7) búsqueda en mazo, 2ª fuga por volumen | 23,5 | 50,4 % | **+1,35 pp** (jugabilidad) **+1,07 pp** (`area 12`) | **R4 — oro** |
| **P2/P3/N2/N6/N10 premios** | opt13 atacar (41,8 %), (1,1) activo inicial (52,1 %), opt9 evolucionar | 8,8 + 0,8 + 10,1 | 41,8 % | no medido | **R5**: teoría fuerte, dato mudo (el corpus no distingue «mató bien» de «mató»). Pero hay **bug vivo** (§3, R5) |
| P?/R7 habilidades | (0,0) opt10: **58,7 % de las activaciones del campo caen en `None`**; (1,13)/(1,16) Munkidori somos aleatorios | 15,2 + 6,1 | 27,1 % | no medido | **R6 — segundo tier**: enorme en volumen pero **ninguna de nuestras dos barajas vivas lo usa**. Su valor es desbloquear el laboratorio de barajas (Deck Score), no la ladder de hoy |
| N5/P12 gusting estrecho | (1,3) nuevo activo tras KO: **Boss's Orders provoca el 75 %** | 3,7 | 59,9 % | gusting general **0,495** | Segundo tier, con puerta |
| E6/N8 banca | — | — | — | **z = +5,6 en contra** | **Congelado** (§1.4) |
| E13 asiento | (9,41) | 1,0 | 99,7 % | **ya correcto** | No tocar (§5) |
| E19 veneno/quemadura | — | 0 | — | 0 estados en 200 partidas | **Congelado** |

## 2.2 Qué dice el cruce, en una frase

Las cuatro reglas «oro» (R1–R4) **no son tácticas de juego**: son *acceso* y *secuenciación*.
Cubren el 55,8 % del volumen de decisiones (fase principal) y el 15,6 % (búsquedas). Las
tácticas bonitas del papel — prize map, rangos, sacrificios — viven en clases de decisión de
1–9 decisiones por partida. **La teoría de torneo y el diagnóstico empírico coinciden en que
primero hay que dejar de tirar recursos a la basura, y solo después jugar bien.**

## 2.3 El problema de la báscula (y es previo a todo)

| medida | n | IC95 (semiancho) | ¿qué efecto detecta? |
|---|---|---|---|
| ISMCTS vs heurístico: **0,529** [0,466, 0,591] | **240** | ±6,2 pp | nada por debajo de 12 pp de swing |
| retirada 0,476 · gusting 0,495 | 1.500 | ±2,5 pp | swings ≥5 pp |
| lo que hace falta para resolver ±1 pp | **9.604** | ±1,0 pp | — |

Tamaños de muestra para 80 % de potencia, α=0,05, sobre una base de 0,5:
`n ≈ 16·p(1−p)/d²` → **d=5 pp → 400 · d=3 pp → 1.100 · d=2 pp → 2.500 · d=1 pp → 10.000**.

Al ritmo del motor (0,208 s/partida en serie; ~6 partidas/s con `--procs 3`) **n=4.000 son ~11
minutos**. Conclusión operativa dura: **la corrida de n=240 que enterró ISMCTS no midió nada**
(0,529 con n=4.000 daría [0,514, 0,544], es decir, significativo). No estoy diciendo que ISMCTS
funcione; estoy diciendo que **nunca se comprobó**, y que repetir ese error con R1–R5 sería el
peor uso posible del tiempo que queda.

**Protocolo de medición que propongo para todo lo que sigue** (tres niveles, de barato a caro):

- **Nivel 1 — proxy offline, 0 partidas.** Política sombra sobre el corpus de 1.000 episodios
  (`reglas_candidatas.py`) → acuerdo por clase de decisión; y los detectores sobre nuestros
  propios episodios de ladder (`kaggle competitions episodes 55407312`) → `energía_enterrada`,
  `cartas_inertes`, `rango_perdido`, `letal_perdido`. **150.000 decisiones ⇒ potencia sobrada.**
  Recordatorio obligatorio: el acuerdo **no** predice ganar (r = −0,028). Es dirección, no valor.
- **Nivel 2 — A/B propio, espejo.** `arena.py --a <variante> --b research/agentes/heuristico.py
  --n 4000 --procs 3`, misma baraja en los dos lados (aísla piloto). Gate: **no empeora** =
  límite inferior del IC95 ≥ 0,47.
- **Nivel 3 — consistencia contra el campo.** `research/gauntlet.py --n 500 --procs 3` contra
  `c1..c8` (89,8 % del campo real). Métrica que puntúa el Model Score: **WR ponderada por share
  Y peor emparejamiento**. Un cambio que suba la media y hunda el peor emparejamiento **no
  entra**.

---

# 3. TOP-5: especificación de implementación

Formato fijo: **dónde actúa · condición exacta con campos de la obs · qué hace · cómo se mide ·
qué esperaríamos ver · riesgo**. No implemento ninguna.

---

## R1 — Secuenciación: los recursos antes que el compromiso irreversible

> *«Attaching an Energy card is one of the most significant and irreversible commitments you can
> make on your turn, and you should often make it one of the very last actions you take, just
> before you attack.»* —
> <https://tcgprotectors.com/blogs/pokemon-blog/pokemon-tcg-advanced-sequencing-guide-grandmaster-playbook>

**Dónde actúa.** `select.type == 0`, `context == 0` (fase principal). No añade ninguna rama
nueva: **reordena los pasos ya escritos de `_fase_principal`**.

**Condición exacta.** Ninguna: es orden. Actual → propuesto:

```
ACTUAL:    1 bancar<4 · 2 evolucionar · 2b habilidad'robo' · 3 ENERGÍA · 3b acel · 4 tool
           · 5 item"search" · 6 supporter"draw" si mano≤4 · 7 estadio · 7b estadio-efecto
           · 8 atacar · 9 fin
PROPUESTO: 1 bancar<4 · 2b habilidad'robo' · 5' item de recurso · 6' supporter de recurso
           · 2 evolucionar · 3 ENERGÍA · 3b acel · 4 tool · 7 estadio · 7b estadio-efecto
           · 8 atacar · 9 fin
```

Dos matices que **no** están en `diagnostico-expertos.md` R1 y que sí hay que meter:

1. **Evolucionar también baja** (detrás de los recursos, delante de la energía). El dato: cuando
   coexisten «carta de mano» y «evolución», el experto evoluciona el 50,4 % y nosotros el
   **81,4 %**; con «evolución vs habilidad» nosotros evolucionamos el 87,4 % y activamos la
   habilidad el **0,0 %**. Sobre-evolucionar tapa todo lo demás. *Pero* evolucionar sigue por
   delante de la energía: evolucionar cambia a quién conviene adjuntar.
2. **Excepción de refresco de mano (N12).** Si en la mano hay un Supporter cuyo texto contiene
   `shuffle your hand into your deck` o `discard your hand` (Lillie's Determination **1227** —
   2 copias en las **dos** barajas vivas —, Judge 1213, TR Ariana 1216, Harlequin 1223, Lucian
   1237), ese Supporter se juega **el último** del bloque de recursos, después de haber jugado
   items, evolución y energía. Condición evaluable con `textos.get(cid,"")`, que ya está cargado.

**Qué hace.** Jugar Poffin/Ultra Ball/Poké Pad/Cheren cambia qué Pokémon hay en mesa y qué hay en
la mano → cambia **a quién** va la energía, que es el único recurso del turno que no se puede
deshacer (`current["energyAttached"]` se pone a True y no vuelve).

**Cómo se mide.**
- *Nivel 1*: `reglas_candidatas.py` ya lo midió aislado (**O1 = +1,57 pp en (0,0)**, +0,89 global)
  y en combinación (**O1+O3+O5+O6 = +3,66 pp en (0,0)**). Repetir con la excepción N12 añadida y
  con el sub-cambio de evolución, que no se probó.
- *Nivel 1bis, detector nuevo*: `SEQ_ENERGIA_PRONTO` = fracción de turnos propios en que el log 11
  (energía) aparece **antes** del primer log 10 (trainer jugado) del mismo turno. Baseline del
  campo ganador vs perdedor sobre el corpus ya descargado. Es ~30 líneas y da un número absoluto,
  no relativo.
- *Nivel 2*: `arena.py --n 4000`, espejo `hops-snorlax`.
- *Nivel 3*: gauntlet n=500.

**Qué esperaríamos ver.** Nivel 1: acuerdo (0,0) de 33,4 % → ~37 %. Nivel 1bis:
`SEQ_ENERGIA_PRONTO` bajando de ~0,6 a <0,2. Nivel 2: **el efecto honesto esperado es pequeño,
0–3 pp**; con n=4.000 se resuelve. Si sale ≥+2 pp con el límite inferior sobre 0,50, entra.

**Riesgo.** Muy bajo. Cero riesgo de ilegalidad: el motor vuelve a ofrecer el option 8 mientras
`current["energyAttached"]` sea falso, así que retrasar la energía no la pierde. El único riesgo
real es de **coste de reloj**: más selects encadenados por turno; irrelevante con 0,03 ms/decisión
sobre un banco de 600 s.

---

## R2 — Cobertura: dejar de tratar el 45 % de los ítems como si no existieran

**Dónde actúa.** `(0,0)`, options type 7 (jugar carta de la mano). Pasos 5 y 6 de
`_fase_principal`.

**Condición exacta.** Hoy:

```python
if cid is not None and clase(cid) == 1 and "search" in textos.get(cid, ""):   # paso 5, items
if sum(1 for c in mano if clase(c["id"]) not in (5,6)) <= 4:                  # paso 6, supporters
    ... if "draw" in txt or "search" in txt
```

Propuesto — **lista blanca explícita de patrones de recurso**, evaluada sobre
`textos.get(cid, "")` (ya en minúsculas, ya cargado del CSV):

```
RECURSO = ("search", "draw", "look at the top", "look at the bottom",
           "into your hand", "put a pokémon", "attach")
```

y **quitar** la condición «mano no-energía ≤4» del paso 6 (un Supporter es un recurso que caduca
cada turno; el campo lo juega igual — medido **+0,60 pp**).

**Exclusiones deliberadas, y son la mitad de la regla:**

| Patrón | Por qué NO entra |
|---|---|
| `switch in 1 of your opponent's` (Boss's Orders 1182) | gusting general medido **0,495** con n=1.500. Entra solo con la puerta de R5/N5, en su propia corrida |
| `switch your active pokémon` (Switch 1123) | movilidad = retirada por otro medio; retirada medida **0,476** |
| `do 30 more damage` (Premium Power Pro 1141) | es un modificador de daño: jugarlo «porque sí» lo desperdicia. Va en R6-bis, con puerta de umbral |
| efectos de descarte del rival (Crushing/Enhanced Hammer) | no están en nuestras listas; y su puerta correcta es de estado, no de texto |

**Qué hace sobre las barajas vivas** (calculado carta a carta hoy):

| baraja | muertas con v2 | muertas con R2 | qué revive |
|---|---|---|---|
| `hops-snorlax` (envío 55407312) | **6/60** | **4/60** | 2× Night Stretcher 1097 |
| `mega-lucario` (2º envío) | **10/60** | **6/60** | 2× Night Stretcher 1097, 2× Tarragon 1238 |

Las 4 y 6 que quedan son exactamente las exclusiones de arriba (Switch, Boss's Orders, Premium
Power Pro) — es decir, **el resto de cartas muertas no es un bug del filtro, es una decisión de
baraja**: o se sustituyen por cartas que sí jugamos, o se abre R6-bis. Eso es §6.

**Cómo se mide.**
- *Nivel 1*: medido, **O6 = +0,61 pp** solo, **+1,06 pp** con R1. Con las exclusiones nuevas hay
  que remedirlo (la medida original incluía patrones que aquí quito).
- *Nivel 1bis, detector nuevo y el más informativo del plan*: `cartas_inertes_por_partida` sobre
  **nuestros propios episodios de ladder**: por cada carta que pasó por nuestra mano, ¿existió
  alguna vez un option type 7 que la ofreciera y que la política jamás pudiera devolver? Esperado
  hoy: ~0,70 cartas muertas por mano de 7 en `hops-snorlax`, ~1,17 en `mega-lucario`.
- *Nivel 2 y 3*: idem R1.

**Qué esperaríamos ver.** `cartas_inertes` bajando ~33 % en `hops-snorlax` y ~40 % en
`mega-lucario`. En winrate: es la regla con más upside teórico y también la más difícil de
predecir, porque Night Stretcher es una carta de *recursión* y su valor depende de partidas
largas — que es justo donde más divergemos (acuerdo 47,6 % en turnos 0-4 → 23,1 % en turnos 30+).

**Riesgo.** Medio-bajo pero real: **una carta nueva abre selects nuevos**. Night Stretcher abre un
`(1,x)` de descarte que `_elige_cartas` ya cubre (`area 3`, min 1, ya validado 25/25 en
`lab-barajas.md` §4bis). Tarragon abre un select multi-pick de descarte→banca que **no está
verificado**. **Gate obligatorio antes de subir: una sonda corta que confirme la forma de los
selects de cada carta que se activa** — a nivel Kaggle la primera excepción mata la partida.

---

## R3 — La energía va donde vaya a sobrevivir (y nunca al muerto)

> *«To keep ahead in the prize race, your stream of attackers must give up fewer prize cards than
> your opponent's when knocked out—or must avoid being knocked out.»* —
> <https://www.justinbasil.com/guide/main-attacker>

**Dónde actúa.** `(0,0)`, options type 8 con `clase(cid) in (5,6)` (energía). Paso 3 de
`_fase_principal` — solo cambia el **criterio de desempate**, no el orden.

**Condición exacta.** Hoy el criterio es `(0 si le faltan energías, 0 si es el activo, −daño
potencial)`. Es decir: **el activo primero, siempre**. Propuesto, con los campos de la obs:

```
para cada candidato (i, o) con pkm = _pokemon_en(o["inPlayArea"], o["inPlayIndex"], yo):
    faltan   = _coste_mejor(pkm.id) - len(pkm.energies)
    amenaza  = _dano_contra(activo_rival, pkm, cards, atks, atkids=None, extra=1)   # v3, línea 215
    muere    = amenaza >= pkm.hp            # el rival lo mata en su próximo turno
    util     = _mejor_ataque(pkm.id)
orden: (0 si faltan>0 else 1,           # el que no puede atacar aún, primero
        1 si muere else 0,              # NUEVO: penaliza al que va a morir
        0 si es activo else 1,
        -util)
```

`_dano_contra(..., extra=1)` ya existe en `research/agentes/heuristico_v3.py:215` y está
documentado: `extra=1` concede al rival la energía que va a adjuntar en su turno, o sea calcula
la **amenaza del turno siguiente**, no el daño de hoy. Todos los campos que necesita
(`hp`, `energies`, `id`, `weakness` vía catálogo) están en la observación.

**Qué hace.** Implementa E4/N11 y, de paso, N4 (sacrificio deliberado): si el activo muere igual,
la energía se va a la banca y el activo muere **barato**. Ojo con la lectura: el v3 midió que
*huir* (retirarse) es malo (0,476); **esto no es huir, es invertir en el que sobrevive mientras
el otro muere**. Son cosas distintas y hay que decirlo así en el writeup.

**Puerta dura obligatoria.** No aplicar la penalización si el activo es el **único** Pokémon con
energía suficiente para atacar este turno, ni si dejarlo sin energía nos deja sin ataque en un
turno en que teníamos KO disponible.

**Cómo se mide.** Aquí está lo bueno: **esta regla tiene un proxy con potencia estadística
enorme.**
- *Nivel 1*: `energía_enterrada` = Σ energías que murieron adjuntas a su Pokémon ÷ Σ energías
  invertidas, seguida por `serial` (máximo de `len(energies)` visto por serial; se suman los
  serials que desaparecen de `active`+`bench`). **Baseline medido sobre 695 lados de partida del
  campo: 0,448 ganadores vs 0,718 perdedores, z = −14,6.** Medirlo sobre 200 partidas espejo de
  `arena.py` con y sin la regla da ~2.000 energías invertidas por brazo: **detecta diferencias de
  0,03 con holgura**, mientras que el winrate con esas mismas 200 partidas no detecta nada.
- *Nivel 2*: `arena.py --n 4000` espejo. *Nivel 3*: gauntlet n=500.

**Qué esperaríamos ver.** `energía_enterrada` bajando de ~0,7 (somos el perfil del perdedor) hacia
0,5. **Aviso de causalidad, obligatorio en el writeup**: la métrica está confundida — perder
implica que te maten cosas. No se puede leer como «bajar 0,27 da +X % de winrate». Sirve como
**función objetivo intermedia**: si un cambio baja la energía enterrada sin bajar el winrate, va
en la dirección buena.

**Riesgo.** Medio. El fallo modal: el agente deja de cargar al activo y se queda sin atacante.
Por eso la puerta dura. Y `_dano_contra` estima **solo con lo que el rival tiene en mesa**: no ve
su mano, así que subestima sistemáticamente (§1.3). Eso es conservador en la dirección correcta.

---

## R4 — Buscar la pieza que se puede jugar, y no tirar los efectos gratis

**Dónde actúa.** `select.type == 1` (elegir cartas), función `_elige_cartas`. Dos sub-reglas que
comparten función y se miden juntas.

### R4a — `area 12` (`current["looking"]`)

**Condición exacta.** En `id_de(o)`, añadir la rama que falta:

```python
if area == 12:
    return (cur.get("looking") or [])[idx]["id"]
```

y añadir `12` a la lista de áreas de **ganancia**: `if area in (1, 2, 3, 6, 12): return
puntuados[:min(maxCount, len(ops))]`. Y **nunca declinar** un select con `area 12` aunque
`minCount == 0`.

**Por qué.** Hoy `area 12` cae en `CASOS_RAROS` → `None` → `_fallback` → con `minCount 0` devuelve
`[]`: **declinamos el efecto entero**. Pasa en el **5,1 %** de todas las (1,7); el experto declina
el 0,8 %. Cartas afectadas: Pokégear 3.0 **1122**, Bug Catching Set 1094, Dusk Ball 1102. Y hay
confirmación independiente en `lab-barajas.md` §4bis: *«1122 Pokégear funciona (15/20 trae
supporter) pero el heurístico v2 lo declina»*. **Es el arreglo más barato de todo el plan: dos
líneas.**

### R4b — Jugabilidad en `_util` para las búsquedas

**Condición exacta.** En `_elige_cartas`, cuando `area in (1, 12)`, sumar a la utilidad de un
Pokémon:

```
+2,0  si es jugable YA:  cards[cid]["basic"] and len(bench) < 5
                      o cards[cid]["evolvesFrom"] coincide por nombre con un Pokémon propio
                        en juego (active+bench) que NO tenga appearThisTurn
−1,5  si no lo es
```

Los campos `basic` y `evolvesFrom` **están en el catálogo `AllCard` del motor** (verificado).
`appearThisTurn` está en cada Pokémon de la obs y evita buscar la evolución de algo que acaba de
bajar (no se puede evolucionar el turno en que aparece).

**Por qué.** `_util` puntúa Pokémon como `3.0 + daño/1000 + hp/10000`: **la jugabilidad no entra en
la fórmula**. Ejemplo canónico (ep 91002135): con Abra activo, Kadabra en banca y 2 Alakazam en la
mano, el experto busca **Kadabra**; nosotros buscamos **Dudunsparce** (140 hp) porque tiene más
PS — y no hay ningún Dunsparce en la mesa. Patrón agregado: Marnie's Morgrem → nosotros Grimmsnarl
ex (322 veces), Kadabra → Dudunsparce (275). **Siempre igual: el experto busca la pieza que puede
jugar ya, nosotros el ex de más HP.**

**Cómo se mide.**
- *Nivel 1*: medido, **B1 = +1,35 pp** y **B2 = +1,07 pp** en type 1; juntas **+0,90 pp global**
  (acuerdo type1 48,38 % → 50,92 %).
- *Nivel 1bis*: `busquedas_declinadas` (selects con `minCount 0` respondidos `[]`) — hoy 5,1 %,
  objetivo <1 %. Y `busqueda_muerta` = fracción de cartas buscadas que no se juegan ni ese turno
  ni el siguiente.
- *Nivel 2/3*: idem.

**Qué esperaríamos ver.** `busquedas_declinadas` → ~0. En la ladder, esta regla es la que más
probable es que **no** mueva el winrate por sí sola y sí lo mueva combinada con R1+R2 (buscar
mejor solo sirve si luego puedes jugar lo que buscaste).

**Riesgo.** Bajo. R4a puede exponer un `area 12` con semántica distinta a la esperada; el
`_es_legal` + `_fallback` del agente lo cubre sin excepción. Sonda de 20 clics antes de subir.

---

## R5 — Contabilidad de premios: el marcador entra en la política

> *«the true objective is to take your six Prize cards before your opponent takes theirs…
> Understanding how to manage this Prize Race is the single biggest skill that separates
> intermediate players from advanced»* —
> <https://tcgprotectors.com/blogs/pokemon-blog/pokemon-tcg-prize-trade-guide-advanced-prize-mapping>

**Es la única de las cinco que enseña conocimiento de juego y no de software. También es la que
menos frecuencia tiene. Va la quinta por eso — y porque tiene un bug vivo que la paga sola.**

**Dónde actúa.** Cuatro puntos, todos con el mismo dato base.

**Dato base (2 líneas, hoy inexistente).** Valor en premios de una carta, desde
`research/cards_clean.csv` (ya cargado por `_catalogo()`), columna `rule`:

```python
PREMIOS = {cid: 3 if rule == "Mega Pokémon ex" else 2 if rule == "Pokémon ex" else 1}
```

**Verificado en el motor**, no supuesto: 29/29 KOs limpios de Mega ex dieron 3 premios,
123/125 de ex dieron 2, 465/497 normales dieron 1. Coincide con la regla oficial:
*«Mega Evolution Pokémon ex are even more powerful and give up 3 Prize cards when Knocked Out!»*
(<https://tcg.pokemon.com/en-us/expansions/mega-evolution/>). Y el marcador es visible:
`len(cur["players"][i]["prize"])` para **los dos** jugadores (el contenido no, la longitud sí).

**R5a — Ataques condicionados al marcador (BUG VIVO en el envío).**
`Hop's Cramorant 311` lleva `Fickle Spitting [●] 120 :: If your opponent doesn't have exactly 3 or
4 Prize cards remaining, this attack does nothing.` **Hay 2 copias en `hops-snorlax`, que es el
envío que está jugando en la ladder ahora mismo.** `_dmg` devuelve el campo `damage` de
`AllAttack` sin mirar el texto (**confirmar de una sonda que ahí vale 120 y no 0**; el CSV lo
escribe como `Fickle Spitting [●] 120`) → la greedy la elige siempre sobre Smash Kick (50) y
Headbutt (80), y con el rival a 6, 5, 2 o 1 premios **el turno hace 0 daño**. Es decir: cuatro de
los seis valores posibles del marcador. Es literalmente un *dead-end play* — la etiqueta que usa
<https://sixprizes.com/2014/10/02/deft-decisions/> — y lo estamos cometiendo por diseño.
Condición: si el texto del ataque contiene `this attack does nothing`, evaluar su condición contra
`len(prize_rival)` antes de puntuarlo; si no se cumple, **daño 0**. En el pool son 26 ataques.

**R5b — Modificadores condicionales infravalorados.** `Regirock ex 447` tiene
`Giant Rock [{F}●●●] 140 :: If your opponent's Active Pokémon is a Stage 2 Pokémon, this attack
does 140 more damage` = **280 contra el 59 % del campo** (Grimmsnarl + Alakazam + Garchomp +
Dragapult son Stage 2). `_dmg` lee 140 → **infravaloramos nuestro propio atacante a la mitad**
contra la mayoría del campo. Son 184 ataques del pool (11,8 %) con «+N more damage» condicional.
Condición: `supertype` del activo rival está en el catálogo; la comparación es una igualdad.

**R5c — Elegir el objetivo por premios, no por HP.** En opt13, cuando hay más de un objetivo
alcanzable (activo rival, o banca si hay gusting en mano), preferir el que cierre la partida:
`if Σ premios_de_los_KO_alcanzables >= len(mis_premios): esa es la jugada`. Este es el **único**
uso de gusting que no está medido en contra (el general dio 0,495): *gustear solo para letal*.

**R5d — Apertura barata y no sobre-evolucionar (N10/N2).** En `(1,1)` activo inicial y `(1,2)`
banca inicial: preferir `PREMIOS[cid] == 1` a igualdad de utilidad. Y en opt9: **no** evolucionar
a un cuerpo de 3 premios si `_dano_contra(activo_rival, pkm, extra=1) >= hp_de_la_evolución`
(muere igual, y de 1 premio en vez de 3). Regla de papel citada literal:
*«typically you want to open with Solrock against single-Prize decks and with Mega Lucario ex
against the decks where you need to set up»*
(<https://www.pokemon.com/us/features/pokemon-tcg-deck-list-and-strategy-building-a-mega-lucario-ex-deck>);
y de Dark Fox, *«have 2 Riolu down to start, evolve one into Mega Lucario ex, then leave the other
as a Riolu»* (<https://www.darkfoxtcg.com/blogs/news/mega-lucario-deck-matchup-guide>).
**Nota**: `hops-snorlax` es 100 % single-prize, así que R5d **no le afecta**; su valor es para
`mega-lucario` y para el laboratorio de barajas.

**Cómo se mide.**
- *R5a — el más barato y el más urgente*: detector `ataque_nulo` sobre nuestros episodios de
  ladder = veces que atacamos con Fickle Spitting con el rival fuera del rango 3–4 premios. **Si
  ese número es >0,5 por partida, es un arreglo de una línea con efecto directo en el envío
  vivo.** Se mide sin jugar nada.
- *R5b*: detector `dano_infravalorado` = turnos en que elegimos un ataque cuyo daño real
  (con la condición cumplida) era menor que el de otro disponible.
- *R5c/R5d*: detectores `LETAL_PERDIDA` (existía línea con Σpremios ≥ mis premios y no se jugó) y
  `apertura_barata`. Frecuencia esperada baja — por eso van al final.
- *Nivel 2/3*: A/B propio, pero **atención**: R5c toca gusting, que ya dio 0,495. Corrida separada.

**Qué esperaríamos ver.** R5a+R5b son correcciones de estimación: deberían mover el acuerdo en
opt13 (hoy 41,8 %) sin tocar nada más. R5c/R5d son raras pero decisivas: métrica de partida
`premios_ganados / KOs_hechos` (baseline del campo: **1,29**) subiendo, y
`premios_cedidos / KOs_recibidos` bajando.

**Riesgo.** Bajo para a/b (solo cambian una puntuación). Medio para c (gusting). Bajo para d, pero
con una trampa: **no** convertirlo en «nunca evoluciones a Mega ex» — el dato de la banca (§1.4)
ya nos enseñó que las reglas de «expón menos» a ciegas salen al revés.

---

## Segundo tier (no entran en el top-5, y por qué)

| # | Regla | Volumen | Por qué no está arriba |
|---|---|---|---|
| **R6** | **Habilidades: los 3 parches** — `area 7` con `search their deck` → clase `robo` (Spikemuth Gym, 1.665 activaciones del campo); `look at the top/bottom` → `robo` (Drakloak, 644); clase nueva «mover contadores» (Munkidori, 1.852, y destapa (1,13)/(1,16) donde somos aleatorios) | **enorme**: 15,2 decisiones/partida, 58,7 % de las activaciones del campo caen en `None` | **Ninguna de nuestras dos barajas vivas usa esas habilidades.** Su valor es desbloquear el Tramo B del laboratorio (Lunatone, Hariyama, Dudunsparce, `iono-bellibolt` entero) = Deck Score, no ladder de hoy. Si la decisión de baraja del §6 se mueve hacia el shell del campo, **R6 pasa a ser prerrequisito y sube al nº1** |
| R6-bis | Modificador de daño con puerta de umbral: jugar Premium Power Pro 1141 / Black Belt's Training 1211 **solo** si cruza un KO | 2 cartas en `mega-lucario` | Deck-específico. Barato y bonito para el writeup (es «damage control» del papel: <https://www.justinbasil.com/guide/damage>), pero mueve poco |
| R7 | Gusting al que no puede volver (N5/P12): `retreat(objetivo) > len(energies(objetivo))` | 2 copias de Boss's Orders por baraja | Es la tercera puerta que le faltaba al gusting del v3. Merece **una corrida propia** antes de dar el gusting por muerto, no ir mezclada |
| R8 | Marcador → familia de cartas condicionadas (Briar 1201, Counter Gain 1168, Rosa's 1240, Unfair Stamp 1080, N's Sigilyph 277 «ganas la partida») | 0 hoy | **Es decisión de baraja primero.** Sin llevarlas, la puerta no dispara. Pero R5 las habilita gratis |
| ❄️ | Retirada, gusting general, banca menos, veneno/quemadura | — | Medidos en contra o congelados (§1.4) |

---

# 4. Qué NO hacer (lista corta y explícita)

1. **No cambiar la elección de asiento** sin un A/B propio de n≥4.000 (§5).
2. **No implementar retirada ni gusting general.** Dos negativos con n=1.500.
3. **No reducir la banca** por la regla del manual. z=+5,6 en contra.
4. **No copiar el shell del campo** (Lunatone/Hariyama/Dudunsparce) antes de R6: mediría peor.
5. **No volver a lanzar A/B de n=240–400.** No miden nada (§2.3).
6. **No citar cartas del §1.1** en el writeup. Los jueces las conocen.
7. **No subir una carta nueva sin sonda de sus selects.** La primera excepción mata la partida.

---

# 5. PRIMERO O SEGUNDO — la decisión que hacíamos sin pensar (y estaba bien)

## 5.1 Qué dice la teoría del papel

El debate es real y **depende del mazo**, no hay consenso universal:

- El reglamento oficial lo deja escrito como decisión: *«On the first turn of the game, the
  starting player skips this step [attack]… **Think carefully if you want to go first or
  second!**»*, *«The player who goes first cannot play a Supporter card on their first turn»*,
  *«Neither player can evolve a Pokémon on that player's first turn»*
  (<https://www.pokemon.com/static-assets/content-assets/cms2/pdf/trading-card-game/rulebook/tef_rulebook_en.pdf>).
- **Regla de reparto que sí sirve**: los mazos de **montaje / evolución** prefieren **primero**
  (energía primero, evolucionar primero); los mazos **rápidos de 1 energía** prefieren **segundo**
  (atacan primero y ganan la carrera de energía). Fuente:
  <https://sixprizes.com/2009/07/30/is-it-better-to/> — *«quick decks only use 1 energy for their
  usual attacks anyway»* frente a mazos lentos que quieren *«the initial energy attachment»*;
  el mismo reparto aparece en <https://community.pokemon.com/en-us/discussion/18049/going-first-going-second>.
- El «going second is almost always better» que devuelven los buscadores
  (<https://community.pokemon.com/en-us/discussion/13427/going-first-is-simply-worse-than-going-second>)
  es en su mayoría de **TCG Pocket** (§1.2) y no aplica.

**Y aquí está lo importante para nosotros: nuestro campo es de montaje.** El 59 % gana con un
Stage 2 (Grimmsnarl, Alakazam, Garchomp, Dragapult) y otro tramo con Megas (Lopunny/Froslass
12,8 %, Kangaskhan 6,9 %). O sea, **la teoría del papel bien aplicada predice exactamente lo que
medimos**: en un campo de evolución, primero.

## 5.2 Qué dicen nuestros datos

| Fuente | n | Resultado |
|---|---|---|
| Elección del campo | 9.337 | **PRIMERO en el 99,37 %** [0,9919; 0,9951]. Semántica confirmada contra el estado: `option.type==1` → `firstPlayer` en 9.278/9.278 |
| Winrate del que va primero | 9.331 | **54,49 %** [0,5347; 0,5549] |
| Espejo grimmsnarl (aísla la baraja) | 917 | 0,537 [0,504; 0,569] |
| Espejo alakazam | 326 | 0,518 [0,464; 0,572] |
| Espejo dragapult | 64 | 0,562 [0,441; 0,677] |
| Consistencia por arquetipo | 7/7 | Δ(p0−p1) entre **+6,3 y +11,9 pp**; ninguno prefiere segundo |

**Aclaración de unidades que hay que llevar al writeup para no sobrevender**: «ir primero gana el
54,5 %» y «ir primero vale +9 puntos» **son el mismo número**. Δ = WR_primero − WR_segundo =
2·WR_primero − 1 = 9,0 pp. La *ventaja* es **+4,5 pp**; el *swing* entre las dos elecciones es
**9,0 pp**. Las dos formas son correctas; mezclarlas suena a inflar el dato.

## 5.3 Qué dicen nuestros datos **por baraja** (y por qué no bastan)

Del laboratorio de barajas, espejo con n=300 por lista (`docs/writeup-borrador.md` §5, figura 5):

| baraja | primero | segundo | swing | ¿resuelve? |
|---|---|---|---|---|
| Mega Kangaskhan | 0,633 | 0,300 | **+33 pp** | **No.** Con n=300 el SE del swing es ~8 pp → IC95 ±16 pp. Es grande pero medido con una regla de plástico |
| `hops-snorlax` (envío vivo) | 0,540 | 0,480 | +6 pp | **No.** ±16 pp: compatible con cualquier cosa entre −10 y +22 |
| `okidogi` | — | — | **−14,6 pp** | **No**, pero es la única señal de nuestro corpus que apunta a **preferir segundo**, y merece comprobarse |

## 5.4 Recomendación

1. **Mantener PRIMERO como constante.** La evidencia del campo (n=9.331, unánime en 7/7
   arquetipos) es 30× más fuerte que la nuestra por baraja, y **la teoría del papel, bien aplicada
   a un campo de evolución, dice lo mismo**. Cambiarlo por folclore de foros arriesga 9 puntos de
   swing. `heuristico.py:473` (`if t == 9`) está bien y **no se toca**.
2. **Pero medirlo una vez, con potencia.** `arena.py --n 4000 --procs 3`, espejo con la baraja del
   envío, variante idéntica salvo la constante del select (9,41). Coste: 1 línea + ~11 minutos.
   Es la decisión más barata de auditar de todo el proyecto y hoy no está auditada **con nuestra
   baraja**.
3. **Por arquetipo, la hipótesis a comprobar** (no la conclusión) sale de §5.1 y de
   `estrategia-arquetipos.md` §7.7: mazos de montaje lento → primero; mazos rápidos de atacante
   **básico** que ya pegan en su primer turno → segundo. `hops-snorlax` es el único candidato
   nuestro del lado «rápido»: atacante básico (Hop's Snorlax 304, no necesita evolucionar) que
   pega **200 con 2 energías incoloras** gracias a Hop's Choice Band 1171 (`cost {C} less`
   verificado en el motor). **Pero el cálculo fino le quita fuerza al argumento**: aun con la
   rebaja, Dynamic Press pide 2 energías y solo se adjunta 1 por turno, así que ataca en su
   **segundo** turno vaya primero o segundo — el «atacas antes» de ir segundo no le aplica, y el
   turno extra de montaje de ir primero sí. Es decir: la teoría, bien aplicada, tampoco le manda
   ir segundo. La corrida sigue mereciendo la pena, pero la predicción es «primero».
4. **Si algún día se quiere ir segundo por baraja**, el pool tiene soporte dedicado y hoy no lo
   llevamos: Call Bell 1101 y Chill Teaser Toy 1108 (`only if you go second, and only during your
   first turn`) y Scream Tail ex 969 (bloquea el Supporter del rival). Y si se va primero, las
   cartas que **rompen el handicap** atacando en el turno 1: Volbeat 88, Delibird 757, Tapu Koko
   872, Exeggcute 177.
5. **Si la corrida sale ambigua** (IC95 cruzando 0,50), **quedarse en PRIMERO**: es el prior del
   campo y el coste de equivocarse es asimétrico.

*(Todas las corridas de este plan asumen la máquina libre: hoy hay otro trabajo en paralelo y se
ha respetado 1 proceso, sin jugar ni una partida.)*

---

# 6. LA DECISIÓN DE BARAJA — el número que resume todo (para el propietario)

Coste de implementación: **cero líneas de código**. Impacto: 20 % del Deck Score y, por lo que
dice §8.0 de `estrategia-deckbuilding.md`, buena parte del «perdemos de forma consistente».

Calculado hoy carta a carta sobre las 23 listas (`rule` de `cards_clean.csv`, 3/2/1 premios):

| lista | Pk | 1p | 2p | 3p | **premios por cuerpo** | **KOs que necesita el rival (mejor caso)** |
|---|---|---|---|---|---|---|
| **`propios/mega-lucario`** (2º envío) | 12 | 4 | 4 | 4 | **2,00** | **2** |
| `propios/mega-kangaskhan` | 10 | 6 | 0 | 4 | 1,80 | 2 |
| `propios/abomasnow-plus` | 11 | 7 | 0 | 4 | 1,73 | 2 |
| `propios/okidogi` | 8 | 4 | 4 | 0 | 1,50 | 3 |
| `campo/c7-lucario-campo` (la misma carta ganadora) | 16 | 12 | 0 | 4 | **1,50** | 2 |
| `campo/c1-grimmsnarl` (31,2 % del campo) | 18 | 15 | 3 | 0 | **1,17** | 3 |
| `campo/c2-alakazam` (18,2 %) | 19 | 18 | 1 | 0 | **1,05** | 5 |
| `campo/c8-dipplin` · `meta/alakazam-v10` · `meta/great-tusk-v10` | 18/19/13 | todos | 0 | 0 | **1,00** | **6** |
| **`propios/hops-snorlax`** (envío vivo) | 12 | 12 | 0 | 0 | **1,00** | **6** |

Y el cruce con el campo real ponderado por su share medido (c1..c8 = 89,8 % de 18.674 barajas):

> **Contra el campo medio, nosotros necesitamos ~4,8 KOs** (mejor caso 3,3). El campo, contra
> `hops-snorlax`, necesita **6,0**. Contra `mega-lucario`, **3,0** (y en el mejor caso **2**).

Es decir: `hops-snorlax` gana la carrera de premios **0,80 KOs contra 1**; `mega-lucario` la pierde
**1,59 contra 1**, con la misma calidad de piloto y sin depender de ningún emparejamiento. El
baseline del campo (1,29 premios por KO, medido sobre 264 KOs) confirma la escala del cálculo.

**Consecuencia práctica**: cualquier trabajo de piloto sobre `mega-lucario` está pagando un peaje
de 1,59× antes de empezar. Si el propietario quiere conservar el arquetipo, las tres palancas
baratas y reversibles ya están escritas en `estrategia-deckbuilding.md` §9bis Tramo A (energía
19→12; 4 Regirock ex → paquete de 1 premio; ACE SPEC Master Ball → Maximum Belt 1158), y todas
funcionan **con el piloto de hoy**. Lo que **no** se puede hacer hoy es el Tramo B (Lunatone /
Hariyama / Dudunsparce): su motor son habilidades y necesita R6.

**Esto es una puerta del propietario, no mía**: fija dirección y compromiso con el envío.

---

# 7. MATERIAL DE WRITEUP (inglés, listo para pegar)

Contexto: `docs/writeup-borrador.md` ya está en **1.993 palabras** sobre un límite de 2.000. Estos
cinco párrafos son **sustituciones/ampliaciones**, no añadidos: §7.1 y §7.2 refuerzan la sección 6
(Deck concept, 20 % Deck Score), §7.3 y §7.4 van a la sección 4-5 (Model Score), §7.5 a la
sección 8. Cada número está medido o calculado por nosotros; ninguna carta citada está fuera del
pool.

## 7.1 — Deck concept: the prize map (Deck Score)

> **The deck is a prize map, not a damage plan.** Six prizes end the game, so the only question
> that matters is how many knockouts each side needs. We computed this for all 23 lists we hold —
> ours, the field's, and the public samples — by scoring every Pokémon 1/2/3 prizes from its rule
> box, a mapping we verified inside the engine rather than assuming: over 250 sampled episodes,
> clean knockouts on a Mega Evolution Pokémon ex paid 3 prizes in **29 of 29** cases, Pokémon ex
> paid 2 in 123 of 125, and ordinary Pokémon paid 1 in 465 of 497. Our Mega Lucario list averages
> **2.00 prizes per body**: an opponent wins it in **two** knockouts. Our Hop's Snorlax list
> averages **1.00**: it takes **six**. Weighted by the measured share of the real field (eight
> lists covering 89.8% of 18,674 decks read out of ladder replays), we need about **4.8** knockouts
> to close a game. So the same pilot, holding the same cards, wins the prize race 6-to-4.8 with one
> list and loses it 3-to-4.8 with the other. That is what "consistent, not matchup-dependent" looks
> like when you write it as arithmetic instead of as a claim.

## 7.2 — Deck concept: why these cards (Deck Score)

> **Hop's Snorlax, single-prize, two colourless energy.** Dynamic Press costs three Colorless for
> 140; Hop's Choice Band makes it cost one Colorless *less* and hit 30 harder, and Snorlax's own
> Extra Helpings adds another 30 to every Hop's attack. We verified all three modifiers stacking
> against the engine's damage log: **200** damage, or **230** under our Postwick stadium, from an
> attacker holding **two energies of any type**. Two colourless energies is a deckbuilding decision
> as much as a damage one — it removes every colour decision from the pilot and every dead energy
> from the hand. Around it: Hop's Bag puts two Basic Hop's Pokémon straight onto the bench
> (verified: bench +2), Hop's Dubwool drags a benched attacker into the Active spot *as it
> evolves*, which is a gust that does not spend our one Supporter for the turn, and Hop's Cramorant
> is a finisher gated on the opponent sitting at exactly three or four prizes. Nothing in the list
> has a rule box. There is no card whose loss costs us half the game, and nothing to play around:
> a deck with no ex cannot be blown out by one unlucky knockout, which is the "does not depend on
> situational swings" axis written into the sixty cards rather than into the agent.

## 7.3 — Going first: measuring instead of quoting (Model Score)

> **We looked up the received wisdom, then measured it, and it was the wrong game.** In this
> environment player 0 always receives the choice of going first or second — there is no coin flip
> for it, so half of all ladder games contain a free decision made before a single card is seen.
> The most common advice online is to go second; almost all of it turns out to describe Pokémon TCG
> Pocket, a different game with three prizes, a three-slot bench and automatic energy. We read the
> choice out of **9,337** episodes: the field takes first **99.4%** of the time, and the player who
> goes first wins **54.5%** of 9,331 decisive games (95% CI [53.5, 55.5]) — a **9-point swing**
> between the two options. The effect holds in all seven archetypes we can identify, from +6.3 to
> +11.9 points, and it survives in mirrors where both sides play the same list. The paper theory,
> applied properly rather than quoted, agrees: setup and evolution decks want the first energy
> attachment and the first evolution, and **59% of this field wins with a Stage 2**. Our agent was
> already choosing first — but it was choosing first as a constant, and the difference between a
> constant that happens to be right and a decision we can defend is the whole point of the rubric.

## 7.4 — The turn is a sequence, and energy is the irreversible part (Model Score)

> **The largest single leak in our policy was not what it played but when.** We reconstructed
> 161,644 (observation, action) pairs from the replays of the strongest teams and asked our own
> heuristic what it would have done in each. It agrees 44% of the time against a 21% random-legal
> floor — and the disagreement concentrates in one place. When both an energy attachment and a card
> from hand are legal, the strong players play the card 41% of the time and attach 22%; **we do the
> exact opposite**, playing the card 26% and attaching 40%. That is the classic sequencing error
> with a number attached to it: the energy attachment is the one action of the turn that cannot be
> undone, and playing it before the searches and the draws means committing before you know what
> your board will be. The same ordering shows up in the field's own turns: strong players open 64%
> of their turns with a resource — a card or an ability — and leave the attack for the end. The
> engine agrees with the physical rulebook here, which we confirmed rather than assumed: across 269
> games there were **zero** Supporters, **zero** attacks and **zero** evolutions on the first
> player's first turn. With a median game of **12 turns**, that first turn is a twelfth of the
> game, and half of the game is setup: the winner has **3.17** energies in play on turn 5, the
> loser **1.91**.

## 7.5 — What we measured and then retracted (Model Score / honesty)

> **Three of our own recommendations died on contact with the data, and we think that is the
> result worth reporting.** We had written down "bench fewer Pokémon, expose fewer prizes" from the
> standard literature; in this field the *winners* carry the fuller bench (3.45 bodies against 3.07)
> and expose *more* prizes (4.33 against 3.74), at z = +5.6. The honest reading is that the
> correlation is confounded — a full bench is mostly a symptom of a functioning engine, and the
> player who stalls benches nothing — but it is still enough to stop us shipping the rule, and only
> the narrow version survives ("do not bench a multi-prize Pokémon until the turn you use it"). We
> also built and measured a retreat rule (0.476 over 1,500 games) and a gusting rule (0.495 over
> 1,500) and shipped neither. The strongest correlation we found points the other way and is one we
> can act on: across 695 player-games, losers finish with **72%** of the energy they invested buried
> on Pokémon that were knocked out, against **45%** for winners — the largest effect size in the
> project, and, unlike win rate, a quantity we can measure to significance in two hundred games
> instead of four thousand. We report it as an intermediate objective, not as a causal claim.

---

# 8. Fuentes

**Primarias y verificables.** Reglamento oficial en PDF de pokemon.com (citado literal);
<https://tcg.pokemon.com/en-us/expansions/mega-evolution/> para «3 Prize cards» de Mega ex;
<https://www.pokemon.com/us/features/pokemon-tcg-deck-list-and-strategy-building-a-mega-lucario-ex-deck>
para la regla de apertura del arquetipo. **Y nuestro propio corpus**: todas las cifras de §2, §5 y
§6 salen de `data/replays/` y de `research/cards_clean.csv`, no de la web.

**Comunidad sólida.** <https://www.justinbasil.com/guide/main-attacker> (responsabilidad en
premios), `/guide/secondary-attackers` (atacantes de un premio), `/guide/gusting`,
`/guide/disruption`, `/guide/deck-strategy` (taxonomía agresión/control/mill/stall),
`/guide/damage` (umbrales), `/guide/consistency`. <https://sixprizes.com/2013/05/08/card-advantage-in-the/>
(ventaja de cartas), <https://sixprizes.com/2014/10/02/deft-decisions/> (*technical* vs *strategic
play*, y el concepto de **dead-end play** que R5a detecta literalmente),
<https://sixprizes.com/2009/07/30/is-it-better-to/> (asiento por tipo de mazo; era Diamond/Pearl,
usar solo el reparto cualitativo).

**Secundarias, con pinzas.** `tcgprotectors.com` y `levelsptcg.com` son blogs de tienda: sus
**principios** coinciden con el resto, pero **ningún dato numérico ni nombre de carta de ahí debe
ir al writeup sin comprobarlo** contra `cards_clean.csv`. `pokebeach.com` devuelve HTTP 403: lo
citado viene de extractos del buscador. `play.limitlesstcg.com`: matchups de otro campo (§1.2).

**Descartadas por no ser este juego.** game8.co, cardgamer.com, sportskeeda (TCG Pocket);
trainertower.com (VGC).
