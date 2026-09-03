# Presupuesto de búsqueda y corpus de 30 días: dos palancas medidas a 60 h del corte

Fecha: 2026-08-14 · Tickets: `PKM-007`, `PKM-009` (cerrados), `PKM-004`, `PKM-008` (en curso)

## Resumen

Las dos palancas que quedaban abiertas se han medido. El **presupuesto de
búsqueda** compra: la configuración `RC` (rollout 32 pasos y 5 candidatas) gana
**0,6350 [0,6111, 0,6582]** al agente que está en la ladder. Los **datos**
también: con 30 días de replays en vez de 7, el acierto de imitación sube de
**0,6234 a 0,6435** medido con la misma vara. Falta la arena del modelo nuevo,
que es lo único que autoriza usarlo, y está corriendo.

De paso se cazó un tercer bug de medición del mismo tipo que los dos anteriores:
el empaquetador no fijaba los parámetros de búsqueda, así que un envío con `RC`
habría salido con los valores por defecto sin dar ni un error.

El rating, mientras tanto, subió solo: **709,0 → 729,7** y del puesto 1.973 al
**1.609 de 6.807** en trece horas, sin enviar nada. El leaderboard sigue jugando
partidas hasta que converge.

## 1. Presupuesto de búsqueda (`PKM-007`)

El agente de la ladder gastaba **~1% del banco de 600 s**. Ocho configuraciones
medidas contra él, misma red y misma baraja en los dos lados:

| tag | qué mueve | n | tasa | veredicto |
|---|---|---|---|---|
| **RC** | R=32 **y** C=5 | 1600 | **0,6350** [0,6111, 0,6582] | **gana** |
| R32 | rollout 16 → 32 | 1600 | 0,5850 [0,5607, 0,6089] | gana |
| C5 | candidatas 3 → 5 | 1600 | 0,5656 [0,5412, 0,5897] | gana |
| K16 | determinizaciones 8 → 16 | 1600 | 0,5212 | empate |
| P1_banda | regla `hueco` → `banda` | 2000 | 0,4920 | empate |
| M075 | margen 1,5 → 0,75 | 1600 | 0,4775 | empate/peor |
| P0_hueco | regla `hueco` con tope | 2000 | 0,4620 | pierde |
| MINF | buscar siempre | 1600 | 0,4387 | pierde |

**Buscar más no es jugar mejor.** MINF, que busca en todas las decisiones, es el
peor de los ocho — por debajo de no tocar nada. La condición de disparo no era una
limitación que quitar: concentra el presupuesto donde la red duda, y ahí está su
valor. Lo que sí compra es gastar más *en cada* decisión que ya merecía búsqueda.

Y por tercera vez en el proyecto, **dos ejes ortogonales se suman**: 0,585 y 0,566
por separado, 0,635 juntos.

## 2. La palanca de datos (`PKM-008`)

| | ladder (7 días) | nuevo (30 días) |
|---|---|---|
| decisiones de entrenamiento | 1,10 M | **11,42 M** |
| episodios | 7.289 | 74.291 |
| top-1 sobre el **mismo** test (2,45 M) | 0,6234 | **0,6435** |
| log-loss | 1,1149 | **1,0361** |

La comparación con vara común importa: el número anterior (0,6288/0,6201) se medía
sobre el test del corpus pequeño, y comparar modelos sobre tests distintos no dice
nada. Aquí los dos se pasan por `evalua3.py` sobre el test del corpus grande.

La curva **no ha saturado** (351 k → 11,42 M sube 0,6219 → 0,6435) y el modelo ni
siquiera está convergido: se entrenó con 3 épocas por falta de tiempo y seguía
subiendo en la última. Queda margen sin cobrar.

## 3. El tercer bug de medición (`PKM-009`)

`clon_busq2.py` lee su configuración de `os.environ` **en tiempo de import**. El
paquete no fijaba ninguna variable, así que el envío habría llevado rollout 16 y 3
candidatas en vez de 32 y 5 — jugando peor que lo medido, en silencio.

Misma forma que los dos anteriores (`__file__` inexistente en el envío, self-play
silencioso en la arena): **no falla, miente**. Arreglado con `--env K=V`, que
escribe las variables en `main.py` antes del import, y verificado descomprimiendo
el tar en un directorio limpio y ejecutándolo con `exec` sin `__file__`:

```text
PARAMS   R_PASOS=32 N_CAND=5 K_MAX=8 MARGEN=1.5 REGLA=banda TOPE=10.0 DIV=60.0
BÚSQUEDA 165 de 324 decisiones buscadas · 85 cambian la jugada
ERRORES  0 ilegales · 0 excepciones · 0 det. fallidas · 0 cortes de reloj
```

Como subproducto, `verifica_tar.py` leía un contador que el módulo no expone y
devolvía `None` sin quejarse. Cuarta verificación del proyecto que no medía lo que
creía medir; ahora imprime también los parámetros efectivos.

## 4. Una tanda que murió en silencio

La extracción de replays murió el 13-ago a las 20:23 con 13 de 30 shards, mientras
competía con el barrido (15 procesos) y un entrenamiento. Los scripts encadenados
esperaban una línea `FIN-EXTRACCION` que nunca llegó, así que la fusión y el
entrenamiento grande **no arrancaron y no se quejaron**: a la mañana siguiente el
log estaba vacío y todo parecía «en curso».

Relanzada con `--procs 4` terminó en 47 minutos. La lección operativa es la de
siempre en esta casa: un `until grep -q FIN` sin timeout convierte un fallo en un
silencio.

## 5. Estado y lo que falta

- **En la ladder**: μ 729,7, puesto 1.609 de 6.807 (snapshot 14-ago 07:37 UTC).
- **En curso**: dos arenas de 2.000 partidas — red 30d contra red 7d con la misma
  búsqueda, y el candidato completo (red 30d + `RC`) contra el de la ladder.
- **Falta antes de poder enviar**: la fase 3 (campo de 12 arquetipos, auditoría de
  500 partidas, banco reducido a 120 y 30 s) y medir `RC` en `c1-grimmsnarl`, que
  no está probado — el barrido entero se hizo sobre `c2-alakazam`.
- **Riesgo abierto**: `RC` toca el techo del banco (976 cortes, 80.236 decisiones
  sin presupuesto en 312.187), aunque sin perder una sola partida por reloj. Las
  cifras de tiempo están infladas por contención; la medida limpia es el banco
  reducido.
- **Gate del propietario**: qué se sube antes del 16-ago 23:59 UTC. Si nada bate a
  los 729,7 actuales con intervalo limpio, mantener lo que está es la decisión
  correcta.
