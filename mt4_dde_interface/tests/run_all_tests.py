"""
Master test runner for all MT4 DDE Interface tests
"""
import unittest
import sys
import os
import time
import json
from datetime import datetime
import importlib
import traceback

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Import test modules
test_modules = [
    'test_dde_connection',
    'test_indicators',
]


class TestResult:
    """Custom test result class for detailed reporting"""
    
    def __init__(self):
        self.tests_run = 0
        self.failures = []
        self.errors = []
        self.skipped = []
        self.success_count = 0
        self.start_time = None
        self.end_time = None
        self.duration = 0
    
    def start_test_run(self):
        """Called when test run starts"""
        self.start_time = time.time()
    
    def stop_test_run(self):
        """Called when test run ends"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
    
    def add_test_result(self, test_name, status, error_msg=None):
        """Add a test result"""
        self.tests_run += 1
        
        if status == 'success':
            self.success_count += 1
        elif status == 'failure':
            self.failures.append((test_name, error_msg))
        elif status == 'error':
            self.errors.append((test_name, error_msg))
        elif status == 'skipped':
            self.skipped.append((test_name, error_msg))
    
    def was_successful(self):
        """Return True if all tests passed"""
        return len(self.failures) == 0 and len(self.errors) == 0
    
    def get_summary(self):
        """Get test summary"""
        return {
            'total_tests': self.tests_run,
            'successes': self.success_count,
            'failures': len(self.failures),
            'errors': len(self.errors),
            'skipped': len(self.skipped),
            'duration': self.duration,
            'success_rate': (self.success_count / self.tests_run * 100) if self.tests_run > 0 else 0
        }


class TestRunner:
    """Main test runner for the DDE interface"""
    
    def __init__(self, verbose=True, generate_report=True):
        self.verbose = verbose
        self.generate_report = generate_report
        self.results = {}
        self.overall_result = TestResult()
        
    def run_module_tests(self, module_name):
        """Run tests for a specific module"""
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Running {module_name} tests...")
            print('='*60)
        
        try:
            # Import the test module
            module = importlib.import_module(module_name)
            
            # Get the test function
            if hasattr(module, f'run_{module_name.replace("test_", "")}_tests'):
                run_tests_func = getattr(module, f'run_{module_name.replace("test_", "")}_tests')
            elif hasattr(module, 'run_all_tests'):
                run_tests_func = module.run_all_tests
            else:
                # Use unittest discovery
                loader = unittest.TestLoader()
                suite = loader.loadTestsFromModule(module)
                runner = unittest.TextTestRunner(verbosity=2 if self.verbose else 1)
                result = runner.run(suite)
                return result.wasSuccessful()
            
            # Run the tests
            success = run_tests_func()
            
            if self.verbose:
                if success:
                    print(f"✓ {module_name} tests PASSED")
                else:
                    print(f"✗ {module_name} tests FAILED")
            
            return success
            
        except Exception as e:
            if self.verbose:
                print(f"✗ Error running {module_name} tests: {e}")
                traceback.print_exc()
            return False
    
    def run_all_tests(self):
        """Run all test modules"""
        if self.verbose:
            print("MT4 DDE Interface - Test Suite")
            print("="*60)
            print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Test modules: {', '.join(test_modules)}")
        
        self.overall_result.start_test_run()
        
        all_passed = True
        module_results = {}
        
        for module_name in test_modules:
            try:
                success = self.run_module_tests(module_name)
                module_results[module_name] = success
                
                if not success:
                    all_passed = False
                    
            except Exception as e:
                if self.verbose:
                    print(f"Critical error in {module_name}: {e}")
                all_passed = False
                module_results[module_name] = False
        
        self.overall_result.stop_test_run()
        
        # Print summary
        if self.verbose:
            self._print_summary(module_results, all_passed)
        
        # Generate report if requested
        if self.generate_report:
            self._generate_report(module_results, all_passed)
        
        return all_passed
    
    def _print_summary(self, module_results, all_passed):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        for module, success in module_results.items():
            status = "PASS" if success else "FAIL"
            symbol = "✓" if success else "✗"
            print(f"{symbol} {module:<30} {status}")
        
        print("-"*60)
        passed_count = sum(1 for success in module_results.values() if success)
        total_count = len(module_results)
        
        print(f"Modules passed: {passed_count}/{total_count}")
        print(f"Overall result: {'PASS' if all_passed else 'FAIL'}")
        print(f"Duration: {self.overall_result.duration:.2f} seconds")
        
        if not all_passed:
            print("\nFailed modules:")
            for module, success in module_results.items():
                if not success:
                    print(f"  - {module}")
    
    def _generate_report(self, module_results, all_passed):
        """Generate JSON test report"""
        report_data = {
            'test_run': {
                'timestamp': datetime.now().isoformat(),
                'duration': self.overall_result.duration,
                'overall_success': all_passed,
                'modules_tested': len(module_results),
                'modules_passed': sum(1 for success in module_results.values() if success)
            },
            'module_results': module_results,
            'environment': {
                'python_version': sys.version,
                'platform': sys.platform,
                'working_directory': os.getcwd()
            }
        }
        
        # Write report file
        report_file = os.path.join(
            os.path.dirname(__file__), 
            f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        try:
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            if self.verbose:
                print(f"\nTest report written to: {report_file}")
                
        except Exception as e:
            if self.verbose:
                print(f"Warning: Could not write test report: {e}")


class QuickTest:
    """Quick smoke test for critical functionality"""
    
    @staticmethod
    def run_smoke_tests():
        """Run quick smoke tests"""
        print("Running smoke tests...")
        
        tests_passed = 0
        tests_total = 0
        
        # Test 1: Import all main modules
        tests_total += 1
        try:
            from dde_client import MT4DDEClient
            from price_manager import PriceManager
            from indicator_engine import IndicatorEngine
            from moving_averages import SimpleMovingAverage
            from oscillators import RelativeStrengthIndex
            from volatility import BollingerBands
            print("✓ Module imports successful")
            tests_passed += 1
        except Exception as e:
            print(f"✗ Module import failed: {e}")
        
        # Test 2: Basic indicator creation
        tests_total += 1
        try:
            from moving_averages import create_moving_average
            sma = create_moving_average('SMA', 'test', 20)
            
            # Add some data
            for i in range(25):
                result = sma.update(100.0 + i)
            
            if sma.is_initialized and sma.get_current_value() is not None:
                print("✓ Basic indicator functionality works")
                tests_passed += 1
            else:
                print("✗ Indicator not working properly")
        except Exception as e:
            print(f"✗ Indicator test failed: {e}")
        
        # Test 3: Configuration management
        tests_total += 1
        try:
            from config_manager import ConfigurationManager
            config_mgr = ConfigurationManager()
            
            # Test basic operations
            dde_config = config_mgr.get_dde_config()
            symbols = config_mgr.get_default_symbols()
            
            if dde_config and symbols:
                print("✓ Configuration management works")
                tests_passed += 1
            else:
                print("✗ Configuration management failed")
        except Exception as e:
            print(f"✗ Configuration test failed: {e}")
        
        # Test 4: Price manager
        tests_total += 1
        try:
            from price_manager import PriceManager
            pm = PriceManager()
            
            # Add test price data
            test_data = {
                'bid': 1.10500,
                'ask': 1.10520,
                'timestamp': datetime.now()
            }
            
            success = pm.add_price_tick('EURUSD', test_data)
            latest = pm.get_latest_price('EURUSD')
            
            if success and latest:
                print("✓ Price manager works")
                tests_passed += 1
            else:
                print("✗ Price manager failed")
        except Exception as e:
            print(f"✗ Price manager test failed: {e}")
        
        print(f"\nSmoke test results: {tests_passed}/{tests_total} passed")
        return tests_passed == tests_total


def main():
    """Main test execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MT4 DDE Interface Test Runner')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output')
    parser.add_argument('--smoke', '-s', action='store_true', 
                       help='Run smoke tests only')
    parser.add_argument('--no-report', action='store_true', 
                       help='Do not generate test report')
    parser.add_argument('--module', '-m', 
                       help='Run tests for specific module only')
    
    args = parser.parse_args()
    
    # Run smoke tests if requested
    if args.smoke:
        success = QuickTest.run_smoke_tests()
        return 0 if success else 1
    
    # Create test runner
    runner = TestRunner(
        verbose=args.verbose, 
        generate_report=not args.no_report
    )
    
    # Run specific module or all tests
    if args.module:
        if args.module in test_modules:
            success = runner.run_module_tests(args.module)
        else:
            print(f"Error: Module '{args.module}' not found")
            print(f"Available modules: {', '.join(test_modules)}")
            return 1
    else:
        success = runner.run_all_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Critical error in test runner: {e}")
        traceback.print_exc()
        sys.exit(1)