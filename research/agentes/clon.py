#!/usr/bin/env python3
"""Agente CLON: red de política entrenada por imitación sobre los replays de los
equipos mejor valorados de la ladder. Inferencia numpy pura.

Cómo decide: puntúa CADA opción del select por separado con la red
(research/clon/entrenar.py) y se queda con el argmax; cuando `minCount == 0` hay
una opción virtual «no elegir nada» que compite con las demás, así que pasar una
búsqueda es una jugada que la red puede elegir.

Blindaje (una acción ilegal = derrota instantánea, no un punto perdido):
  1. toda la ruta va dentro de un try; cualquier excepción cae al heurístico;
  2. la acción construida se valida con `heuristico._es_legal` antes de salir;
  3. si no es legal, se usa `heuristico._politica` y, si esa tampoco, `_fallback`.
Es decir: el peor caso del clon es «jugar como heuristico.py», nunca perder por
formato.

Híbrido: `MODO` decide qué clases de decisión van a la red.
  "todo"      — la red decide siempre (clon puro)
  "principal" — red solo en la fase principal (0,0)
  "auxiliar"  — red en todo MENOS la fase principal
  "sel7"      — red solo en la búsqueda en mazo (1,7)
  "principal+busqueda" — (0,0) y (1,7)
Se puede fijar con la variable de entorno CLON_MODO.
"""
import importlib.util
import os
import sys

import numpy as np

_D = os.path.dirname(os.path.abspath(__file__))

# Rutas tolerantes a DOS disposiciones: el repo (research/agentes + research/clon +
# research/valor) y el paquete de envio, donde todo cae junto en una carpeta.
# `main.py` no tiene __file__, pero los modulos que IMPORTA si (docs/empaquetado-y-envio.md).
for _p in (_D, os.path.join(_D, "..", "clon"), os.path.join(_D, "..", "valor")):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)
import rasgos  # noqa: E402


def _busca(nombre):
    for _p in (_D, os.path.join(_D, "..", "clon"), os.path.join(_D, "..", "agentes")):
        r = os.path.join(_p, nombre)
        if os.path.exists(r):
            return r
    return os.path.join(_D, nombre)


_s = importlib.util.spec_from_file_location("clon_heur_base", _busca("heuristico.py"))
_heur = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_heur)

MODO = os.environ.get("CLON_MODO", "todo")
_RUTA = os.environ.get("CLON_PESOS") or _busca("politica.npz")

DECK = [677, 677, 677, 677, 678, 678, 678, 678, 447, 447, 447, 447, 1142, 1142,
        1142, 1142, 1121, 1121, 1121, 1121, 1125, 1123, 1123, 1097, 1097, 1141,
        1141, 1238, 1238, 1224, 1224, 1224, 1224, 1236, 1236, 1236, 1236, 1227,
        1227, 1182, 1182, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6]

CONTADORES = {"red": 0, "heuristico": 0, "excepcion": 0, "ilegal": 0, "sin_pesos": 0}

_P = None


def _pesos():
    global _P
    if _P is None:
        z = np.load(_RUTA)
        _P = {k: z[k] for k in ("W1s", "W1o", "b1", "W2", "b2", "w3", "b3", "bc")}
        _P["ncart"] = len(_P["bc"])
    return _P


def _puntua(sel, cur):
    """Puntuación de cada fila de opciones (la última es «pasar» si minCount==0)."""
    P = _pesos()
    s = rasgos.rasgos_estado(sel, cur)
    O, C = rasgos.rasgos_opciones(sel, cur)
    if len(O) == 0:
        return None
    h1 = np.maximum(s @ P["W1s"] + O @ P["W1o"] + P["b1"], 0.0)
    h2 = np.maximum(h1 @ P["W2"] + P["b2"], 0.0)
    z = (h2 @ P["w3"]).ravel() + P["b3"][0]
    nc = P["ncart"]
    ci = np.where((C >= 0) & (C < nc - 1), C, nc - 1)
    return z + P["bc"][ci]


def _decide(sel, cur):
    """Acción (lista de índices) a partir de las puntuaciones de la red."""
    opt = sel.get("option") or []
    k = len(opt)
    if k == 0:
        return [0]                      # confirmación (0,7): el motor acepta [0]
    z = _puntua(sel, cur)
    if z is None:
        return None
    mn = int(sel.get("minCount") or 0)
    mx = int(sel.get("maxCount") or 1)
    hay_pasa = len(z) == k + 1
    zo = z[:k]
    orden = np.argsort(-zo)
    if mn == mx:
        return [int(i) for i in orden[:mn]]
    if hay_pasa:
        umbral = float(z[k])
        sel_i = [int(i) for i in orden[:mn]]
        for i in orden[mn:mx]:
            if float(zo[i]) > umbral:
                sel_i.append(int(i))
            else:
                break
        return sel_i
    return [int(i) for i in orden[:max(mn, 1)]]


def _usa_red(sel):
    if MODO == "todo":
        return True
    t, c = sel.get("type"), sel.get("context")
    if MODO == "principal":
        return (t, c) == (0, 0)
    if MODO == "auxiliar":
        return (t, c) != (0, 0)
    if MODO == "sel7":
        return (t, c) == (1, 7)
    if MODO == "principal+busqueda":
        return (t, c) in ((0, 0), (1, 7))
    return True


def _heuristica(sel, cur):
    try:
        acc = _heur._politica(sel, cur)
    except Exception:
        acc = None
    if not _heur._es_legal(acc, sel):
        acc = _heur._fallback(sel)
    return acc


def agent(obs) -> list:
    sel = obs["select"]
    if sel is None:
        return list(DECK)
    cur = obs["current"]
    if _usa_red(sel):
        acc = None
        try:
            acc = _decide(sel, cur)
        except Exception:
            CONTADORES["excepcion"] += 1
            acc = None
        if acc is not None and _heur._es_legal(acc, sel):
            CONTADORES["red"] += 1
            return acc
        if acc is not None:
            CONTADORES["ilegal"] += 1
    CONTADORES["heuristico"] += 1
    return _heuristica(sel, cur)
