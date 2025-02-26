#!/usr/bin/env python3
import sys
import json

THRESHOLD = 100e9  # 100 milliards

for line in sys.stdin:
    try:
        crypto = json.loads(line.strip())  # Charger chaque ligne JSON
        market_cap = crypto.get("market_cap", 0)
        if market_cap > THRESHOLD:
            print(f"high_market_cap\t1")  # Émettre clé-valeur
    except:
        continue  # Ignorer les erreurs
