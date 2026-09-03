#!/usr/bin/env python3
"""Replays diarios -> dataset (estado, opciones, acción del experto) para la red
de POLÍTICA. Sucesor de research/replays/extraer.py con el esquema rico de
research/clon/rasgos.py (114 rasgos de estado, 96 por opción).

DESFASE +1 (verificado en research/notas/replays-imitacion.md §2): la acción que
responde a `steps[k][p].observation` está en `steps[k+1][p].action`.

Diferencias con el piloto:
  * rasgos de estado v2 (62) + forma del select (52), no los 30 de la v1;
  * rasgos de opción que describen lo que la opción HACE (carta resuelta,
    objetivo en juego, ataque concreto), no solo sus campos crudos;
  * resuelve `area == 1` contra `select.deck` (búsquedas en mazo: era >50% de
    las opciones no resueltas del piloto) y el `type 7` sin `area` (mano);
  * admite acciones MULTI (objetivo repartido) y la acción VACÍA (slot «pasar»).

Salida .npz (ragged con punteros):
    S    (n, 114) float32
    O    (m, 96)  float16   (mitad de RAM; se castea a float32 por lote)
    C    (m,)     int32     id de carta de la opción (-1 si no resoluble)
    ptr  (n+1,)   int32
    T    (m,)     float32   objetivo: 1/len(accion) en las elegidas, 0 el resto
    y    (n,)     int32     argmax del objetivo (para top-1)
    ep   (n,)     int32     índice de episodio (corte train/val/test SIN fuga)
    meta (n, 8)   float32   [sel_type, sel_context, turno, rmin, ravg, k, nsel,
                             acierta_heuristico]  <- suelo medido en LAS MISMAS
                             decisiones, no citado de otra tanda
"""
import argparse
import csv
import io
import json
import multiprocessing as mp
import os
import sys
import zipfile

import numpy as np

_D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _D)
import rasgos  # noqa: E402

# El heuristico de la ladder, como SUELO medido decision a decision (no citado).
import importlib.util  # noqa: E402
_hs = importlib.util.spec_from_file_location(
    "heur_suelo", os.path.join(_D, "..", "agentes", "heuristico.py"))
_heur = importlib.util.module_from_spec(_hs)
_hs.loader.exec_module(_heur)


def _heuristico(sel, cur):
    """Lo que devolveria research/agentes/heuristico.py (con su propio fallback)."""
    try:
        acc = _heur._politica(sel, cur)
    except Exception:
        acc = None
    if not _heur._es_legal(acc, sel):
        acc = _heur._fallback(sel)
    return acc

RUTA = None
_MAN = {}


def una(nm):
    z = zipfile.ZipFile(RUTA)
    ep = json.loads(z.read(nm))
    eid = ep["info"]["EpisodeId"]
    rmin, ravg = _MAN.get(eid, (0.0, 0.0))
    pasos = ep["steps"]
    S, O, C, tam, T, Y, M = [], [], [], [], [], [], []
    for p in (0, 1):
        for k in range(len(pasos) - 1):
            e = pasos[k][p]
            if e.get("status") != "ACTIVE":
                continue
            obs = e["observation"]
            sel = obs.get("select")
            cur = obs.get("current")
            if not sel or not cur:
                continue
            opt = sel.get("option") or []
            mn = sel.get("minCount") or 0
            npos = len(opt) + (1 if mn == 0 else 0)
            if npos < 2:
                continue                       # sin elección: no enseña nada
            a = pasos[k + 1][p].get("action")
            if a is None or not isinstance(a, list):
                continue
            if len(a) == 0:
                if mn != 0:
                    continue
                elegidas = [len(opt)]          # slot «pasar»
            else:
                if not all(isinstance(i, int) and 0 <= i < len(opt) for i in a):
                    continue                   # incoherente con el desfase: fuera
                elegidas = sorted(set(a))
            Ov, Cv = rasgos.rasgos_opciones(sel, cur)
            if len(Ov) != npos:
                continue
            t = np.zeros(npos, np.float32)
            t[elegidas] = 1.0 / len(elegidas)
            ah = _heuristico(sel, cur)
            esperado = [] if elegidas == [len(opt)] else elegidas
            ok_h = 1.0 if sorted(set(ah or [])) == esperado else 0.0
            S.append(rasgos.rasgos_estado(sel, cur))
            O.append(Ov.astype(np.float16))
            C.append(Cv)
            tam.append(npos)
            T.append(t)
            Y.append(int(np.argmax(t)))
            M.append((sel.get("type", -1), sel.get("context", -1),
                      float(cur.get("turn") or 0), rmin, ravg,
                      float(npos), float(len(elegidas)), ok_h))
    if not S:
        return None
    return (np.asarray(S, np.float32), np.concatenate(O),
            np.concatenate(C), np.asarray(tam, np.int32),
            np.concatenate(T), np.asarray(Y, np.int32),
            np.asarray(M, np.float32), eid)


def main():
    global RUTA, _MAN
    ap = argparse.ArgumentParser()
    ap.add_argument("zip", nargs="+")
    ap.add_argument("--salida", required=True)
    ap.add_argument("--episodios", type=int, default=800, help="por zip")
    ap.add_argument("--procs", type=int, default=3)
    ap.add_argument("--min-rating", type=float, default=0.0)
    a = ap.parse_args()
    todo = []
    off = 0
    for zp in a.zip:
        RUTA = zp
        z = zipfile.ZipFile(zp)
        man = list(csv.DictReader(io.StringIO(z.read("manifest.csv").decode())))
        _MAN = {int(r["episode_id"]): (float(r["min_score"]), float(r["avg_score"]))
                for r in man}
        buenos = {e for e, (mn, _) in _MAN.items() if mn >= a.min_rating}
        nombres = [n for n in z.namelist()
                   if n.endswith(".json") and int(n[:-5]) in buenos][:a.episodios]
        print("%s: pasan rating>=%.0f  %d ; se usan %d"
              % (os.path.basename(zp), a.min_rating, len(buenos), len(nombres)),
              flush=True)
        with mp.Pool(a.procs, initializer=_init, initargs=(zp, _MAN)) as pool:
            res = [r for r in pool.imap_unordered(una, nombres, chunksize=4) if r]
        for i, r in enumerate(res):
            todo.append((r, off + i))
        off += len(res)

    S = np.concatenate([r[0] for r, _ in todo])
    O = np.concatenate([r[1] for r, _ in todo])
    C = np.concatenate([r[2] for r, _ in todo])
    tam = np.concatenate([r[3] for r, _ in todo])
    T = np.concatenate([r[4] for r, _ in todo])
    Y = np.concatenate([r[5] for r, _ in todo])
    M = np.concatenate([r[6] for r, _ in todo])
    ep = np.concatenate([np.full(len(r[5]), i, np.int32) for r, i in todo])
    ptr = np.zeros(len(tam) + 1, np.int32)
    np.cumsum(tam, out=ptr[1:])
    np.savez(a.salida, S=S, O=O, C=C, ptr=ptr, T=T, y=Y, ep=ep, meta=M)
    print("decisiones %d  opciones %d (%.2f/dec)  episodios %d"
          % (len(Y), len(O), len(O) / len(Y), len(todo)))
    print("cartas resueltas %.1f%%   fichero %.0f MB"
          % (100.0 * (C >= 0).mean(), os.path.getsize(a.salida) / 1e6))


def _init(zp, man):
    global RUTA, _MAN
    RUTA, _MAN = zp, man


if __name__ == "__main__":
    main()
