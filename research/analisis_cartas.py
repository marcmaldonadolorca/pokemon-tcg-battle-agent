# Análisis del pool de cartas — competición Kaggle Pokémon TCG (cabt)
# Genera research/cards_clean.csv (una fila por carta) y saca el censo por stdout.
# Uso: .venv/bin/python research/analisis_cartas.py
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "raw" / "EN_Card_Data.csv"
OUT = ROOT / "research" / "cards_clean.csv"

STAGE_COL = "Stage (Pokémon)/Type (Energy and Trainer)"

df = pd.read_csv(CSV)

# ---------- 1. Verificación de estructura multi-fila ----------
print("== Estructura ==")
print(f"filas={len(df)}  Card ID únicos={df['Card ID'].nunique()}")
print("filas por carta:", df.groupby("Card ID").size().value_counts().to_dict())
static_cols = [
    "Card Name", "Expansion", "Collection No.", STAGE_COL, "Rule", "Category",
    "Previous stage", "HP", "Type", "Weakness", "Resistance (Type)", "Retreat",
]
incons = df.groupby("Card ID")[static_cols].nunique(dropna=False).gt(1).any(axis=1).sum()
print(f"cartas con columnas estáticas inconsistentes: {incons} (0 = una fila por movimiento, resto constante)")

# Tipos de fila: ataque normal, [Ability] o [Tera]
mv = df["Move Name"].astype(str)
df["_row_kind"] = "attack"
df.loc[mv.str.startswith("[Ability]"), "_row_kind"] = "ability"
df.loc[mv == "[Tera]", "_row_kind"] = "tera"
df.loc[df["Move Name"].isna() | (mv == "n/a"), "_row_kind"] = "none"
print("tipos de fila:", df["_row_kind"].value_counts().to_dict())

# ---------- 2. Tabla limpia una-fila-por-carta ----------
def fmt_attack(r):
    dmg = "" if pd.isna(r["Damage"]) else str(r["Damage"])
    eff = "" if pd.isna(r["Effect Explanation"]) else str(r["Effect Explanation"]).replace("\n", " ")
    return f"{r['Move Name']} [{r['Cost']}] {dmg} :: {eff}".strip()

rows = []
for cid, g in df.groupby("Card ID", sort=True):
    r0 = g.iloc[0]
    atks = g[g["_row_kind"] == "attack"]
    abil = g[g["_row_kind"] == "ability"]
    tera = g[g["_row_kind"] == "tera"]
    trainer_eff = ""
    if r0[STAGE_COL] in ("Item", "Supporter", "Stadium", "Pokémon Tool", "Special Energy", "Basic Energy"):
        effs = g["Effect Explanation"].dropna().astype(str)
        trainer_eff = " || ".join(e.replace("\n", " ") for e in effs)
    rows.append({
        "card_id": cid,
        "name": r0["Card Name"],
        "expansion": r0["Expansion"],
        "supertype": r0[STAGE_COL],
        "rule": r0["Rule"] if pd.notna(r0["Rule"]) else "",
        "category": r0["Category"] if pd.notna(r0["Category"]) else "",
        "prev_stage": r0["Previous stage"] if pd.notna(r0["Previous stage"]) else "",
        "hp": r0["HP"],
        "type": r0["Type"] if pd.notna(r0["Type"]) else "",
        "weakness": r0["Weakness"] if pd.notna(r0["Weakness"]) else "",
        "retreat": r0["Retreat"],
        "n_attacks": len(atks),
        "has_ability": len(abil) > 0,
        "is_tera": len(tera) > 0,
        "ability_text": " || ".join(
            f"{a['Move Name']} :: {str(a['Effect Explanation']).replace(chr(10), ' ')}" for _, a in abil.iterrows()
        ),
        "attacks": " ;; ".join(fmt_attack(a) for _, a in atks.iterrows()),
        "trainer_effect": trainer_eff,
    })
clean = pd.DataFrame(rows)
clean.to_csv(OUT, index=False)
print(f"\ncards_clean.csv: {len(clean)} cartas -> {OUT}")

# ---------- 3. Censo ----------
print("\n== Censo ==")
print(clean["supertype"].value_counts().to_string())
is_pkm = clean["supertype"].str.contains("Pokémon") & ~clean["supertype"].isin(["Pokémon Tool"])
pkm = clean[is_pkm]
print(f"\nPokémon: {len(pkm)}  (ex={len(pkm[pkm.rule=='Pokémon ex'])}, Mega ex={len(pkm[pkm.rule=='Mega Pokémon ex'])}, "
      f"single-prize={len(pkm[pkm.rule==''])})")
print(f"Trainers: Item={len(clean[clean.supertype=='Item'])}, Supporter={len(clean[clean.supertype=='Supporter'])}, "
      f"Stadium={len(clean[clean.supertype=='Stadium'])}, Tool={len(clean[clean.supertype=='Pokémon Tool'])}")
print(f"Energía: básica={len(clean[clean.supertype=='Basic Energy'])}, especial={len(clean[clean.supertype=='Special Energy'])}")
print("Tipos de energía básica:", clean[clean.supertype == "Basic Energy"]["type"].tolist())
print("ACE SPEC:", len(clean[clean.rule == "ACE SPEC"]))
print("\nDistribución de HP (Pokémon):")
print(pkm["hp"].describe().to_string())
print(pkm.groupby("supertype")["hp"].agg(["min", "median", "max"]).to_string())
print("HP máximos:", pkm.nlargest(5, "hp")[["card_id", "name", "hp"]].values.tolist())

# ---------- Líneas evolutivas completas ----------
# Enlace por 'Previous stage' (nombre). Nombres con múltiples versiones cuentan una vez.
names_by_stage = {
    s: set(pkm[pkm.supertype == s]["name"]) for s in ("Basic Pokémon", "Stage 1 Pokémon", "Stage 2 Pokémon")
}
s2 = pkm[pkm.supertype == "Stage 2 Pokémon"].drop_duplicates("name")
s1 = pkm[pkm.supertype == "Stage 1 Pokémon"].drop_duplicates("name")
s1_prev = dict(zip(s1["name"], s1["prev_stage"]))
full_lines = []
for _, r in s2.iterrows():
    mid = r["prev_stage"]
    base = s1_prev.get(mid)
    if mid in names_by_stage["Stage 1 Pokémon"] and base in names_by_stage["Basic Pokémon"]:
        full_lines.append((base, mid, r["name"]))
print(f"\nLíneas evolutivas Basic→Stage1→Stage2 completas: {len(full_lines)}")
# Stage1 con básico presente (líneas de 2 piezas jugables)
s1_ok = [n for n, p in s1_prev.items() if p in names_by_stage["Basic Pokémon"]]
print(f"Líneas Basic→Stage1 completas: {len(s1_ok)} (de {len(s1)} Stage 1 únicos)")
s2_names = {x[2] for x in full_lines}
print("Stage 2 SIN línea completa:", sorted(set(s2["name"]) - s2_names)[:20])

# ---------- 4. Motores de robo / búsqueda / aceleración ----------
def dump(title, sub, col="trainer_effect", n=60):
    print(f"\n== {title} ({len(sub)}) ==")
    for _, r in sub.head(n).iterrows():
        print(f"  {r['card_id']:>4} {r['name']:<38} {str(r[col])[:130]}")

tr = clean[clean.supertype.isin(["Item", "Supporter", "Stadium", "Pokémon Tool"])]
draw_sup = tr[(tr.supertype == "Supporter") & tr.trainer_effect.str.contains(r"[Dd]raw", na=False)]
dump("Supporters de robo", draw_sup)
search_it = tr[(tr.supertype == "Item") & tr.trainer_effect.str.contains(r"Search your deck", na=False)]
dump("Items de búsqueda", search_it)
accel = clean[
    clean.trainer_effect.str.contains(r"[Aa]ttach.*Energy", na=False)
    | clean.ability_text.str.contains(r"[Aa]ttach.*Energy", na=False)
]
dump("Aceleración de energía (trainers)", accel[accel.trainer_effect != ""])
acc_ab = accel[accel.ability_text != ""]
print(f"\n== Aceleración por habilidad ({len(acc_ab)}) ==")
for _, r in acc_ab.iterrows():
    print(f"  {r['card_id']:>4} {r['name']:<32} {r['supertype']:<16} {r['rule']:<16} {str(r['ability_text'])[:120]}")

# ---------- 5. Baraja de ejemplo del motor ----------
print("\n== Baraja de ejemplo de cabt.py ==")
example = [721, 721, 722, 722, 722, 722, 723, 723, 723, 723, 1092, 1121, 1121, 1145, 1145,
           1163, 1163, 1219, 1219, 1219, 1219, 1227, 1227, 1227, 1227, 1262, 1262] + [3] * 33
from collections import Counter
for cid, n in Counter(example).items():
    r = clean[clean.card_id == cid].iloc[0]
    print(f"  {n}x [{cid}] {r['name']} ({r['supertype']}{', ' + r['rule'] if r['rule'] else ''})")

# ---------- 6. Exploración para arquetipos ----------
pkm2 = clean[is_pkm].copy()
def maxdmg(s):
    return max((int(d) for d in re.findall(r"\] (\d+)[+x×]?\s*(?:::|;;|$)", str(s))), default=0)
pkm2["maxdmg"] = pkm2["attacks"].apply(maxdmg)

def top(title, sub, n=15):
    print(f"\n== {title} ==")
    for _, r in sub.nlargest(n, "maxdmg").iterrows():
        print(f"  {r['card_id']:>4} {r['name']:<30} {r['supertype'][:7]} {r['type']:<4} HP{r['hp']:.0f} :: {str(r['attacks'])[:150]}")

top("Top daño single-prize Basic", pkm2[(pkm2.rule == "") & (pkm2.supertype == "Basic Pokémon")])
top("Top daño single-prize evolución", pkm2[(pkm2.rule == "") & (pkm2.supertype != "Basic Pokémon")])
top("Top daño Basic Pokémon ex (2 premios)", pkm2[(pkm2.rule == "Pokémon ex") & (pkm2.supertype == "Basic Pokémon")])
top("Top daño Mega ex (3 premios)", pkm2[pkm2.rule == "Mega Pokémon ex"])

print("\n== Debilidades (censo, a qué tipo pega más gente) ==")
print(pkm2.weakness.value_counts().to_string())

print("\n== Paquetes de 'Trainer's Pokémon' (censo por dueño) ==")
print(clean[clean.category.str.contains("Trainer's", na=False)].category.value_counts().to_string())
