import random
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm  # 用于显示进度条

# 单次模拟：直到收集到 {2, 3, 4}
def simulate_once():
    seen = set()
    count = 0
    while len(seen) < 3:
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        s = d1 + d2
        if s in {2, 3, 4}:
            seen.add(s)
        count += 1
    return count

# 批量模拟函数（供线程使用）
def simulate_batch(n):
    return [simulate_once() for _ in range(n)]

# 主函数
def run_simulation(total_trials=100000, workers=4):
    trials_per_worker = total_trials // workers
    results = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(simulate_batch, trials_per_worker) for _ in range(workers)]
        for future in tqdm(futures, desc="Simulating"):
            results.extend(future.result())

    average = sum(results) / len(results)
    print(f"\n✅ 模拟 {total_trials:,} 次后的期望掷骰次数：{average:.5f}")

if __name__ == "__main__":
    run_simulation(total_trials=500000, workers=4)
