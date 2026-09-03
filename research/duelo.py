#!/usr/bin/env python3
"""arena.py + contador de ILEGALES y de USOS de la palanca, en una sola pasada.

Mismo protocolo que arena.py (intercambio de asiento, IC de Wilson) pero ademas:
  - status de cada jugador al final: cualquier cosa distinta de DONE en el que estamos
    midiendo es una accion ilegal / excepcion (INVALID o ERROR) -> se cuenta y se
    guarda el episodio para inspeccion;
  - agrega los diccionarios USOS y FALLBACKS del modulo A (se resetean por partida
    porque arena recarga el modulo en cada tarea, asi que se suman).

Uso:
  .venv/bin/python duelo.py --a rutaA.py --b rutaB.py --n 600 --procs 3
"""
import argparse
import importlib.util
import json
import math
import multiprocessing as mp
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, c - r, c + r


def _carga(spec):
    s = importlib.util.spec_from_file_location("agente_mod_%d" % abs(hash(spec)), spec)
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod


def _juega(t):
    i, spec_a, spec_b = t
    a_empieza = (i % 2 == 0)
    from kaggle_environments import make
    ma, mb = _carga(spec_a), _carga(spec_b)
    decks = [ma.DECK, mb.DECK] if a_empieza else [mb.DECK, ma.DECK]
    env = make("cabt", configuration={"decks": [list(d) for d in decks]}, debug=False)
    par = [ma.agent, mb.agent] if a_empieza else [mb.agent, ma.agent]
    env.run(par)
    idx_a = 0 if a_empieza else 1
    r0 = env.state[0].reward
    gana_a = (r0 == 1) if a_empieza else (r0 == -1)
    st = [env.state[0].status, env.state[1].status]
    usos = dict(getattr(ma, "USOS", None) or {})
    fb = dict(getattr(ma, "FALLBACKS", None) or {})
    return dict(i=i, a_empieza=a_empieza, gana_a=int(gana_a), pasos=len(env.steps),
                st_a=st[idx_a], st_b=st[1 - idx_a], usos=usos, fb=fb)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--n", type=int, default=600)
    ap.add_argument("--procs", type=int, default=3)
    ap.add_argument("--etiqueta", default="")
    ap.add_argument("--salida", default="")
    a = ap.parse_args()

    tareas = [(i, a.a, a.b) for i in range(a.n)]
    with mp.Pool(a.procs) as pool:
        res = pool.map(_juega, tareas, chunksize=2)

    k = sum(r["gana_a"] for r in res)
    p, lo, hi = wilson(k, a.n)
    n0 = sum(1 for r in res if r["a_empieza"])
    as0 = sum(r["gana_a"] for r in res if r["a_empieza"]) / max(n0, 1)
    as1 = sum(r["gana_a"] for r in res if not r["a_empieza"]) / max(a.n - n0, 1)
    mal_a = [r for r in res if r["st_a"] != "DONE"]
    mal_b = [r for r in res if r["st_b"] != "DONE"]
    usos, fb = {}, {}
    for r in res:
        for d, acc in ((r["usos"], usos), (r["fb"], fb)):
            for kk, vv in d.items():
                acc[kk] = acc.get(kk, 0) + vv

    out = dict(etiqueta=a.etiqueta, a=a.a, b=a.b, n=a.n, victorias=k, tasa=p,
               ic95=[lo, hi], as0=as0, as1=as1,
               pasos_medios=sum(r["pasos"] for r in res) / a.n,
               ilegales_a=len(mal_a), ilegales_b=len(mal_b),
               estados_a=sorted({r["st_a"] for r in res}),
               estados_b=sorted({r["st_b"] for r in res}),
               usos=usos, fallbacks=fb)
    print(json.dumps(out, ensure_ascii=False))
    if a.salida:
        with open(a.salida, "w") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
    print("%-22s n=%d tasa=%.3f IC95[%.3f,%.3f] as0=%.3f as1=%.3f ilegalesA=%d ilegalesB=%d"
          % (a.etiqueta or "?", a.n, p, lo, hi, as0, as1, len(mal_a), len(mal_b)),
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
