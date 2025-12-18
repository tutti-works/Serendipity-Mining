import argparse
import collections
import json
import pathlib


def load_items(plan_path: pathlib.Path):
    if not plan_path.exists():
        raise FileNotFoundError(f"Plan not found: {plan_path}")
    for line in plan_path.read_text().splitlines():
        if not line.strip():
            continue
        yield json.loads(line)


def summarize(plan_path: pathlib.Path, top_n: int):
    axis_counts = collections.Counter()
    tag_counts = collections.defaultdict(collections.Counter)
    token_counts = collections.Counter()

    for item in load_items(plan_path):
        axis_counts[item.get("axis_id", "unknown")] += 1
        slots = item.get("slots") or {}
        token_counts.update(slots.values())
        for cat, tag in (item.get("slot_tags") or {}).items():
            tag_counts[cat][tag] += 1

    print(f"[PATH] {plan_path}")
    print(f"[TOTAL] items={sum(axis_counts.values())}")
    print("[AXIS]")
    for axis, cnt in axis_counts.most_common():
        print(f"  {axis}: {cnt}")

    if tag_counts:
        print("[TAG COUNTS]")
        for cat, counter in tag_counts.items():
            total = sum(counter.values())
            uniques = len(counter)
            top = counter.most_common(top_n)
            top_str = ", ".join(f"{k}:{v}" for k, v in top)
            print(f"  {cat}: total={total}, uniq={uniques}, top{top_n}=[{top_str}]")
    else:
        print("[TAG COUNTS] none (slot_tags not present; tag_sampling=off?)")

    if token_counts:
        print("[TOKENS top{0}]".format(top_n))
        for token, cnt in token_counts.most_common(top_n):
            print(f"  {token}: {cnt}")


def main():
    parser = argparse.ArgumentParser(description="Plan bias checker (axis / tag / token distribution)")
    parser.add_argument("plan", type=pathlib.Path, help="Path to plan jsonl (e.g., out/4cats/explore.jsonl)")
    parser.add_argument("--top", type=int, default=10, help="Top-N to display")
    args = parser.parse_args()
    summarize(args.plan, args.top)


if __name__ == "__main__":
    main()
