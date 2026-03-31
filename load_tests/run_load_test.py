"""
TechCorp Customer Success AI Agent - Load Test Runner

Runs load tests using Locust in headless mode.

Usage:
    python load_tests/run_load_test.py [light|medium|heavy|endurance]
    
Configurations:
    light     - 10 users, 30 seconds (quick verify)
    medium    - 50 users, 60 seconds (normal load)
    heavy     - 100 users, 120 seconds (stress test)
    endurance - 20 users, 86400 seconds (24 hour)
"""

import subprocess
import sys
import time
import os
from pathlib import Path
from datetime import datetime


# ============================================================================
# TEST CONFIGURATIONS
# ============================================================================

CONFIGURATIONS = {
    "light": {
        "users": 10,
        "spawn_rate": 2,
        "duration": 30,
        "description": "Quick verify test"
    },
    "medium": {
        "users": 50,
        "spawn_rate": 5,
        "duration": 60,
        "description": "Normal load test"
    },
    "heavy": {
        "users": 100,
        "spawn_rate": 10,
        "duration": 120,
        "description": "Stress test"
    },
    "endurance": {
        "users": 20,
        "spawn_rate": 2,
        "duration": 86400,
        "description": "24 hour endurance test"
    }
}


# ============================================================================
# LOAD TEST RUNNER
# ============================================================================

def run_load_test(config_name: str = "light", host: str = "http://localhost:8000"):
    """
    Run a load test with the specified configuration.
    
    Args:
        config_name: Configuration name (light/medium/heavy/endurance).
        host: Target host URL.
        
    Returns:
        True if test completed successfully.
    """
    if config_name not in CONFIGURATIONS:
        print(f"Error: Unknown configuration '{config_name}'")
        print(f"Valid options: {list(CONFIGURATIONS.keys())}")
        return False
    
    config = CONFIGURATIONS[config_name]
    
    # Create results directory
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    
    # Generate output file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = results_dir / f"load_test_{config_name}_{timestamp}.txt"
    
    print("=" * 70)
    print("TechCorp Customer Success FTE - Load Test")
    print("=" * 70)
    print(f"Configuration: {config_name.upper()}")
    print(f"Description: {config['description']}")
    print(f"Users: {config['users']}")
    print(f"Spawn Rate: {config['spawn_rate']} users/sec")
    print(f"Duration: {config['duration']} seconds")
    print(f"Target: {host}")
    print(f"Output: {output_file}")
    print("=" * 70)
    print("")
    print("Starting load test...")
    print("")
    
    # Build locust command
    cmd = [
        sys.executable, "-m", "locust",
        "-f", str(Path(__file__).parent / "locustfile.py"),
        "--host", host,
        "--users", str(config["users"]),
        "--spawn-rate", str(config["spawn_rate"]),
        "--run-time", str(config["duration"]),
        "--headless",
        "--only-summary"
    ]
    
    # Run locust
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=config["duration"] + 60
        )
        
        # Save output
        output = result.stdout + result.stderr
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Configuration: {config_name}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Host: {host}\n")
            f.write("=" * 70 + "\n\n")
            f.write(output)
        
        # Print summary
        print("")
        print("=" * 70)
        print("LOAD TEST COMPLETE")
        print("=" * 70)
        print(f"Results saved to: {output_file}")
        print("")
        
        # Parse and display key metrics
        if "Aggregated" in output:
            print("Key Metrics:")
            for line in output.split('\n'):
                if 'Aggregated' in line or 'RPS' in line or 'failures' in line.lower():
                    print(f"  {line.strip()}")
        
        print("=" * 70)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"Error: Test timed out after {config['duration'] + 60} seconds")
        return False
    except Exception as e:
        print(f"Error running load test: {e}")
        return False


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point."""
    # Get configuration from command line
    config_name = sys.argv[1] if len(sys.argv) > 1 else "light"
    host = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"
    
    success = run_load_test(config_name, host)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
