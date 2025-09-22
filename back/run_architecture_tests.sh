#!/bin/bash

# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

# Architecture Testing Suite Runner
# This script runs all architecture tests and generates a comprehensive report

echo "🏗️ Running Architecture Testing Suite for The Open Music Box"
echo "============================================================"

# Run individual test suites
echo ""
echo "📋 Running Domain Purity Tests..."
python -m pytest tests/architecture/test_domain_purity.py -v --tb=short

echo ""
echo "🔄 Running Dependency Direction Tests..."
python -m pytest tests/architecture/test_dependency_direction.py -v --tb=short

echo ""
echo "🔗 Running Circular Dependencies Tests..."
python -m pytest tests/architecture/test_circular_dependencies.py -v --tb=short

echo ""
echo "📍 Running Class Placement Tests..."
python -m pytest tests/architecture/test_class_placement.py -v --tb=short

echo ""
echo "📝 Running Naming Convention Tests..."
python -m pytest tests/architecture/test_naming_conventions.py -v --tb=short

echo ""
echo "📊 Generating Comprehensive Report..."
python -m tests.architecture.test_runner

echo ""
echo "✅ Architecture Testing Suite Complete!"
echo "📄 Check ARCHITECTURE_TEST_REPORT.md for detailed results"
echo ""
echo "🎯 To achieve 10/10 architecture score:"
echo "   1. Fix Domain layer violations"
echo "   2. Move misplaced classes to correct layers"
echo "   3. Improve naming conventions"
echo ""
echo "Run this script regularly to maintain architectural quality! 🚀"