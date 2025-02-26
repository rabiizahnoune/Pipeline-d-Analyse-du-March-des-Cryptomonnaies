#!/usr/bin/env python
import sys
import json

for line in sys.stdin:
    sys.stderr.write("DEBUG: Received line: %s\n" % line.strip())
    try:
        record = json.loads(line.strip())
        sys.stderr.write("DEBUG: Parsed record: %s\n" % json.dumps(record))
        
        required_fields = ['datetime', 'open_price', 'high_price', 'low_price', 
                          'close_price', 'volume', 'coin']
        if not all(field in record and record[field] is not None for field in required_fields):
            sys.stderr.write("DEBUG: Missing or null field in record: %s\n" % json.dumps(record))
            continue
        
        coin = record['coin']
        metrics = {
            'open_price': float(record['open_price']),
            'high_price': float(record['high_price']),
            'low_price': float(record['low_price']),
            'close_price': float(record['close_price']),
            'volume': float(record['volume']),
            'timestamp': record['datetime']
        }
        output = "%s\t%s" % (coin, json.dumps(metrics))
        print(output)
        sys.stderr.write("DEBUG: Emitted: %s\n" % output)
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        sys.stderr.write("DEBUG: Error parsing line: %s - %s\n" % (line.strip(), str(e)))
        continue