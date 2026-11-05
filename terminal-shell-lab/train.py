"""Train logistic regression on real lesson metadata, without dependencies.

Reference: phases/00-setup-and-tooling/10-terminal-and-shell/docs/en.md.
Predicts the existing Build label from document size/structure features.
Finite runs, real loss/accuracy, train-only normalization and held-out data.
"""

import argparse
import csv
import json
import math
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parent


def sigmoid(value):
    if value >= 0:
        return 1 / (1 + math.exp(-value))
    exp = math.exp(value)
    return exp / (1 + exp)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--lr", type=float, default=0.1)
    parser.add_argument("--delay", type=float, default=0.2)
    parser.add_argument("--model", default="models/latest.json")
    args = parser.parse_args()
    if (args.epochs < 1 or not math.isfinite(args.lr) or args.lr <= 0
            or not math.isfinite(args.delay) or args.delay < 0):
        parser.error("epochs >= 1, finite lr > 0 and finite delay >= 0 required")
    with (ROOT / "data/lessons.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    random.Random(42).shuffle(rows)
    split = int(len(rows) * 0.8)
    if split < 2 or split == len(rows):
        parser.error("Run prepare.py first: dataset too small")
    keys = ("words", "code_blocks", "headings")
    means = [sum(float(row[k]) for row in rows[:split]) / split for k in keys]
    scales = [max((sum((float(row[k]) - mean) ** 2 for row in rows[:split])
                   / split) ** 0.5, 1) for k, mean in zip(keys, means)]
    data = [([1.0] + [(float(row[k]) - mean) / scale
                     for k, mean, scale in zip(keys, means, scales)], int(row["is_build"]))
            for row in rows]
    train, test = data[:split], data[split:]
    weights = [0.0] * 4
    print(f"INFO train={len(train)} held_out={len(test)} seed=42", file=sys.stderr, flush=True)
    for epoch in range(1, args.epochs + 1):
        gradient = [0.0] * 4
        for features, label in train:
            error = sigmoid(sum(w * x for w, x in zip(weights, features))) - label
            for index, feature in enumerate(features):
                gradient[index] += error * feature
        weights = [w - args.lr * g / len(train) for w, g in zip(weights, gradient)]
        loss = 0.0
        for features, label in train:
            z = sum(w * x for w, x in zip(weights, features))
            loss += max(z, 0) - z * label + math.log1p(math.exp(-abs(z)))
        correct = sum((sigmoid(sum(w * x for w, x in zip(weights, f))) >= 0.5) == y
                      for f, y in test)
        accuracy = correct / len(test)
        print(f"epoch {epoch} accuracy: {accuracy:.6f} loss: {loss / len(train):.6f}", flush=True)
        time.sleep(args.delay)
    model = {"features": keys, "means": means, "scales": scales, "weights": weights,
             "seed": 42, "epochs": args.epochs, "lr": args.lr,
             "held_out_accuracy": accuracy, "train_rows": len(train), "test_rows": len(test)}
    destination = Path(args.model)
    if not destination.is_absolute():
        destination = ROOT / destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(model, indent=2) + "\n")
    print(f"final_accuracy={accuracy:.6f}", flush=True)


if __name__ == "__main__":
    main()
