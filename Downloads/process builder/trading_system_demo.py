#!/usr/bin/env python3
"""
Trading System Process Documentation Demo
Shows practical usage of the atomic process framework for the reentry trading system
"""

import json
from pathlib import Path
from datetime import datetime
from atomic_process_framework import (
    AtomicProcessFramework, ProcessFlow, ProcessSection, ProcessStep, 
    SubProcess, SubProcessCall, ProcessInput, ProcessOutput, ValueSpec
)
from process_sync_manager import ProcessSyncManager

class TradingSystemDocumentationDemo:
    """Demonstration of the framework for trading system documentation"""
    
    def __init__(self, demo_dir: str = "trading_system_docs"):
        self.demo_dir = Path(demo_dir)
        self.demo_dir.mkdir(exist_ok=True)
        
        self.framework = AtomicProcessFramework(str(self.demo_dir))
        self.sync_manager = ProcessSyncManager(str(self.demo_dir))
        
    def create_complete_trading_flow(self) -> ProcessFlow:
        """Create the complete trading system flow with all sub-processes"""
        
        # Create all sub-processes
        subprocesses = self._create_all_subprocesses()
        
        # Create main sections with sub-process integration
        sections = self._create_complete_sections()
        
        # Global I/O for the entire system
        global_inputs = ProcessInput(inputs=[
            ValueSpec("economic_calendar_file", "string", "Path to economic calendar data", True),
            ValueSpec("market_session", "string", "Current trading session (LONDON/NY/ASIA)", True),
            ValueSpec("global_risk_percent", "number", "Base risk percentage for all trades", True, 1.0),
            ValueSpec("volatility_adjustment", "number", "Market volatility multiplier", True, 1.0),
            ValueSpec("system_parameters", "object", "Global system configuration", True)
        ])
        
        global_outputs = ProcessOutput(outputs=[
            ValueSpec("trade_signals", "array", "Generated trading signals ready for execution", True),
            ValueSpec("system_health_status", "object", "Overall system health metrics", True),
            ValueSpec("trade_results", "array", "Completed trade outcomes and statistics", True),
            ValueSpec("error_log", "array", "System errors and warnings", False, [])
        ])
        
        return ProcessFlow(
            title="Atomic Process Flow — Reentry Trading System",
            version="v3.1",
            date=datetime.now().strftime("%Y-%m-%d"),
            id_conventions="Format: SECTION.STEP (e.g., 1.001). Sub-processes: PREFIX.STEP (e.g., RC.001)",
            legend="Each step is atomic (one action). Sub-processes are reusable components called from main steps.",
            sections=sections,
            subprocesses=subprocesses,
            global_inputs=global_inputs,
            global_outputs=global_outputs,
            file_paths={
                "trading_signals": "bridge\\trading_signals.csv",
                "trade_responses": "bridge\\trade_responses.csv", 
                "parameter_log": "logs\\parameter_log.csv",
                "economic_calendar": "data\\economic_calendar.csv",
                "matrix_map": "config\\matrix_map.csv"
            },
            metadata={
                "actors": {
                    "PY": "Python Service - Main orchestration and data processing",
                    "EA": "MT4 Expert Advisor - Trade execution and validation",
                    "FS": "Filesystem - File operations and data persistence",
                    "BR": "CSV Bridge - Inter-process communication",
                    "TEST": "QA Testing - Validation and test scenarios"
                },
                "error_codes": {
                    "E0000": "Version mismatch between components",
                    "E1001": "Risk limit exceeded (>3.50%)",
                    "E1012": "Take profit must be greater than stop loss",
                    "E1020": "ATR validation failed",
                    "E1030": "Maximum generation limit exceeded",
                    "E1040": "News cutoff time violation",
                    "E1050": "Order placement failed after retries"
                },
                "sla_categories": {
                    "fast": "≤50ms - Simple calculations and validations",
                    "standard": "≤500ms - File operations and API calls", 
                    "complex": "≤2000ms - Complex calculations and transformations",
                    "broker": "≤5000ms - Broker operations (network dependent)"
                }
            }
        )
    
    def _create_all_subprocesses(self) -> list[SubProcess]:
        """Create all reusable sub-processes for the trading system"""
        
        # 1. Risk Calculation Sub-process (Enhanced)
        risk_calc = SubProcess(
            subprocess_id="RISK_CALC",
            name="Risk Calculation and Position Sizing",
            description="Calculate effective risk percentage and convert to position size with validation",
            version="1.1",
            inputs=ProcessInput(inputs=[
                ValueSpec("base_risk_percent", "number", "Base risk percentage (0.1-3.5)", True),
                ValueSpec("volatility_multiplier", "number", "Volatility adjustment factor", True, 1.0),
                ValueSpec("symbol_info", "object", "Symbol contract specifications", True),
                ValueSpec("account_balance", "number", "Current account balance", True),
                ValueSpec("currency_conversion_rate", "number", "USD conversion rate", False, 1.0)
            ]),
            outputs=ProcessOutput(outputs=[
                ValueSpec("effective_risk", "number", "Final calculated risk percentage", True),
                ValueSpec("lot_size", "number", "Position size in lots", True),
                ValueSpec("dollar_risk", "number", "Risk amount in account currency", True),
                ValueSpec("validation_warnings", "array", "Risk validation warnings", False, [])
            ]),
            steps=[
                ProcessStep(
                    step_id="RC.001",
                    actor="PY",
                    description="Apply volatility multiplier to base risk",
                    input_variables=["base_risk_percent", "volatility_multiplier"],
                    output_variables=["adjusted_risk"],
                    validation_rules=["volatility_multiplier > 0", "base_risk_percent > 0"],
                    sla_ms=5
                ),
                ProcessStep(
                    step_id="RC.002", 
                    actor="PY",
                    description="Enforce maximum risk cap of 3.50%",
                    input_variables=["adjusted_risk"],
                    output_variables=["effective_risk"],
                    validation_rules=["effective_risk <= 3.50"],
                    error_codes=["E1001"],
                    sla_ms=5
                ),
                ProcessStep(
                    step_id="RC.003",
                    actor="PY", 
                    description="Calculate dollar risk amount",
                    input_variables=["effective_risk", "account_balance"],
                    output_variables=["dollar_risk"],
                    sla_ms=10
                ),
                ProcessStep(
                    step_id="RC.004",
                    actor="PY",
                    description="Convert to lot size using symbol contract specifications",
                    input_variables=["dollar_risk", "symbol_info", "currency_conversion_rate"],
                    output_variables=["lot_size"],
                    validation_rules=["lot_size >= symbol_info.min_lot", "lot_size <= symbol_info.max_lot"],
                    sla_ms=15
                )
            ],
            tags=["risk", "calculation", "position-sizing", "validation"],
            complexity_score=4
        )
        
        # 2. File Validation Sub-process
        file_validation = SubProcess(
            subprocess_id="FILE_VALIDATE",
            name="File Integrity Validation",
            description="Validate file integrity with hash checking and atomic operations",
            version="1.0",
            inputs=ProcessInput(inputs=[
                ValueSpec("file_path", "string", "Path to file to validate", True),
                ValueSpec("expected_hash", "string", "Expected SHA-256 hash", False),
                ValueSpec("max_age_hours", "number", "Maximum file age in hours", False, 24)
            ]),
            outputs=ProcessOutput(outputs=[
                ValueSpec("is_valid", "boolean", "File validation result", True),
                ValueSpec("actual_hash", "string", "Computed file hash", True),
                ValueSpec("file_size", "number", "File size in bytes", True),
                ValueSpec("file_age_hours", "number", "File age in hours", True)
            ]),
            steps=[
                ProcessStep(
                    step_id="FV.001",
                    actor="PY",
                    description="Check file exists and compute basic metrics",
                    input_variables=["file_path"],
                    output_variables=["file_exists", "file_size", "file_age_hours"],
                    conditions=["If not file_exists"],
                    goto_targets=["FV.004"],
                    sla_ms=50
                ),
                ProcessStep(
                    step_id="FV.002",
                    actor="PY",
                    description="Compute SHA-256 hash of file content",
                    dependencies=["FV.001"],
                    input_variables=["file_path"],
                    output_variables=["actual_hash"],
                    sla_ms=300
                ),
                ProcessStep(
                    step_id="FV.003",
                    actor="PY", 
                    description="Compare with expected hash if provided",
                    dependencies=["FV.002"],
                    input_variables=["actual_hash", "expected_hash", "file_age_hours", "max_age_hours"],
                    output_variables=["is_valid"],
                    sla_ms=5
                ),
                ProcessStep(
                    step_id="FV.004",
                    actor="PY",
                    description="Set validation failed for missing file",
                    input_variables=[],
                    output_variables=["is_valid"],
                    notes="is_valid = False when file doesn't exist",
                    sla_ms=1
                )
            ],
            tags=["file", "validation", "integrity", "security"],
            complexity_score=2
        )
        
        # 3. Economic Calendar Processing Sub-process
        eco_calendar_proc = SubProcess(
            subprocess_id="ECO_PROCESS",
            name="Economic Calendar Processing",
            description="Transform raw economic calendar data into normalized trading signals",
            version="1.0",
            inputs=ProcessInput(inputs=[
                ValueSpec("raw_calendar_data", "object", "Raw calendar data from source", True),
                ValueSpec("impact_filter", "array", "Impact levels to include", True, ["HIGH", "MED"]),
                ValueSpec("currency_filter", "array", "Currencies to process", False, ["USD", "EUR", "GBP", "JPY"])
            ]),
            outputs=ProcessOutput(outputs=[
                ValueSpec("normalized_events", "array", "Normalized calendar events", True),
                ValueSpec("anticipation_events", "array", "Generated anticipation signals", True),
                ValueSpec("processing_stats", "object", "Processing statistics", True)
            ]),
            steps=[
                ProcessStep(
                    step_id="EP.001",
                    actor="PY",
                    description="Filter events by impact and currency",
                    input_variables=["raw_calendar_data", "impact_filter", "currency_filter"],
                    output_variables=["filtered_events"],
                    sla_ms=100
                ),
                ProcessStep(
                    step_id="EP.002",
                    actor="PY",
                    description="Normalize event data structure",
                    dependencies=["EP.001"],
                    input_variables=["filtered_events"],
                    output_variables=["normalized_events"],
                    validation_rules=["All events have required fields"],
                    sla_ms=200
                ),
                ProcessStep(
                    step_id="EP.003",
                    actor="PY",
                    description="Generate anticipation events (1hr, 8hr before)",
                    dependencies=["EP.002"],
                    input_variables=["normalized_events"],
                    output_variables=["anticipation_events"],
                    sla_ms=300
                ),
                ProcessStep(
                    step_id="EP.004",
                    actor="PY",
                    description="Compute processing statistics",
                    dependencies=["EP.002", "EP.003"],
                    input_variables=["normalized_events", "anticipation_events"],
                    output_variables=["processing_stats"],
                    sla_ms=50
                )
            ],
            tags=["calendar", "processing", "normalization", "signals"],
            complexity_score=5
        )
        
        # 4. Order Validation Sub-process
        order_validation = SubProcess(
            subprocess_id="ORDER_VALIDATE",
            name="Order Validation",
            description="Comprehensive validation of order parameters before submission",
            version="1.0",
            inputs=ProcessInput(inputs=[
                ValueSpec("order_params", "object", "Complete order parameters", True),
                ValueSpec("market_info", "object", "Current market state", True),
                ValueSpec("account_info", "object", "Account constraints", True)
            ]),
            outputs=ProcessOutput(outputs=[
                ValueSpec("is_valid", "boolean", "Order validation result", True),
                ValueSpec("validation_errors", "array", "List of validation errors", False, []),
                ValueSpec("warnings", "array", "Non-fatal warnings", False, []),
                ValueSpec("adjusted_params", "object", "Adjusted order parameters", True)
            ]),
            steps=[
                ProcessStep(
                    step_id="OV.001",
                    actor="EA",
                    description="Validate order type and symbol",
                    input_variables=["order_params", "market_info"],
                    output_variables=["basic_valid"],
                    validation_rules=["Valid order type", "Symbol tradeable"],
                    sla_ms=10
                ),
                ProcessStep(
                    step_id="OV.002",
                    actor="EA",
                    description="Validate lot size against broker limits",
                    dependencies=["OV.001"],
                    input_variables=["order_params", "account_info"],
                    output_variables=["lot_valid"],
                    validation_rules=["Lot >= min_lot", "Lot <= max_lot", "Sufficient margin"],
                    sla_ms=20
                ),
                ProcessStep(
                    step_id="OV.003",
                    actor="EA",
                    description="Validate SL/TP levels and distances",
                    dependencies=["OV.001"],
                    input_variables=["order_params", "market_info"],
                    output_variables=["levels_valid"],
                    validation_rules=["SL distance >= min_distance", "TP > SL (if FIXED)"],
                    error_codes=["E1012"],
                    sla_ms=15
                ),
                ProcessStep(
                    step_id="OV.004",
                    actor="EA",
                    description="Apply broker-specific adjustments",
                    dependencies=["OV.001", "OV.002", "OV.003"],
                    input_variables=["order_params", "basic_valid", "lot_valid", "levels_valid"],
                    output_variables=["adjusted_params", "is_valid"],
                    sla_ms=25
                )
            ],
            tags=["order", "validation", "broker", "safety"],
            complexity_score=6
        )
        
        return [risk_calc, file_validation, eco_calendar_proc, order_validation]
    
    def _create_complete_sections(self) -> list[ProcessSection]:
        """Create main process sections with comprehensive sub-process integration"""
        
        sections = []
        
        # 0.000 - System Bootstrap
        bootstrap_steps = [
            ProcessStep(
                step_id="0.001",
                actor="PY",
                description="Load and validate parameters.schema.json",
                subprocess_calls=[
                    SubProcessCall(
                        subprocess_id="FILE_VALIDATE",
                        input_mapping={
                            "schema_file_path": "file_path",
                            "schema_expected_hash": "expected_hash"
                        },
                        output_mapping={
                            "is_valid": "schema_valid",
                            "actual_hash": "schema_hash"
                        },
                        description="Validate schema file integrity before loading"
                    )
                ],
                input_variables=["schema_file_path", "schema_expected_hash"],
                output_variables=["schema_content", "schema_valid", "schema_hash"],
                conditions=["If not schema_valid"],
                goto_targets=["11.010"],
                sla_ms=500,
                file_operations=["READ: parameters.schema.json"],
                validation_rules=["Schema file exists", "SHA-256 matches"]
            ),
            ProcessStep(
                step_id="0.002",
                actor="PY",
                description="Validate schema self-integrity and load into memory",
                dependencies=["0.001"],
                input_variables=["schema_content"],
                output_variables=["schema_loaded"],
                validation_rules=["$id field present", "$schema field present", "Valid JSON schema"],
                conditions=["If validation fails"],
                goto_targets=["11.010"],
                sla_ms=200
            ),
            ProcessStep(
                step_id="0.003",
                actor="PY",
                description="Initialize directory structure and file handles",
                dependencies=["0.002"],
                output_variables=["directories_ready", "file_handles"],
                sla_ms=1000,
                file_operations=[
                    "CREATE_DIR: bridge/",
                    "CREATE_DIR: logs/", 
                    "CREATE_DIR: config/",
                    "CREATE_DIR: data/",
                    "OPEN_APPEND: bridge/trading_signals.csv",
                    "OPEN_READ_TAIL: bridge/trade_responses.csv"
                ]
            )
        ]
        
        bootstrap_section = ProcessSection(
            section_id="0.000",
            title="System Bootstrap (One-Time on Service Start)",
            description="Initialize system components, validate configuration, and establish file handles",
            actors=["PY"],
            transport="Filesystem",
            steps=bootstrap_steps
        )
        
        # 1.000 - Economic Calendar Ingestion
        calendar_steps = [
            ProcessStep(
                step_id="1.001",
                actor="PY",
                description="Scan Downloads folder for new economic calendar files",
                output_variables=["calendar_files_found"],
                sla_ms=1000,
                file_operations=["SCAN: %USERPROFILE%\\Downloads"],
                notes="Looks for pattern: economic_calendar*.{csv,xlsx}"
            ),
            ProcessStep(
                step_id="1.002",
                actor="PY",
                description="Copy newest calendar file with atomic operation",
                dependencies=["1.001"],
                input_variables=["calendar_files_found"],
                subprocess_calls=[
                    SubProcessCall(
                        subprocess_id="FILE_VALIDATE",
                        input_mapping={"newest_file": "file_path"},
                        output_mapping={"actual_hash": "file_hash"},
                        description="Compute hash of new calendar file"
                    )
                ],
                output_variables=["calendar_copied", "new_file_path"],
                conditions=["If no files found"],
                goto_targets=["1.010"],
                sla_ms=500,
                file_operations=["COPY_ATOMIC: data/economic_calendar_raw_*.ext"]
            ),
            ProcessStep(
                step_id="1.003",
                actor="PY",
                description="Process and normalize calendar data",
                dependencies=["1.002"],
                input_variables=["new_file_path"],
                subprocess_calls=[
                    SubProcessCall(
                        subprocess_id="ECO_PROCESS",
                        input_mapping={
                            "file_content": "raw_calendar_data",
                            "impact_levels": "impact_filter"
                        },
                        output_mapping={
                            "normalized_events": "processed_events",
                            "anticipation_events": "anticipation_signals",
                            "processing_stats": "calendar_stats"
                        },
                        description="Transform raw calendar into normalized trading events"
                    )
                ],
                output_variables=["processed_events", "anticipation_signals", "calendar_stats"],
                sla_ms=2000
            ),
            ProcessStep(
                step_id="1.010",
                actor="PY",
                description="Update in-memory calendar index for fast lookups",
                dependencies=["1.003"],
                input_variables=["processed_events", "anticipation_signals"],
                output_variables=["calendar_index_updated"],
                sla_ms=200
            )
        ]
        
        calendar_section = ProcessSection(
            section_id="1.000",
            title="Economic Calendar Ingestion (Hourly From Sunday 12:00 Local)",
            description="Ingest, validate, and process economic calendar data into trading signals",
            actors=["PY", "FS"],
            transport="CSV-only",
            steps=calendar_steps
        )
        
        # 3.000 - Matrix Routing & Parameter Resolution
        routing_steps = [
            ProcessStep(
                step_id="3.001",
                actor="PY",
                description="Lookup combination_id in matrix mapping table",
                input_variables=["combination_id"],
                output_variables=["parameter_set_id", "routing_decision"],
                sla_ms=20,
                file_operations=["READ_CACHE: config/matrix_map.csv"]
            ),
            ProcessStep(
                step_id="3.006",
                actor="PY",
                description="Calculate effective risk and position sizing",
                dependencies=["3.001"],
                input_variables=["global_risk_percent", "volatility_factor", "symbol_info", "account_balance"],
                subprocess_calls=[
                    SubProcessCall(
                        subprocess_id="RISK_CALC",
                        input_mapping={
                            "global_risk_percent": "base_risk_percent",
                            "volatility_factor": "volatility_multiplier",
                            "symbol_info": "symbol_info",
                            "account_balance": "account_balance"
                        },
                        output_mapping={
                            "effective_risk": "calculated_risk",
                            "lot_size": "position_size",
                            "dollar_risk": "risk_amount",
                            "validation_warnings": "risk_warnings"
                        },
                        description="Calculate risk-adjusted position sizing with validation"
                    )
                ],
                output_variables=["calculated_risk", "position_size", "risk_amount", "risk_warnings"],
                sla_ms=50
            )
        ]
        
        routing_section = ProcessSection(
            section_id="3.000",
            title="Matrix Routing & Parameter Resolution",
            description="Route signals through matrix mapping and calculate trading parameters",
            actors=["PY"],
            transport="Memory",
            steps=routing_steps
        )
        
        # 7.000 - EA Order Workflow with Validation
        order_steps = [
            ProcessStep(
                step_id="7.001",
                actor="EA",
                description="Validate order parameters comprehensively",
                input_variables=["order_parameters", "market_state", "account_state"],
                subprocess_calls=[
                    SubProcessCall(
                        subprocess_id="ORDER_VALIDATE",
                        input_mapping={
                            "order_parameters": "order_params",
                            "market_state": "market_info",
                            "account_state": "account_info"
                        },
                        output_mapping={
                            "is_valid": "order_valid",
                            "validation_errors": "order_errors",
                            "adjusted_params": "final_params"
                        },
                        description="Comprehensive order validation before submission"
                    )
                ],
                output_variables=["order_valid", "order_errors", "final_params"],
                conditions=["If not order_valid"],
                goto_targets=["REJECT_TRADE"],
                error_codes=["E1050"],
                sla_ms=100
            ),
            ProcessStep(
                step_id="7.002",
                actor="EA",
                description="Submit order to broker with retry logic",
                dependencies=["7.001"],
                input_variables=["final_params"],
                output_variables=["order_ids", "execution_result"],
                sla_ms=5000,
                validation_rules=["Broker connection active", "Market hours check"],
                error_codes=["E1050"],
                notes="SLA depends on broker latency - target ≤5s"
            )
        ]
        
        order_section = ProcessSection(
            section_id="7.000", 
            title="EA Side: Order Workflow (On TRADE_SIGNAL)",
            description="Execute orders with comprehensive validation and error handling",
            actors=["EA"],
            transport="CSV Bridge",
            steps=order_steps
        )
        
        sections.extend([bootstrap_section, calendar_section, routing_section, order_section])
        return sections
    
    def demonstrate_framework_usage(self):
        """Demonstrate practical usage of the framework"""
        
        print("🚀 Trading System Process Documentation Demo")
        print("=" * 60)
        
        # Step 1: Create the complete process flow
        print("\n📋 Step 1: Creating complete process flow with sub-processes...")
        flow = self.create_complete_trading_flow()
        self.framework.process_flow = flow
        
        # Step 2: Validate the flow
        print("\n🔍 Step 2: Validating process flow...")
        errors = self.framework.validate_flow(flow)
        if errors:
            print("❌ Validation errors found:")
            for error in errors:
                print(f"   • {error}")
        else:
            print("✅ Process flow validation passed!")
        
        # Step 3: Generate sync report
        print("\n📊 Step 3: Generating synchronization report...")
        sync_report = self.framework.generate_sync_report(flow)
        print(f"   • Main process: {sync_report['main_process_stats']['sections']} sections, {sync_report['main_process_stats']['total_steps']} steps")
        print(f"   • Sub-processes: {sync_report['subprocess_stats']['total_subprocesses']} defined, {sync_report['subprocess_stats']['subprocess_calls']} calls")
        print(f"   • Actors involved: {', '.join(sync_report['main_process_stats']['actors'])}")
        
        # Step 4: Save all formats
        print("\n💾 Step 4: Saving in all synchronized formats...")
        
        # YAML (primary machine-readable)
        yaml_content = self.framework.save_machine_readable(flow, "yaml")
        yaml_file = self.demo_dir / "trading_system_process.yaml"
        with open(yaml_file, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        print(f"   ✅ Saved YAML: {yaml_file}")
        
        # JSON (secondary machine-readable)
        json_content = self.framework.save_machine_readable(flow, "json")
        json_file = self.demo_dir / "trading_system_process.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            f.write(json_content)
        print(f"   ✅ Saved JSON: {json_file}")
        
        # Markdown (human-readable)
        human_content = self.framework.generate_human_readable(flow)
        md_file = self.demo_dir / "trading_system_process.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(human_content)
        print(f"   ✅ Saved Markdown: {md_file}")
        
        # Draw.io XML (visual)
        xml_content = self.framework.generate_drawio_xml(flow)
        xml_file = self.demo_dir / "trading_system_process.drawio"
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        print(f"   ✅ Saved Draw.io XML: {xml_file}")
        
        # Step 5: Initialize sync manager
        print("\n🔄 Step 5: Setting up synchronization manager...")
        self.sync_manager.create_initial_files()
        
        # Create custom sync config
        sync_config = {
            "version": "1.0",
            "sync_strategy": "yaml_primary",
            "auto_backup": True,
            "backup_retention_days": 30,
            "validation_on_sync": True,
            "files": {
                "machine_yaml": "trading_system_process.yaml",
                "machine_json": "trading_system_process.json",
                "human_md": "trading_system_process.md", 
                "visual_xml": "trading_system_process.drawio",
                "hash_store": ".trading_sync_hashes.json",
                "sync_log": "trading_sync.log"
            }
        }
        
        config_file = self.demo_dir / "sync_config.json"
        with open(config_file, 'w') as f:
            json.dump(sync_config, f, indent=2)
        print(f"   ✅ Sync configuration: {config_file}")
        
        # Step 6: Demonstrate programmatic editing
        print("\n✏️  Step 6: Demonstrating programmatic sub-process injection...")
        
        # Add a new validation step to the bootstrap process
        new_validation_call = SubProcessCall(
            subprocess_id="FILE_VALIDATE",
            input_mapping={"matrix_config_path": "file_path"},
            output_mapping={"is_valid": "matrix_config_valid"},
            description="Validate matrix configuration file"
        )
        
        success = self.framework.inject_subprocess("0.002", new_validation_call)
        if success:
            print("   ✅ Successfully injected FILE_VALIDATE into step 0.002")
        
        # Step 7: Generate final status report
        print("\n📈 Step 7: Final status report...")
        status_report = self.sync_manager.generate_status_report()
        
        print(f"   • Files generated: {len([f for f in status_report['files'].values() if f['exists']])}")
        print(f"   • Total file size: {sum(f['size'] for f in status_report['files'].values()):.1f} bytes")
        print(f"   • Validation status: {'✅ Passed' if status_report['sync_health']['validation_passed'] else '❌ Failed'}")
        
        # Save status report
        status_file = self.demo_dir / "status_report.json"
        with open(status_file, 'w') as f:
            json.dump(status_report, f, indent=2)
        print(f"   📄 Status report saved: {status_file}")
        
        print(f"\n🎉 Demo completed successfully!")
        print(f"📁 All files saved to: {self.demo_dir.absolute()}")
        print("\n📋 Generated files:")
        for file_path in self.demo_dir.glob("*"):
            if file_path.is_file():
                print(f"   • {file_path.name}")
        
        print("\n🔧 Next steps:")
        print("   1. Edit the YAML file to modify the process")
        print("   2. Run sync manager to update all formats:")
        print(f"      python process_sync_manager.py --dir {self.demo_dir} --sync")
        print("   3. Use --watch mode for automatic synchronization")
        print("   4. Import the .drawio file into draw.io for visual editing")
        
        return flow

def main():
    """Run the trading system documentation demo"""
    demo = TradingSystemDocumentationDemo()
    demo.demonstrate_framework_usage()

if __name__ == "__main__":
    main()