"""
Motor de análisis estadístico y heurístico para el análisis de combinaciones.
"""
from __future__ import annotations
import random
from collections import defaultdict
import numpy as np
from config import (RECENT_DRAWS_ANALYSIS, REDUCTION_TARGET_PCT, MIN_SIMILAR_MATCHES)
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
# 3. Ley del Tercio — números repetidos por posición
# ═══════════════════════════════════════════════════════════════════════════

def _thirds_window(min_num: int, max_num: int) -> int:
    """Devuelve cuántos sorteos recientes revisar según el universo de la lotería."""
    universe = max_num - min_num + 1
    if universe <= 5:
        return 2
    if universe <= 10:
        return 3
    if universe <= 30:
        return 6
    if universe <= 40:
        return 7
    if universe <= 60:
        return 8
    if universe <= 80:
        return 10
    return 12  # 80-100+


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
                   recent_n: int | None = None,
                   ranges: list[tuple[int, int]] | None = None) -> list[dict]:
    """
    Para cada posición, identifica los números que han aparecido 2 o más
    veces en esa misma posición en los últimos N sorteos.

    La ventana N depende del universo de la lotería (max - min + 1):
      - ≤5     → 2 sorteos
      - ≤10    → 3 sorteos
      - ≤30    → 6 sorteos
      - ≤40    → 7 sorteos
      - ≤60    → 8 sorteos
      - ≤80    → 10 sorteos
      - ≤100   → 12 sorteos

    Estos números repetidos son los que se deben EVITAR.

    Si se proporciona ``ranges`` (lista de (min, max) por posición), cada
    posición usa su propio rango para calcular la ventana.

    Retorna una lista (por posición) con:
      { 'window': int, 'avoid': [números repetidos ≥2 veces] }
    """
    # Ventana por defecto usando el rango principal
    default_window = recent_n if recent_n is not None else _thirds_window(min_num, max_num)

    result = []
    for pos in range(positions):
        # Cada posición puede tener su propia ventana si tiene rango distinto
        if ranges and pos < len(ranges):
            pos_min, pos_max = ranges[pos]
            window = recent_n if recent_n is not None else _thirds_window(pos_min, pos_max)
        else:
            window = default_window
        recent = draws[-window:] if len(draws) > window else draws
        freq: dict[int, int] = {}
        for draw in recent:
            if pos < len(draw):
                n = draw[pos]
                freq[n] = freq.get(n, 0) + 1

        # Números que aparecen 2+ veces en esta posición → evitar
        avoid = sorted(n for n, cnt in freq.items() if cnt >= 2)
        result.append({"window": window, "avoid": avoid})
    return result


# ═══════════════════════════════════════════════════════════════════════════
# 4. Predictor Mayor / Menor por posición
# ═══════════════════════════════════════════════════════════════════════════

def predict_higher_lower(draws: list[list[int]], positions: int,
                          recent_n: int = RECENT_DRAWS_ANALYSIS,
                          min_num: int | None = None,
                          max_num: int | None = None,
                          ranges: list[tuple[int, int]] | None = None) -> list[dict]:
    """
    Para cada posición predice si el siguiente número será MAYOR o MENOR
    usando el método de **Equilibrio de Números Posicional**: comparación
    del último valor con el valor esperado de esa posición (estadístico
    de orden), NO con el punto medio global del rango.

    Cada posición k (1-indexada) en una lotería ordenada de N balotas
    extraídas de [min, max] tiene un valor esperado:
        E[X_(k)] = min + (max - min) * k / (N + 1)

      - Último < E[X_(k)]  →  MAYOR ▲  (tiende a subir hacia su centro)
      - Último > E[X_(k)]  →  MENOR ▼  (tiende a bajar hacia su centro)

    Adicionalmente calcula estadísticas de transiciones (subidas/bajadas)
    como información complementaria.

    Si se proporciona ``ranges`` (lista de (min, max) por posición), cada
    posición usa su propio rango en lugar de ``min_num``/``max_num``.  Esto
    es fundamental para loterías con balotas adicionales cuyo universo es
    más pequeño (ej. Euromillones: 5 principales 1-50 + 2 estrellas 1-12).

    Retorna lista de dicts por posición:
      { 'last': int, 'up_pct': float, 'down_pct': float, 'prediction': str,
        'up_count': int, 'down_count': int, 'equal_count': int,
        '_strength': float }
    """
    recent = draws[-recent_n:] if len(draws) > recent_n else draws

    # ── Detectar si la lotería es de posiciones independientes ───────────
    # La fórmula de estadístico de orden sólo es válida para loterías
    # ordenadas (balotas extraídas SIN reposición y ordenadas de menor a
    # mayor dentro del mismo sorteo).  Si los sorteos no están ordenados
    # internamente, o si hay números repetidos dentro de un mismo sorteo,
    # se trata de una lotería de dígitos independientes → usar punto medio
    # simple (min+max)/2 para todas las posiciones.
    sample = recent[:min(30, len(recent))]
    _has_repeats    = any(len(set(d)) < len(d) for d in sample)
    _is_sorted_draws = all(d == sorted(d) for d in sample) if sample else True
    _use_simple_midpoint = _has_repeats or not _is_sorted_draws

    result = []
    for pos in range(positions):
        # ── Rango para esta posición ─────────────────────────────────
        if ranges and pos < len(ranges):
            pos_min, pos_max = ranges[pos]
        else:
            pos_min = min_num
            pos_max = max_num

        # ── Punto medio posicional ───────────────────────────────────
        # Para posiciones con rango propio (adicionales) se usa el punto
        # medio global de su rango.  Para posiciones principales en
        # universos grandes se usa el estadístico de orden, EXCEPTO cuando
        # se detecta que la lotería es de posiciones independientes.
        midpoint = None
        if pos_min is not None and pos_max is not None:
            universe = pos_max - pos_min + 1
            if universe <= 5 or _use_simple_midpoint:
                # Loterías con universo pequeño o de dígitos independientes:
                # punto medio simple igual para todas las posiciones.
                midpoint = (pos_min + pos_max) / 2
            else:
                # Lotería ordenada (balotas sin reposición, ordenadas):
                # usar estadístico de orden posicional.
                if ranges and pos < len(ranges):
                    same_range = [i for i in range(len(ranges)) if ranges[i] == (pos_min, pos_max)]
                    rank_in_group = same_range.index(pos) + 1
                    group_size = len(same_range)
                else:
                    rank_in_group = pos + 1
                    group_size = positions
                midpoint = pos_min + (pos_max - pos_min) * rank_in_group / (group_size + 1)

        # ── Estadísticas de transiciones (informativas) ──────────────
        raw_up = raw_down = raw_equal = 0
        for i in range(1, len(recent)):
            prev = recent[i - 1]
            curr = recent[i]
            if pos < len(prev) and pos < len(curr):
                if curr[pos] > prev[pos]:
                    raw_up += 1
                elif curr[pos] < prev[pos]:
                    raw_down += 1
                else:
                    raw_equal += 1

        total_raw = raw_up + raw_down + raw_equal
        last_val = recent[-1][pos] if (recent and pos < len(recent[-1])) else None
        up_pct = (raw_up / total_raw) if total_raw else 0.0
        down_pct = (raw_down / total_raw) if total_raw else 0.0

        # ── Predicción por Equilibrio Posicional ────────────────────
        # Compara el último valor contra el valor esperado de esta
        # posición específica (no el punto medio global).
        if midpoint is not None and last_val is not None:
            if last_val < midpoint:
                pred = "MAYOR ▲"
                strength = (midpoint - last_val) / (midpoint - pos_min) if midpoint > pos_min else 0.0
            elif last_val > midpoint:
                pred = "MENOR ▼"
                strength = (last_val - midpoint) / (pos_max - midpoint) if pos_max > midpoint else 0.0
            else:
                # Exactamente en el punto medio → usar transiciones como desempate
                if raw_up > raw_down:
                    pred = "MAYOR ▲"
                elif raw_down > raw_up:
                    pred = "MENOR ▼"
                else:
                    pred = "INDETERMINADO"
                strength = 0.0
        elif total_raw > 0:
            # Fallback sin rango: usar transiciones
            if raw_up > raw_down:
                pred = "MAYOR ▲"
                strength = (raw_up - raw_down) / total_raw
            elif raw_down > raw_up:
                pred = "MENOR ▼"
                strength = (raw_down - raw_up) / total_raw
            else:
                pred = "INDETERMINADO"
                strength = 0.0
        else:
            pred = "SIN DATOS"
            strength = 0.0

        result.append({
            "last": last_val,
            "up_pct": round(up_pct * 100, 1),
            "down_pct": round(down_pct * 100, 1),
            "prediction": pred,
            "up_count": raw_up,
            "down_count": raw_down,
            "equal_count": raw_equal,
            "_strength": round(strength, 4),
        })

    return result


def numbers_to_avoid(hl_data: list[dict], min_num: int, max_num: int) -> list[list[int]]:
    """
    Genera los números a evitar por posición basándose en la dirección esperada.

    Lógica simple:
      - Si dirección = MAYOR → evitar todos los números ≤ último (se espera uno más alto)
      - Si dirección = MENOR → evitar todos los números ≥ último (se espera uno más bajo)
      - Si INDETERMINADO/SIN DATOS → lista vacía
    """
    result = []
    for data in hl_data:
        last = data.get("last")
        pred = data.get("prediction", "")
        if last is None:
            result.append([])
            continue

        if "MAYOR" in pred:
            result.append(list(range(min_num, last + 1)))
        elif "MENOR" in pred:
            result.append(list(range(last, max_num + 1)))
        else:
            result.append([])
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
                            target_pct: float = REDUCTION_TARGET_PCT) -> list[list[int]]:
    """
    Combina scores estadísticos y de ML, luego selecciona los mejores números
    por posición garantizando una reducción ≥ target_pct del universo total.

    Estrategia:
      1. Mezcla scores: 50% estadístico + 50% ML (si disponible).
      2. Ordena números de mayor a menor score.
      3. Selecciona números en orden hasta cubrir al menos el 50% del pool
         Y alcanzar el 70% de probabilidad acumulada (ambas condiciones).
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

        # Selección acumulativa: mínimo 50% del pool, máximo 100%
        min_count = max(2, int(pool_size * target_pct))
        chosen = []
        chosen_set: set[int] = set()
        cum = 0.0
        for n, sc in sorted_nums:
            chosen.append(n)
            chosen_set.add(n)
            cum += sc / total_score
            # Sólo detener si ya se alcanzó la reducción mínima del 50%
            if len(chosen) >= min_count and cum >= 0.70:
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
        # Universo menor que posiciones → se permiten repetidos
        allow_repeats = True
    else:
        allow_repeats = False

    for _ in range(max_attempts):
        if len(results) >= count:
            break
        if allow_repeats:
            combo = tuple(sorted(random.choices(pool, k=positions)))
        else:
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
