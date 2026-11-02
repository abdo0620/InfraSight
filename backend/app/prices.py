"""Unit prices for the cost estimate of the full AI report. Muse Spark only chooses the work items and the quantities
(from the measured damage); the amounts are computed here, from these rates, so every euro can be traced to a source.

The rates are EUR excluding VAT, taken from public French price schedules (BPU, bordereau des prix unitaires) of
communes and public bodies, 2021-2024. They vary by region and contract: a commune should replace them with the
rates of its own works contract (marché à bons de commande), and keep the source of each line."""
import math

SRC = {
    "retep": ("BPU travaux, Régie des eaux Terre de Provence, 2022",
              "https://eaux-terredeprovence.fr/wp-content/uploads/2022/06/BPU_TP_RETEP.pdf"),
    "prunelli": ("BPU annexe 2, commune de Prunelli-di-Fiumorbu, 2021",
                 "https://www.prunellidifiumorbu.fr/wp-content/uploads/2021/03/DEL220321-3-Annexe-2-RSA-BPU-AR.pdf"),
    "bourg": ("Grille des réfections de tranchées, Bourg-en-Bresse",
              "https://www.bourgenbresse.fr/uploads/Document/8a/1389_205_Telecharger-la-grille-tarifaire-des-refections"
              "-definitives-de-tranchees.pdf"),
    "presto": ("Prix de l'enrobé au m², Habitatpresto (market prices)",
               "https://www.habitatpresto.com/mag/maconnerie/prix-enrobe"),
}

# code: (work item, unit, min rate, max rate, sources)
PRICES = {
    "cold_patch": ("Temporary cold-mix patch, to make safe", "m²", 26, 47, ["presto", "prunelli"]),
    "hot_patch_small": ("Final hot-mix asphalt repair, under 10 m² (4 to 8 cm)", "m²", 79, 104, ["retep", "prunelli"]),
    "hot_patch_large": ("Final hot-mix asphalt repair, over 10 m²", "m²", 28, 83, ["retep", "prunelli"]),
    "planing": ("Planing (rabotage) of the old asphalt, 1 to 6 cm, under 50 m²", "m²", 15.75, 15.75, ["bourg"]),
    "signage_setup": ("Temporary road signage: set up and removal", "lump sum", 578, 578, ["retep"]),
    "signage_day": ("Temporary road signage: upkeep", "day", 29, 29, ["retep"]),
}
UNPRICED = "unpriced"  # work with no rate in the catalogue (a lamp, a tree, bulky waste): the AI amount, to verify


def catalogue() -> list[dict]:
    """What the AI may choose from (no rates: it does not compute amounts)."""
    return [{"code": k, "item": v[0], "unit": v[1]} for k, v in PRICES.items()] + [
        {"code": UNPRICED, "item": "Any other work (give your own min and max in EUR, it will be marked to verify)",
         "unit": "lump sum"}]


def apply(cost: dict, size: dict | None) -> dict:
    """cost: the AI answer {"lines": [{"code", "quantity", "why", "min"?, "max"?}], ...}. Returns the cost with each
    line priced and sourced, the total range, and a basis that says where the quantities and the rates come from.
    With a low-confidence size the upper quantity is 1.5 times the estimate."""
    spread = 1.5 if (size or {}).get("confidence") == "low" else 1.0
    lines, lo, hi, used, guessed = [], 0.0, 0.0, [], False
    for x in cost.get("lines") or []:
        q = max(0.0, float(x.get("quantity") or 0))
        code = x.get("code")
        if code in PRICES:
            item, unit, rmin, rmax, src = PRICES[code]
            q = math.ceil(q * 100) / 100
            qmax = q * spread if unit == "m²" else q
            a, b = q * rmin, qmax * rmax
            used += [s for s in src if s not in used]
            line = {"code": code, "item": item, "unit": unit, "quantity": q, "rate_min": rmin, "rate_max": rmax,
                    "sources": [{"name": SRC[s][0], "url": SRC[s][1]} for s in src]}
        else:
            a, b = sorted((float(x.get("min") or 0), float(x.get("max") or 0)))
            guessed = True
            line = {"code": UNPRICED, "item": (x.get("item") or "Other work") + " [verify]", "unit": "lump sum",
                    "quantity": q or 1, "rate_min": None, "rate_max": None, "sources": []}
        lines.append(line | {"why": x.get("why") or "", "total_min": round(a), "total_max": round(b)})
        lo, hi = lo + a, hi + b
    if not lines:                                   # nothing usable: keep the AI range, clearly marked
        return {**cost, "lines": [], "basis": (cost.get("basis") or "No work items chosen.") + " [verify]"}
    measured = (f"Quantities from the measured damage: about {size['width_m']} × {size['length_m']} m, "
                f"{size['area_m2']} m² ({size['confidence']} confidence, SAM 3.1 outline + Muse Spark)."
                if size and size.get("area_m2") else
                "No measured size: quantities estimated from the photo [verify]. Run “Outline and measure the "
                "damage” for measured quantities.")
    rates = ("Unit rates from public French price schedules (" + "; ".join(SRC[s][0] for s in used) + "): replace "
             "them with the commune's own contract rates." if used else "")
    return {"min": round(lo), "max": round(hi), "lines": lines,
            "basis": " ".join(x for x in (measured, rates, "Some lines have no reference price [verify]." if guessed
                                          else "") if x)}
