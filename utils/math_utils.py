"""
Utilidades matemáticas para el análisis de combinaciones de lotería.
Nota: el número 1 se trata como PRIMO según el requerimiento del sistema.
"""
from math import comb, isqrt


# ─────────────────────────── Primos ────────────────────────────────────────

def is_prime(n: int) -> bool:
    """
    Devuelve True si n es primo.
    REGLA ESPECIAL: el 1 se considera primo en este sistema.
    """
    if n < 1:
        return False
    if n == 1:
        return True          # regla especial
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, isqrt(n) + 1, 2):
        if n % i == 0:
            return False
    return True


def classify_numbers(numbers: list[int]) -> dict[int, str]:
    """
    Devuelve un dict {número: 'prime' | 'composite'} para cada número de la lista.
    """
    return {n: ("prime" if is_prime(n) else "composite") for n in numbers}


def get_primes_in_range(min_num: int, max_num: int) -> list[int]:
    """Lista de primos en [min_num, max_num] (incluye el 1 como primo)."""
    return [n for n in range(min_num, max_num + 1) if is_prime(n)]


def get_composites_in_range(min_num: int, max_num: int) -> list[int]:
    """Lista de compuestos en [min_num, max_num]."""
    return [n for n in range(min_num, max_num + 1) if not is_prime(n)]


# ─────────────────────────── Combinaciones ─────────────────────────────────

def total_combinations(max_num: int, positions: int, min_num: int = 1) -> int:
    """
    C(pool_size, k) — combinaciones sin repetición y sin orden.
    pool_size = max_num - min_num + 1, k = positions.
    """
    pool = max_num - min_num + 1
    if pool < positions:
        return 0
    return comb(pool, positions)


def prime_only_combinations(min_num: int, max_num: int, positions: int) -> int:
    """C(cantidad_primos, k) — sólo usando números primos."""
    primes = get_primes_in_range(min_num, max_num)
    p = len(primes)
    if p < positions:
        return 0
    return comb(p, positions)


def composite_only_combinations(min_num: int, max_num: int, positions: int) -> int:
    """C(cantidad_compuestos, k) — sólo usando compuestos."""
    comps = get_composites_in_range(min_num, max_num)
    c = len(comps)
    if c < positions:
        return 0
    return comb(c, positions)


def mixed_combinations(min_num: int, max_num: int, positions: int) -> int:
    """Combinaciones mixtas (al menos un primo Y un compuesto)."""
    total = total_combinations(max_num, positions, min_num)
    po = prime_only_combinations(min_num, max_num, positions)
    co = composite_only_combinations(min_num, max_num, positions)
    return max(0, total - po - co)


def format_large_number(n: int) -> str:
    """Formatea un entero grande con separadores de miles."""
    return f"{n:,}"


# ─────────────────────────── Validación ────────────────────────────────────

def is_all_consecutive(numbers: list[int]) -> bool:
    """True si todos los números forman una secuencia consecutiva."""
    if len(numbers) < 2:
        return False
    s = sorted(numbers)
    return all(s[i + 1] - s[i] == 1 for i in range(len(s) - 1))


def is_all_prime(numbers: list[int]) -> bool:
    """True si todos los números son primos (incl. 1)."""
    return all(is_prime(n) for n in numbers)


def is_all_composite(numbers: list[int]) -> bool:
    """True si todos los números son compuestos."""
    return all(not is_prime(n) for n in numbers)


def has_many_consecutive(numbers: list[int], max_consec: int = 4) -> bool:
    """True si hay max_consec o más números consecutivos en la combinación."""
    s = sorted(numbers)
    count = 1
    for i in range(1, len(s)):
        if s[i] - s[i - 1] == 1:
            count += 1
            if count >= max_consec:
                return True
        else:
            count = 1
    return False
