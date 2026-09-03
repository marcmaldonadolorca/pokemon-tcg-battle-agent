# Escalado del clon: capacidad, datos, filtros de calidad — y un fallo de la báscula

Fecha: 2026-08-12. Encargo: exprimir el clon con más datos y más capacidad.
Piezas nuevas: `research/clon/entrenar2.py` (checkpoints, fracción de datos,
filtros), `research/clon/extraer2.py` (meta con jugador y ganador),
`research/agentes/clon_v2.py`, pesos en `research/clon/politica_7d_*.npz`,
corpus en `data/clon/pol7d_1030.npz` (gitignorado, 3,08 GB).
Instrumentación de laboratorio en `scratchpad/escalado/`.

**Resumen: sí escala, y bastante — pero el resultado importante es que la báscula
con la que se iba a medir estaba rota.** El clon ampliado (7 días de replays,
H1=192) gana al de la ladder **0,5420 [0,5201, 0,5637]** con mega-lucario
(n=2.000) y **0,6778** con c2-alakazam —la lista que está jugando— sobre n=4.000
con muestra de confirmación independiente. Y de paso: la conclusión §4.3 de `clon-politica.md` («más
imitación no es mejor juego») **no se replica** cuando el duelo se mide bien.

| | resultado |
|---|---|
| Corpus nuevo | 7 días (08-05 → 08-11), **10.413 episodios**, 1.573.776 decisiones, 11,4 M opciones |
| Techo de capacidad (2 días) | satura en **H1=384**; H1=768 no mejora; una 3.ª capa tampoco |
| Curva de datos (H1=192) | 1.042 → 7.289 episodios: top-1 **0,5984 → 0,6235**, sin saturar |
| Top-1 en el MISMO test | ladder `politica.npz` **0,5766** · clon_v2 **0,6235** (+4,7 pp) |
| **Arena mega-lucario** (n=2.000) | **0,5420 [0,5201, 0,5637]** |
| **Arena c2-alakazam** (n=4.000, con confirmación) | **0,6778** · descubrimiento 0,6755 · confirmación **0,6800** |
| Y con H1=384 y c2-alakazam (n=2.000) | **0,7190 [0,6989, 0,7383]** — pero pierde con mega-lucario |
| Filtro «solo el que ganó» | **no compra nada**: vale exactamente su volumen |
| Filtro por rating alto | **destruye**: peor que la misma cantidad de datos sin filtrar |
| **Fallo encontrado** | `CLON_PESOS` se hereda entre agentes → el duelo se vuelve **self-play** |
| Coste | ver §7 |

---

## 0. El fallo de la báscula (léase antes que ningún número)

`research/agentes/clon.py` resuelve sus pesos **en tiempo de importación**:

    _RUTA = os.environ.get("CLON_PESOS") or _busca("politica.npz")

`arena.py` carga los dos agentes **en el mismo proceso** y en orden: primero A,
después B. Si A es un envoltorio que hace `os.environ['CLON_PESOS'] = <pesos_A>`
y B es el `clon.py` pelado, entonces B lee la variable que acaba de dejar A y
**juega con los pesos de A**. El duelo deja de ser un duelo: es self-play, y da
0,50 pase lo que pase.

Comprobado, no deducido:

    candidato  _RUTA: .../d7_h192_f10_e2.npz
    referencia _RUTA: .../d7_h192_f10_e2.npz
    IGUALES (=> el duelo era self-play): True

Esto invalidó **toda la primera tanda de mega-lucario** de esta sesión (unas 20
celdas, todas «0,50 ± ruido», que es exactamente lo que produce el fallo). Se
repitieron con la báscula arreglada y varias cambiaron de signo.

**La regla que queda**: los dos lados tienen que ser envoltorios que fijen sus
propios pesos justo antes de ejecutar `clon.py`. Nunca envoltorio contra
`clon.py` pelado. `scratchpad/escalado/arena_lote.py` ya envuelve siempre la
referencia y lo documenta en el sitio.

**Hay un segundo caso, peor, en el repo**: cuatro variantes usan
`os.environ.setdefault("CLON_PESOS", ...)` —
`variantes/clon_c1_grimmsnarl.py`, `clon_c2_alakazam.py`,
`clon_c3_lopunny_froslass.py`, `clon_gate_v6_mega_lucario.py`. Con `setdefault`,
si otro agente ya dejó la variable puesta, la variante **no la sobreescribe** y
juega con los pesos del vecino, en silencio. Las que hacen asignación dura
(`clon_e3_*`, `clon_ep2_*`, `clon_final_*`) están bien. Cambiar los cuatro
`setdefault` por asignación dura es una línea por fichero.

**Control de la báscula arreglada** (los mismos pesos a los dos lados,
mega-lucario, n=800): **0,4850 [0,4505, 0,5196]**. Compatible con el suelo de
ruido ya medido del proyecto (0,4959 [0,4848, 0,5070], n=7.800).

## 1. El corpus ampliado

`research/clon/extraer2.py` = el extractor de siempre con dos columnas más en
`meta` (**jugador** y **gana**, esta última de `ep['rewards']`), que es lo que
hacía falta para el filtro de calidad. Mismo desfase +1, mismos rasgos, mismo
filtro `min_score >= 1030`.

Se bajaron 5 días más con la CLI de Kaggle (08-05, 08-06, 08-07, 08-10, 08-11).
**No hace falta descomprimir nada**: el extractor lee cada JSON directamente del
zip, así que el coste en disco son los 707 MiB del zip y ya (el aviso de
`replays-imitacion.md` sobre los 21 GB descomprimidos por día no aplica a esta
ruta). Disco tras la sesión: 80% usado, 181 GB libres.

| | 2 días (el de la ladder) | 7 días (nuevo) |
|---|---:|---:|
| episodios | 2.773 | **10.413** |
| decisiones | 418.068 | **1.573.776** |
| opciones | 3.015.620 | **11.402.689** |
| cartas resueltas | 84,5% | 84,7% |
| fichero | 812 MB | 3.080 MB |
| train / val / test (por episodio) | 293k / 62k / 63k | 1.099k / 238k / **237k** |

El test de 236.708 decisiones (1.562 episodios no vistos) es la vara de esta nota.

## 2. Curva de capacidad y de épocas (corpus de 2 días, para aislar la variable)

Top-1 en test (63.037 decisiones). Suelos en ese mismo test: azar 0,2180,
`heuristico.py` 0,4303.

| H1 (H2) | ép. 2 | ép. 5 | ép. 10 | ép. 20 | mejor-val |
|---|---:|---:|---:|---:|---|
| 96 (48) — *el de la ladder* | 0,5874 | 0,5970 | 0,6032 | 0,6107 | e20 · 0,6107 |
| 192 (96) | 0,5866 | 0,6047 | 0,6134 | 0,6187 | e15 · 0,6157 |
| **384 (192)** | 0,5914 | 0,6082 | 0,6131 | **0,6234** | e20 · **0,6234** |
| 768 (384) | 0,5909 | 0,6080 | 0,6145 | 0,6207 | e20 · 0,6207 |
| 192 (96) + 3.ª capa | 0,5884 | 0,6042 | 0,6127 | 0,6184 | e20 · 0,6184 |

- **Satura en H1=384.** Duplicar a 768 no mejora (−0,3 pp): con 2 días de datos
  la capacidad ya no es el cuello de botella.
- **Una tercera capa no compra nada** (0,6184 vs 0,6187 a ancho igual). La
  arquitectura ya tenía dos capas ocultas; la profundidad extra es ruido.
- **No hay sobreajuste dentro de 20 épocas**: la mejor época de validación es la
  20 en cuatro de las cinco filas y la curva de val está plana, no cayendo. Lo
  que hay es saturación, no sobreajuste.
- El coste es ridículo: 5 s/época con H1=96 y 130 s/época con H1=768.

## 3. Curva de datos (corpus de 7 días, H1=192, 12 épocas)

Fracción de EPISODIOS de entrenamiento; validación y test intactos y comunes.

| episodios de train | decisiones | top-1 (ép. 12) | mejor-val |
|---:|---:|---:|---:|
| 1.042 | 154.919 | 0,5984 | 0,5984 |
| 2.085 | 310.538 | 0,6053 | 0,6055 |
| 4.162 | 626.088 | 0,6175 | 0,6175 |
| **7.289** | **1.099.430** | **0,6237** | **0,6235** |

**Sigue subiendo**: +2,5 pp al multiplicar los datos por 7, con rendimientos
decrecientes pero sin plano (+0,6 pp en la última duplicación). No está saturado:
bajar más días seguiría comprando top-1.

**Capacidad × datos**: con 7 días, H1=384 llega a **0,6275** (mejor predictor de
toda la tanda) — o sea, más datos mueven el punto de saturación de capacidad
hacia arriba. Pero juega peor (§5).

**Comparación honesta con el modelo de la ladder**, los cuatro sobre el MISMO
test de 7 días (`scratchpad/escalado/evalua_pesos.py`):

| pesos | H1 | top-1 | log-loss |
|---|---:|---:|---:|
| `politica.npz` (2 días, 2 épocas) — el de la ladder | 96 | 0,5766 | 1,2177 |
| `politica_e20.npz` (2 días, 20 épocas) | 128 | 0,6064 | 1,1464 |
| `politica_7d_h192_e2.npz` (7 días, 2 épocas) | 192 | 0,6061 | 1,1378 |
| **`politica_7d_h192_mejorval.npz`** (7 días, ép. 11) | 192 | **0,6235** | **1,0928** |

## 4. Filtros de calidad del corpus: los dos pierden

### 4.1 Entrenar solo con el jugador que GANÓ

Se queda con el 52,1% de las decisiones (todas las partidas siguen aportando: la
mitad de cada una).

| entrenamiento | episodios | decisiones | top-1 (ép. 12) |
|---|---:|---:|---:|
| todo | 7.289 | 1.099.430 | **0,6237** |
| solo el ganador | 7.284 | 574.641 | 0,6180 |
| *mitad al azar (frac 0,571), para comparar a volumen igual* | 4.162 | 626.088 | *0,6175* |

**El filtro vale exactamente lo que vale su volumen y ni un punto más**: 0,6180
con 575k decisiones filtradas frente a 0,6175 con 626k sin filtrar. Contra el
corpus entero pierde 0,6 pp. En imitación se suele decir que la calidad importa
más que el volumen; aquí, con este corpus, **no**: las decisiones del que perdió
enseñan tanto como las del que ganó. Tiene sentido — la mayoría de las
decisiones de una partida perdida son igual de correctas, y quien pierde suele
perder por el emparejamiento o por dos jugadas, no por las 150 restantes.

### 4.2 Entrenar solo con partidas de rating alto

El filtro poda solo el train; el test sigue siendo el mismo (todos los ratings).

| filtro | decisiones de train | top-1 (ép. 12) | mejor-val |
|---|---:|---:|---:|
| `min_score >= 1030` (todo) | 1.099.430 | 0,6237 | 0,6235 |
| `min_score >= 1060` | 592.128 | 0,6049 | 0,6121 |
| `min_score >= 1100` | 241.633 | 0,5922 | 0,5956 |
| ganador + `>= 1060` | 309.249 | 0,5578 | 0,5859 |

Peor que la misma cantidad de datos sin filtrar en todos los casos (626k sin
filtrar da 0,6175; 592k filtrados a 1060 dan 0,6049). Clonar a los mejores, con
este corpus, **sale caro**: se paga volumen y no se cobra calidad. Queda cerrada
la sugerencia #2 de `clon-politica.md`.

Cautela justa: el test mezcla todos los ratings, así que un modelo entrenado solo
con partidas buenas parte con desventaja en esta métrica. Pero la arena, que no
tiene ese sesgo, tampoco lo rescata (§5).

## 5. Arena: qué juega mejor de verdad

Protocolo de casa: `arena.py`, **la misma baraja a los dos lados**, asientos
intercambiados, `--procs 3`, IC de Wilson, báscula arreglada (§0). El rival es
siempre `research/agentes/clon.py` con `politica.npz`, o sea **el que está en la
ladder**.

### 5.1 Las dos celdas que deciden (n=2.000 cada una)

| modelo | mega-lucario | c2-alakazam |
|---|---|---|
| `politica_7d_h192_e2` (7 días, 2 ép., H1=192) | 0,4633 *(n=600)* | 0,5840 → conf. 0,5755 → **agrupado 0,5798** (n=4.000) |
| `cap_h192_e2` (2 días, 2 ép., H1=192) | 0,5325 **[0,5106, 0,5543]** | 0,6225 **[0,6010, 0,6435]** |
| **`politica_7d_h192_mejorval`** (7 días, ép. 11, H1=192) | **0,5420 [0,5201, 0,5637]** | 0,6755 [0,6547, 0,6957] · conf. **0,6800 [0,6592, 0,7001]** · agrupado **0,6778** (n=4.000) |
| `politica_7d_h384_mejorval` (7 días, H1=384) — *el mejor predictor* | **0,4300 [0,3961, 0,4646]** *(n=800)* | **0,7190 [0,6989, 0,7383]** |

Las dos celdas de c2-alakazam del modelo H1=192 se midieron con muestras
independientes y coinciden (0,6755 y 0,6800): el resultado no es la maldición del
ganador. La de H1=384 replica su descubrimiento (0,7350 con n=800 → 0,7190 con
n=2.000).

**Y aquí está la bifurcación que hay que decidir**: `H1=384` con 7 días es
**+21,9 puntos** contra el clon de la ladder jugando c2-alakazam —la lista que
está en la ladder ahora mismo— y a la vez **pierde** con mega-lucario (0,4300).
`H1=192` gana con las dos, por menos. Si lo que se envía es c2-alakazam, el
H1=384 es estrictamente mejor en lo único que se mide; si se quiere un piloto que
no dependa de la lista, es el H1=192.

El ganador es **`politica_7d_h192_mejorval`**: gana con las dos listas, y con la
que está en la ladder gana por **+17,6 puntos**. La celda de mega-lucario
replica su muestra de descubrimiento (0,5567 con n=600 → 0,5420 con n=2.000: la
maldición del ganador de siempre, 1,5 pp) y la de c2-alakazam también (0,6900 con
n=600 → 0,6755 con n=2.000).

### 5.2 El efecto depende de la BARAJA, y mucho

Todos los modelos nuevos medidos con c2-alakazam (n=600 salvo indicación):

| modelo | c2-alakazam | mega-lucario |
|---|---:|---:|
| `cap_h192_e2` (2 días) | 0,6217 | 0,5567 |
| `d7_h192_gana_e2` (solo ganador) | 0,6333 | — |
| `d7_h192_f10_e5` | 0,6533 | — |
| `d7_h192_f10_mejorval` | **0,6900** | 0,5567 |

Con c2-alakazam **todo lo nuevo gana con holgura**; con mega-lucario la mejora es
real pero tres veces menor, y algunos modelos incluso pierden. Es el mismo patrón
del ADR PKM-012 visto desde el otro lado: allí la báscula de BARAJAS se invertía
según el piloto; aquí la báscula de PILOTOS cambia de tamaño según la baraja.
**Corolario operativo: un modelo se mide con la lista con la que se va a enviar,
y con ninguna otra.**

### 5.3 «Más imitación no es mejor juego» NO se replica

`clon-politica.md` §4.3 midió `politica_e20` contra `politica.npz` en 0,468
[0,440, 0,497] (ganaba el corto) y sacó de ahí que el criterio de parada de un
clon no puede ser la log-verosimilitud. Re-medido con la báscula arreglada,
mega-lucario, **n=2.000**:

    politica_e20 vs politica.npz : 0,4925  IC95 [0,4706, 0,5144]   -> EMPATE

Y en esta tanda el orden va al revés del que decía aquella nota: dentro de
H1=192, el modelo de 11 épocas (top-1 0,6235) juega **mejor** que el de 2 épocas
(top-1 0,6061) en las dos barajas — con c2-alakazam, 0,6900 contra 0,5840.

Lo que sí sobrevive, y en su versión fuerte, es que **top-1 no es una escalera
monótona hacia el juego**: el mejor predictor de toda la tanda
(`d7_h384_mejorval`, top-1 0,6275) es el que **peor juega** con mega-lucario
(0,4300 [0,3961, 0,4646]). La lectura corregida no es «menos imitación es mejor»,
sino: **hay un óptimo, está en H1=192 con el corpus entero, y pasado ese punto la
capacidad extra se gasta en clonar manías del campo que no son nuestra baraja.**

## 6. Gauntlet del campo (piloto `clon_v2`, `--rivales ampliado`, n=150/celda)

Recordatorio de lo que mide: **el mismo piloto a los dos lados**, cambiando
nuestra LISTA. Es la báscula de barajas, no de agentes; no es comparable con el
0,8155 de `clon-politica.md` §4.2, que era otra cosa (campo pilotado por v2).

| piloto | lista | POND | IC95 | PEOR emparejamiento | cobertura |
|---|---|---:|---|---|---:|
| `clon` (ladder) | c1-grimmsnarl | 0,558 | [0,530, 0,586] | 0,125 ogerpon | 96% |
| `clon` (ladder) | c2-alakazam | 0,454 | [0,427, 0,482] | 0,320 grimmsnarl | 96% |
| `clon` (ladder) | mega-lucario | 0,362 | [0,337, 0,386] | 0,105 alakazam | 96% |
| **`clon_v2`** (pesos finales, 7d H1=192) | **c1-grimmsnarl** | **0,587** | [0,554, 0,619] | 0,127 ogerpon | 96% |
| **`clon_v2`** | c2-alakazam | 0,494 | [0,463, 0,526] | **0,273** grimmsnarl | 96% |
| **`clon_v2`** | mega-lucario | 0,317 | [0,288, 0,346] | 0,087 alakazam | 96% |
| *(pesos intermedios 7d, 2 ép.)* | *c2-alakazam* | *0,493* | *[0,461, 0,526]* | *0,340* | *96%* |
| *(pesos intermedios 7d, 2 ép.)* | *mega-lucario* | *0,335* | *[0,306, 0,365]* | *0,093* | *96%* |

Con el piloto nuevo **se mantiene el orden de PKM-012**: c1-grimmsnarl por
delante (0,587), c2-alakazam en medio (0,494), mega-lucario último (0,317). O sea
que el hallazgo que fijó el ADR no depende de esta versión del clon.

Lo que se mueve, y conviene decirlo en los dos sentidos: la media de la mejor
lista **sube** (c1-grimmsnarl 0,558 → **0,587**) y el PEOR emparejamiento
**baja** en las otras dos (c2-alakazam 0,320 → 0,273 contra grimmsnarl;
mega-lucario 0,105 → 0,087 contra alakazam). O sea que el piloto nuevo mejora la
media y **empeora el suelo**, que es justo la mitad del rubric que no interesa
empeorar. Ninguna de estas diferencias tiene los IC separados (n=150 por celda
aquí contra n=200 en el piloto viejo): son señales, no resultados declarados, y
si se va a decidir con ellas hay que volver a medirlas con más n.

Tablas completas en `scratchpad/escalado/gauntlet_v2_mejorval.log` (pesos
finales) y `gauntlet_v2_pesos_e2.log` (intermedios), y en `data/gauntlet.json`
bajo el piloto `clon_v2`.

## 7. Coste

Medido con `research/clon/auditar.py` (partidas en el mismo proceso, para que los
contadores del agente sobrevivan), mega-lucario a los dos lados:

| | `politica.npz` (ladder) | `politica_7d_h192_mejorval` | `politica_7d_h384_mejorval` |
|---|---:|---:|---:|
| H1 / H2 | 96 / 48 | 192 / 96 | 384 / 192 |
| fichero .npz | 0,098 MB | **0,233 MB** | 0,608 MB |
| ms por decisión | 0,208 | **0,224** | 0,271 |
| margen sobre los 600 s de producción | ×64.066 | **×55.010** | ×43.337 |
| decisiones por la red | 97,78% | 97,95% | 98,04% |
| **ilegales / excepciones / fallbacks** | 0 / 0 / 0 | **0 / 0 / 0** | **0 / 0 / 0** |

Cuadruplicar los parámetros cuesta **0,016 ms por decisión**: el coste está
dominado por construir los rasgos, no por multiplicar matrices. El paquete admite
197,7 MiB y el modelo grande ocupa el **0,3%** del límite. Ni el reloj ni el
tamaño son restricciones aquí, y no lo van a ser: hay sitio para un modelo 300
veces mayor.

## 8. Veredicto

1. **El clon escala, y mucho más de lo que parecía.** Con 7 días de replays y el
   doble de ancho gana al de la ladder en las dos listas medidas; con
   c2-alakazam —la que está jugando— por **+17,8 puntos** (n=4.000, con
   confirmación independiente). Con el cuádruple de ancho, **+21,9** en esa misma
   lista, a costa de perder con mega-lucario.
2. **Los filtros de calidad no escalan**: ni «solo el ganador» ni el rating alto.
   Volumen bruto gana. Queda cerrada esa vía.
3. **La capacidad tiene óptimo, no rampa**: H1=192 con el corpus entero. H1=384
   predice mejor y juega peor.
4. **La báscula estaba rota** y lo estuvo durante una tanda entera de medidas.
   Cualquier número de arena que compare dos juegos de pesos del clon y no venga
   de dos envoltorios con asignación dura hay que volver a mirarlo.

### Qué NO se ha demostrado

- **Nada de esto es la ladder.** El rival de todas estas celdas es el clon actual
  con la misma baraja, no los agentes de RL de verdad. Que gane +17,6 pp a su
  propio antecesor no dice cuánto rating sube.
- **Solo dos listas medidas** (mega-lucario y c2-alakazam) y el efecto depende
  fuerte de la lista. Con c1-grimmsnarl, que es la mejor del gauntlet bajo el
  clon, **no está medido**.
- **El gauntlet del piloto nuevo se corrió con n=150**, la mitad de la n de las
  filas del piloto viejo; las comparaciones POND entre pilotos son indicativas.
- **Frescura vs volumen sin separar**: el corpus nuevo es a la vez 3,8× más
  grande y 3 días más fresco. No se ha aislado cuál de las dos cosas paga.

### Qué necesita decisión del propietario

- **Si se sube clon_v2, con qué pesos y con qué lista.** Lo medido:
  `politica_7d_h384_mejorval` + c2-alakazam es la mejor combinación (0,7190
  contra el piloto que está jugando esa misma lista ahora mismo), pero es el
  modelo que peor se porta si algún día cambia la lista;
  `politica_7d_h192_mejorval` gana con las dos y por menos. Es un cambio de
  pesos, no de arquitectura: el paquete se construye igual, cambiando `--extra`
  de `politica.npz` al `.npz` elegido. `clon_v2.py` viene con el H1=192 por
  defecto y acepta `CLON_V2_PESOS` para apuntar al H1=384 sin tocar nada.
- **Si se arreglan los cuatro `setdefault`** de `research/agentes/variantes/`
  (§0). Es mecánico, pero toca ficheros que han producido números publicados.

### Reproducir

    # corpus (no descomprime nada: lee del zip)
    .venv/bin/python research/clon/extraer2.py data/replays/pokemon-tcg-ai-battle-episodes-2026-08-0{5,6,7,8,9}.zip \
        data/replays/pokemon-tcg-ai-battle-episodes-2026-08-1{0,1}.zip \
        --salida data/clon/pol7d_1030.npz --episodios 3000 --procs 3 --min-rating 1030

    # el modelo que gana
    .venv/bin/python research/clon/entrenar2.py data/clon/pol7d_1030.npz \
        --h1 192 --epocas 12 --checkpoints 2,5,12 --prefijo research/clon/politica_7d_h192

    # arena (los DOS lados envueltos: ver §0)
    .venv/bin/python scratchpad/escalado/arena_lote.py --n 2000 --deck c2-alakazam \
        --cands v2=research/clon/politica_7d_h192_mejorval.npz
