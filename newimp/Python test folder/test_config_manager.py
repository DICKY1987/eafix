import pytest
import tempfile
import os
import yaml
import json
import time
from unittest.mock import patch, Mock, mock_open
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'Python', 'src'))

from services.config_manager import ConfigManager
from utils.config_validator import ConfigValidator

class TestConfigManager:
    """Test suite for configuration management"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory with test config files"""
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp()
        
        # Create test config files
        server_config = {
            'server': {
                'host': 'localhost',
                'port': 8888,
                'max_connections': 10
            },
            'signal_generation': {
                'confidence_threshold': 0.7,
                'max_signals_per_minute': 5,
                'symbol_filters': ['EURUSD', 'GBPUSD']
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/trading_server.log',
                'max_size': '10MB'
            }
        }
        
        system_config = {
            'database': {
                'path': 'data/trading.db',
                'backup_interval': 3600,
                'max_connections': 5
            },
            'communication': {
                'socket_timeout': 30,
                'retry_attempts': 3,
                'named_pipe_name': 'TradingSystemPipe'
            }
        }
        
        pair_config = {
            'EURUSD': {
                'enabled': True,
                'lot_size': 0.1,
                'max_spread': 2.0,
                'trading_hours': {
                    'start': '00:00',
                    'end': '23:59'
                },
                'strategy_params': {
                    'entry_threshold': 0.8,
                    'stop_loss_pips': 50,
                    'take_profit_pips': 100
                }
            },
            'GBPUSD': {
                'enabled': True,
                'lot_size': 0.1,
                'max_spread': 3.0,
                'trading_hours': {
                    'start': '01:00',
                    'end': '22:00'
                },
                'strategy_params': {
                    'entry_threshold': 0.75,
                    'stop_loss_pips': 60,
                    'take_profit_pips': 120
                }
            }
        }
        
        # Write config files
        with open(os.path.join(temp_dir, 'server_config.yaml'), 'w') as f:
            yaml.dump(server_config, f)
            
        with open(os.path.join(temp_dir, 'system_config.yaml'), 'w') as f:
            yaml.dump(system_config, f)
            
        with open(os.path.join(temp_dir, 'pairs_config.yaml'), 'w') as f:
            yaml.dump(pair_config, f)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Create config manager with test directory"""
        manager = ConfigManager(config_dir=temp_config_dir)
        yield manager
        manager.stop_watching()
    
    def test_config_loading(self, config_manager):
        """Test loading configuration files"""
        config_manager.load_all_configs()
        
        # Check server config
        server_config = config_manager.get_config('server')
        assert server_config is not None
        assert server_config['server']['host'] == 'localhost'
        assert server_config['server']['port'] == 8888
        assert server_config['signal_generation']['confidence_threshold'] == 0.7
        
        # Check system config
        system_config = config_manager.get_config('system')
        assert system_config is not None
        assert system_config['database']['path'] == 'data/trading.db'
        assert system_config['communication']['socket_timeout'] == 30
        
        # Check pairs config
        pairs_config = config_manager.get_config('pairs')
        assert pairs_config is not None
        assert 'EURUSD' in pairs_config
        assert pairs_config['EURUSD']['enabled'] is True
        assert pairs_config['EURUSD']['lot_size'] == 0.1
    
    def test_config_validation(self, config_manager):
        """Test configuration validation"""
        config_manager.load_all_configs()
        
        # Should validate successfully
        assert config_manager.validate_all_configs() is True
        
        # Test invalid config
        invalid_config = {
            'server': {
                'host': '',  # Invalid empty host
                'port': -1   # Invalid port
            }
        }
        
        validator = ConfigValidator()
        assert validator.validate_server_config(invalid_config) is False
    
    def test_environment_variable_override(self, config_manager, monkeypatch):
        """Test environment variable overrides"""
        # Set environment variables
        monkeypatch.setenv('TRADING_SERVER_HOST', '192.168.1.100')
        monkeypatch.setenv('TRADING_SERVER_PORT', '9999')
        monkeypatch.setenv('TRADING_DB_PATH', '/custom/path/trading.db')
        
        config_manager.load_all_configs()
        
        server_config = config_manager.get_config('server')
        system_config = config_manager.get_config('system')
        
        # Environment variables should override file values
        assert server_config['server']['host'] == '192.168.1.100'
        assert server_config['server']['port'] == 9999
        assert system_config['database']['path'] == '/custom/path/trading.db'
    
    def test_config_hot_reload(self, config_manager, temp_config_dir):
        """Test hot reloading of configuration files"""
        config_manager.load_all_configs()
        config_manager.start_watching()
        
        original_port = config_manager.get_config('server')['server']['port']
        assert original_port == 8888
        
        # Modify config file
        server_config_path = os.path.join(temp_config_dir, 'server_config.yaml')
        
        with open(server_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        config['server']['port'] = 9000
        
        with open(server_config_path, 'w') as f:
            yaml.dump(config, f)
        
        # Wait for file watcher to detect change
        time.sleep(1.1)  # File watchers typically have 1s resolution
        
        # Config should be reloaded
        updated_port = config_manager.get_config('server')['server']['port']
        assert updated_port == 9000
    
    def test_config_backup_and_restore(self, config_manager, temp_config_dir):
        """Test configuration backup and restore functionality"""
        config_manager.load_all_configs()
        
        # Create backup
        backup_path = os.path.join(temp_config_dir, 'backup')
        config_manager.backup_configs(backup_path)
        
        # Verify backup files exist
        assert os.path.exists(os.path.join(backup_path, 'server_config.yaml'))
        assert os.path.exists(os.path.join(backup_path, 'system_config.yaml'))
        assert os.path.exists(os.path.join(backup_path, 'pairs_config.yaml'))
        
        # Modify original config
        server_config_path = os.path.join(temp_config_dir, 'server_config.yaml')
        with open(server_config_path, 'w') as f:
            f.write("corrupted: data")
        
        # Restore from backup
        config_manager.restore_configs(backup_path)
        
        # Reload and verify restoration
        config_manager.load_all_configs()
        server_config = config_manager.get_config('server')
        assert server_config['server']['host'] == 'localhost'
        assert server_config['server']['port'] == 8888
    
    def test_pair_specific_config_access(self, config_manager):
        """Test accessing pair-specific configuration"""
        config_manager.load_all_configs()
        
        # Get EURUSD config
        eur_config = config_manager.get_pair_config('EURUSD')
        assert eur_config is not None
        assert eur_config['enabled'] is True
        assert eur_config['lot_size'] == 0.1
        assert eur_config['strategy_params']['entry_threshold'] == 0.8
        
        # Get GBPUSD config
        gbp_config = config_manager.get_pair_config('GBPUSD')
        assert gbp_config is not None
        assert gbp_config['strategy_params']['entry_threshold'] == 0.75
        
        # Test non-existent pair
        nonexistent_config = config_manager.get_pair_config('USDJPY')
        assert nonexistent_config is None
    
    def test_config_merging_and_inheritance(self, config_manager, temp_config_dir):
        """Test configuration merging and inheritance"""
        # Create base config
        base_config = {
            'default_strategy': {
                'entry_threshold': 0.7,
                'stop_loss_pips': 50,
                'take_profit_pips': 100,
                'max_spread': 2.0
            }
        }
        
        with open(os.path.join(temp_config_dir, 'base_config.yaml'), 'w') as f:
            yaml.dump(base_config, f)
        
        config_manager.load_all_configs()
        
        # Test config inheritance
        merged_config = config_manager.get_merged_pair_config('EURUSD')
        assert merged_config['entry_threshold'] == 0.8  # Override from pair config
        assert merged_config['stop_loss_pips'] == 50    # From pair config
        assert merged_config['max_spread'] == 2.0       # From pair config
    
    def test_config_validation_errors(self, temp_config_dir):
        """Test handling of invalid configuration files"""
        # Create invalid YAML file
        invalid_config_path = os.path.join(temp_config_dir, 'invalid_config.yaml')
        with open(invalid_config_path, 'w') as f:
            f.write("invalid: yaml: content: [unclosed")
        
        # Should handle invalid YAML gracefully
        manager = ConfigManager(config_dir=temp_config_dir)
        with pytest.raises(yaml.YAMLError):
            manager.load_config('invalid_config')
    
    def test_config_change_callbacks(self, config_manager):
        """Test configuration change callback system"""
        config_manager.load_all_configs()
        
        callback_called = []
        
        def config_change_callback(config_name, old_config, new_config):
            callback_called.append({
                'config_name': config_name,
                'old_port': old_config.get('server', {}).get('port'),
                'new_port': new_config.get('server', {}).get('port')
            })
        
        # Register callback
        config_manager.register_change_callback('server', config_change_callback)
        
        # Simulate config change
        new_server_config = config_manager.get_config('server').copy()
        new_server_config['server']['port'] = 9000
        config_manager._notify_config_change('server', config_manager.get_config('server'), new_server_config)
        
        # Verify callback was called
        assert len(callback_called) == 1
        assert callback_called[0]['config_name'] == 'server'
        assert callback_called[0]['old_port'] == 8888
        assert callback_called[0]['new_port'] == 9000
    
    def test_config_performance_with_frequent_access(self, config_manager):
        """Test configuration access performance"""
        config_manager.load_all_configs()
        
        import time
        
        # Test frequent config access
        start_time = time.time()
        for _ in range(1000):
            server_config = config_manager.get_config('server')
            pair_config = config_manager.get_pair_config('EURUSD')
        access_time = time.time() - start_time
        
        # Should be very fast (cached access)
        assert access_time < 0.1, f"Config access too slow: {access_time:.3f}s"
        
        # Test frequent validation
        start_time = time.time()
        for _ in range(100):
            config_manager.validate_all_configs()
        validation_time = time.time() - start_time
        
        # Validation should be reasonably fast
        assert validation_time < 1.0, f"Config validation too slow: {validation_time:.3f}s"
    
    def test_config_threading_safety(self, config_manager):
        """Test thread safety of configuration manager"""
        import threading
        import time
        
        config_manager.load_all_configs()
        
        results = []
        errors = []
        
        def access_config(thread_id, iterations):
            try:
                for i in range(iterations):
                    # Read config
                    server_config = config_manager.get_config('server')
                    pair_config = config_manager.get_pair_config('EURUSD')
                    
                    # Validate access
                    assert server_config is not None
                    assert pair_config is not None
                    
                    time.sleep(0.001)  # Small delay
                
                results.append(f"Thread {thread_id} completed")
            except Exception as e:
                errors.append(f"Thread {thread_id} error: {e}")
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=access_config, args=(i, 50))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Threading errors: {errors}"
        assert len(results) == 5

class TestConfigManagerIntegration:
    """Integration tests for config manager with other components"""
    
    def test_config_integration_with_server_startup(self, temp_config_dir):
        """Test configuration integration during server startup"""
        # Create config manager
        config_manager = ConfigManager(config_dir=temp_config_dir)
        config_manager.load_all_configs()
        
        # Simulate server startup using configs
        server_config = config_manager.get_config('server')
        
        # Server should be able to use config values
        host = server_config['server']['host']
        port = server_config['server']['port']
        confidence_threshold = server_config['signal_generation']['confidence_threshold']
        
        assert host == 'localhost'
        assert port == 8888
        assert confidence_threshold == 0.7
        
        # Test pair configuration for trading logic
        eur_config = config_manager.get_pair_config('EURUSD')
        lot_size = eur_config['lot_size']
        entry_threshold = eur_config['strategy_params']['entry_threshold']
        
        assert lot_size == 0.1
        assert entry_threshold == 0.8
    
    def test_config_driven_signal_filtering(self, temp_config_dir):
        """Test using configuration for signal filtering logic"""
        config_manager = ConfigManager(config_dir=temp_config_dir)
        config_manager.load_all_configs()
        
        server_config = config_manager.get_config('server')
        
        # Test signal filtering based on config
        symbol_filters = server_config['signal_generation']['symbol_filters']
        confidence_threshold = server_config['signal_generation']['confidence_threshold']
        
        # Simulate signals
        test_signals = [
            {'symbol': 'EURUSD', 'confidence': 0.8},  # Should pass
            {'symbol': 'USDJPY', 'confidence': 0.9},  # Should fail (not in filter)
            {'symbol': 'GBPUSD', 'confidence': 0.6},  # Should fail (low confidence)
            {'symbol': 'EURUSD', 'confidence': 0.75}, # Should pass
        ]
        
        filtered_signals = []
        for signal in test_signals:
            if (signal['symbol'] in symbol_filters and 
                signal['confidence'] >= confidence_threshold):
                filtered_signals.append(signal)
        
        assert len(filtered_signals) == 2
        assert all(s['symbol'] in ['EURUSD', 'GBPUSD'] for s in filtered_signals)
        assert all(s['confidence'] >= 0.7 for s in filtered_signals)

if __name__ == "__main__":
    # Run config manager tests
    pytest.main([__file__, "-v", "--tb=short"])