"""
Motor de análisis estadístico y heurístico para el análisis de combinaciones.
"""
from __future__ import annotations
import random
from collections import defaultdict
import numpy as np
from config import (RECENT_DRAWS_ANALYSIS, MIN_SIMILAR_MATCHES,
                    THIRDS_HOT_FACTOR, HL_CONFIDENCE)
from utils.math_utils import is_prime, is_all_consecutive, is_all_prime, has_many_consecutive


# ═══════════════════════════════════════════════════════════════════════════
# 1. Verificación de combinaciones
# ═══════════════════════════════════════════════════════════════════════════

def find_exact_match(combination: list[int], draws: list[dict]) -> list[dict]:
    """Retorna sorteos donde la combinación aparece exactamente (sin importar orden)."""
    target = set(combination)
    return [d for d in draws if set(d["numbers"]) == target]


def find_similar(combination: list[int], draws: list[dict],
                 min_matches: int = MIN_SIMILAR_MATCHES) -> list[dict]:
    """
    Retorna lista de sorteos donde al menos `min_matches` posiciones coinciden
    exactamente (misma posición, mismo número).
    Agrega campo 'matched_positions' con los índices que coinciden.
    """
    results = []
    for d in draws:
        nums = d["numbers"]
        length = min(len(combination), len(nums))
        matched = [i for i in range(length) if combination[i] == nums[i]]
        if len(matched) >= min_matches:
            entry = dict(d)
            entry["matched_positions"] = matched
            results.append(entry)
    return sorted(results, key=lambda x: len(x["matched_positions"]), reverse=True)


# ═══════════════════════════════════════════════════════════════════════════
# 2. Frecuencia por posición
# ═══════════════════════════════════════════════════════════════════════════

def frequency_per_position(draws: list[list[int]], positions: int,
                            min_num: int, max_num: int,
                            recent_n: int = RECENT_DRAWS_ANALYSIS) -> list[dict[int, int]]:
    """
    Para cada posición devuelve {número: frecuencia} usando los últimos `recent_n` sorteos.
    """
    recent = draws[-recent_n:] if len(draws) > recent_n else draws
    freq_list = []
    for pos in range(positions):
        freq: dict[int, int] = {n: 0 for n in range(min_num, max_num + 1)}
        for draw in recent:
            if pos < len(draw):
                n = draw[pos]
                if min_num <= n <= max_num:
                    freq[n] += 1
        freq_list.append(freq)
    return freq_list


def global_frequency(draws: list[list[int]], min_num: int, max_num: int) -> dict[int, int]:
    """Frecuencia global (sin posición) de todos los sorteos."""
    freq: dict[int, int] = {n: 0 for n in range(min_num, max_num + 1)}
    for draw in draws:
        for n in draw:
            if min_num <= n <= max_num:
                freq[n] += 1
    return freq


# ═══════════════════════════════════════════════════════════════════════════
# 3. Ley del Tercio
# ═══════════════════════════════════════════════════════════════════════════

def get_thirds(min_num: int, max_num: int) -> tuple[range, range, range]:
    """Divide el rango en tres tercios lo más iguales posible."""
    pool = max_num - min_num + 1
    t = pool // 3
    r = pool % 3
    end1 = min_num + t + (1 if r >= 1 else 0) - 1
    end2 = end1 + t + (1 if r >= 2 else 0)
    t1 = range(min_num, end1 + 1)
    t2 = range(end1 + 1, end2 + 1)
    t3 = range(end2 + 1, max_num + 1)
    return t1, t2, t3


def law_of_thirds(draws: list[list[int]], positions: int,
                   min_num: int, max_num: int,
                   recent_n: int = RECENT_DRAWS_ANALYSIS) -> list[dict]:
    """
    Para cada posición, determina qué números evitar según la Ley del Tercio.

    Lógica:
      - Se divide el rango en 3 tercios iguales.
      - Se cuentan las apariciones de cada tercio en los últimos `recent_n` sorteos.
      - Si un tercio excede el umbral (esperado × THIRDS_HOT_FACTOR), está "caliente"
        y sus números deben evitarse en el siguiente sorteo.

    Retorna una lista (una entrada por posición) con:
      {
        'thirds': [{'range': range, 'count': int, 'expected': float, 'hot': bool}, ...],
        'avoid': [lista de números a evitar],
      }
    """
    recent = draws[-recent_n:] if len(draws) > recent_n else draws
    t1, t2, t3 = get_thirds(min_num, max_num)
    thirds_ranges = [t1, t2, t3]
    expected = len(recent) / 3.0

    result = []
    for pos in range(positions):
        counts = [0, 0, 0]
        for draw in recent:
            if pos < len(draw):
                n = draw[pos]
                for idx, tr in enumerate(thirds_ranges):
                    if n in tr:
                        counts[idx] += 1
                        break

        thirds_info = []
        avoid = []
        for idx, (tr, cnt) in enumerate(zip(thirds_ranges, counts)):
            hot = cnt > expected * THIRDS_HOT_FACTOR
            thirds_info.append({
                "range": tr,
                "label": f"T{idx + 1} [{tr.start}–{tr.stop - 1}]",
                "count": cnt,
                "expected": round(expected, 1),
                "hot": hot,
            })
            if hot:
                avoid.extend(list(tr))

        result.append({"thirds": thirds_info, "avoid": avoid})
    return result


# ═══════════════════════════════════════════════════════════════════════════
# 4. Predictor Mayor / Menor por posición
# ═══════════════════════════════════════════════════════════════════════════

def predict_higher_lower(draws: list[list[int]], positions: int,
                          recent_n: int = RECENT_DRAWS_ANALYSIS) -> list[dict]:
    """
    Para cada posición compara pares consecutivos de sorteos y predice si el
    siguiente número será MAYOR, MENOR o INDETERMINADO respecto al último.

    Retorna lista de dicts por posición:
      { 'last': int, 'up_pct': float, 'down_pct': float, 'prediction': str,
        'up_count': int, 'down_count': int, 'equal_count': int }
    """
    recent = draws[-recent_n:] if len(draws) > recent_n else draws
    result = []

    for pos in range(positions):
        up = down = equal = 0
        for i in range(1, len(recent)):
            prev = recent[i - 1]
            curr = recent[i]
            if pos < len(prev) and pos < len(curr):
                if curr[pos] > prev[pos]:
                    up += 1
                elif curr[pos] < prev[pos]:
                    down += 1
                else:
                    equal += 1

        total = up + down + equal
        if total == 0:
            result.append({"last": None, "up_pct": 0.0, "down_pct": 0.0,
                           "prediction": "SIN DATOS", "up_count": 0,
                           "down_count": 0, "equal_count": 0})
            continue

        up_pct = up / total
        down_pct = down / total
        last_val = recent[-1][pos] if pos < len(recent[-1]) else None

        if up_pct >= HL_CONFIDENCE:
            pred = "MAYOR ▲"
        elif down_pct >= HL_CONFIDENCE:
            pred = "MENOR ▼"
        else:
            pred = "INDETERMINADO"

        result.append({
            "last": last_val,
            "up_pct": round(up_pct * 100, 1),
            "down_pct": round(down_pct * 100, 1),
            "prediction": pred,
            "up_count": up,
            "down_count": down,
            "equal_count": equal,
        })
    return result


# ═══════════════════════════════════════════════════════════════════════════
# 5. Puntuación combinada (frecuencia + recencia) para reducción
# ═══════════════════════════════════════════════════════════════════════════

def score_numbers(draws: list[list[int]], positions: int,
                   min_num: int, max_num: int,
                   recent_n: int = RECENT_DRAWS_ANALYSIS) -> list[dict[int, float]]:
    """
    Para cada posición devuelve {número: score} normalizado en [0,1].
    Score = 0.6 × frecuencia_relativa  +  0.4 × recencia_ponderada
    Los sorteos más recientes tienen mayor peso (decaimiento exponencial).
    """
    recent = draws[-recent_n:] if len(draws) > recent_n else draws
    n_draws = len(recent)
    scores_list = []

    for pos in range(positions):
        num_range = range(min_num, max_num + 1)
        freq: dict[int, float] = {n: 0.0 for n in num_range}
        recency: dict[int, float] = {n: 0.0 for n in num_range}
        total_weight = 0.0

        for idx, draw in enumerate(recent):
            age = n_draws - idx              # más reciente → mayor edad inversa
            weight = np.exp(0.1 * (idx - n_draws + 1))   # decae hacia atrás
            total_weight += weight
            if pos < len(draw):
                n = draw[pos]
                if min_num <= n <= max_num:
                    freq[n] += 1
                    recency[n] += weight

        # Normalizar
        max_freq = max(freq.values()) or 1
        max_rec = max(recency.values()) or 1
        combined: dict[int, float] = {}
        for n in num_range:
            f = freq[n] / max_freq
            r = recency[n] / max_rec
            combined[n] = round(0.6 * f + 0.4 * r, 6)

        scores_list.append(combined)
    return scores_list


def build_reduced_universe(scores_per_pos: list[dict[int, float]],
                            ml_scores_per_pos: list[dict[int, float]] | None,
                            min_num: int, max_num: int, positions: int,
                            target_pct: float = 0.5) -> list[list[int]]:
    """
    Combina scores estadísticos y de ML, luego selecciona los mejores números
    por posición de manera que la reducción sea ≤ target_pct del universo total.

    Estrategia:
      1. Mezcla scores: 50% estadístico + 50% ML (si disponible).
      2. Ordena números de mayor a menor score.
      3. Selecciona el mínimo de números cuya probabilidad acumulada ≥ 70%.
      4. Garantiza al menos 2 números por posición para poder generar combos.
      5. La unión de todos los números seleccionados es el universo reducido.

    Devuelve lista de listas: una por posición con los números seleccionados.
    """
    pool_size = max_num - min_num + 1
    selected_per_pos: list[list[int]] = []

    for pos in range(positions):
        stat = scores_per_pos[pos]
        ml = (ml_scores_per_pos[pos] if ml_scores_per_pos
              and pos < len(ml_scores_per_pos) else None)

        if ml:
            mixed = {n: 0.5 * stat.get(n, 0) + 0.5 * ml.get(n, 0)
                     for n in range(min_num, max_num + 1)}
        else:
            mixed = stat

        sorted_nums = sorted(mixed.items(), key=lambda x: x[1], reverse=True)
        total_score = sum(v for _, v in sorted_nums) or 1.0

        # Selección acumulativa hasta 70% de probabilidad o ≤50% del pool
        max_count = max(2, int(pool_size * target_pct))
        chosen = []
        cum = 0.0
        for n, sc in sorted_nums:
            chosen.append(n)
            cum += sc / total_score
            if cum >= 0.70 and len(chosen) >= 2:
                break
            if len(chosen) >= max_count:
                break

        selected_per_pos.append(sorted(chosen))

    return selected_per_pos


def generate_combinations(reduced_universe: list[list[int]],
                            all_draws: list[list[int]],
                            count: int,
                            positions: int,
                            min_num: int, max_num: int,
                            # ── Filtros de composición ──────────────────
                            composition: str = "mixta",
                            # "mixta" | "solo_primos" | "solo_compuestos"
                            # ── Filtros de exclusión ────────────────────
                            excl_all_consecutive: bool = True,
                            excl_all_prime: bool = True,
                            excl_all_composite: bool = False,
                            excl_repeated_historical: bool = True,
                            excl_many_consecutive: bool = True,
                            max_consecutive: int = 3,
                            ) -> list[list[int]]:
    """
    Genera hasta `count` combinaciones únicas desde el universo reducido.

    composition:
        "mixta"           — primos y compuestos mezclados (default)
        "solo_primos"     — solo números primos en la combinación
        "solo_compuestos" — solo números compuestos en la combinación

    Filtros de exclusión configurables:
        excl_all_consecutive      — excluir si TODOS son consecutivos
        excl_all_prime            — excluir si TODOS son primos
        excl_all_composite        — excluir si TODOS son compuestos
        excl_repeated_historical  — excluir si ya apareció exactamente
        excl_many_consecutive     — excluir si hay ≥ max_consecutive seguidos
    """
    from utils.math_utils import is_all_composite

    # Universo: unión de los mejores números por posición
    universe_set: set[int] = set()
    for nums in reduced_universe:
        universe_set.update(nums)
    pool = sorted(universe_set)

    # Aplicar filtro de composición al pool
    if composition == "solo_primos":
        pool = [n for n in pool if is_prime(n)]
    elif composition == "solo_compuestos":
        pool = [n for n in pool if not is_prime(n)]
    # "mixta" usa el pool completo

    historical = {tuple(sorted(d)) for d in all_draws}
    results = []
    seen = set(historical) if excl_repeated_historical else set()
    max_attempts = count * 3000

    if len(pool) < positions:
        return []

    for _ in range(max_attempts):
        if len(results) >= count:
            break
        combo = tuple(sorted(random.sample(pool, positions)))
        if excl_repeated_historical and combo in seen:
            continue
        combo_list = list(combo)

        # Filtros de exclusión
        if excl_all_consecutive and is_all_consecutive(combo_list):
            continue
        if excl_all_prime and is_all_prime(combo_list):
            continue
        if excl_all_composite and is_all_composite(combo_list):
            continue
        if excl_many_consecutive and has_many_consecutive(
                combo_list, max_consec=max_consecutive):
            continue

        seen.add(combo)
        results.append(combo_list)

    return results


# ═══════════════════════════════════════════════════════════════════════════
# 6. Historial con marcas
# ═══════════════════════════════════════════════════════════════════════════

def mark_history(draws: list[dict]) -> list[dict]:
    """
    Añade campos de marcas a cada sorteo del historial:
      - 'consecutive_positions': índices de números que son consecutivos
        con algún otro número dentro del mismo sorteo.
      - 'repeated_from_prev': índices de números que aparecieron en el sorteo anterior.
    """
    annotated = []
    prev_nums: set[int] = set()

    for draw in draws:
        nums = draw["numbers"]
        nums_set = set(nums)

        # Consecutivos internos
        consec_idx = set()
        sorted_nums = sorted(nums)
        for i, n in enumerate(sorted_nums):
            if n + 1 in nums_set or n - 1 in nums_set:
                orig_idx = [j for j, x in enumerate(nums) if x == n]
                consec_idx.update(orig_idx)

        # Repetidos del sorteo anterior
        repeated_idx = [i for i, n in enumerate(nums) if n in prev_nums]

        entry = dict(draw)
        entry["consecutive_positions"] = list(consec_idx)
        entry["repeated_from_prev"] = repeated_idx
        annotated.append(entry)
        prev_nums = nums_set

    return annotated
