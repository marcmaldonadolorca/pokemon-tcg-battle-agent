# Diagnóstico contra expertos reales — dónde se separa heuristico.py del campo top (2026-08-10)

Qué es: se reconstruyen pares (observación, acción del experto) de los replays diarios de los
equipos mejor valorados, se le pregunta a `research/agentes/heuristico.py` qué habría hecho en
esa misma observación y se desglosa el acuerdo por clase de decisión. **No se juega ni una
partida ni se ejecuta código de terceros.** El objetivo es localizar fugas, no clonar.

Scripts nuevos (todos en `research/replays/`):
`diagnostico_expertos.py` (pasada principal → `data/replays/diagnostico_expertos.pkl`),
`informe_expertos.py` (tablas), `ejemplos_expertos.py` (ejemplos concretos con nombres de carta),
`fugas_detalle.py` (co-disponibilidad, orden de turno, contextos), `cobertura_trainers.py`
(qué cartas son inalcanzables), `reglas_candidatas.py` (política sombra: mide el efecto de cada
regla candidata **sin tocar `heuristico.py`**), `habilidades_y_señal.py`.

Muestra: **1.000 episodios** (500 de 2026-08-08 + 500 de 2026-08-09, muestreo aleatorio con semilla),
**303 equipos distintos**, **161.644 decisiones**, de las cuales **150.729 con elección real**
(10.915 forzadas: una sola acción legal posible). El desfase +1 se vuelve a validar aquí:
**0 acciones del experto ilegales en 161.644** (con desfase 0 serían ~34% imposibles).

---

## 0. Titulares

| medida | valor |
|---|---|
| Acuerdo heurístico v2 ↔ expertos | **43,83%** (n=150.729) |
| Suelo: aleatorio legal (probabilidad exacta, no muestreada) | **21,10%** |
| Neto sobre el suelo | **+22,73 pp**; normalizado (acc−azar)/(1−azar) = **28,8%** |
| Acuerdo corregido por **identidad de carta** (elegir otra copia de la misma carta no es desacuerdo) | **47,84%** (base 43,13% en la submuestra de 300 ep.) |
| Fallback de la política (no supo / propuso ilegal) | 2,29% de las decisiones |
| Fugas concentradas | (0,0) fase principal = **55,8%** del volumen y **65,7%** de los fallos |

Dos cautelas que hay que llevarse al writeup, medidas aquí:

1. **Elegir otra copia de la misma carta cuenta como desacuerdo y no lo es.** Al comparar por
   identidad de carta en vez de por índice, el acuerdo sube de 43,13% a **47,84%** (+4,71 pp).
   El 42,66% de `replays-imitacion.md` está deprimido por lo mismo. La cifra honesta es ~47-48%.
2. **Parecerse a nosotros NO predice perder.** Correlación entre el acuerdo de un jugador-episodio
   con nuestra política y ganar esa partida: **r = −0,028** (n=1.000 jugador-episodios);
   winrate por quintil de acuerdo: 48,0% / 51,0% / 49,5% / 56,0% / 45,5% — sin tendencia.
   → *El acuerdo es una medida de divergencia, no de calidad.* Cerrar una fuga es una hipótesis
   con evidencia de dirección, no una mejora demostrada de winrate. **Toda regla que salga de aquí
   tiene que pasar por `arena.py` antes de subir.**

---

## 1. Tabla de acuerdo por clase de decisión `(select.type, select.context)`

`dec/part` = decisiones de esa clase por partida (2 jugadores). `neto` = acuerdo − suelo aleatorio.

| (type,ctx) | qué es | n | %tot | acuerdo | azar | neto | dec/part | fallos |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| (0,0) | fase principal | 84.038 | 55,8% | **33,8%** | 16,0% | +17,8 | 84,0 | 55.595 |
| (1,7) | búsqueda en mazo | 23.509 | 15,6% | **50,4%** | 19,7% | +30,7 | 23,5 | 11.664 |
| (1,4) | nuevo activo al retirar | 4.391 | 2,9% | 55,5% | 27,4% | +28,1 | 4,4 | 1.953 |
| (1,21) | Grimmsnarl ex / Mega Lucario ex | 3.976 | 2,6% | 70,9% | 36,7% | +34,2 | 4,0 | 1.157 |
| (9,43) | — | 3.756 | 2,5% | 96,1% | 50,0% | +46,1 | 3,8 | 148 |
| (1,13) | **Munkidori (Adrena-Brain)** | 3.698 | 2,5% | **25,2%** | 22,7% | **+2,5** | 3,7 | 2.767 |
| (1,3) | nuevo activo tras KO | 3.691 | 2,4% | 59,9% | 26,9% | +33,0 | 3,7 | 1.481 |
| (8,40) | Munkidori | 3.508 | 2,3% | 99,3% | 36,2% | +63,1 | 3,5 | 25 |
| (1,5) | Buddy-Buddy Poffin | 2.962 | 2,0% | 58,5% | 21,5% | +37,0 | 3,0 | 1.229 |
| (1,14) | **Dragapult ex** | 2.772 | 1,8% | **30,2%** | 27,4% | **+2,8** | 2,8 | 1.935 |
| (1,22) | elegir del descarte | 2.397 | 1,6% | 70,0% | 25,6% | +44,4 | 2,4 | 720 |
| (1,16) | **Munkidori** | 2.396 | 1,6% | **42,9%** | 39,7% | **+3,2** | 2,4 | 1.368 |
| (1,8) | **descarte de coste (Ultra Ball, Xerosic)** | 2.064 | 1,4% | **10,8%** | 10,7% | **+0,1** | 2,1 | 1.841 |
| (1,15) | Grimmsnarl ex | 1.994 | 1,3% | 34,3% | 26,9% | +7,4 | 2,0 | 1.310 |
| (9,41) | primero/segundo | 1.000 | 0,7% | 99,7% | 50,0% | +49,7 | 1,0 | 3 |
| (1,2) | banca inicial | 900 | 0,6% | 69,8% | 44,4% | +25,4 | 0,9 | 272 |
| (4,30) | descartar energía adjunta | 846 | 0,6% | 66,9% | 40,5% | +26,4 | 0,8 | 280 |
| (1,1) | activo inicial | 842 | 0,6% | 52,1% | 45,8% | +6,3 | 0,8 | 403 |
| (7,37) | Rare Candy | 507 | 0,3% | 92,3% | 40,2% | +52,1 | 0,5 | 39 |
| (8,38) | robo extra por mulligan | 441 | 0,3% | 98,0% | 44,0% | +53,9 | 0,4 | 9 |
| (1,9) | — | 337 | 0,2% | 37,1% | 15,4% | +21,7 | 0,3 | 212 |
| (6,35) | — | 246 | 0,2% | 96,3% | 50,0% | +46,3 | 0,2 | 9 |
| (4,33) | — | 175 | 0,1% | 41,1% | 27,2% | +13,9 | 0,2 | 103 |
| (1,17) | — | 141 | 0,1% | 48,2% | 46,9% | +1,3 | 0,1 | 73 |
| resto (10 clases) | | 142 | 0,1% | — | — | — | — | 66 |

**Clases donde somos literalmente aleatorios** (neto ≤ +3,2 pp): `(1,13)`, `(1,14)`, `(1,16)`,
`(1,8)`, `(1,17)`. Juntas: 11.071 decisiones (7,3% del total) y **7.984 fallos**. Se identifica
por fin quién las provoca (`fugas_detalle.py` §E, campo `effect`):

| contexto | carta que lo provoca | qué es |
|---|---|---|
| (1,13) y (1,16) | **Munkidori** (100%) | Adrena-Brain: mover contadores de daño |
| (1,14) | **Dragapult ex** (100%) | reparto de daño del ataque |
| (1,8) | **Ultra Ball** (52%), Xerosic's Machinations, Lunatone, Hand Trimmer | descartar N de la mano como coste |
| (1,21) | Marnie's Grimmsnarl ex (78%), Mega Lucario ex | — |
| (1,5) | Buddy-Buddy Poffin (85%) | — |
| (1,15) | Marnie's Grimmsnarl ex (97%) | — |
| (7,37) | Rare Candy (100%) | elegir el básico a evolucionar |
| (1,3) | **Boss's Orders (75%)**, Switch | promoción forzada del rival |

Nota: `(1,8)` **no** es «elegir 3 de la mano» como decía `motor-mecanica.md`; en el campo real es
el descarte de coste de Ultra Ball y similares, y ahí estamos exactamente en el suelo aleatorio
(10,8% vs 10,7%). Como Ultra Ball va **4× en las dos barajas vivas**, esto nos toca de lleno.

---

## 2. Dentro de (0,0): desglose por tipo de jugada del experto

| opt | jugada | n | %tot | acuerdo | azar | neto | dec/part | fallos |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 7 | jugar carta de la mano | 34.991 | 23,2% | **29,0%** | 16,2% | +12,8 | 35,0 | **24.840** |
| 10 | habilidad | 15.182 | 10,1% | **27,1%** | 13,9% | +13,2 | 15,2 | **11.074** |
| 9 | evolucionar | 10.128 | 6,7% | 69,0% | 12,1% | +56,9 | 10,1 | 3.142 |
| 8 | adjuntar (energía/tool) | 10.063 | 6,7% | **26,0%** | 10,4% | +15,7 | 10,1 | 7.446 |
| 13 | atacar | 8.763 | 5,8% | 41,8% | 23,5% | +18,3 | 8,8 | 5.096 |
| 14 | fin de turno | 2.613 | 1,7% | 35,0% | 35,0% | **−0,1** | 2,6 | 1.699 |
| 12 | **retirada** | 2.298 | 1,5% | **0,0%** | 19,5% | **−19,5** | 2,3 | 2.298 |

### Matriz de confusión (filas = experto, columnas = nosotros)

```
experto \ nuestro        7        8        9       10       12       13       14  |  total
7  jugar carta       19237     6737     3057     2265        0     2273     1422  |  34991
8  adjuntar           1540     6409     1124      990        0        0        0  |  10063
9  evolucionar        1565        0     8563        0        0        0        0  |  10128
10 habilidad          3570     2231     2644     4483        0     1535      719  |  15182
12 retirada            712      386      255      279        0      353      313  |   2298
13 atacar             2380      724      904      847        0     3908        0  |   8763
14 fin de turno       1172      200      198       58        0       71      914  |   2613
total nuestro        30176    16687    16745     8922        0     8140     3368  |  84038
```

### La tabla que lo explica todo: quién elige qué cuando ambas jugadas están disponibles

| par disponible | n | experto | nosotros | lectura |
|---|---:|---|---|---|
| **7 vs 8** (carta vs energía) | 20.689 | 7: 41,2% / 8: 22,2% | 7: 26,0% / **8: 39,7%** | **adjuntamos energía demasiado pronto**: la relación se invierte |
| **7 vs 10** (carta vs habilidad) | 18.577 | 10: **40,0%** / 7: 34,5% | 10: 25,0% / 7: 31,9% | infrautilizamos habilidades |
| **8 vs 10** | 10.678 | 10: **42,8%** / 8: 18,4% | 10: 29,7% / 8: 30,4% | ídem, y otra vez energía primero |
| **7 vs 9** (carta vs evolución) | 10.274 | 9: 50,4% / 7: 23,8% | 9: **81,4%** / 7: 18,6% | **sobre-evolucionamos** |
| **9 vs 10** | 5.340 | 9: 37,8% / 10: 32,6% | 9: **87,4%** / 10: **0,0%** | evolucionar tapa por completo la habilidad |
| **9 vs 13** | 6.560 | 9: 48,9% / 13: 8,9% | 9: 86,6% / 13: **0,0%** | ídem con el ataque |
| **8 vs 9** | 6.066 | 9: 51,2% / 8: 12,3% | 9: 82,8% / 8: **0,0%** | ídem |
| **cualquiera vs 12** | 46.375 | 12: 5,0% | 12: **0,0%** | nunca nos retiramos |

Orden de jugada del experto dentro del turno (posición 0 = primera acción del turno):

| posición | opt7 | opt8 | opt9 | opt10 | opt12 | opt13 | opt14 | n |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 37,5% | 11,0% | 18,4% | **26,1%** | 1,3% | 3,5% | 2,2% | 7.974 |
| 3 | 44,6% | 12,9% | 11,6% | 17,0% | 2,8% | 7,7% | 3,3% | 6.223 |
| 7+ | 38,5% | 9,4% | 7,8% | 11,4% | 3,5% | **24,9%** | 4,5% | 8.908 |

El campo abre el turno con **recursos** (cartas de mano y habilidades: 63,6% de las primeras
jugadas) y deja el adjunte de energía repartido y el ataque para el final. Nuestra prioridad
fija es: bancar básicos → **evolucionar** → habilidad de robo → **energía** → tool → item de
búsqueda → supporter → estadio → ataque. Es decir, gastamos el recurso irreversible del turno
(la energía) y la evolución **antes** de haber jugado las cartas que cambian lo que hay en la mano.

---

## 3. Cobertura: el 17,1% de las jugadas de carta del experto son INALCANZABLES para nosotros

`cobertura_trainers.py` comprueba, carta a carta, si `_fase_principal` podría devolverla alguna vez.
De 55.182 jugadas de tipo 7/8/9 del experto, **9.441 (17,1%) son imposibles para nuestra política,
y explican el 26,6% de sus fallos**.

| opción / tipo de carta | n | fallos | inalcanzables | % |
|---|---:|---:|---:|---:|
| opt7 **Item** | 15.336 | 12.439 | **6.966** | **45,4%** |
| opt7 **Supporter** | 8.544 | 7.072 | **2.475** | **29,0%** |
| opt7 Pokémon / opt9 evolución / opt8 energía y tool / opt7 estadio | 31.302 | 15.917 | 0 | 0% |

Causa exacta: en `_fase_principal` un **item** solo es jugable si su texto contiene `"search"`
(paso 5) y un **supporter** solo si contiene `"draw"`/`"search"` **y** la mano no-energía es ≤4
(paso 6). Todo lo demás no tiene ninguna rama que lo devuelva.

Cartas que el campo juega y nosotros nunca podemos jugar (top): Night Stretcher (1.694),
Boss's Orders (1.170), Pokégear 3.0 (1.107), Rare Candy (846), Bug Catching Set (613),
Unfair Stamp (599), Crushing Hammer (580), Wally's Compassion (531), Xerosic's Machinations (502),
Enhanced Hammer (334), Jumbo Ice Cream (249), Sacred Ash (224), Lana's Aid (199), Switch (135).

### Esto nos afecta a NOSOTROS, no solo al campo

Aplicando la misma comprobación a las dos barajas que están en la ladder:

| baraja | cartas muertas para nuestro propio agente | % del mazo |
|---|---|---:|
| `hops-snorlax` (envío 55407312) | 2× Boss's Orders, 2× Switch, 2× Night Stretcher | **10,0%** |
| `mega-lucario` (2º envío) | 2× Switch, 2× Night Stretcher, 2× Premium Power Pro, 2× Tarragon, 2× Boss's Orders | **16,7%** |

Son 6 y 10 cartas de 60 que el piloto **jamás jugará**. En una mano de 7 son 0,70 y 1,17 cartas
muertas de media, todos los turnos. Sumado a que nunca nos retiramos y nunca jugamos Switch,
**el agente no tiene ninguna manera de cambiar su Pokémon activo salvo que se lo noqueen**.

---

## 4. Ranking de fugas (volumen × brecha)

Ordenado por decisiones perdidas = n·(1−acuerdo). `f/part` = fallos por partida.

| # | clase | n | acuerdo | azar | fallos | f/part | diagnóstico |
|---|---|---:|---:|---:|---:|---:|---|
| 1 | **(0,0) opt7 jugar carta** | 34.991 | 29,0% | 16,2% | **24.840** | 24,8 | orden (energía antes que recursos) + 45% de los items inalcanzables |
| 2 | **(1,7) búsqueda en mazo** | 23.509 | 50,4% | 19,7% | **11.664** | 11,7 | `_util` es codicioso de estadísticas e ignora si la carta es jugable |
| 3 | **(0,0) opt10 habilidad** | 15.182 | 27,1% | 13,9% | **11.074** | 11,1 | 58,7% de las habilidades que activa el campo caen en `None` |
| 4 | (0,0) opt8 adjuntar | 10.063 | 26,0% | 10,4% | 7.446 | 7,4 | adjuntamos pronto y al objetivo equivocado |
| 5 | (0,0) opt13 atacar | 8.763 | 41,8% | 23,5% | 5.096 | 5,1 | `_dmg` estima mal los ataques condicionales |
| 6 | (0,0) opt9 evolucionar | 10.128 | 69,0% | 12,1% | 3.142 | 3,1 | acertamos cuál, fallamos cuándo (sobre-evolucionamos) |
| 7 | (1,13)+(1,16) Munkidori | 6.094 | 32,2% | 29,4% | 4.135 | 4,1 | **aleatorios**: no sabemos mover contadores de daño |
| 8 | (0,0) opt12 retirada | 2.298 | **0,0%** | 19,5% | 2.298 | 2,3 | recorte deliberado; ver §6 |
| 9 | (1,4) nuevo activo al retirar | 4.391 | 55,5% | 27,4% | 1.953 | 2,0 | — |
| 10 | (1,14) Dragapult ex | 2.772 | 30,2% | 27,4% | 1.935 | 1,9 | **aleatorios** |
| 11 | (1,8) descarte de coste (Ultra Ball) | 2.064 | 10,8% | 10,7% | 1.841 | 1,8 | **exactamente aleatorios**, y llevamos 4× Ultra Ball |
| 12 | (0,0) opt14 fin de turno | 2.613 | 35,0% | 35,0% | 1.699 | 1,7 | terminamos el turno antes de tiempo |

El acuerdo cae con la complejidad y con la duración de la partida: 73,6% con 2 opciones →
23,4% con ≥15 opciones; 47,6% en los turnos 0-4 → 23,1% en los turnos 30+. **Las partidas
largas contra barajas del meta son exactamente donde más divergemos**, y son las que decide el
Model Score por consistencia.

---

## 5. Ejemplos concretos de las tres fugas mayores

Reproducibles con `.venv/bin/python research/replays/ejemplos_expertos.py 00:7:8 5` etc.

### Fuga 1 — (0,0) opt7: el experto juega una carta, nosotros adjuntamos energía

**a)** ep 91088154, paso 110, Luca (ganó), turno 10. Activo N's Zoroark ex a **40/280 hp**;
mano: N's PP Up, 2× Poké Pad, Boss's Orders, **Night Stretcher**, 2× Basic {D} Energy.
Experto: **juega Night Stretcher** (recupera Pokémon/energía del descarte a la mano).
Nosotros: adjuntamos {D} Energy al banca#2. Night Stretcher **no tiene ninguna rama** en
nuestra política (item sin `"search"`).

**b)** ep 91087127, paso 113, A. R. SEKKAT, turno 12. Grimmsnarl ex activo con 6 energías (ya
puede atacar por 180), mano de 8 con Team Rocket's Petrel.
Experto: **juega el supporter Petrel**. Nosotros: adjuntamos otra {D} Energy al banca#0 — energía
número 7 sobre un atacante que ya tenía de sobra, y perdemos el supporter del turno.

**c)** ep 91199326, paso 15, Jie Orkarin (ganó), turno 2. Mano con Petrel, **Pokégear 3.0**,
2× Rare Candy, Grimmsnarl ex.
Experto: **Pokégear 3.0** (busca supporter entre las 7 primeras). Nosotros: energía al activo.
Pokégear 3.0 y Rare Candy son ambos inalcanzables para nosotros.

**d)** Patrón agregado (n=20.689): cuando hay a la vez carta de mano y adjunte, el experto juega
la carta 41,2% / adjunta 22,2%; nosotros jugamos la carta 26,0% / adjuntamos **39,7%**.

**e)** Patrón agregado de cobertura: 45,4% de todas las jugadas de item del campo caen en cartas
que nuestro código no puede devolver nunca.

### Fuga 2 — (1,7) búsqueda en mazo: buscamos la carta más gorda, no la jugable

**a)** ep 91002135, paso 47, Team Rot-Weiß, turno 4. En juego: **Abra** activo, **Kadabra** en
banca, otro Abra en banca; mano con **2× Alakazam**. Opciones del mazo: 2× Dudunsparce, 2× Kadabra.
Experto: **Kadabra** (evoluciona el segundo Abra y encadena a Alakazam). Nosotros: **Dudunsparce**,
que evoluciona de Dunsparce — carta **muerta**, no hay ningún Dunsparce en juego ni en la mano.
Causa: `_util` puntúa Pokémon como `3.0 + daño/1000 + hp/10000`; Dudunsparce (140 hp) gana a
Kadabra (80 hp). **La jugabilidad no entra en la fórmula.**

**b)** El mismo patrón, agregado: Marnie's Morgrem → nosotros Grimmsnarl ex (322 veces),
Kadabra → Dudunsparce (275), Marnie's Impidimp → Grimmsnarl ex (261), Dunsparce → Dudunsparce (161).
Siempre igual: el experto busca **la pieza que puede jugar ya**, nosotros **el ex de más HP**.

**c)** ep 91462123, paso 55, YumeNeko (ganó), turno 5, efecto **Pokégear 3.0**, 3 opciones de
`area 12`, `minCount 0`. Experto: coge una. Nosotros: **`[]` — declinamos el efecto entero.**
Causa: `_elige_cartas` no contempla `area 12`, cae a `CASOS_RAROS` → `None` → `_fallback` →
con `minCount 0` devuelve `[]`. **Descubrimiento del día: `area 12` = `current["looking"]`, y
`current["looking"] SÍ viene poblado` en partidas reales** (nuestras sondas con la baraja de
ejemplo lo vieron siempre `null` porque esa baraja no tiene cartas de «mira las N primeras»).
`option.index` indexa `current["looking"]`. Pasa el **5,1%** de todas las (1,7): declinamos
efectos gratis (Pokégear 3.0, Bug Catching Set, Dusk Ball…). El experto declina el 0,8%.

**d)** ep 91143030, paso 175, Dries @ Tufa Labs (ganó), turno 11, efecto Petrel, 13 opciones.
Experto: **Night Stretcher**. Nosotros: Lillie's Determination. Buscamos por texto (`"draw"` = 2,0)
sin mirar el estado: teníamos 3 cartas en mano y 6 Pokémon en mesa; el experto recupera recursos.

### Fuga 3 — (0,0) opt10: no reconocemos el 58,7% de las habilidades que activa el campo

De 7.756 activaciones de habilidad del experto, `_habilidad_activable` devuelve `None` en el
**58,7%**, `robo` en el 40,4% y `acel` en el 0,9%. Tres cartas explican el 91% de los `None`:

| carta | n | por qué falla nuestra clasificación |
|---|---:|---|
| **Munkidori** (Adrena-Brain) | 1.852 | mueve contadores de daño; no hay clase para «daño» |
| **Spikemuth Gym** (estadio) | 1.665 | `area 7` solo se acepta si el texto dice `"discard pile into their hand"` (Levincia); esta dice `search their deck` |
| **Drakloak** (Recon Directive) | 644 | «look at the top 2 cards» — no contiene `"draw"` ni `"search your deck"` |

**a)** ep 91088154, paso 60, Dipam Chakraborty, turno 7: experto activa **Drakloak** (mira 2);
nosotros jugamos Poké Pad.
**b)** ep 91027318, paso 90, Lunariz (ganó), turno 7: experto activa **Spikemuth Gym**; nosotros
jugamos el supporter Dawn — quemando el supporter del turno por una habilidad gratis y repetible.

---

## 6. Reglas candidatas, ordenadas por (volumen × brecha) — CON EFECTO YA MEDIDO

`reglas_candidatas.py` implementa cada regla en una **política sombra** (copia parametrizada; no
toca `heuristico.py`) y vuelve a medir el acuerdo sobre 300 episodios (44.104 decisiones:
25.184 en (0,0), 15.694 en type 1, 3.226 otras).

| regla | acuerdo (0,0) | acuerdo type1 | GLOBAL | Δ global |
|---|---:|---:|---:|---:|
| BASE heurístico v2 | 33,35% | 48,38% | 43,13% | — |
| **O1** recursos antes que energía | **34,92%** | — | 44,03% | **+0,89** |
| **O6** ampliar el reconocimiento de items | 34,41% | — | 43,74% | +0,61 |
| **O3** supporter sin la condición «mano corta» | 33,95% | — | 43,48% | +0,34 |
| **O5** cualquier trainer antes de terminar el turno | 34,01% | — | 43,51% | +0,37 |
| **B1** búsqueda: priorizar lo jugable ya | — | **49,73%** | 43,62% | +0,48 |
| **B2** resolver `area 12` (`looking`) | — | 49,45% | 43,52% | +0,38 |
| O2 habilidad antes que evolucionar | 32,97% | — | 42,91% | **−0,22** |
| O4 retirarse siempre que el activo no pueda atacar | 33,03% | — | 42,95% | **−0,18** |
| O4b retirarse solo si además la banca sí puede pegar | 33,43% | — | 43,18% | +0,05 |
| O1+O3+O6 | 36,95% | — | 45,19% | +2,06 |
| O1+O3+O5+O6 | **37,01%** | — | 45,22% | +2,09 |
| B1+B2 | — | **50,92%** | 44,04% | +0,90 |
| **O1+O3+O5+O6+O4b+B1+B2** | **37,01%** | **50,92%** | **46,13%** | **+3,00** |

Referencia: el clon por imitación entrenado (`bc_piloto.py`) sacaba 45,79%. **Estas siete reglas,
escritas a mano y sin entrenar nada, ponen al heurístico por encima de ese número** (46,13%; y
49,96% con la métrica corregida por identidad de carta).

### Especificación para implementar (por prioridad)

**R1 — Reordenar `_fase_principal` (la fuga #1).** Mover los pasos 5 (item de búsqueda) y 6
(supporter de robo/búsqueda) **delante** del paso 3 (energía del turno). Orden nuevo:
`bancar básicos<4 → evolucionar → habilidad 'robo' → item de recurso → supporter de recurso →
energía del turno → habilidad 'acel' → tool → estadio → habilidad 'estadio' → atacar → fin`.
Es un cambio de orden de dos bloques ya escritos. Medido: **+1,57 pp en (0,0)**.
*Razón:* jugar Poffin/Ultra Ball/Pokégear cambia qué Pokémon hay en mesa y por tanto **a quién
conviene adjuntar la energía**, que es el recurso irreversible del turno.

**R2 — Ampliar el reconocimiento de items de recurso (paso 5).** Hoy: `"search" in txt`.
Nuevo: `"search"` OR `"look at the top"` OR `"look at the bottom"` OR `"into your hand"` OR
`"put a pokémon"` OR `"draw"`. Cubre Night Stretcher, Pokégear 3.0, Bug Catching Set, Dusk Ball,
Energy Retrieval, Sacred Ash. Medido con R1: **+1,06 pp adicionales en (0,0)**.
*No incluir* `"switch in 1 of your opponent's"` (Boss's Orders / gusting): el gusting ya salió
negativo en `agente-heuristico-v3.md` (0,495) y aquí no hay dato que lo contradiga.

**R3 — Quitar la condición «mano no-energía ≤ 4» al supporter de robo (paso 6).** Un supporter
por turno es un recurso que caduca; el campo lo juega igual. Medido: **+0,60 pp en (0,0)**.

**R4 — `area 12` (`current["looking"]`) en `_elige_cartas`.** Añadir `12: cur["looking"]` a la
resolución de `id_de` y tratarlo como ganancia (`area in (1,2,3,6,12)` → mejores, al máximo).
**Nunca declinar** un select con `area 12`. Medido: **+1,07 pp en type 1**, y elimina el 5,1% de
efectos que hoy tiramos a la basura. Es además el arreglo más barato: dos líneas.

**R5 — Jugabilidad en `_util` para las búsquedas.** En `_elige_cartas` con `area` 1 ó 12, sumar a
la utilidad de un Pokémon `+2,0` si es **jugable ya** (`cards[cid]["basic"]` y banca<5, **o**
`cards[cid]["evolvesFrom"]` coincide por nombre con un Pokémon propio en juego) y `−1,5` si no.
Los campos `basic` y `evolvesFrom` **ya están en el catálogo `AllCard` del motor** (verificado).
Medido: **+1,35 pp en type 1**. Es la corrección directa de la fuga #2.

**R6 — Trainer cualquiera como último recurso.** Antes de `terminar turno` (paso 9), si no se
disparó nada más, jugar el primer item o supporter disponible. Medido: **+0,66 pp en (0,0)**.
Riesgo: puede quemar un supporter útil; conviene meterlo **detrás** de atacar y solo si el turno
ya no tiene nada mejor.

**R7 — Habilidades: tres parches concretos** (no medido en la política sombra, pero son 58,7% de
las activaciones del campo y el mecanismo está identificado):
- `area 7` (estadio): aceptar también `"search their deck"` → clase `robo` si `deckCount > 0`
  (Spikemuth Gym: 1.665 activaciones, 21% del total del campo).
- `"look at the top"` / `"look at the bottom"` → clase `robo` (Drakloak: 644).
- Munkidori-like («move damage counter»): clase nueva; disparar solo si con el traslado el activo
  rival queda a ≤0 hp, o si un Pokémon propio herido pasa a fuera de rango. **1.852 activaciones**
  y además destapa `(1,13)`/`(1,16)`, otras 6.094 decisiones donde hoy somos aleatorios.

**R8 — Retirada: NO hay regla determinista barata.** Medido: el campo se retira solo el **5,0%**
de las veces que puede, y ninguna condición simple sube de ahí lo suficiente:

| estado del activo cuando la retirada está disponible | n | se retira |
|---|---:|---:|
| ≤50% hp / ex / **la banca ya puede atacar** | 1.605 | **13,4%** |
| 100% hp / no-ex / la banca ya puede atacar | 2.125 | 11,2% |
| ≤25% hp / ex / la banca ya puede atacar | 622 | 10,3% |
| 100% hp / ex / la banca ya puede atacar | 2.799 | 5,3% |
| cualquiera / la banca **no** puede atacar | 12.075 | 1,2%–3,7% |

El único predictor fuerte es **«hay en banca un Pokémon que ya puede atacar»** (×4 a ×6 la tasa),
pero incluso en la mejor celda la regla se equivocaría 6 de cada 7 veces. Encaja con los dos
negativos medidos en `agente-heuristico-v3.md` (0,476 / 0,495). **Verdicto: no reabrir la retirada
por regla.** El ejemplo canónico que sí importa (ep 91045699: Grimmsnarl ex a **30/320** activo con
otro Grimmsnarl ex a 300/320 en banca) es «salvar al ex herido» y necesita evaluar el riesgo de KO,
o sea la red de valor — no una heurística de texto.

**R9 — Decisión de baraja (20% del Deck Score, y coste cero).** Las cartas que el piloto no puede
jugar son cartas muertas. En `hops-snorlax` son 6/60 (10,0%) y en `mega-lucario` 10/60 (16,7%).
Dos salidas, ambas válidas y ninguna cara:
- **enseñar** las que R2 ya cubre (Night Stretcher entra sola con R2), o
- **sustituir** las que quedan (Switch, Premium Power Pro, Tarragon, Boss's Orders) por copias de
  cartas que sí jugamos. Sustituir es reversible y no toca el código.
Esto es además un argumento de writeup de primera: *«medimos qué cartas de nuestra propia lista
nuestra política nunca juega y las quitamos»* ataca directamente la consistencia.

---

## 7. Qué NO se debe concluir de aquí

- **El acuerdo no es winrate** (§0, r = −0,028). Las siete reglas suman +3,00 pp de acuerdo; eso
  es evidencia de *dirección*, no de valor. Cada una tiene que pasar `arena.py` (n≥1.000, procs 3)
  contra `heuristico.py` antes de entrar en un envío, y el gate es «no empeora», no «coincide más».
- **Parte de la divergencia es de baraja, no de política.** Los replays son barajas ajenas; nuestro
  heurístico no entiende cartas que no juega. Por eso §3 (cobertura) y §6-R9 se miden **sobre
  nuestras propias listas**, que es donde la conclusión es limpia.
- El corpus es la franja alta de la ladder (mediana `avg_score` 1021), no el campo entero. Las
  conclusiones valen para «cómo juega el top-150», que es contra quien hay que ser consistente.
