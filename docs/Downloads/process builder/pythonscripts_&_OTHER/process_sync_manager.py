#!/usr/bin/env python3
"""
Multi-Format Process Synchronization Manager
Keeps YAML/JSON (machine), Markdown (human), and XML (visual) formats in perfect sync
"""

import os
import sys
import hashlib
import argparse
import time
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Dict, List, Optional, Tuple
import shutil
import json

# Import our enhanced framework
from atomic_process_framework import AtomicProcessFramework, ProcessFlow

class ProcessSyncManager:
    """Comprehensive synchronization manager for all process document formats"""
    
    def __init__(self, base_dir: str = ".", config_file: str = "sync_config.json"):
        self.base_dir = Path(base_dir)
        self.config_file = self.base_dir / config_file
        self.framework = AtomicProcessFramework(str(self.base_dir))
        
        # Load or create configuration
        self.config = self._load_or_create_config()
        
        # File paths based on config
        self.files = {
            'machine_yaml': self.base_dir / self.config['files']['machine_yaml'],
            'machine_json': self.base_dir / self.config['files']['machine_json'],
            'human_md': self.base_dir / self.config['files']['human_md'],
            'visual_xml': self.base_dir / self.config['files']['visual_xml'],
            'hash_store': self.base_dir / self.config['files']['hash_store'],
            'sync_log': self.base_dir / self.config['files']['sync_log']
        }
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Load process flow
        self.process_flow = None
        self._load_current_flow()
    
    def _load_or_create_config(self) -> Dict:
        """Load sync configuration or create default"""
        default_config = {
            "version": "1.0",
            "sync_strategy": "yaml_primary",  # yaml_primary, json_primary, or manual
            "auto_backup": True,
            "backup_retention_days": 30,
            "validation_on_sync": True,
            "files": {
                "machine_yaml": "process_flow.yaml",
                "machine_json": "process_flow.json", 
                "human_md": "process_flow_human.md",
                "visual_xml": "process_flow_visual.drawio",
                "hash_store": ".process_sync_hashes.json",
                "sync_log": "process_sync.log"
            },
            "watch_patterns": ["*.yaml", "*.json", "*.md"],
            "ignore_patterns": [".*", "__pycache__", "*.pyc"],
            "notification_webhook": None,
            "git_integration": {
                "enabled": False,
                "auto_commit": False,
                "commit_message_template": "Auto-sync process documentation - {timestamp}"
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults to handle new fields
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            except Exception as e:
                print(f"⚠️  Warning: Could not load config ({e}), using defaults")
        
        # Save default config
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        self.base_dir.mkdir(exist_ok=True)
        
        # Create backup directory
        backup_dir = self.base_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        # Create logs directory
        logs_dir = self.base_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
    
    def _load_current_flow(self):
        """Load the current process flow from primary source"""
        primary_source = self.config['sync_strategy']
        
        if primary_source == "yaml_primary" and self.files['machine_yaml'].exists():
            try:
                with open(self.files['machine_yaml'], 'r', encoding='utf-8') as f:
                    content = f.read()
                self.process_flow = self.framework.load_machine_readable(content, "yaml")
                self.framework.process_flow = self.process_flow
            except Exception as e:
                self._log(f"❌ Error loading YAML: {e}")
        
        elif primary_source == "json_primary" and self.files['machine_json'].exists():
            try:
                with open(self.files['machine_json'], 'r', encoding='utf-8') as f:
                    content = f.read()
                self.process_flow = self.framework.load_machine_readable(content, "json")
                self.framework.process_flow = self.process_flow
            except Exception as e:
                self._log(f"❌ Error loading JSON: {e}")
    
    def compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file content"""
        if not file_path.exists():
            return ""
        
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""
    
    def load_stored_hashes(self) -> Dict[str, str]:
        """Load previously stored file hashes"""
        if not self.files['hash_store'].exists():
            return {}
        
        try:
            with open(self.files['hash_store'], 'r') as f:
                return json.load(f)
        except Exception as e:
            self._log(f"Warning: Could not load hash store: {e}")
            return {}
    
    def save_hashes(self, hashes: Dict[str, str]):
        """Save current file hashes"""
        try:
            with open(self.files['hash_store'], 'w') as f:
                json.dump({
                    **hashes,
                    "last_sync": datetime.now().isoformat(),
                    "sync_count": hashes.get("sync_count", 0) + 1
                }, f, indent=2)
        except Exception as e:
            self._log(f"Warning: Could not save hashes: {e}")
    
    def _log(self, message: str, level: str = "INFO"):
        """Log message to file and console"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}"
        
        print(log_entry)
        
        try:
            with open(self.files['sync_log'], 'a', encoding='utf-8') as f:
                f.write(log_entry + "\n")
        except Exception:
            pass  # Don't fail on logging errors
    
    def create_backup(self, file_path: Path, reason: str = "sync"):
        """Create backup of file before modification"""
        if not self.config['auto_backup'] or not file_path.exists():
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}_{reason}{file_path.suffix}"
        backup_path = self.base_dir / "backups" / backup_name
        
        try:
            shutil.copy2(file_path, backup_path)
            self._log(f"📦 Backup created: {backup_name}")
        except Exception as e:
            self._log(f"⚠️  Backup failed for {file_path.name}: {e}", "WARNING")
    
    def cleanup_old_backups(self):
        """Remove backups older than retention period"""
        if not self.config['auto_backup']:
            return
        
        backup_dir = self.base_dir / "backups"
        if not backup_dir.exists():
            return
        
        retention_days = self.config['backup_retention_days']
        cutoff_time = time.time() - (retention_days * 24 * 60 * 60)
        
        cleaned_count = 0
        for backup_file in backup_dir.glob("*"):
            if backup_file.stat().st_mtime < cutoff_time:
                try:
                    backup_file.unlink()
                    cleaned_count += 1
                except Exception as e:
                    self._log(f"Could not remove old backup {backup_file.name}: {e}", "WARNING")
        
        if cleaned_count > 0:
            self._log(f"🧹 Cleaned up {cleaned_count} old backup files")
    
    def sync_machine_to_others(self, source_format: str = "yaml"):
        """Generate all other formats from machine-readable source"""
        if not self.process_flow:
            self._log("❌ No process flow loaded - cannot sync")
            return False
        
        try:
            self._log(f"🔄 Syncing from {source_format} to all other formats...")
            
            # Validate before generating
            if self.config['validation_on_sync']:
                errors = self.framework.validate_flow(self.process_flow)
                if errors:
                    self._log("❌ Validation errors found:")
                    for error in errors:
                        self._log(f"   • {error}")
                    return False
            
            # Create backups
            for file_type in ['machine_yaml', 'machine_json', 'human_md', 'visual_xml']:
                self.create_backup(self.files[file_type], "sync")
            
            # Generate machine-readable formats
            if source_format != "yaml":
                yaml_content = self.framework.save_machine_readable(self.process_flow, "yaml")
                with open(self.files['machine_yaml'], 'w', encoding='utf-8') as f:
                    f.write(yaml_content)
                self._log(f"✅ Generated {self.files['machine_yaml'].name}")
            
            if source_format != "json":
                json_content = self.framework.save_machine_readable(self.process_flow, "json")
                with open(self.files['machine_json'], 'w', encoding='utf-8') as f:
                    f.write(json_content)
                self._log(f"✅ Generated {self.files['machine_json'].name}")
            
            # Generate human-readable
            human_content = self.framework.generate_human_readable(self.process_flow)
            
            # Add generation metadata
            header = f"<!-- AUTO-GENERATED from {source_format} on {datetime.now().isoformat()} -->\n"
            header += f"<!-- DO NOT EDIT MANUALLY - Edit the {source_format.upper()} file instead -->\n"
            header += f"<!-- Sync strategy: {self.config['sync_strategy']} -->\n\n"
            
            with open(self.files['human_md'], 'w', encoding='utf-8') as f:
                f.write(header + human_content)
            self._log(f"✅ Generated {self.files['human_md'].name}")
            
            # Generate visual diagram
            xml_content = self.framework.generate_drawio_xml(self.process_flow)
            
            # Add XML metadata
            xml_header = f"<!-- AUTO-GENERATED from {source_format} on {datetime.now().isoformat()} -->\n"
            xml_header += f"<!-- Sync strategy: {self.config['sync_strategy']} -->\n"
            
            with open(self.files['visual_xml'], 'w', encoding='utf-8') as f:
                f.write(xml_header + xml_content)
            self._log(f"✅ Generated {self.files['visual_xml'].name}")
            
            return True
            
        except Exception as e:
            self._log(f"❌ Error during sync: {e}", "ERROR")
            return False
    
    def check_and_sync(self) -> Tuple[bool, List[str]]:
        """Check which files changed and sync accordingly"""
        current_hashes = {
            'machine_yaml': self.compute_file_hash(self.files['machine_yaml']),
            'machine_json': self.compute_file_hash(self.files['machine_json']),
            'human_md': self.compute_file_hash(self.files['human_md']),
            'visual_xml': self.compute_file_hash(self.files['visual_xml'])
        }
        
        stored_hashes = self.load_stored_hashes()
        changes = []
        
        # Detect changes
        for file_type, current_hash in current_hashes.items():
            stored_hash = stored_hashes.get(file_type, '')
            if current_hash != stored_hash and current_hash != '':  # File exists and changed
                changes.append(file_type)
        
        if not changes:
            self._log("ℹ️  No changes detected")
            return True, []
        
        self._log(f"🔍 Changes detected in: {', '.join(changes)}")
        
        # Determine sync strategy
        strategy = self.config['sync_strategy']
        primary_changed = False
        
        if strategy == "yaml_primary":
            primary_changed = 'machine_yaml' in changes
            primary_format = "yaml"
        elif strategy == "json_primary":
            primary_changed = 'machine_json' in changes
            primary_format = "json"
        else:  # manual strategy
            self._log("⚠️  Manual sync strategy - please resolve conflicts manually")
            return False, changes
        
        # Handle conflicts
        if len(changes) > 1 and primary_changed:
            self._log("⚠️  Multiple files changed including primary source")
            self._log("   Regenerating all from primary source...")
            
            # Reload from primary
            self._load_current_flow()
            if self.process_flow:
                success = self.sync_machine_to_others(primary_format)
                if success:
                    current_hashes = {
                        'machine_yaml': self.compute_file_hash(self.files['machine_yaml']),
                        'machine_json': self.compute_file_hash(self.files['machine_json']),
                        'human_md': self.compute_file_hash(self.files['human_md']),
                        'visual_xml': self.compute_file_hash(self.files['visual_xml'])
                    }
        
        elif len(changes) > 1 and not primary_changed:
            self._log("⚠️  Multiple secondary files changed - regenerating from primary")
            success = self.sync_machine_to_others(primary_format)
            if success:
                current_hashes = {
                    'machine_yaml': self.compute_file_hash(self.files['machine_yaml']),
                    'machine_json': self.compute_file_hash(self.files['machine_json']),
                    'human_md': self.compute_file_hash(self.files['human_md']),
                    'visual_xml': self.compute_file_hash(self.files['visual_xml'])
                }
        
        elif primary_changed:
            self._log(f"📝 Primary source ({primary_format}) changed - syncing all formats")
            
            # Reload from primary
            self._load_current_flow()
            if self.process_flow:
                success = self.sync_machine_to_others(primary_format)
                if success:
                    current_hashes = {
                        'machine_yaml': self.compute_file_hash(self.files['machine_yaml']),
                        'machine_json': self.compute_file_hash(self.files['machine_json']),
                        'human_md': self.compute_file_hash(self.files['human_md']),
                        'visual_xml': self.compute_file_hash(self.files['visual_xml'])
                    }
        
        else:
            self._log("ℹ️  Secondary files changed - recommend editing primary source instead")
        
        # Save updated hashes
        self.save_hashes(current_hashes)
        return True, changes
    
    def create_initial_files(self):
        """Create initial process flow files if they don't exist"""
        if not any(self.files[key].exists() for key in ['machine_yaml', 'machine_json']):
            self._log("🆕 Creating initial process flow files...")
            
            # Create sample process flow using framework
            flow = self.framework.create_trading_system_flow()
            self.process_flow = flow
            self.framework.process_flow = flow
            
            # Save initial files
            self.sync_machine_to_others("yaml")
            self._log("✅ Initial files created successfully")
        else:
            self._log("ℹ️  Process flow files already exist")
    
    def watch_files(self):
        """Watch files for changes and auto-sync"""
        class SyncHandler(FileSystemEventHandler):
            def __init__(self, sync_manager):
                self.sync = sync_manager
                self.last_sync = 0
                self.debounce_seconds = 2  # Prevent rapid-fire syncs
                super().__init__()
            
            def on_modified(self, event):
                if event.is_directory:
                    return
                
                current_time = time.time()
                if current_time - self.last_sync < self.debounce_seconds:
                    return  # Debounce rapid changes
                
                file_path = Path(event.src_path)
                
                # Check if this is a file we care about
                if file_path.name in [f.name for f in self.sync.files.values()]:
                    self.sync._log(f"🔍 File changed: {file_path.name}")
                    self.sync.check_and_sync()
                    self.last_sync = current_time
        
        event_handler = SyncHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(self.base_dir), recursive=False)
        
        observer.start()
        self._log(f"👁️  Watching {self.base_dir} for changes...")
        self._log("   Press Ctrl+C to stop")
        
        try:
            while True:
                time.sleep(1)
                # Periodic cleanup
                if time.time() % 3600 < 1:  # Every hour
                    self.cleanup_old_backups()
        except KeyboardInterrupt:
            observer.stop()
            self._log("🛑 Stopped watching")
        
        observer.join()
    
    def generate_status_report(self) -> Dict:
        """Generate comprehensive sync status report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "config": self.config,
            "files": {},
            "sync_health": {
                "all_files_exist": True,
                "hashes_match": True,
                "validation_passed": False
            }
        }
        
        # File status
        for file_type, file_path in self.files.items():
            if file_type == 'hash_store' or file_type == 'sync_log':
                continue
            
            report["files"][file_type] = {
                "exists": file_path.exists(),
                "size": file_path.stat().st_size if file_path.exists() else 0,
                "modified": file_path.stat().st_mtime if file_path.exists() else 0,
                "hash": self.compute_file_hash(file_path)
            }
            
            if not file_path.exists():
                report["sync_health"]["all_files_exist"] = False
        
        # Validation
        if self.process_flow:
            errors = self.framework.validate_flow(self.process_flow)
            report["sync_health"]["validation_passed"] = len(errors) == 0
            report["validation_errors"] = errors
            
            # Process flow stats
            sync_report = self.framework.generate_sync_report(self.process_flow)
            report["process_stats"] = sync_report
        
        return report
    
    def force_rebuild_all(self):
        """Force rebuild all formats from primary source"""
        self._log("🔄 Force rebuilding all formats from primary source...")
        
        # Backup everything first
        for file_type in ['machine_yaml', 'machine_json', 'human_md', 'visual_xml']:
            self.create_backup(self.files[file_type], "force_rebuild")
        
        # Reload and sync
        self._load_current_flow()
        if self.process_flow:
            primary_format = "yaml" if self.config['sync_strategy'] == "yaml_primary" else "json"
            success = self.sync_machine_to_others(primary_format)
            
            if success:
                self._log("✅ Force rebuild completed successfully")
                
                # Update hashes
                current_hashes = {
                    'machine_yaml': self.compute_file_hash(self.files['machine_yaml']),
                    'machine_json': self.compute_file_hash(self.files['machine_json']),
                    'human_md': self.compute_file_hash(self.files['human_md']),
                    'visual_xml': self.compute_file_hash(self.files['visual_xml'])
                }
                self.save_hashes(current_hashes)
            else:
                self._log("❌ Force rebuild failed")
        else:
            self._log("❌ Could not load process flow for rebuild")

def main():
    """Command-line interface for process synchronization"""
    parser = argparse.ArgumentParser(description="Multi-format process synchronization manager")
    parser.add_argument("--dir", "-d", default=".", help="Base directory for files")
    parser.add_argument("--config", "-c", default="sync_config.json", help="Configuration file")
    
    # Actions
    parser.add_argument("--init", action="store_true", help="Create initial files and config")
    parser.add_argument("--sync", action="store_true", help="Check and sync once")
    parser.add_argument("--watch", action="store_true", help="Watch for changes (auto-sync)")
    parser.add_argument("--force-rebuild", action="store_true", help="Force rebuild all formats")
    parser.add_argument("--status", action="store_true", help="Show sync status report")
    parser.add_argument("--cleanup", action="store_true", help="Clean up old backups")
    
    args = parser.parse_args()
    
    sync_manager = ProcessSyncManager(args.dir, args.config)
    
    if args.init:
        sync_manager.create_initial_files()
    elif args.force_rebuild:
        sync_manager.force_rebuild_all()
    elif args.sync:
        success, changes = sync_manager.check_and_sync()
        if success:
            print(f"✅ Sync completed. Changes: {changes if changes else 'none'}")
        else:
            print("❌ Sync failed or requires manual intervention")
    elif args.watch:
        sync_manager.watch_files()
    elif args.status:
        report = sync_manager.generate_status_report()
        print(json.dumps(report, indent=2))
    elif args.cleanup:
        sync_manager.cleanup_old_backups()
    else:
        print("🚀 Multi-Format Process Synchronization Manager")
        print("Available commands:")
        print("  --init                 Create initial files and configuration")
        print("  --sync                 Check and sync all formats once")
        print("  --watch                Watch for changes (auto-sync mode)")
        print("  --force-rebuild        Force rebuild all from primary source")
        print("  --status               Show detailed sync status report")
        print("  --cleanup              Clean up old backup files")
        print("\nRecommended workflow:")
        print("  1. Run --init to create initial files")
        print("  2. Edit the primary source file (YAML or JSON)")
        print("  3. Run --sync or --watch to keep all formats synchronized")
        print("  4. Use --status to monitor sync health")

if __name__ == "__main__":
    main()