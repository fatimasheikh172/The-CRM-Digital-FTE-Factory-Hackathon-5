"""
TechCorp Customer Success AI Agent - Performance Benchmarks

Defines expected performance targets for load testing.
"""


# ============================================================================
# PERFORMANCE BENCHMARKS
# ============================================================================

BENCHMARKS = {
    "web_form": {
        "p50_response_ms": 500,
        "p95_response_ms": 3000,
        "p99_response_ms": 5000,
        "error_rate": 0.01,
        "min_rps": 10
    },
    "email_webhook": {
        "p50_response_ms": 300,
        "p95_response_ms": 2000,
        "p99_response_ms": 4000,
        "error_rate": 0.01,
        "min_rps": 5
    },
    "whatsapp_webhook": {
        "p50_response_ms": 300,
        "p95_response_ms": 2000,
        "p99_response_ms": 4000,
        "error_rate": 0.01,
        "min_rps": 5
    },
    "health_check": {
        "p50_response_ms": 50,
        "p95_response_ms": 100,
        "p99_response_ms": 200,
        "error_rate": 0.0,
        "min_rps": 50
    },
    "metrics": {
        "p50_response_ms": 200,
        "p95_response_ms": 1000,
        "p99_response_ms": 2000,
        "error_rate": 0.01,
        "min_rps": 10
    }
}


# ============================================================================
# BENCHMARK VALIDATOR
# ============================================================================

class BenchmarkValidator:
    """
    Validates load test results against benchmarks.
    
    Usage:
        validator = BenchmarkValidator()
        results = await run_load_test()
        validation = validator.validate_results(results)
        report = validator.generate_report(validation)
    """
    
    def __init__(self, benchmarks: dict = None):
        """
        Initialize validator.
        
        Args:
            benchmarks: Custom benchmarks dict (uses defaults if None).
        """
        self.benchmarks = benchmarks or BENCHMARKS
    
    def validate_results(self, results: dict) -> dict:
        """
        Compare actual results vs expected benchmarks.
        
        Args:
            results: Load test results dict.
            
        Returns:
            Dict with pass/fail per endpoint:
            {
                "web_form": {"passed": True, "details": {...}},
                ...
            }
        """
        validation = {}
        
        for endpoint, benchmark in self.benchmarks.items():
            if endpoint not in results:
                validation[endpoint] = {
                    "passed": False,
                    "reason": "No results for endpoint"
                }
                continue
            
            actual = results[endpoint]
            details = {}
            all_passed = True
            
            # Check P95 latency
            if "p95_ms" in actual:
                p95_passed = actual["p95_ms"] <= benchmark["p95_response_ms"]
                details["p95_latency"] = {
                    "actual": actual["p95_ms"],
                    "expected": benchmark["p95_response_ms"],
                    "passed": p95_passed
                }
                if not p95_passed:
                    all_passed = False
            
            # Check error rate
            if "total" in actual and "failed" in actual:
                actual_error_rate = actual["failed"] / max(actual["total"], 1)
                error_passed = actual_error_rate <= benchmark["error_rate"]
                details["error_rate"] = {
                    "actual": round(actual_error_rate * 100, 2),
                    "expected": benchmark["error_rate"] * 100,
                    "passed": error_passed
                }
                if not error_passed:
                    all_passed = False
            
            # Check RPS
            if "rps" in actual:
                rps_passed = actual["rps"] >= benchmark["min_rps"]
                details["rps"] = {
                    "actual": actual["rps"],
                    "expected": benchmark["min_rps"],
                    "passed": rps_passed
                }
                if not rps_passed:
                    all_passed = False
            
            validation[endpoint] = {
                "passed": all_passed,
                "details": details
            }
        
        return validation
    
    def generate_report(self, validation: dict) -> str:
        """
        Generate readable performance report.
        
        Args:
            validation: Validation results dict.
            
        Returns:
            Formatted report string.
        """
        lines = []
        lines.append("=" * 70)
        lines.append("PERFORMANCE BENCHMARK REPORT")
        lines.append("=" * 70)
        lines.append("")
        
        total_passed = sum(1 for v in validation.values() if v["passed"])
        total_failed = len(validation) - total_passed
        
        for endpoint, result in validation.items():
            status = "✓ PASS" if result["passed"] else "✗ FAIL"
            lines.append(f"{endpoint.upper()}: {status}")
            
            if "details" in result:
                for metric, data in result["details"].items():
                    if isinstance(data, dict):
                        actual = data.get("actual", "N/A")
                        expected = data.get("expected", "N/A")
                        passed = data.get("passed", False)
                        metric_status = "✓" if passed else "✗"
                        lines.append(f"  {metric_status} {metric}: {actual} (expected: {expected})")
            
            lines.append("")
        
        lines.append("-" * 70)
        lines.append(f"Summary: {total_passed} passed, {total_failed} failed")
        lines.append("=" * 70)
        
        return "\n".join(lines)


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Print benchmark configuration."""
    print("TechCorp Customer Success FTE - Performance Benchmarks")
    print("=" * 70)
    print("")
    
    for endpoint, benchmark in BENCHMARKS.items():
        print(f"{endpoint.upper()}:")
        for metric, value in benchmark.items():
            print(f"  {metric}: {value}")
        print("")


if __name__ == "__main__":
    main()
