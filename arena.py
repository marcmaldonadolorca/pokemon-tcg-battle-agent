#!/usr/bin/env python3
"""Arena: enfrenta dos agentes N partidas y reporta tasa de victoria con IC de Wilson.

La báscula del proyecto: toda comparación entre agentes o barajas pasa por aquí.
Intercambia asientos (mitad de partidas cada lado) para cancelar cualquier efecto
de ir primero, y paraleliza con procesos porque el motor muere con hilos.

Uso:
    .venv/bin/python arena.py --n 200 --procs 8            # random vs random
    .venv/bin/python arena.py --a mi_agente.py --b random  # módulo con agent()

Un agente es "random", "first", o la ruta a un .py con una función agent(obs)->list[int]
y opcionalmente DECK (list[int] de 60 IDs; si falta, usa la baraja de ejemplo del motor).
"""
import argparse
import importlib.util
import math
import multiprocessing as mp
from dataclasses import dataclass


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """Tasa observada e intervalo de Wilson al 95%."""
    if n == 0:
        return 0.0, 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, c - r, c + r


def _carga(spec: str):
    """Devuelve (agente, deck) a partir de un nombre builtin o una ruta .py."""
    if spec in ("random", "first"):
        return spec, None
    s = importlib.util.spec_from_file_location("agente_mod", spec)
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod.agent, getattr(mod, "DECK", None)


@dataclass
class Tarea:
    spec_a: str
    spec_b: str
    a_empieza: bool
    seed_idx: int


def _juega(t: Tarea) -> tuple[int, int]:
    """Una partida en un proceso limpio. Devuelve (gana_a, pasos)."""
    from kaggle_environments import make

    ag_a, deck_a = _carga(t.spec_a)
    ag_b, deck_b = _carga(t.spec_b)
    config = {}
    decks = [deck_a, deck_b] if t.a_empieza else [deck_b, deck_a]
    if any(d is not None for d in decks):
        # El que no aporte baraja usa la de ejemplo del motor
        from kaggle_environments.envs.cabt.cabt import deck as deck_defecto
        config["decks"] = [d if d is not None else list(deck_defecto) for d in decks]
    env = make("cabt", configuration=config, debug=False)
    par = [ag_a, ag_b] if t.a_empieza else [ag_b, ag_a]
    env.run(par)
    r0 = env.state[0].reward
    gana_a = (r0 == 1) if t.a_empieza else (r0 == -1)
    return int(gana_a), len(env.steps)


def enfrenta(spec_a: str, spec_b: str, n: int, procs: int) -> dict:
    tareas = [Tarea(spec_a, spec_b, i % 2 == 0, i) for i in range(n)]
    with mp.Pool(procs) as pool:
        res = pool.map(_juega, tareas)
    victorias = sum(r[0] for r in res)
    v_primero = sum(r[0] for r, t in zip(res, tareas) if t.a_empieza)
    v_segundo = victorias - v_primero
    n_prim = sum(1 for t in tareas if t.a_empieza)
    p, lo, hi = wilson(victorias, n)
    return {
        "n": n,
        "victorias_a": victorias,
        "tasa": p,
        "ic95": (lo, hi),
        "tasa_yendo_primero": v_primero / max(n_prim, 1),
        "tasa_yendo_segundo": v_segundo / max(n - n_prim, 1),
        "pasos_medios": sum(r[1] for r in res) / n,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", default="random")
    ap.add_argument("--b", default="random")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--procs", type=int, default=8)
    args = ap.parse_args()

    r = enfrenta(args.a, args.b, args.n, args.procs)
    lo, hi = r["ic95"]
    print(f"A={args.a}  vs  B={args.b}   ({r['n']} partidas)")
    print(f"tasa de victoria A : {r['tasa']:.3f}  IC95 [{lo:.3f}, {hi:.3f}]")
    print(f"  yendo primero    : {r['tasa_yendo_primero']:.3f}")
    print(f"  yendo segundo    : {r['tasa_yendo_segundo']:.3f}")
    print(f"pasos medios       : {r['pasos_medios']:.0f}")
    if lo > 0.5:
        print("VEREDICTO          : A es mejor (significativo al 95%)")
    elif hi < 0.5:
        print("VEREDICTO          : B es mejor (significativo al 95%)")
    else:
        print("VEREDICTO          : sin diferencia significativa")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
