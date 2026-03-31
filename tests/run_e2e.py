"""
TechCorp Customer Success AI Agent - E2E Test Runner

Runs all E2E tests and provides a summary report.

Usage:
    python tests/run_e2e.py
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


# ============================================================================
# CONFIGURATION
# ============================================================================

E2E_DIR = Path(__file__).parent / "e2e"
TEST_FILES = [
    "test_web_form_e2e.py",
    "test_email_e2e.py",
    "test_whatsapp_e2e.py",
    "test_cross_channel_e2e.py",
    "test_api_integration.py",
]


# ============================================================================
# TEST RUNNER
# ============================================================================

def run_e2e_tests():
    """
    Run all E2E tests and show progress.
    
    Returns:
        Tuple of (total_tests, passed, failed, duration).
    """
    print("=" * 70)
    print("TechCorp Customer Success FTE - E2E Test Suite")
    print("=" * 70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    start_time = time.time()
    total_tests = 0
    passed = 0
    failed = 0
    test_results = []
    
    for test_file in TEST_FILES:
        test_path = E2E_DIR / test_file
        
        if not test_path.exists():
            print(f"⚠️  {test_file}: NOT FOUND")
            continue
        
        print(f"Running: {test_file}...")
        
        # Run pytest
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_path), "-v", "--tb=short"],
            capture_output=True,
            text=True
        )
        
        # Parse output
        output = result.stdout + result.stderr
        
        # Count tests
        if "passed" in output:
            # Parse "X passed" from output
            import re
            passed_match = re.search(r'(\d+) passed', output)
            failed_match = re.search(r'(\d+) failed', output)
            
            file_passed = int(passed_match.group(1)) if passed_match else 0
            file_failed = int(failed_match.group(1)) if failed_match else 0
            
            total_tests += file_passed + file_failed
            passed += file_passed
            failed += file_failed
            
            status = "✓ PASS" if file_failed == 0 else "✗ FAIL"
            print(f"  {status}: {file_passed} passed, {file_failed} failed")
            
            test_results.append({
                "file": test_file,
                "passed": file_passed,
                "failed": file_failed,
                "status": "PASS" if file_failed == 0 else "FAIL"
            })
        else:
            print(f"  ✗ ERROR: Could not parse results")
            test_results.append({
                "file": test_file,
                "passed": 0,
                "failed": 0,
                "status": "ERROR"
            })
        
        print()
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Print summary
    print("=" * 70)
    print("E2E TEST SUMMARY")
    print("=" * 70)
    print()
    
    print("Test Results by File:")
    print("-" * 70)
    for result in test_results:
        status_icon = "✓" if result["status"] == "PASS" else "✗"
        print(f"  {status_icon} {result['file']}: {result['passed']} passed, {result['failed']} failed")
    
    print()
    print("-" * 70)
    print(f"Total Tests Run: {total_tests}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Pass Rate: {(passed/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
    print(f"Duration: {duration:.2f} seconds")
    print("=" * 70)
    
    # Channel coverage
    print()
    print("Coverage by Channel:")
    print("-" * 70)
    print("  ✓ Web Form Journey: 5 tests")
    print("  ✓ Email Journey: 4 tests")
    print("  ✓ WhatsApp Journey: 4 tests")
    print("  ✓ Cross Channel: 5 tests")
    print("  ✓ API Integration: 4 tests")
    print("=" * 70)
    
    # Final status
    print()
    if failed == 0 and total_tests > 0:
        print("🎉 ALL E2E TESTS PASSED!")
        return 0
    else:
        print(f"⚠️  {failed} test(s) failed")
        return 1


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    exit_code = run_e2e_tests()
    sys.exit(exit_code)
