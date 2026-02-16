
#!/bin/bash

set -e

echo "========================================"
echo "  Running DragonAI Tests"
echo "========================================"
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run unit tests
echo ""
echo "Running unit tests..."
echo ""
pytest tests/unit/ -v --cov=app --cov-report=term-missing

echo ""
echo "========================================"
echo "  Unit tests completed!"
echo "========================================"
echo ""

# Run integration tests
echo ""
echo "Running integration tests..."
echo ""
pytest tests/integration/ -v

echo ""
echo "========================================"
echo "  All tests completed!"
echo "========================================"
echo ""

