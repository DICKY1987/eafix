#!/usr/bin/env python3
"""
Process Documentation CLI Tool
Unified command-line interface for the atomic process framework
"""

import os
import sys
import json
import yaml
import argparse
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

# Import our framework components
try:
    from atomic_process_framework import AtomicProcessFramework, ProcessFlow
    from process_sync_manager import ProcessSyncManager
    from process_analysis_tools import ProcessAnalyzer
    from trading_system_demo import TradingSystemDocumentationDemo
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all framework files are in the same directory")
    sys.exit(1)

class ProcessCLI:
    """Unified CLI for process documentation framework"""
    
    def __init__(self):
        self.framework = None
        self.sync_manager = None
        self.analyzer = None
        self.current_dir = Path.cwd()
    
    def setup_project(self, project_dir: str, template: str = "basic"):
        """Initialize a new process documentation project"""
        
        project_path = Path(project_dir)
        project_path.mkdir(exist_ok=True)
        
        print(f"🚀 Setting up process documentation project in {project_path}")
        
        # Copy framework files
        framework_files = [
            "atomic_process_framework.py",
            "process_sync_manager.py", 
            "process_analysis_tools.py"
        ]
        
        current_dir = Path(__file__).parent
        for file_name in framework_files:
            source = current_dir / file_name
            target = project_path / file_name
            if source.exists():
                shutil.copy2(source, target)
                print(f"   ✅ Copied {file_name}")
            else:
                print(f"   ⚠️  Warning: {file_name} not found")
        
        # Initialize sync manager
        self.sync_manager = ProcessSyncManager(str(project_path))
        
        # Create template-specific content
        if template == "trading":
            self._create_trading_template(project_path)
        else:
            self._create_basic_template(project_path)
        
        # Initialize git repository if requested
        self._init_git_repo(project_path)
        
        print(f"✅ Project initialized successfully!")
        print(f"📁 Project directory: {project_path.absolute()}")
        print("\n🔧 Next steps:")
        print(f"   cd {project_dir}")
        print("   process-doc sync --watch  # Start auto-sync")
        print("   process-doc edit          # Edit the process")
        
    def _create_basic_template(self, project_path: Path):
        """Create basic template structure"""
        
        # Create basic config
        config = {
            "version": "1.0",
            "sync_strategy": "yaml_primary",
            "auto_backup": True,
            "validation_on_sync": True,
            "files": {
                "machine_yaml": "process_flow.yaml",
                "machine_json": "process_flow.json",
                "human_md": "process_flow.md",
                "visual_xml": "process_flow.drawio"
            }
        }
        
        with open(project_path / "sync_config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        # Create basic process template
        basic_template = {
            "title": "Basic Process Flow",
            "version": "1.0",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "id_conventions": "Format: SECTION.STEP (e.g., 1.001)",
            "legend": "Each step is atomic (one action)",
            "sections": [
                {
                    "section_id": "1.000",
                    "title": "Process Section 1",
                    "description": "First section of the process",
                    "actors": ["ACTOR1"],
                    "transport": "API",
                    "steps": [
                        {
                            "step_id": "1.001",
                            "actor": "ACTOR1",
                            "description": "First step in the process",
                            "dependencies": [],
                            "goto_targets": [],
                            "conditions": [],
                            "sla_ms": 100,
                            "subprocess_calls": [],
                            "input_variables": ["input1"],
                            "output_variables": ["output1"],
                            "file_operations": [],
                            "validation_rules": [],
                            "error_codes": [],
                            "notes": "This is a sample step"
                        }
                    ]
                }
            ],
            "subprocesses": [],
            "file_paths": {},
            "metadata": {}
        }
        
        with open(project_path / "process_flow.yaml", "w") as f:
            yaml.dump(basic_template, f, default_flow_style=False, sort_keys=False)
        
        print("   ✅ Created basic process template")
    
    def _create_trading_template(self, project_path: Path):
        """Create trading system template"""
        
        demo = TradingSystemDocumentationDemo(str(project_path))
        flow = demo.create_complete_trading_flow()
        
        # Save the trading system template
        framework = AtomicProcessFramework(str(project_path))
        yaml_content = framework.save_machine_readable(flow, "yaml")
        
        with open(project_path / "process_flow.yaml", "w") as f:
            f.write(yaml_content)
        
        print("   ✅ Created trading system template")
    
    def _init_git_repo(self, project_path: Path):
        """Initialize git repository with appropriate .gitignore"""
        
        try:
            # Initialize git repo
            subprocess.run(["git", "init"], cwd=project_path, capture_output=True)
            
            # Create .gitignore
            gitignore_content = """# Process Documentation Framework
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/

# Backup files
backups/
*.bak
*.backup

# Logs
logs/
*.log

# Analysis outputs
analysis_reports/
*.png
*.pdf

# Sync files
.process_sync_hashes.json
.trading_sync_hashes.json

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db
"""
            
            with open(project_path / ".gitignore", "w") as f:
                f.write(gitignore_content)
            
            print("   ✅ Initialized git repository")
            
        except subprocess.CalledProcessError:
            print("   ⚠️  Git not available - skipping repository initialization")
    
    def sync_project(self, project_dir: str = ".", watch: bool = False, force: bool = False):
        """Synchronize process documentation formats"""
        
        project_path = Path(project_dir).resolve()
        
        if not (project_path / "sync_config.json").exists():
            print("❌ No sync configuration found. Run 'process-doc init' first.")
            return
        
        self.sync_manager = ProcessSyncManager(str(project_path))
        
        if force:
            print("🔄 Force rebuilding all formats...")
            self.sync_manager.force_rebuild_all()
        elif watch:
            print("👁️  Starting watch mode...")
            self.sync_manager.watch_files()
        else:
            print("🔄 Checking for changes...")
            success, changes = self.sync_manager.check_and_sync()
            if success:
                if changes:
                    print(f"✅ Sync completed. Changes detected in: {', '.join(changes)}")
                else:
                    print("✅ No changes detected - all files in sync")
            else:
                print("❌ Sync failed or requires manual intervention")
    
    def analyze_project(self, project_dir: str = ".", output_dir: str = "analysis"):
        """Analyze process for optimization opportunities"""
        
        project_path = Path(project_dir).resolve()
        yaml_file = project_path / "process_flow.yaml"
        
        if not yaml_file.exists():
            print("❌ No process_flow.yaml found. Run 'process-doc init' first.")
            return
        
        print("🔍 Analyzing process flow...")
        
        analyzer = ProcessAnalyzer()
        flow = analyzer.load_process_flow(str(yaml_file), "yaml")
        
        # Generate comprehensive analysis
        report = analyzer.generate_comprehensive_report(flow, str(project_path / output_dir))
        
        # Print summary
        print("\n📊 Analysis Summary:")
        print(f"   • Total Steps: {report['complexity_metrics']['total_steps']}")
        print(f"   • Total Time: {report['performance_metrics']['total_estimated_time_ms']:,} ms")
        print(f"   • Quality Score: {report['quality_metrics']['overall_quality_score']:.1%}")
        print(f"   • Recommendations: {len(report['recommendations'])}")
        
        if report['recommendations']:
            print("\n🎯 Top Recommendations:")
            for i, rec in enumerate(report['recommendations'][:3], 1):
                print(f"   {i}. {rec['title']} ({rec['priority']} priority)")
        
        print(f"\n📁 Full report available in: {project_path / output_dir}")
    
    def edit_process(self, project_dir: str = ".", editor: Optional[str] = None):
        """Open process file in editor"""
        
        project_path = Path(project_dir).resolve()
        yaml_file = project_path / "process_flow.yaml"
        
        if not yaml_file.exists():
            print("❌ No process_flow.yaml found. Run 'process-doc init' first.")
            return
        
        # Determine editor
        if not editor:
            editor = os.environ.get('EDITOR', 'notepad' if os.name == 'nt' else 'nano')
        
        try:
            subprocess.run([editor, str(yaml_file)])
        except FileNotFoundError:
            print(f"❌ Editor '{editor}' not found")
            print("Available alternatives:")
            if os.name == 'nt':
                print("   notepad, code, vim")
            else:
                print("   nano, vim, code, emacs")
    
    def validate_project(self, project_dir: str = "."):
        """Validate process flow for errors"""
        
        project_path = Path(project_dir).resolve()
        yaml_file = project_path / "process_flow.yaml"
        
        if not yaml_file.exists():
            print("❌ No process_flow.yaml found. Run 'process-doc init' first.")
            return
        
        print("🔍 Validating process flow...")
        
        framework = AtomicProcessFramework(str(project_path))
        
        try:
            with open(yaml_file, 'r') as f:
                flow = framework.load_machine_readable(f.read(), "yaml")
            
            errors = framework.validate_flow(flow)
            
            if errors:
                print("❌ Validation errors found:")
                for error in errors:
                    print(f"   • {error}")
                return False
            else:
                print("✅ Process flow validation passed!")
                return True
                
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return False
    
    def status(self, project_dir: str = "."):
        """Show project status"""
        
        project_path = Path(project_dir).resolve()
        
        print(f"📊 Process Documentation Project Status")
        print(f"📁 Project: {project_path}")
        print()
        
        # Check for required files
        required_files = {
            "sync_config.json": "Sync configuration",
            "process_flow.yaml": "Main process file (YAML)",
            "process_flow.json": "Process file (JSON)",
            "process_flow.md": "Human-readable documentation",
            "process_flow.drawio": "Visual diagram"
        }
        
        for filename, description in required_files.items():
            file_path = project_path / filename
            if file_path.exists():
                size = file_path.stat().st_size
                modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                print(f"   ✅ {description}: {size:,} bytes, modified {modified.strftime('%Y-%m-%d %H:%M')}")
            else:
                print(f"   ❌ {description}: Missing")
        
        # Check sync status
        if (project_path / "sync_config.json").exists():
            sync_manager = ProcessSyncManager(str(project_path))
            status_report = sync_manager.generate_status_report()
            
            print(f"\n🔄 Sync Status:")
            print(f"   • All files exist: {'✅' if status_report['sync_health']['all_files_exist'] else '❌'}")
            print(f"   • Validation passed: {'✅' if status_report['sync_health']['validation_passed'] else '❌'}")
        
        # Check for analysis reports
        analysis_dir = project_path / "analysis_reports"
        if analysis_dir.exists():
            print(f"\n📈 Analysis Reports:")
            for report_file in analysis_dir.glob("*"):
                if report_file.is_file():
                    print(f"   • {report_file.name}")
    
    def export_project(self, project_dir: str = ".", format_type: str = "all", output_file: Optional[str] = None):
        """Export process documentation"""
        
        project_path = Path(project_dir).resolve()
        yaml_file = project_path / "process_flow.yaml"
        
        if not yaml_file.exists():
            print("❌ No process_flow.yaml found. Run 'process-doc init' first.")
            return
        
        framework = AtomicProcessFramework(str(project_path))
        
        with open(yaml_file, 'r') as f:
            flow = framework.load_machine_readable(f.read(), "yaml")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == "pdf":
            # Generate comprehensive markdown and convert to PDF
            print("📄 Exporting to PDF...")
            # This would require pandoc or similar
            print("⚠️  PDF export requires pandoc - please install pandoc first")
            
        elif format_type == "html":
            # Generate HTML version
            print("🌐 Exporting to HTML...")
            html_content = self._generate_html_export(flow)
            output_path = output_file or f"process_export_{timestamp}.html"
            with open(project_path / output_path, 'w') as f:
                f.write(html_content)
            print(f"✅ HTML export saved: {output_path}")
            
        elif format_type == "zip":
            # Create ZIP archive of all files
            print("📦 Creating ZIP archive...")
            import zipfile
            
            output_path = output_file or f"process_export_{timestamp}.zip"
            
            with zipfile.ZipFile(project_path / output_path, 'w') as zipf:
                for file_path in project_path.glob("*"):
                    if file_path.is_file() and not file_path.name.startswith('.'):
                        zipf.write(file_path, file_path.name)
            
            print(f"✅ ZIP archive created: {output_path}")
            
        else:  # format_type == "all"
            print("📤 Exporting all formats...")
            self.sync_project(project_dir, force=True)
            print("✅ All formats exported and synchronized")
    
    def _generate_html_export(self, flow: ProcessFlow) -> str:
        """Generate HTML export of process documentation"""
        
        framework = AtomicProcessFramework()
        md_content = framework.generate_human_readable(flow)
        
        # Convert markdown to HTML (basic conversion)
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{flow.title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1, h2, h3 {{ color: #2563eb; }}
        code {{ background: #f3f4f6; padding: 2px 4px; border-radius: 3px; }}
        pre {{ background: #f9fafb; padding: 16px; border-radius: 6px; overflow-x: auto; }}
        .step {{ background: #fef7cd; padding: 12px; margin: 8px 0; border-radius: 6px; border-left: 4px solid #f59e0b; }}
        .subprocess {{ background: #e0f2fe; padding: 8px; margin: 4px 0; border-radius: 4px; }}
    </style>
</head>
<body>
    <div id="content">
        {self._markdown_to_html(md_content)}
    </div>
    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; text-align: center;">
        Generated by Process Documentation Framework on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </footer>
</body>
</html>"""
        
        return html_content
    
    def _markdown_to_html(self, md_content: str) -> str:
        """Basic markdown to HTML conversion"""
        
        # This is a very basic conversion - for production use, consider using a proper markdown library
        html = md_content
        
        # Headers
        html = html.replace('# ', '<h1>').replace('\n## ', '</h1>\n<h2>')
        html = html.replace('\n### ', '</h2>\n<h3>').replace('\n#### ', '</h3>\n<h4>')
        
        # Bold text
        html = html.replace('**', '<strong>').replace('**', '</strong>')
        
        # Lists
        lines = html.split('\n')
        in_list = False
        result_lines = []
        
        for line in lines:
            if line.strip().startswith('- '):
                if not in_list:
                    result_lines.append('<ul>')
                    in_list = True
                result_lines.append(f'<li>{line.strip()[2:]}</li>')
            else:
                if in_list:
                    result_lines.append('</ul>')
                    in_list = False
                result_lines.append(line)
        
        if in_list:
            result_lines.append('</ul>')
        
        html = '\n'.join(result_lines)
        
        # Paragraphs
        html = html.replace('\n\n', '</p>\n<p>')
        html = '<p>' + html + '</p>'
        
        return html

def main():
    """Main CLI entry point"""
    
    parser = argparse.ArgumentParser(
        description="Process Documentation Framework CLI",
        prog="process-doc"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize new project")
    init_parser.add_argument("project_dir", help="Project directory name")
    init_parser.add_argument("--template", choices=["basic", "trading"], default="basic",
                           help="Project template")
    
    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Synchronize formats")
    sync_parser.add_argument("--dir", default=".", help="Project directory")
    sync_parser.add_argument("--watch", action="store_true", help="Watch for changes")
    sync_parser.add_argument("--force", action="store_true", help="Force rebuild all")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze process")
    analyze_parser.add_argument("--dir", default=".", help="Project directory")
    analyze_parser.add_argument("--output", default="analysis", help="Output directory")
    
    # Edit command
    edit_parser = subparsers.add_parser("edit", help="Edit process file")
    edit_parser.add_argument("--dir", default=".", help="Project directory")
    edit_parser.add_argument("--editor", help="Editor to use")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate process")
    validate_parser.add_argument("--dir", default=".", help="Project directory")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show project status")
    status_parser.add_argument("--dir", default=".", help="Project directory")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export documentation")
    export_parser.add_argument("--dir", default=".", help="Project directory")
    export_parser.add_argument("--format", choices=["all", "pdf", "html", "zip"], 
                              default="all", help="Export format")
    export_parser.add_argument("--output", help="Output file name")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = ProcessCLI()
    
    try:
        if args.command == "init":
            cli.setup_project(args.project_dir, args.template)
        elif args.command == "sync":
            cli.sync_project(args.dir, args.watch, args.force)
        elif args.command == "analyze":
            cli.analyze_project(args.dir, args.output)
        elif args.command == "edit":
            cli.edit_process(args.dir, args.editor)
        elif args.command == "validate":
            cli.validate_project(args.dir)
        elif args.command == "status":
            cli.status(args.dir)
        elif args.command == "export":
            cli.export_project(args.dir, args.format, args.output)
    
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        if "--debug" in sys.argv:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()