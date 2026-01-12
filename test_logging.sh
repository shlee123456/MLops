#!/bin/bash
# Test logging integration

echo "======================================"
echo "  Testing Logging System"
echo "======================================"
echo

# Check if venv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Create logs directory
echo "Creating logs directory..."
mkdir -p logs/{training,inference,system,mlflow,vllm,fastapi}

# Test 1: Example training with logging
echo
echo "Test 1: Running example training with logging..."
echo "--------------------------------------"
python src/train/train_with_logging_example.py

# Check if logs were created
echo
echo "Checking generated logs..."
echo "--------------------------------------"

if [ -d "logs/training" ] && [ "$(ls -A logs/training)" ]; then
    echo "✓ Training logs found:"
    ls -lh logs/training/*.log | tail -3
else
    echo "✗ No training logs found"
fi

if [ -d "logs/system" ] && [ "$(ls -A logs/system)" ]; then
    echo "✓ System logs found:"
    ls -lh logs/system/*.log | tail -3
else
    echo "✗ No system logs found"
fi

# Test 2: View log content
echo
echo "Test 2: Sample log content (JSON format)..."
echo "--------------------------------------"

if [ -f "$(ls -t logs/training/*.log | head -1)" ]; then
    echo "Training log sample:"
    cat "$(ls -t logs/training/*.log | head -1)" | head -3 | jq . 2>/dev/null || cat "$(ls -t logs/training/*.log | head -1)" | head -3
fi

echo
echo "======================================"
echo "  Testing Complete!"
echo "======================================"
echo
echo "Next steps:"
echo "  1. Start Docker services: docker-compose up -d"
echo "  2. Open Grafana: http://localhost:3000"
echo "  3. Go to Explore > Loki"
echo "  4. Query: {job=\"training\"}"
echo
echo "To run actual training with logging:"
echo "  python src/train/02_qlora_finetune.py"
echo
