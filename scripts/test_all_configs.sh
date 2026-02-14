#!/bin/bash
echo "Testing all scoring configs..."
for config in baseline pain_boost business aggressive balanced; do
    echo "Testing: $config"
    python backtest.py --days 7 --config ../scoring_config_${config}.json --output test_${config}.json 2>&1 | grep -E "Average Score|High Quality|Top Tier"
    echo "---"
done
