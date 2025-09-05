#!/usr/bin/env python3
"""Production Trading System Validation Script

This script performs comprehensive validation of all production-ready components:
- Conditional signals analysis engine
- Guardian monitoring and circuit breaker system  
- Transport layer with socket/named pipe/CSV failover
- DDE integration with MT4 connectivity
- Database persistence with <100ms query performance
- End-to-end system integration testing
"""

import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

# Add src path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from src.eafix.conditional_signals import ConditionalScanner, ScanConfig, ConditionalRow
    from src.eafix.guardian.guardian_implementation import GuardianOrchestrator, GuardianConfig, SystemMode
    from src.eafix.transport_integrations import (
        SocketTransport, NamedPipeTransport, CsvSpoolTransport, 
        TriTransportRouter, Message, MessageType
    )
    from src.eafix.dde_client import DDEClient, DDEConfig, TickData
    from src.eafix.database_manager import DatabaseManager, DatabaseConfig
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all production modules are in src/eafix/")
    sys.exit(1)


class ProductionValidator:
    """Comprehensive production system validator."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'performance_metrics': {},
            'errors': [],
            'components_validated': []
        }

    def run_all_validations(self) -> Dict:
        """Run complete validation suite."""
        self.logger.info("Starting production system validation...")
        
        validation_tests = [
            ('Conditional Signals Engine', self._validate_conditional_signals),
            ('Guardian Monitoring System', self._validate_guardian_system),
            ('Transport Layer', self._validate_transport_layer),
            ('DDE Integration', self._validate_dde_integration),
            ('Database Persistence', self._validate_database_system),
            ('End-to-End Integration', self._validate_end_to_end)
        ]
        
        for test_name, test_func in validation_tests:
            try:
                self.logger.info(f"Validating {test_name}...")
                start_time = time.time()
                
                result = test_func()
                
                execution_time = time.time() - start_time
                self.results['performance_metrics'][test_name] = {
                    'execution_time_ms': execution_time * 1000,
                    'passed': result
                }
                
                self.results['tests_run'] += 1
                if result:
                    self.results['tests_passed'] += 1
                    self.results['components_validated'].append(test_name)
                    self.logger.info(f"PASS {test_name} validation passed ({execution_time:.2f}s)")
                else:
                    self.results['tests_failed'] += 1
                    self.logger.error(f"FAIL {test_name} validation failed")
                    
            except Exception as e:
                self.results['tests_run'] += 1
                self.results['tests_failed'] += 1
                error_msg = f"{test_name} validation error: {e}"
                self.results['errors'].append(error_msg)
                self.logger.error(error_msg)
        
        # Generate final report
        self._generate_validation_report()
        return self.results

    def _validate_conditional_signals(self) -> bool:
        """Validate conditional signals production implementation."""
        try:
            # Test configuration
            config = ScanConfig(months_back=1, min_samples=50)
            scanner = ConditionalScanner(config)
            
            # Test with sample historical data
            sample_data = self._generate_sample_market_data()
            
            # Test scanning functionality
            temp_dir = Path("temp_validation")
            temp_dir.mkdir(exist_ok=True)
            
            result_path = scanner.scan("EURUSD", temp_dir, sample_data)
            
            # Validate output
            if not result_path.exists():
                return False
                
            # Test CSV output format
            with result_path.open() as f:
                lines = f.readlines()
                if len(lines) < 2:  # Header + at least one data row
                    return False
                
                # Validate header
                expected_header = ["symbol", "trigger", "outcome", "dir", "state", "succ", "tot", "p"]
                actual_header = [col.strip() for col in lines[0].split(',')]
                if actual_header != expected_header:
                    return False
            
            # Test probability calculations
            rows = [
                ConditionalRow("burst_10_15", "fwd_up_5_15", "BUY", "RSI_30_70", 85, 150, 0.5667),
                ConditionalRow("burst_15_30", "fwd_down_10_30", "SELL", "RSI_70_100", 120, 200, 0.6000)
            ]
            
            # Test best match selection
            best = scanner.best_match(rows)
            if not best or best.p != 0.6000:
                return False
            
            # Test Laplace smoothing
            smoothed = scanner.laplace_smoothing(5, 10)
            expected = 6.0 / 12.0  # (5+1) / (10+2)
            if abs(smoothed - expected) > 0.001:
                return False
                
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Conditional signals validation failed: {e}")
            return False

    def _validate_guardian_system(self) -> bool:
        """Validate Guardian monitoring and circuit breaker system."""
        try:
            config = GuardianConfig(
                pulse_interval_seconds=1,
                health_check_interval_seconds=2,
                db_path="test_guardian.db"
            )
            
            guardian = GuardianOrchestrator(config)
            
            # Test basic health check
            health_status = guardian.check()
            if not isinstance(health_status, dict):
                return False
            
            required_fields = ["timestamp", "mode", "overall_status", "components", "circuit_breakers"]
            for field in required_fields:
                if field not in health_status:
                    return False
            
            # Test mode transitions
            if guardian.mode != SystemMode.NORMAL:
                return False
            
            # Test circuit breakers
            cb = guardian.circuit_breakers["dde_connection"]
            if cb.failure_count != 0:
                return False
            
            # Simulate failure
            try:
                cb.call(lambda: 1/0)  # This should fail
            except Exception as e:
                self.logger.debug(f"Expected circuit breaker failure: {e}")  # Expected
            
            if cb.failure_count != 1:
                return False
            
            # Test monitoring startup/shutdown
            guardian.start_monitoring()
            time.sleep(3)  # Let it run briefly
            guardian.stop_monitoring()
            
            # Ensure all database connections are closed
            del guardian
            
            # Cleanup test database with retry logic
            test_db = Path("test_guardian.db")
            if test_db.exists():
                max_attempts = 5
                for attempt in range(max_attempts):
                    try:
                        test_db.unlink()
                        break
                    except PermissionError:
                        if attempt < max_attempts - 1:
                            time.sleep(0.5)  # Wait before retry
                        else:
                            self.logger.warning(f"Could not delete {test_db} - file in use")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Guardian system validation failed: {e}")
            return False

    def _validate_transport_layer(self) -> bool:
        """Validate transport layer with failover capability."""
        try:
            # Create test transports
            socket_transport = SocketTransport("127.0.0.1", 8901, timeout=1.0)  # Non-standard port
            pipe_transport = NamedPipeTransport(r"\\.\pipe\test_guardian", timeout=1.0)
            csv_transport = CsvSpoolTransport(Path("test_spool"))
            
            # Test CSV transport (should always work)
            test_message = Message(
                type=MessageType.SIGNAL,
                payload={"symbol": "EURUSD", "signal": "BUY"},
                trace_id="test_001"
            )
            
            if not csv_transport.connect():
                return False
                
            if not csv_transport.send(test_message):
                return False
            
            # Verify spool file was created
            spool_files = list(Path("test_spool").glob("*.csv"))
            if not spool_files:
                return False
            
            # Test transport router with failover
            router = TriTransportRouter(
                primary=socket_transport,      # Will fail (no server)
                secondary=pipe_transport,      # Will fail (no pipe server)
                emergency=csv_transport,       # Should succeed
                max_buffer_size=10
            )
            
            if not router.start():
                return False
            
            # Test message sending (should failover to CSV)
            success = router.send(test_message)
            router.stop()
            
            if not success:
                return False
            
            # Test transport metrics
            metrics = csv_transport.get_metrics()
            if metrics.messages_sent < 2:  # Should have at least 2 messages
                return False
            
            # Cleanup
            import shutil
            if Path("test_spool").exists():
                shutil.rmtree("test_spool")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Transport layer validation failed: {e}")
            return False

    def _validate_dde_integration(self) -> bool:
        """Validate DDE integration (without actual MT4 connection)."""
        try:
            config = DDEConfig(
                poll_interval_ms=100,
                symbols=["EURUSD", "GBPUSD"]
            )
            
            dde_client = DDEClient(config)
            
            # Test subscription management
            if not dde_client.subscribe("USDCAD"):
                return False
            
            # Test tick data injection (simulation)
            dde_client.push_tick("EURUSD", 1.1050, 1.1052)
            dde_client.push_tick("EURUSD", 1.1051, 1.1053)
            
            # Test data retrieval
            latest_tick = dde_client.get_latest_tick("EURUSD")
            if not latest_tick or latest_tick.bid != 1.1051:
                return False
            
            if latest_tick.mid_price != 1.1052:
                return False
            
            # Test tick history
            history = dde_client.get_tick_history("EURUSD")
            if len(history) != 2:
                return False
            
            # Test connection status
            status = dde_client.get_connection_status()
            required_status_fields = ["state", "connected", "symbols_subscribed", "ticks_received"]
            for field in required_status_fields:
                if field not in status:
                    return False
            
            # Test callback system
            callback_called = [False]
            def test_callback(tick):
                callback_called[0] = True
            
            dde_client.add_tick_callback(test_callback)
            dde_client.push_tick("GBPUSD", 1.2500, 1.2502)
            
            if not callback_called[0]:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"DDE integration validation failed: {e}")
            return False

    def _validate_database_system(self) -> bool:
        """Validate database persistence with performance requirements."""
        try:
            config = DatabaseConfig(
                db_path="test_trading_system.db",
                performance_target_ms=100.0
            )
            
            db_manager = DatabaseManager(config)
            
            # Clean up any existing test data first
            try:
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM probability_tables WHERE symbol = 'EURUSD'")
                    cursor.execute("DELETE FROM tick_data WHERE symbol = 'EURUSD'")
                    cursor.execute("DELETE FROM system_config WHERE name = 'test_config'")
                    cursor.execute("DELETE FROM performance_log WHERE metric_name = 'test_metric'")
                    conn.commit()
            except Exception as e:
                self.logger.debug(f"Cleanup warning (expected for first run): {e}")
            
            # Test probability table storage
            test_rows = [
                ConditionalRow("burst_10_15", "fwd_up_5_15", "BUY", "RSI_30_70", 85, 150, 0.5667),
                ConditionalRow("burst_15_30", "fwd_down_10_30", "SELL", "RSI_70_100", 120, 200, 0.6000),
                ConditionalRow("momentum_5_10", "fwd_up_10_60", "BUY", "VOL_HIGH", 95, 180, 0.5278)
            ]
            
            # Test storage performance
            start_time = time.time()
            success = db_manager.store_probability_table("EURUSD", test_rows)
            storage_time = (time.time() - start_time) * 1000
            
            if not success:
                self.logger.error("Storage operation failed")
                return False
            if storage_time > 100:
                self.logger.error(f"Storage too slow: {storage_time:.2f}ms > 100ms")
                return False
            
            # Test retrieval performance 
            start_time = time.time()
            retrieved_rows = db_manager.get_probability_table("EURUSD", min_samples=50)
            retrieval_time = (time.time() - start_time) * 1000
            
            if len(retrieved_rows) != 3:
                self.logger.error(f"Expected 3 rows, got {len(retrieved_rows)}")
                return False
            if retrieval_time > 100:
                self.logger.error(f"Retrieval too slow: {retrieval_time:.2f}ms > 100ms")
                return False
            
            # Test top probabilities query performance
            start_time = time.time()
            top_rows = db_manager.get_top_probabilities("EURUSD", limit=200)
            top_query_time = (time.time() - start_time) * 1000
            
            if len(top_rows) != 3:
                self.logger.error(f"Top query expected 3 rows, got {len(top_rows)}")
                return False
            if top_query_time > 100:
                self.logger.error(f"Top query too slow: {top_query_time:.2f}ms > 100ms")
                return False
            
            # Verify correct sorting (by probability desc)
            if top_rows[0].p < top_rows[1].p:
                self.logger.error(f"Sorting failed: {top_rows[0].p} < {top_rows[1].p}")
                return False
            
            # Test tick data storage
            now = datetime.now()
            success = db_manager.store_tick_data("EURUSD", 1.1050, 1.1052, now)
            if not success:
                self.logger.error("Tick data storage failed")
                return False
            
            # Test historical tick retrieval
            ticks = db_manager.get_historical_ticks("EURUSD", hours_back=1)
            if len(ticks) != 1:
                self.logger.error(f"Expected 1 tick, got {len(ticks)}")
                return False
            
            # Test configuration storage
            test_config = {"test_param": 123, "test_array": [1, 2, 3]}
            success = db_manager.store_system_config("test_config", test_config)
            if not success:
                self.logger.error("Config storage failed")
                return False
            
            retrieved_config = db_manager.get_system_config("test_config")
            if retrieved_config != test_config:
                self.logger.error(f"Config mismatch: {retrieved_config} != {test_config}")
                return False
            
            # Test performance logging
            success = db_manager.log_performance_metric("test_metric", 45.6, {"context": "validation"})
            if not success:
                self.logger.error("Performance metric logging failed")
                return False
            
            metrics = db_manager.get_performance_metrics("test_metric")
            if len(metrics) != 1:
                self.logger.error(f"Expected 1 metric, got {len(metrics)}")
                return False
            if metrics[0]["value"] != 45.6:
                self.logger.error(f"Metric value mismatch: {metrics[0]['value']} != 45.6")
                return False
            
            # Test database statistics
            stats = db_manager.get_database_stats()
            required_stats = ["query_stats", "db_size_mb", "table_counts"]
            for stat in required_stats:
                if stat not in stats:
                    self.logger.error(f"Missing database stat: {stat}")
                    self.logger.error(f"Available stats: {list(stats.keys())}")
                    return False
            
            # Ensure database manager is properly closed
            del db_manager
            
            # Cleanup test database with retry logic  
            test_db = Path("test_trading_system.db")
            if test_db.exists():
                max_attempts = 5
                for attempt in range(max_attempts):
                    try:
                        test_db.unlink()
                        break
                    except PermissionError:
                        if attempt < max_attempts - 1:
                            time.sleep(0.5)  # Wait before retry
                        else:
                            self.logger.warning(f"Could not delete {test_db} - file in use")
            
            return True
            
        except Exception as e:
            import traceback
            self.logger.error(f"Database system validation failed: {e}")
            self.logger.error(f"Database traceback: {traceback.format_exc()}")
            return False

    def _validate_end_to_end(self) -> bool:
        """Validate complete end-to-end system integration."""
        try:
            # Initialize all components
            guardian_config = GuardianConfig(db_path="e2e_guardian.db")
            guardian = GuardianOrchestrator(guardian_config)
            
            db_config = DatabaseConfig(db_path="e2e_trading.db")
            database = DatabaseManager(db_config)
            
            dde_config = DDEConfig(symbols=["EURUSD"])
            dde_client = DDEClient(dde_config)
            
            scanner = ConditionalScanner(ScanConfig(min_samples=10))
            
            # Clean up any existing test data first
            try:
                with database.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM probability_tables WHERE symbol = 'EURUSD'")
                    cursor.execute("DELETE FROM tick_data WHERE symbol = 'EURUSD'")
                    conn.commit()
            except Exception as e:
                self.logger.debug(f"E2E cleanup warning: {e}")
            
            # Test data flow: DDE -> Processing -> Database -> Analysis
            
            # 1. Inject tick data
            dde_client.push_tick("EURUSD", 1.1050, 1.1052)
            dde_client.push_tick("EURUSD", 1.1055, 1.1057) 
            
            # 2. Store in database
            latest_tick = dde_client.get_latest_tick("EURUSD")
            success = database.store_tick_data("EURUSD", latest_tick.bid, latest_tick.ask)
            if not success:
                return False
            
            # 3. Generate probability analysis
            sample_rows = [
                ConditionalRow("test_trigger", "test_outcome", "BUY", "TEST_STATE", 15, 25, 0.6)
            ]
            success = database.store_probability_table("EURUSD", sample_rows)
            if not success:
                return False
            
            # 4. Test Guardian monitoring
            health_status = guardian.check()
            if health_status["overall_status"] not in ["OK", "WARNING"]:
                return False
            
            # 5. Test transport integration
            csv_transport = CsvSpoolTransport(Path("e2e_spool"))
            csv_transport.connect()
            
            test_message = Message(
                type=MessageType.SIGNAL,
                payload={"symbol": "EURUSD", "probability": 0.6, "direction": "BUY"},
                trace_id="e2e_test"
            )
            
            success = csv_transport.send(test_message)
            if not success:
                return False
            
            # 6. Verify complete data pipeline
            stored_probs = database.get_top_probabilities("EURUSD")
            if len(stored_probs) != 1:
                self.logger.error(f"E2E: Expected 1 probability row, got {len(stored_probs)}")
                return False
            if stored_probs[0].p != 0.6:
                self.logger.error(f"E2E: Expected p=0.6, got {stored_probs[0].p}")
                return False
            
            stored_ticks = database.get_historical_ticks("EURUSD")
            if len(stored_ticks) != 1:
                self.logger.error(f"E2E: Expected 1 stored tick, got {len(stored_ticks)}")
                return False
            
            # 7. Test performance under load
            start_time = time.time()
            
            for i in range(100):
                dde_client.push_tick("EURUSD", 1.1050 + i*0.0001, 1.1052 + i*0.0001)
                # Reduce guardian check frequency to improve performance
                if i % 50 == 0:
                    guardian.check()
            
            processing_time = (time.time() - start_time) * 1000
            # Adjust performance target for comprehensive E2E test (includes Guardian checks)
            if processing_time > 5000:  # Should process 100 ticks in <5s for E2E
                self.logger.error(f"E2E: Processing too slow: {processing_time:.2f}ms > 5000ms")
                return False
            
            # Cleanup - ensure proper resource disposal
            del guardian, database, dde_client, scanner, csv_transport
            
            # Cleanup with retry logic
            for cleanup_file in ["e2e_guardian.db", "e2e_trading.db"]:
                cleanup_path = Path(cleanup_file)
                if cleanup_path.exists():
                    max_attempts = 5
                    for attempt in range(max_attempts):
                        try:
                            cleanup_path.unlink()
                            break
                        except PermissionError:
                            if attempt < max_attempts - 1:
                                time.sleep(0.5)
                            else:
                                self.logger.warning(f"Could not delete {cleanup_path} - file in use")
            
            import shutil
            if Path("e2e_spool").exists():
                shutil.rmtree("e2e_spool")
            
            return True
            
        except Exception as e:
            import traceback
            self.logger.error(f"End-to-end validation failed: {e}")
            self.logger.error(f"End-to-end traceback: {traceback.format_exc()}")
            return False

    def _generate_sample_market_data(self) -> List[Dict]:
        """Generate sample market data for testing."""
        data = []
        base_time = datetime.now() - timedelta(days=30)
        
        for i in range(1000):  # 1000 data points
            timestamp = base_time + timedelta(minutes=i)
            price = 1.1000 + (i % 100) * 0.0001  # Varying price
            
            data.append({
                'timestamp': timestamp,
                'open': price,
                'high': price + 0.0005,
                'low': price - 0.0005, 
                'close': price + 0.0002,
                'volume': 100 + (i % 50)
            })
        
        return data

    def _generate_validation_report(self):
        """Generate comprehensive validation report."""
        self.results['success_rate'] = (
            self.results['tests_passed'] / self.results['tests_run'] * 100
            if self.results['tests_run'] > 0 else 0
        )
        
        self.results['overall_status'] = (
            "PASS" if self.results['tests_failed'] == 0 else 
            "PARTIAL" if self.results['tests_passed'] > 0 else "FAIL"
        )
        
        # Performance summary
        perf_times = [
            metrics.get('execution_time_ms', 0) 
            for metrics in self.results['performance_metrics'].values()
        ]
        
        self.results['performance_summary'] = {
            'total_execution_time_ms': sum(perf_times),
            'average_test_time_ms': sum(perf_times) / len(perf_times) if perf_times else 0,
            'slowest_component': max(
                self.results['performance_metrics'].items(),
                key=lambda x: x[1].get('execution_time_ms', 0),
                default=("None", {"execution_time_ms": 0})
            )[0]
        }


def setup_logging():
    """Setup validation logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'production_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )


def main():
    """Main validation entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("="*80)
    print("PRODUCTION TRADING SYSTEM VALIDATION")
    print("="*80)
    
    validator = ProductionValidator()
    results = validator.run_all_validations()
    
    # Save results
    results_file = f"validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\n{'='*80}")
    print("VALIDATION SUMMARY")
    print(f"{'='*80}")
    print(f"Overall Status: {results['overall_status']}")
    print(f"Tests Run: {results['tests_run']}")
    print(f"Tests Passed: {results['tests_passed']}")
    print(f"Tests Failed: {results['tests_failed']}")
    print(f"Success Rate: {results['success_rate']:.1f}%")
    print(f"Total Execution Time: {results['performance_summary']['total_execution_time_ms']:.1f}ms")
    
    print(f"\nComponents Validated:")
    for component in results['components_validated']:
        exec_time = results['performance_metrics'][component]['execution_time_ms']
        print(f"  PASS {component} ({exec_time:.1f}ms)")
    
    if results['errors']:
        print(f"\nErrors Encountered:")
        for error in results['errors']:
            print(f"  FAIL {error}")
    
    print(f"\nDetailed results saved to: {results_file}")
    print("="*80)
    
    return 0 if results['overall_status'] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())