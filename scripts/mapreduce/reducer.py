#!/usr/bin/env python
import sys
import json

current_coin = None
prices = []
volumes = []
timestamps = []
metrics_list = []

for line in sys.stdin:
    try:
        # Lire la ligne émise par le mapper
        coin, metric_str = line.strip().split('\t', 1)
        metric = json.loads(metric_str)
        
        # Si on change de coin, calculer les métriques du coin précédent
        if current_coin and current_coin != coin:
            min_price = min(prices)
            max_price = max(prices)
            avg_price = sum(prices) / len(prices)
            total_volume = sum(volumes)
            
            sorted_timestamps = sorted(timestamps)
            first_close = next(m['close_price'] for m in metrics_list if m['timestamp'] == sorted_timestamps[0])
            last_close = next(m['close_price'] for m in metrics_list if m['timestamp'] == sorted_timestamps[-1])
            daily_variation = ((last_close - first_close) / first_close) * 100 if first_close != 0 else 0
            
            result = {
                'coin': current_coin,
                'min_price': min_price,
                'max_price': max_price,
                'avg_price': avg_price,
                'total_volume': total_volume,
                'daily_variation_percent': daily_variation
            }
            print(json.dumps(result))
            
            # Réinitialiser pour le nouveau coin
            prices = []
            volumes = []
            timestamps = []
            metrics_list = []
        
        # Ajouter les métriques au coin courant
        current_coin = coin
        prices.extend([metric['high_price'], metric['low_price'], metric['close_price']])
        volumes.append(metric['volume'])
        timestamps.append(metric['timestamp'])
        metrics_list.append(metric)
        
    except (ValueError, json.JSONDecodeError, KeyError):
        continue

# Traiter le dernier coin
if current_coin:
    min_price = min(prices)
    max_price = max(prices)
    avg_price = sum(prices) / len(prices)
    total_volume = sum(volumes)
    
    sorted_timestamps = sorted(timestamps)
    first_close = next(m['close_price'] for m in metrics_list if m['timestamp'] == sorted_timestamps[0])
    last_close = next(m['close_price'] for m in metrics_list if m['timestamp'] == sorted_timestamps[-1])
    daily_variation = ((last_close - first_close) / first_close) * 100 if first_close != 0 else 0
    
    result = {
        'coin': current_coin,
        'min_price': min_price,
        'max_price': max_price,
        'avg_price': avg_price,
        'total_volume': total_volume,
        'daily_variation_percent': daily_variation
    }
    print(json.dumps(result))