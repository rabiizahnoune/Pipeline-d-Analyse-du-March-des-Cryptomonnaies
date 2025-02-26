#!/usr/bin/env python3
import sys

count = 0

for line in sys.stdin:
    key, value = line.strip().split("\t")
    count += int(value)

print(f"Total_high_market_cap\t{count}")
