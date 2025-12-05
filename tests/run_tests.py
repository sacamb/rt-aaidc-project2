#!/usr/bin/env python3
"""Test runner script for Destination Compass."""

import sys
import subprocess
import os

def run_tests():
    """Run all tests."""
    print("Running Destination Compass Test Suite")
    print("=" * 50)
    
    # Add src to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))
    
    # Run pytest
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=os.path.dirname(os.path.dirname(__file__))
    )
    
    return result.returncode


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
