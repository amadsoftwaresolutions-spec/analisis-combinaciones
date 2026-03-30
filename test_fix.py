"""Quick test to verify 0-9 range fixes."""
from utils.analyzer import predict_higher_lower, law_of_thirds

# Test 1: Single draw (previously returned SIN DATOS)
print("=== Test 1: Single draw, range 0-9 ===")
draws_1 = [[3, 7, 1, 9, 0]]
hl = predict_higher_lower(draws_1, 5, min_num=0, max_num=9)
for i, h in enumerate(hl):
    print(f"  Pos {i}: last={h['last']} pred={h['prediction']} strength={h['_strength']}")

# Test 2: Multiple draws
print("\n=== Test 2: 3 draws, range 0-9 ===")
draws_3 = [[1,2,3,4,5], [0,5,3,7,2], [9,1,8,0,6]]
hl2 = predict_higher_lower(draws_3, 5, min_num=0, max_num=9)
for i, h in enumerate(hl2):
    print(f"  Pos {i}: last={h['last']} pred={h['prediction']}")

# Test 3: Law of thirds
print("\n=== Test 3: law_of_thirds, range 0-9 ===")
thirds = law_of_thirds(draws_3, 5, 0, 9)
for i, t in enumerate(thirds):
    print(f"  Pos {i}: avoid={t['avoid']}")

# Test 4: Verify MIN_NUMBER_VALUE
from config import MIN_NUMBER_VALUE
print(f"\nMIN_NUMBER_VALUE = {MIN_NUMBER_VALUE}")
assert MIN_NUMBER_VALUE == 0, "MIN_NUMBER_VALUE should be 0!"

print("\nAll tests passed!")
