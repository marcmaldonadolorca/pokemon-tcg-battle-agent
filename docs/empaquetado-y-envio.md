# Empaquetado y envío a la Simulation — contrato real

Construido y verificado el 2026-08-10 con `empaquetar.py`. El contrato de abajo
está contrastado contra el `sample_submission/` oficial y contra un envío que
falló de verdad.

## Estructura del `.tar.gz`

```text
main.py            # punto de entrada; define agent(obs) -> list[int]
deck.csv           # 60 IDs, uno por línea
cards_clean.csv    # catálogo propio que usa la política
agentes/
  __init__.py
  politica.py      # el heurístico, copiado del repo
cg/                # motor oficial del sample_submission (api.py + libcg.so)
```

`tar -czvf submission.tar.gz *` con `main.py` **en la raíz, no anidado**. En
producción todo aterriza en `/kaggle_simulations/agent/`. Límite 197,7 MiB; el
nuestro pesa 0,5 MiB.

`agentes/politica.py` va en subcarpeta a propósito: el heurístico busca su CSV en
`../cards_clean.csv` relativo a su propio fichero, así que esa jerarquía hace que
la ruta resuelva igual en el repo y en el paquete, sin tocar el código.

## La trampa que nos costó un envío

**Kaggle NO importa `main.py`: lo ejecuta con `exec(code_object, env)`**
(`kaggle_environments/agent.py:57`, función `get_last_callable`, que se queda con
el último callable definido). Por tanto:

> **`__file__` NO EXISTE dentro de `main.py`.**

El envío `55407115` (2026-08-10) quedó en `ERROR` por exactamente esto:

```text
File "/kaggle_simulations/agent/main.py", line 5, in <module>
    _AQUI = os.path.dirname(os.path.abspath(__file__))
NameError: name '__file__' is not defined
```

Por eso el `main.py` oficial usa la ruta literal `/kaggle_simulations/agent/` con
un `os.path.exists` como respaldo. El nuestro hace lo mismo.

Matiz: la restricción es solo de `main.py`. Los módulos que él **importa**
(`agentes/politica.py`) sí tienen `__file__` normal.

## Por qué la validación local no lo cazó (y cómo se arregló)

La primera versión de `validar()` hacía `import main`, y ahí `__file__` sí
existe: la prueba pasaba en verde mientras producción reventaba. Un caso de
libro de verificación que no mide lo que cree medir.

Ahora `validar()` replica el entorno real: `chdir` a la carpeta del paquete, el
repo fuera de `sys.path`, y carga del agente con `compile` + `exec` en un espacio
de nombres sin `__file__` — lo mismo que hace Kaggle. Con eso, el fallo se
reproduce en local en cuatro milésimas.

Comprobación extra que conviene repetir en cada envío: descomprimir el tar en un
directorio limpio y confirmar que el catálogo carga **completo** (1.267 cartas,
1.556 ataques, 1.267 textos de trainer y de habilidad). El heurístico degrada en
silencio si no encuentra el CSV, y jugaría peor sin dar ni un error.

## La segunda trampa: los parámetros que no viajan (2026-08-14)

`clon_busq2.py` lee su configuración de búsqueda de variables de entorno **en
tiempo de import**:

```python
R_PASOS = int(os.environ.get("CB2_R", "16"))   # y K_MAX, N_CAND, MARGEN, REGLA, TOPE, DIV
```

En el paquete no había ninguna variable de entorno, así que un envío con la
configuración `RC` (rollout 32, 5 candidatas) habría salido **con los valores por
defecto** —rollout 16, 3 candidatas— y habría jugado peor que lo medido sin dar un
solo error. Misma forma que el `__file__`: no falla, miente.

Arreglo: `empaquetar.py --env K=V` (repetible) escribe las variables en `main.py`
**antes** del `from agentes import politica`, que es el único momento en que sirven
de algo. Ejemplo real del candidato con búsqueda ampliada:

```bash
.venv/bin/python empaquetar.py \
  --deck research/decks/campo/c2-alakazam.csv \
  --politica research/agentes/clon_busq2.py \
  --env CB2_R=32 --env CB2_C=5 --env CB2_TOPE=10.0 --env CB2_DIV=60 \
  --env CB2_REGLA=banda --env CB2_K=8 --env CB2_MARGEN=1.5 \
  --extra research/clon/rasgos.py --extra research/valor/features_v2.py \
  --extra research/valor/features.py --extra research/agentes/heuristico.py \
  --extra research/agentes/mcts.py --extra research/agentes/tracker.py \
  --extra research/search_wrapper.py --extra <pesos>/politica.npz \
  --salida <destino>.tar.gz --validar --n 6
```

Los ficheros de apoyo **no están todos en `research/agentes/`**: `rasgos.py` vive
en `research/clon/`, `features*.py` en `research/valor/` y `search_wrapper.py` en
`research/`. Y los pesos hay que copiarlos con el nombre `politica.npz`, porque el
agente los resuelve por nombre.

Comprobación en directorio limpio con `scratchpad/verifica_tar.py`, que ahora
imprime los parámetros efectivos y los contadores de la búsqueda:

```text
PARAMS   R_PASOS=32 N_CAND=5 K_MAX=8 MARGEN=1.5 REGLA=banda TOPE=10.0 DIV=60.0
BÚSQUEDA 165 de 324 decisiones buscadas · 85 cambian la jugada
ERRORES  0 ilegales · 0 excepciones · 0 det. fallidas · 0 cortes de reloj
```

Ese fichero leía antes un contador que el módulo no expone (`CONTADORES`) y
devolvía `None` sin quejarse — otra verificación que no medía. Ahora cae a `ESTAD`.

## Obtener el diagnóstico de un envío fallido

```bash
kaggle competitions submissions -c pokemon-tcg-ai-battle     # estado
kaggle competitions episodes <submission_id>                 # episodios
kaggle competitions logs <episode_id> <agent_index>          # traza real
```

Los logs traen el `stderr` íntegro del agente. Es la vía rápida: antes de
especular sobre la causa, se descarga la traza.

## Límites de la división

- 5 envíos al día; **solo los 2 últimos siguen activos**.
- El envío arranca con una partida de validación contra sí mismo; si falla, queda
  en `ERROR` y no entra al emparejamiento.
- Rating gaussiano N(μ, σ²) con μ₀ = 600.
- Recursos del pod según el staff: ~1,6 vCPU y 8 GB, con 600 s de reloj de pared
  por agente y partida.
- Práctica del top documentada en los foros: subir el agente final **dos veces**,
  porque el emparejamiento tiene tanta varianza que dos envíos idénticos han
  llegado a puntuar 940 y 790.
