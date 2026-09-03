# El gauntlet del campo: composición, pesos y validación de la báscula (2026-08-11)

Qué es: la báscula con la que se elige LISTA. Enfrenta una candidata contra las listas
líder del campo real, **con el mismo piloto en los dos lados**, y agrega los resultados
ponderando cada rival por su frecuencia medida en la ladder.

- Script: `research/gauntlet.py` · resultados crudos: `data/gauntlet.json`
- Rivales: `research/decks/campo/` · censo que los produce: `research/replays/censo_campo.py`
- Censo y construcción de las listas: `research/notas/baraja-vs-campo.md`

Sustituye a la báscula vieja («candidata contra la baraja de ejemplo del motor»), que
medía contra un rival que **no aparece ni una vez en 18.674 barajas** del campo.

---

## 1. Composición y pesos

Fuente de los pesos: `data/replays/censo_campo.json`, producido por
`research/replays/censo_campo.py` sobre `data/replays/idx/idx_0808.json` + `idx_0809.json`
— 9.337 episodios, **18.674 barajas** (las dos de cada partida), 203 listas únicas
agrupadas por solapamiento de multiconjunto (`sum(min(a,b))/60 ≥ 0,62`). El peso de cada
rival es el **share** de su grupo; ningún peso es inventado ni uniforme.

| fichero | arquetipo | barajas | peso (share) | WR en la ladder |
|---|---|---|---|---|
| `c1-grimmsnarl.csv` | Marnie's Grimmsnarl ex (+Munkidori/Froslass) | 5.821 | **0,3117** | 0,466 |
| `c2-alakazam.csv` | Alakazam (Abra/Kadabra + Dudunsparce) | 3.408 | **0,1825** | 0,497 |
| `c3-lopunny-froslass.csv` | Mega Lopunny ex + Mega Froslass ex | 2.386 | **0,1278** | 0,510 |
| `c4-dragapult.csv` | Dragapult ex (Dreepy/Drakloak) | 1.523 | 0,0816 | 0,587 |
| `c5-kangaskhan-crustle.csv` | Mega Kangaskhan ex + Crustle | 1.281 | 0,0686 | 0,445 |
| `c6-ogerpon.csv` | Teal Mask Ogerpon ex (mono {G}) | 925 | 0,0495 | 0,463 |
| `c7-lucario-campo.csv` | Mega Lucario ex, versión del campo | 738 | 0,0395 | 0,546 |
| `c8-dipplin-grookey.csv` | Dipplin + Grookey/Thwackey | 651 | 0,0349 | 0,551 |
| `x2-hydrapple.csv` | Hydrapple ex + Meganium | 474 | 0,0254 | 0,561 |
| `x1-slowking.csv` | Slowking + Mega Kangaskhan ex | 327 | 0,0175 | 0,633 |
| `x3-cynthia-garchomp.csv` | Cynthia's Garchomp | 294 | 0,0157 | 0,503 |
| `x4-ns-zoroark.csv` | N's Zoroark ex + N's Zekrom | 156 | 0,0084 | 0,577 |

- `--rivales nucleo` = c1..c8 → **89,6%** del campo. `--rivales ampliado` = los 12 → **96,3%**.
- **Cobertura y renormalización**: los pesos se renormalizan sobre los rivales realmente
  medidos, y la tabla imprime la cobertura de cada fila. Comparar POND entre una fila al
  90% y otra al 96% es comparar dos mezclas distintas: se avisa en la columna `cob`.
- **Lo que NO está**: el 3,7% restante son 20 arquetipos con <0,7% cada uno (el mayor,
  Team Rocket's Murkrow, 0,66%). No se representan; la ponderación asume implícitamente
  que la candidata rinde ahí como en la media. Ningún peso hubo que ponerlo uniforme.
- **`x5`, `x6` y `x7` no son rivales**: son duplicados byte a byte de `c4`, `c7` y `c8`
  (mismo líder). Contarlos duplicaría ese peso. `gauntlet.py` los excluye (`DUPES`).

Verificado hoy: los 12 ficheros son **idénticos al líder exacto de su grupo** en el censo
(multiconjunto de 60 ids), y los tres duplicados son los declarados. Además, las 12 listas
pasan `battle_start` con `errorPlayer −1` (lo comprueba el propio script antes de medir).

**Cuidado al leer los pesos como «el campo que nos tocará»**: el censo son las barajas de
los episodios publicados, mezcla de toda la ladder. Nuestro emparejamiento real depende de
nuestra μ. Es la mejor estimación disponible, no una garantía.

## 2. El script

```bash
.venv/bin/python research/gauntlet.py --cands mega-lucario --rivales ampliado --n 200 --procs 3
.venv/bin/python research/gauntlet.py --tabla --rivales ampliado      # reimprime lo medido
.venv/bin/python research/gauntlet.py --validar --rivales ampliado    # las 5 pruebas de §4
.venv/bin/python research/gauntlet.py --h2h a,b,c --n 200             # duelos directos
.venv/bin/python research/gauntlet.py --cands X --replicar --n 200    # re-mide celdas ya medidas
```

Decisiones que hacen que la medida signifique algo:

- **Mismo piloto en los dos lados** (`--politica`, por defecto `research/agentes/heuristico.py`,
  el de los envíos vivos). Lo único que cambia entre las dos ramas es la lista de 60 ids.
- **Asientos intercambiados** mitad y mitad (hereda `arena.Tarea`), y se reporta `wr_1o`/`wr_2o`
  por celda: el swing de asiento es una métrica de la rúbrica, no un detalle.
- Cada lista se entrega por un wrapper generado en `scratchpad/wrappers/` que devuelve `DECK`
  en el paso de baraja y delega el resto en el piloto: el agente no se toca.
- **IC95 de Wilson** por emparejamiento; para la ponderada, IC normal con
  `se = sqrt(Σ w_i² p_i(1−p_i)/n_i)`.
- **Peor emparejamiento** en la tabla, y además el peor entre rivales que pesan ≥5% del campo
  (`peor_gordo`): el 70% de la rúbrica premia consistencia, no la media.
- Resultados **acumulables e indexados por piloto**; una celda con n suficiente no se repite
  (salvo `--forzar`). Los números de pilotos distintos no son comparables entre sí.
- `--procs` capado a 3 (hay otro workflow midiendo en la máquina) y **guardado fusionado**:
  antes de escribir se relee `data/gauntlet.json` y se conservan las celdas que hayan
  aparecido mientras tanto. Sin eso, dos procesos se pisan las medidas.

## 3. Resultados (piloto `heuristico`, n=200 por emparejamiento, 96,3% de cobertura)

WR de la candidata. n total por fila: 2.400 partidas (2.800 en mega-lucario).

| lista | POND | IC95 | media simple | peor | vs |
|---|---|---|---|---|---|
| **mega-lucario** (ladder) | **0,769** | [0,751 – 0,786] | 0,726 | 0,278 | c5-kangaskhan-crustle |
| mega-kangaskhan | 0,747 | [0,729 – 0,765] | 0,679 | 0,175 | c5-kangaskhan-crustle |
| okidogi | 0,712 | [0,689 – 0,735] | 0,670 | 0,305 | c5-kangaskhan-crustle |
| abomasnow-plus | 0,693 | [0,666 – 0,719] | 0,698 | **0,435** | c5-kangaskhan-crustle |
| tr-mewtwo | 0,500 | [0,472 – 0,528] | 0,528 | 0,120 | c5-kangaskhan-crustle |
| ethans-hooh | 0,475 | [0,447 – 0,504] | 0,458 | 0,150 | c5-kangaskhan-crustle |
| iono-bellibolt | 0,467 | [0,438 – 0,495] | 0,479 | 0,175 | c5-kangaskhan-crustle |
| **hops-snorlax** (ladder) | **0,434** | [0,407 – 0,461] | 0,431 | 0,115 | c6-ogerpon |
| ns-zekrom | 0,358 | [0,330 – 0,385] | 0,340 | 0,050 | c6-ogerpon |

Detalle por emparejamiento de las dos listas vivas:

| | grimmsnarl 31% | alakazam 18% | lopunny 13% | dragapult 8% | kangaskhan 7% | ogerpon 5% | lucario 4% | dipplin 3% | hydrapple | slowking | garchomp | zoroark |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mega-lucario | 0,920 | 0,780 | 0,800 | 0,825 | **0,278** | **0,335** | 0,650 | 0,795 | 0,625 | 0,875 | 0,865 | 0,960 |
| hops-snorlax | 0,395 | 0,780 | 0,265 | 0,345 | 0,290 | **0,115** | 0,290 | 0,615 | 0,380 | 0,585 | 0,365 | 0,750 |

Lo que sale de aquí y no salía de la báscula vieja:

- El agujero de `mega-lucario` es **Mega Kangaskhan + Crustle (0,278)** y **Ogerpon (0,335)**,
  que juntos son el **11,8%** del campo. La lista gana 0,92 contra el 31% más jugado y pierde
  3 de cada 4 contra el 7%. Es el sitio exacto donde tocar la lista.
- El swing de asiento ponderado: mega-lucario **+0,042**, okidogi **−0,002**, hops-snorlax
  −0,020, abomasnow +0,079, mega-kangaskhan +0,099. La rúbrica mira esto.
- **La media y el peor no ordenan igual.** Por peor emparejamiento el orden es
  abomasnow-plus (0,435) > okidogi (0,305) > mega-lucario (0,278) > mega-kangaskhan (0,175).
  Con el criterio del enunciado (0,60/0,20 es peor que 0,55/0,45), `abomasnow-plus` es la
  candidata más consistente y `mega-lucario` la de más media. Decisión de lista pendiente.
- El orden apenas depende de los pesos: con pesos uniformes en vez del share, la única
  permuta en el top-4 es mega-kangaskhan ↔ abomasnow-plus (0,679 vs 0,698). Es decir, la
  ventaja de mega-lucario no la fabrica la ponderación.

## 4. Validación de la báscula

Cuatro pruebas, dos externas y dos internas (`--validar`).

**[A] Contraste limpio contra la ladder real.** Es el único dato del mundo real con el
piloto constante y la lista variable: nuestros dos envíos vivos.

| lista | μ ladder | POND gauntlet |
|---|---|---|
| mega-lucario | 464,8 | 0,769 [0,751 – 0,786] |
| hops-snorlax | 378,4 | 0,434 [0,407 – 0,461] |

**El gauntlet ordena igual que la ladder**, con IC95 disjuntos y margen 0,290. Pero hay que
decir hasta dónde vale: la separación en la ladder es de **86 μ**, y este proyecto tiene
documentado que **dos envíos idénticos** se separaron 150 μ (940 vs 790). El dato real es
más ruidoso que el hueco que pretende explicar. Conclusión honesta: la báscula **no
contradice** la realidad y coincide en signo; con dos puntos y ese ruido no se puede afirmar
que la prediga. Es una prueba superada, no una demostración.

**[B] Contraste confundido: WR real de cada arquetipo del campo.** Spearman(WR ladder,
POND gauntlet) = **−0,515** sobre 10 arquetipos. No invalida [A], porque el WR de ladder de
cada arquetipo lo produce el piloto de su dueño: la prueba mezcla lista y agente. Lo que
dice es doble y hay que tenerlo presente:
1. En este campo **la lista no explica el WR** (Grimmsnarl es el 31% con 46,6%).
2. **Nuestro heurístico pilota unas listas mucho mejor que otras**: convierte
   `c5-kangaskhan-crustle` en la mejor baraja de la mesa (POND 0,810) cuando en la ladder es
   la 5.ª con 44,5%, y hunde `x1-slowking` (0,345) que allí es la mejor (63,3%). El gauntlet
   mide **lista × nuestro piloto**, que es exactamente lo que enviamos — pero por eso mismo
   sus resultados **no son transferibles a otro piloto**: si cambia el agente, hay que
   volver a medir (por eso el JSON está indexado por piloto).

**[C] Calibración nula: espejos.** La misma lista en los dos lados debe dar 0,500. Media de
los 8 espejos del campo: **0,4975** (se 0,0125), **8/8 con IC95 cubriendo 0,5**. El banco de
pruebas —intercambio de asientos, wrappers, agregación— **no introduce sesgo medible**. Esta
prueba la ladder no la puede dar.

**[D] Resolución: POND contra el duelo directo.** 15 parejas, n=200 cada una, mismo piloto.
11/15 coinciden en signo, Spearman(ΔPOND, WR duelo) = **+0,625**. El corte es nítido:

| ΔPOND | parejas | aciertos |
|---|---|---|
| ≥ 0,10 | 8 | **8/8** |
| < 0,10 | 7 | 3/7 (azar) |

**La báscula resuelve diferencias de POND ≥ 0,10; por debajo de eso no ordena.** Las cuatro
inversiones son todas de ≤0,076 y giran alrededor de `abomasnow-plus`, que pierde en POND
contra mega-lucario (0,693 vs 0,769) y sin embargo le gana el duelo directo 0,670. No es un
fallo: los emparejamientos son **intransitivos**, y ganar a una lista concreta no es lo que
puntúa la ladder. Justo eso es lo que rompía la báscula vieja, que ordenaba 15 listas por su
duelo contra una sola baraja — y `abomasnow-plus` es precisamente de la estirpe de esa
baraja de ejemplo, con **0 apariciones en 18.674**.

**[E] Test-retest: las mismas celdas, medidas otra vez con partidas nuevas** (2026-08-11).
El RNG del motor no es sembrable, así que *que una celda sea estable* era una hipótesis sin
comprobar: todos los IC del gauntlet asumen que la única fuente de ruido es binomial. Se
re-midieron **30 celdas** (las 12 de `mega-lucario`, las 12 de `hops-snorlax`, y los dos
emparejamientos-agujero de `okidogi`, `abomasnow-plus` y `mega-kangaskhan`), n=200 nuevas
partidas cada una, rama `replica` del JSON.

| | resultado |
|---|---|
| celdas con `\|z\|` > 1,96 | **0 de 30** (esperado 1,5 por azar) |
| media de z | −0,198 |
| **sd(z)** | **0,82** |
| \|d\| medio por celda | 0,025 (máx 0,095) |

`sd(z) ≈ 1` significa que **la celda solo tiene ruido binomial**: no hay una fuente de
varianza escondida (deriva del motor, contaminación entre procesos) que estuviera inflando
la confianza. Los IC del gauntlet no mienten. Y en agregado la reproducción es exacta:

| lista | POND original | POND réplica | POND agrupado (n=400/celda) |
|---|---|---|---|
| mega-lucario | 0,769 | **0,769** | 0,769 [0,756 – 0,781] |
| hops-snorlax | 0,434 | 0,446 | 0,440 [0,421 – 0,459] |

**Pero el test-retest sí tumba una lectura del §3: la IDENTIDAD del peor emparejamiento no
es un dato fiable.** El peor de `mega-lucario` era `c5-kangaskhan-crustle` (0,278) y en la
réplica pasa a ser `c6-ogerpon` (0,305 frente a 0,325 de c5). No es un fallo de la báscula:
c5 y c6 están empatados. Monte Carlo sobre los valores agrupados (20.000 gauntlets
simulados a n=200):

- el **valor** del peor está bien medido: sesgo del mínimo-de-12 solo −0,008, con
  p5–p95 = [0,240 – 0,330] para mega-lucario;
- el **argmin** solo se identifica bien el **74%** de las veces en mega-lucario (c5 74% /
  c6 26%), y el **100%** en hops-snorlax, donde c6 gana por mucho.

Regla de uso: **citar los agujeros como conjunto, no el mínimo como si fuera un rival
concreto.** Lo robusto de mega-lucario es «dos agujeros de ~0,29–0,32 que suman el 11,8%
del campo», no «su peor rival es Kangaskhan». Con los datos agrupados:

| lista | peor (n=400) | 2.º peor |
|---|---|---|
| mega-lucario | 0,293 c5-kangaskhan (n=600) | 0,320 c6-ogerpon (n=400) |
| abomasnow-plus | **0,448** c5-kangaskhan (n=400) | 0,490 c6-ogerpon (n=400) |
| okidogi | 0,270 c5-kangaskhan (n=400) | 0,365 c7-lucario-campo (n=200) |
| mega-kangaskhan | 0,185 c5-kangaskhan (n=400) | 0,275 c6-ogerpon (n=400) |
| hops-snorlax | 0,098 c6-ogerpon (n=400) | 0,282 c5-kangaskhan (n=400) |

El orden por consistencia del §3 **sobrevive a la réplica**: `abomasnow-plus` (0,448) sigue
siendo la más sólida en su peor emparejamiento y `mega-lucario` (0,293) la de más media.

## 5. Veredicto

**La báscula es fiable para lo que se va a usar: separar listas cuyo POND difiera ≥0,10, con
el piloto `heuristico`.** Está calibrada en el nulo (espejos 0,4975), **reproduce sus propios
números con partidas nuevas** (30 celdas re-medidas, 0 discrepancias, sd(z)=0,82, POND de
mega-lucario idéntica a la tercera cifra), coincide con el único contraste real disponible
(orden de los dos envíos vivos) y su resolución está medida (8/8 por encima de 0,10; azar
por debajo).

Los cuatro límites que hay que respetar al usarla:

1. **Resolución 0,10 de POND.** Diferencias menores no son un orden; para decidir entre dos
   listas próximas hace falta subir n (n=200 por emparejamiento da ±0,018 a ±0,027 de IC en
   POND según la lista; bajar a ±0,015 pide ~650 partidas por emparejamiento) o decidir por
   el peor emparejamiento.
2. **Está atada al piloto.** Mide lista × agente; cambiar de agente invalida los números.
3. **Es un promedio del campo, no un duelo.** Un rival puede batir a la candidata y aun así
   la candidata ser mejor elección, porque solo pesa el 7% de las partidas.
4. **El *valor* del peor emparejamiento se puede citar; el *nombre* del peor rival, no**
   (§4[E]): con 12 celdas a n=200 el argmin acierta el 74% cuando los dos agujeros están
   empatados. Hablar de «los agujeros» en plural y con su n.

Y el resultado accionable: `mega-lucario`, la lista que está en la ladder, es la mejor en
media (0,769, replicada) pero tiene **dos agujeros estadísticamente empatados** contra el
11,8% del campo: Kangaskhan-Crustle **0,293** (n=600) y Ogerpon **0,320** (n=400). Ahí es
donde una lista nueva tiene que ganar **sin romper el 0,92 contra Grimmsnarl** (que es el
31% del campo y replicó exacto, 0,920/0,920). Una lista que arregle un agujero y rompa
Grimmsnarl pierde POND: 0,31 de peso contra 0,12.
