# Cierre de la Simulation: el envío final no se realizó

Fecha: 2026-08-17. Ticket: `PKM-004` (cerrado sin ejecutar), `PKM-008` (medido).

## Qué pasó

El corte de envíos de la Simulation (2026-08-16 23:59 UTC) se cumplió con el agente
del **12-ago**. El envío final, autorizado por el propietario el 14-ago (`PKM-017`),
**no se subió**.

| hecho | dato |
|---|---|
| Puesto final | **2.138 de 6.892** |
| Score final | **690,7** (`c1-grimmsnarl`), 643,3 (`c2-alakazam`) |
| Envíos del equipo | **2**, el último 2026-08-12 15:20:26 |
| Equipos que subieron el 16-ago | **1.696** |
| Equipos que subieron tras el corte | **0** de 6.892 (el corte era firme) |

El `deadline` que la API de Kaggle reporta para `pokemon-tcg-ai-battle` es
**2026-08-31**, que es el cierre de la competición, no el de envíos. La evidencia de
que el corte real fue el 16-ago es que ni un solo equipo tiene envío posterior.

## El candidato que se quedó sin subir

Arena terminada el 2026-08-14 a las 19:35, n=1.600, asientos intercambiados:

**`30d+RC` (corpus de 30 días + `R_PASOS=32`, `N_CAND=5`) contra el agente de la
ladder: tasa 0,7462, IC95 [0,7244, 0,7670].** Gana el 74,6% de las partidas.
Datos en `scratchpad/cierre/d30rc_c2.json`. Cumplía de sobra la regla del IC limpio
de `PKM-017`.

Con un riesgo sin cerrar: `s_partida_max` **595,6 s frente al banco de 600 s**, 528
cortes de reloj, `ms_max` 11.380 ms, 38.543 decisiones sin presupuesto. Sin partidas
perdidas (3.200 asientos `DONE`, 0 ilegales, 0 excepciones), pero **margen cero**.
Las cifras están infladas por contención y swap; la prueba de banco reducido que lo
habría discriminado seguía pendiente.

## Causa raíz del fallo

El resultado llegó 15 minutos después de terminar el turno de la sesión que lo lanzó.
Los guardianes en segundo plano **no reactivan una sesión**: sus notificaciones se
entregaron el 17-ago, ya cerrado el plazo. Se prometió ejecutar el envío "el sábado"
apoyándose en un mecanismo que no ejecuta nada por sí mismo, y no se programó ninguna
tarea real (`/schedule`, cron) que empaquetara y subiera sin intervención humana.

**Lección operativa:** un compromiso de ejecutar algo con plazo, en ausencia del
propietario, sólo es real si existe una tarea programada que lo dispare. Un aviso en
segundo plano informa; no ejecuta.

## Qué sigue vivo

La **Strategy** (writeup hasta el **2026-09-13**, 415 equipos, 8 finalistas a 30.000
USD) no se ve afectada en su parte principal: el 70% es Model Score por análisis y
consistencia, y el puesto de la ladder sólo «se considera». El material medido está
en disco y es exactamente lo que premia el criterio:

- barrido de presupuesto de búsqueda, 8 configuraciones (`research/notas/busqueda-presupuesto.md`)
- escalado del corpus de imitación a 30 días (`research/notas/clon-datos-final.md`)
- once hipótesis heurísticas medidas y refutadas
- dos bugs de medición propios cazados (`__file__` en el envío; self-play silencioso)
- esta arena de 0,7462 y el coste de reloj que la acompaña

Coste real del fallo: el rank de la Simulation, no la candidatura de la Strategy.
