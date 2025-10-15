#!/bin/bash
# Test script to verify Docker Compose detection

echo "=== Docker Compose Detection Test ==="
echo ""

# Test 1: Check what's available
echo "Test 1: Available commands"
echo "--------------------------"
if command -v docker-compose >/dev/null 2>&1; then
    echo "✓ docker-compose found"
    docker-compose --version
else
    echo "✗ docker-compose not found"
fi

echo ""

if docker compose version >/dev/null 2>&1; then
    echo "✓ docker compose available"
    docker compose version
else
    echo "✗ docker compose not available"
fi

echo ""
echo ""

# Test 2: Makefile detection
echo "Test 2: Makefile detection logic"
echo "---------------------------------"
if docker compose version > /dev/null 2>&1; then
    DETECTED="docker compose"
else
    DETECTED="docker-compose"
fi
echo "Makefile would detect: $DETECTED"

echo ""
echo ""

# Test 3: With environment variable
echo "Test 3: Environment variable override"
echo "--------------------------------------"
export DOCKER_COMPOSE="docker-compose"
echo "DOCKER_COMPOSE=$DOCKER_COMPOSE"

if [ -n "$DOCKER_COMPOSE" ]; then
    echo "Would use: $DOCKER_COMPOSE"
else
    echo "Would auto-detect"
fi

echo ""
echo ""

# Test 4: Actual command test
echo "Test 4: Test actual commands"
echo "-----------------------------"

if command -v docker-compose >/dev/null 2>&1; then
    echo "Testing: docker-compose ps"
    if docker-compose ps >/dev/null 2>&1; then
        echo "✓ docker-compose ps works"
    else
        echo "✗ docker-compose ps failed (maybe no docker-compose.yml?)"
    fi
fi

echo ""

if docker compose version >/dev/null 2>&1; then
    echo "Testing: docker compose ps"
    if docker compose ps >/dev/null 2>&1; then
        echo "✓ docker compose ps works"
    else
        echo "✗ docker compose ps failed (maybe no compose.yml?)"
    fi
fi

echo ""
echo ""

# Test 5: Recommended command
echo "Test 5: Recommendation"
echo "----------------------"
if command -v docker-compose >/dev/null 2>&1; then
    echo "✓ Use: docker-compose"
    echo "  In Makefile: DOCKER_COMPOSE := docker-compose"
    echo "  Or set: export DOCKER_COMPOSE=docker-compose"
elif docker compose version >/dev/null 2>&1; then
    echo "✓ Use: docker compose"
    echo "  In Makefile: DOCKER_COMPOSE := docker compose"  
    echo "  Or set: export DOCKER_COMPOSE='docker compose'"
else
    echo "✗ No Docker Compose found - install it first"
fi
