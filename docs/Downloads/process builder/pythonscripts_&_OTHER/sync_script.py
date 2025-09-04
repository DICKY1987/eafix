#!/usr/bin/env python3
"""
Process Flow Synchronization Script
Keeps machine-readable and human-readable versions in perfect sync
"""

import os
import sys
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Import the ProcessFlowManager from the previous artifact
# In practice, you'd import from a separate module
from process_flow_manager import ProcessFlowManager

class ProcessFlowSynchronizer:
    """Maintains synchronization between machine and human readable formats"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.manager = ProcessFlowManager()
        
        # File paths
        self.machine_file = self.base_dir / "reentry_process_flow.yaml"
        self.human_file = self.base_dir / "reentry_process_flow_human.md"
        self.hash_file = self.base_dir / ".process_flow_sync.hash"
        
        # Ensure directory exists
        self.base_dir.mkdir(exist_ok=True)
    
    def compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file content"""
        if not file_path.exists():
            return ""
        
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def load_stored_hash(self) -> dict:
        """Load previously stored file hashes"""
        if not self.hash_file.exists():
            return {}
        
        try:
            with open(self.hash_file, 'r') as f:
                lines = f.readlines()
                hashes = {}
                for line in lines:
                    if ':' in line:
                        file_name, hash_value = line.strip().split(':', 1)
                        hashes[file_name] = hash_value
                return hashes
        except Exception as e:
            print(f"Warning: Could not load hash file: {e}")
            return {}
    
    def save_hashes(self, hashes: dict):
        """Save current file hashes"""
        with open(self.hash_file, 'w') as f:
            for file_name, hash_value in hashes.items():
                f.write(f"{file_name}:{hash_value}\n")
    
    def sync_machine_to_human(self):
        """Generate human-readable from machine-readable (YAML/JSON source)"""
        try:
            print("🔄 Syncing machine → human...")
            
            # Load machine-readable format
            with open(self.machine_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            flow = self.manager.load_machine_readable(content, "yaml")
            
            # Validate before generating
            errors = self.manager.validate_flow(flow)
            if errors:
                print("❌ Validation errors found:")
                for error in errors:
                    print(f"   • {error}")
                return False
            
            # Generate human-readable
            human_content = self.manager.generate_human_readable(flow)
            
            # Add generation timestamp
            header = f"<!-- AUTO-GENERATED from {self.machine_file.name} on {datetime.now().isoformat()} -->\n"
            header += "<!-- DO NOT EDIT MANUALLY - Edit the YAML file instead -->\n\n"
            
            with open(self.human_file, 'w', encoding='utf-8') as f:
                f.write(header + human_content)
            
            print(f"✅ Generated {self.human_file.name}")
            return True
            
        except Exception as e:
            print(f"❌ Error syncing machine → human: {e}")
            return False
    
    def sync_human_to_machine(self):
        """Parse human-readable back to machine format (advanced parsing)"""
        print("🔄 Syncing human → machine...")
        print("⚠️  This requires advanced parsing - recommend editing YAML directly")
        
        # This would require sophisticated parsing of the human format
        # For now, we recommend YAML as the source of truth
        # But you could implement parsers for specific sections
        
        return False
    
    def check_and_sync(self):
        """Check which files changed and sync accordingly"""
        current_hashes = {
            'machine': self.compute_file_hash(self.machine_file),
            'human': self.compute_file_hash(self.human_file)
        }
        
        stored_hashes = self.load_stored_hash()
        
        machine_changed = current_hashes['machine'] != stored_hashes.get('machine', '')
        human_changed = current_hashes['human'] != stored_hashes.get('human', '')
        
        if machine_changed and human_changed:
            print("⚠️  Both files changed! Manual resolution required.")
            print("   Recommend: keep YAML as source of truth, regenerate human doc")
            response = input("Regenerate human doc from YAML? [y/N]: ")
            if response.lower() == 'y':
                if self.sync_machine_to_human():
                    current_hashes['human'] = self.compute_file_hash(self.human_file)
        
        elif machine_changed:
            print("📝 Machine-readable file changed")
            if self.sync_machine_to_human():
                current_hashes['human'] = self.compute_file_hash(self.human_file)
        
        elif human_changed:
            print("📝 Human-readable file changed")
            print("   Recommended: Edit YAML file instead for better control")
            # Could implement human→machine parsing here
        
        # Save current hashes
        self.save_hashes(current_hashes)
        
        return True
    
    def create_initial_files(self):
        """Create initial process flow files if they don't exist"""
        if not self.machine_file.exists():
            print("🆕 Creating initial machine-readable file...")
            
            # Create sample process flow
            flow = self.manager.create_reentry_system_flow()
            yaml_content = self.manager.save_machine_readable(flow, "yaml")
            
            with open(self.machine_file, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            
            print(f"✅ Created {self.machine_file.name}")
        
        # Always regenerate human file from machine file
        self.sync_machine_to_human()
    
    def watch_files(self):
        """Watch files for changes and auto-sync"""
        class SyncHandler(FileSystemEventHandler):
            def __init__(self, synchronizer):
                self.sync = synchronizer
                super().__init__()
            
            def on_modified(self, event):
                if event.is_directory:
                    return
                
                file_path = Path(event.src_path)
                if file_path.name in [self.sync.machine_file.name, self.sync.human_file.name]:
                    print(f"\n📁 File changed: {file_path.name}")
                    self.sync.check_and_sync()
        
        event_handler = SyncHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(self.base_dir), recursive=False)
        
        observer.start()
        print(f"👁️  Watching {self.base_dir} for changes...")
        print("   Press Ctrl+C to stop")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print("\n🛑 Stopped watching")
        
        observer.join()

def main():
    """Command-line interface for process flow synchronization"""
    parser = argparse.ArgumentParser(description="Synchronize process flow documents")
    parser.add_argument("--dir", "-d", default=".", help="Base directory for files")
    parser.add_argument("--init", action="store_true", help="Create initial files")
    parser.add_argument("--sync", action="store_true", help="Check and sync once")
    parser.add_argument("--watch", action="store_true", help="Watch for changes")
    parser.add_argument("--machine-to-human", action="store_true", help="Force machine → human sync")
    
    args = parser.parse_args()
    
    synchronizer = ProcessFlowSynchronizer(args.dir)
    
    if args.init:
        synchronizer.create_initial_files()
    elif args.machine_to_human:
        synchronizer.sync_machine_to_human()
    elif args.sync:
        synchronizer.check_and_sync()
    elif args.watch:
        synchronizer.watch_files()
    else:
        print("🚀 Process Flow Synchronizer")
        print("Available commands:")
        print("  --init                 Create initial files")
        print("  --sync                 Check and sync once")
        print("  --watch                Watch for changes (auto-sync)")
        print("  --machine-to-human     Force regenerate human doc")
        print("\nRecommended workflow:")
        print("  1. Run --init to create initial files")
        print("  2. Edit the YAML file for changes")
        print("  3. Run --sync or --watch to keep in sync")

if __name__ == "__main__":
    import time
    main()

# Example usage functions for programmatic editing
def example_add_validation_step():
    """Example: Add a new validation step programmatically"""
    manager = ProcessFlowManager()
    
    # Load existing flow
    with open("reentry_process_flow.yaml", 'r') as f:
        flow = manager.load_machine_readable(f.read(), "yaml")
    
    # Add new step
    from process_flow_manager import ProcessStep
    new_step = ProcessStep(
        step_id="6.009",
        actor="EA",
        description="Validate market hours and trading session status.",
        dependencies=["6.008"],
        goto_targets=["REJECT_SET"],
        conditions=["If market closed"],
        sla_ms=10,
        validation_rules=["Market open", "Session active"],
        error_codes=["E1060"],
        notes="Prevent trading outside market hours"
    )
    
    # Find and update the EA validation section
    for section in flow.sections:
        if section.section_id == "6.000":
            section.steps.append(new_step)
            section.steps.sort(key=lambda s: s.step_id)
            break
    
    # Save back
    yaml_content = manager.save_machine_readable(flow, "yaml")
    with open("reentry_process_flow.yaml", 'w') as f:
        f.write(yaml_content)
    
    print("✅ Added validation step 6.009")

def example_update_sla():
    """Example: Update SLA targets across multiple steps"""
    manager = ProcessFlowManager()
    
    # Load existing flow
    with open("reentry_process_flow.yaml", 'r') as f:
        flow = manager.load_machine_readable(f.read(), "yaml")
    
    # Update all file operation SLAs
    for section in flow.sections:
        for step in section.steps:
            if any("WRITE" in op or "READ" in op for op in step.file_operations):
                step.sla_ms = min(step.sla_ms or 1000, 300)  # Cap at 300ms
    
    # Save back
    yaml_content = manager.save_machine_readable(flow, "yaml")
    with open("reentry_process_flow.yaml", 'w') as f:
        f.write(yaml_content)
    
    print("✅ Updated file operation SLAs")
