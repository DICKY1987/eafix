#!/usr/bin/env python3
"""Trading Framework Scanner - Full Implementation

Analyzes trading system bundles to identify frameworks, patterns, and components.
Provides detailed insights into trading system architecture and dependencies.
"""
import argparse
import json
import os
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Set, Optional
from dataclasses import dataclass, asdict


@dataclass
class FrameworkInfo:
    """Framework detection information"""
    name: str
    version: Optional[str]
    confidence: float
    files: List[str]
    indicators: List[str]
    description: str


@dataclass
class TradingPattern:
    """Detected trading pattern"""
    pattern_type: str
    name: str
    confidence: float
    files: List[str]
    parameters: Dict[str, Any]


class TradingFrameworkScanner:
    """Comprehensive trading framework analysis engine"""
    
    def __init__(self):
        self.framework_patterns = {
            "MQL4": {
                "extensions": [".mq4", ".mqh"],
                "keywords": ["Expert", "OnTick", "OnInit", "OnDeinit", "OrderSend", "OrderModify"],
                "functions": ["Symbol", "Period", "Bid", "Ask", "AccountBalance"],
                "includes": ["#include", "#property"]
            },
            "MQL5": {
                "extensions": [".mq5", ".mqh"],
                "keywords": ["CTrade", "CPositionInfo", "OnTick", "OnTradeTransaction"],
                "functions": ["SymbolInfoTick", "PositionsTotal", "OrdersTotal"],
                "includes": ["#include <Trade\\Trade.mqh>"]
            },
            "Python-Trading": {
                "extensions": [".py"],
                "keywords": ["pandas", "numpy", "matplotlib", "backtrader", "zipline"],
                "functions": ["ohlcv", "technical_indicators", "strategy", "portfolio"],
                "imports": ["import pandas", "from backtrader", "import zipline"]
            },
            "C++-Bridge": {
                "extensions": [".cpp", ".hpp", ".h"],
                "keywords": ["extern", "WINAPI", "__declspec", "dllexport"],
                "functions": ["socket", "connect", "send", "recv"],
                "patterns": [r"MT4_.*Bridge", r"Socket.*Bridge"]
            },
            "Database-Integration": {
                "extensions": [".py", ".sql"],
                "keywords": ["sqlite3", "pymongo", "sqlalchemy", "CREATE TABLE"],
                "functions": ["execute", "fetchall", "commit", "connect"],
                "patterns": [r"trading_system\.db", r"trade_.*\.sql"]
            }
        }
        
        self.trading_patterns = {
            "Scalping": {
                "indicators": ["RSI", "MACD", "Bollinger", "StochRSI"],
                "timeframes": ["M1", "M5"],
                "keywords": ["quick_profit", "scalp", "fast_exit"],
                "risk_params": ["tight_stop", "small_lot"]
            },
            "Swing-Trading": {
                "indicators": ["MA", "EMA", "Fibonacci", "Support_Resistance"],
                "timeframes": ["H1", "H4", "D1"],
                "keywords": ["swing", "trend_follow", "position_hold"],
                "risk_params": ["trailing_stop", "position_size"]
            },
            "Grid-Trading": {
                "indicators": ["Grid", "Martingale", "Recovery"],
                "keywords": ["grid_size", "multiplier", "recovery_zone"],
                "risk_params": ["max_trades", "grid_step"]
            },
            "News-Trading": {
                "indicators": ["News", "Calendar", "Volatility"],
                "keywords": ["news_filter", "economic_calendar", "high_impact"],
                "risk_params": ["news_stop", "volatility_filter"]
            },
            "Arbitrage": {
                "indicators": ["Spread", "Correlation", "Cointegration"],
                "keywords": ["arbitrage", "hedge", "correlation_trade"],
                "risk_params": ["spread_threshold", "hedge_ratio"]
            }
        }

    def scan_bundle(self, bundle_path: str) -> Dict[str, Any]:
        """Scan trading bundle for frameworks and patterns"""
        if not os.path.exists(bundle_path):
            return {"frameworks": [], "patterns": [], "summary": {"error": "Bundle path not found"}}
            
        path = Path(bundle_path)
        
        # Collect all files
        all_files = []
        if path.is_file():
            all_files = [path]
        else:
            for ext in [".mq4", ".mq5", ".py", ".cpp", ".h", ".hpp", ".sql", ".txt", ".csv"]:
                all_files.extend(path.rglob(f"*{ext}"))
        
        frameworks = self._detect_frameworks(all_files)
        patterns = self._detect_trading_patterns(all_files)
        architecture = self._analyze_architecture(all_files)
        dependencies = self._analyze_dependencies(all_files)
        
        return {
            "frameworks": [asdict(f) for f in frameworks],
            "patterns": [asdict(p) for p in patterns],
            "architecture": architecture,
            "dependencies": dependencies,
            "summary": {
                "total_files": len(all_files),
                "framework_count": len(frameworks),
                "pattern_count": len(patterns),
                "complexity_score": self._calculate_complexity(all_files, frameworks, patterns)
            }
        }

    def _detect_frameworks(self, files: List[Path]) -> List[FrameworkInfo]:
        """Detect trading frameworks in files"""
        frameworks = []
        
        for framework_name, config in self.framework_patterns.items():
            framework_files = []
            indicators = []
            confidence = 0.0
            
            for file_path in files:
                if file_path.suffix.lower() in config["extensions"]:
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        file_confidence = 0.0
                        file_indicators = []
                        
                        # Check keywords
                        for keyword in config["keywords"]:
                            if keyword.lower() in content.lower():
                                file_confidence += 0.1
                                file_indicators.append(f"keyword:{keyword}")
                        
                        # Check functions
                        for function in config["functions"]:
                            if function in content:
                                file_confidence += 0.15
                                file_indicators.append(f"function:{function}")
                        
                        # Check includes/imports
                        if "includes" in config:
                            for include in config["includes"]:
                                if include in content:
                                    file_confidence += 0.2
                                    file_indicators.append(f"include:{include}")
                        
                        # Check imports for Python
                        if "imports" in config:
                            for import_stmt in config["imports"]:
                                if import_stmt in content:
                                    file_confidence += 0.2
                                    file_indicators.append(f"import:{import_stmt}")
                        
                        # Check patterns
                        if "patterns" in config:
                            for pattern in config["patterns"]:
                                if re.search(pattern, content, re.IGNORECASE):
                                    file_confidence += 0.25
                                    file_indicators.append(f"pattern:{pattern}")
                        
                        if file_confidence > 0.3:  # Threshold for framework detection
                            framework_files.append(str(file_path.name))
                            indicators.extend(file_indicators)
                            confidence += file_confidence
                    
                    except Exception:
                        continue
            
            if framework_files:
                # Extract version if possible
                version = self._extract_version(framework_files, files)
                
                frameworks.append(FrameworkInfo(
                    name=framework_name,
                    version=version,
                    confidence=min(confidence / len(framework_files), 1.0),
                    files=framework_files,
                    indicators=list(set(indicators)),
                    description=self._get_framework_description(framework_name)
                ))
        
        return sorted(frameworks, key=lambda x: x.confidence, reverse=True)

    def _detect_trading_patterns(self, files: List[Path]) -> List[TradingPattern]:
        """Detect trading patterns and strategies"""
        patterns = []
        
        for pattern_name, config in self.trading_patterns.items():
            pattern_files = []
            confidence = 0.0
            parameters = {}
            
            for file_path in files:
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    file_confidence = 0.0
                    
                    # Check indicators
                    for indicator in config["indicators"]:
                        if indicator.lower() in content.lower():
                            file_confidence += 0.2
                            parameters[f"uses_{indicator.lower()}"] = True
                    
                    # Check timeframes
                    if "timeframes" in config:
                        for timeframe in config["timeframes"]:
                            if timeframe in content:
                                file_confidence += 0.15
                                parameters[f"timeframe_{timeframe}"] = True
                    
                    # Check keywords
                    for keyword in config["keywords"]:
                        if keyword.lower() in content.lower():
                            file_confidence += 0.1
                            parameters[f"feature_{keyword}"] = True
                    
                    # Check risk parameters
                    for risk_param in config["risk_params"]:
                        if risk_param.lower() in content.lower():
                            file_confidence += 0.05
                            parameters[f"risk_{risk_param}"] = True
                    
                    if file_confidence > 0.2:
                        pattern_files.append(str(file_path.name))
                        confidence += file_confidence
                
                except Exception:
                    continue
            
            if pattern_files:
                patterns.append(TradingPattern(
                    pattern_type="Strategy",
                    name=pattern_name,
                    confidence=min(confidence / len(pattern_files), 1.0),
                    files=pattern_files,
                    parameters=parameters
                ))
        
        return sorted(patterns, key=lambda x: x.confidence, reverse=True)

    def _analyze_architecture(self, files: List[Path]) -> Dict[str, Any]:
        """Analyze system architecture"""
        architecture = {
            "layers": [],
            "components": {},
            "communication": [],
            "data_flow": []
        }
        
        # Detect architectural layers
        for file_path in files:
            if "core" in str(file_path):
                architecture["layers"].append("Core Business Logic")
            elif "ui" in str(file_path) or "gui" in str(file_path):
                architecture["layers"].append("User Interface")
            elif "bridge" in str(file_path) or "connector" in str(file_path):
                architecture["layers"].append("Communication Bridge")
            elif "database" in str(file_path) or ".db" in str(file_path):
                architecture["layers"].append("Data Persistence")
            elif ".mq" in file_path.suffix:
                architecture["layers"].append("Trading Execution")
        
        # Component analysis
        component_types = ["Expert Advisor", "Indicator", "Script", "Library", "GUI", "Database", "Bridge"]
        for comp_type in component_types:
            count = sum(1 for f in files if comp_type.lower().replace(" ", "_") in str(f).lower())
            if count > 0:
                architecture["components"][comp_type] = count
        
        # Communication patterns
        comm_patterns = ["Socket", "DDE", "File", "Registry", "Memory"]
        for pattern in comm_patterns:
            found = any(pattern.lower() in f.read_text(encoding='utf-8', errors='ignore').lower() 
                       for f in files if f.suffix == '.py' and f.stat().st_size < 1000000)
            if found:
                architecture["communication"].append(pattern)
        
        architecture["layers"] = list(set(architecture["layers"]))
        return architecture

    def _analyze_dependencies(self, files: List[Path]) -> Dict[str, List[str]]:
        """Analyze system dependencies"""
        dependencies = {
            "external_libraries": [],
            "system_requirements": [],
            "framework_dependencies": [],
            "file_dependencies": []
        }
        
        for file_path in files:
            try:
                if file_path.suffix == '.py':
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    
                    # Python imports
                    import_patterns = [
                        r'import\s+(\w+)',
                        r'from\s+(\w+)\s+import',
                        r'pip install\s+(\S+)',
                        r'requirements.*:\s*(\S+)'
                    ]
                    
                    for pattern in import_patterns:
                        matches = re.findall(pattern, content)
                        dependencies["external_libraries"].extend(matches)
                
                elif file_path.suffix in ['.mq4', '.mq5']:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    
                    # MQL includes
                    includes = re.findall(r'#include\s*[<"]([^">]+)[">]', content)
                    dependencies["file_dependencies"].extend(includes)
                    
                    # System DLLs
                    dlls = re.findall(r'#import\s*"([^"]+\.dll)"', content)
                    dependencies["system_requirements"].extend(dlls)
            
            except Exception:
                continue
        
        # Clean up and deduplicate
        for key in dependencies:
            dependencies[key] = list(set(dependencies[key]))
        
        return dependencies

    def _extract_version(self, framework_files: List[str], all_files: List[Path]) -> Optional[str]:
        """Extract version information from files"""
        version_patterns = [
            r'version\s*[=:]\s*["\']?([0-9]+\.[0-9]+(?:\.[0-9]+)?)["\']?',
            r'VERSION\s*=\s*["\']([^"\']+)["\']',
            r'#property\s+version\s+["\']([^"\']+)["\']'
        ]
        
        for file_path in all_files:
            if file_path.name in framework_files:
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    for pattern in version_patterns:
                        match = re.search(pattern, content, re.IGNORECASE)
                        if match:
                            return match.group(1)
                except Exception:
                    continue
        return None

    def _get_framework_description(self, framework_name: str) -> str:
        """Get framework description"""
        descriptions = {
            "MQL4": "MetaTrader 4 Expert Advisor framework for algorithmic trading",
            "MQL5": "MetaTrader 5 advanced trading platform framework",
            "Python-Trading": "Python-based trading and analysis framework",
            "C++-Bridge": "C++ communication bridge for MT4/MT5 integration",
            "Database-Integration": "Database layer for trade data persistence"
        }
        return descriptions.get(framework_name, "Unknown trading framework")

    def _calculate_complexity(self, files: List[Path], frameworks: List[FrameworkInfo], 
                            patterns: List[TradingPattern]) -> float:
        """Calculate system complexity score"""
        base_score = len(files) * 0.1
        framework_score = len(frameworks) * 5
        pattern_score = len(patterns) * 3
        
        # File type diversity
        extensions = set(f.suffix for f in files)
        diversity_score = len(extensions) * 2
        
        # Total lines of code
        total_lines = 0
        for file_path in files:
            try:
                if file_path.suffix in ['.py', '.mq4', '.mq5', '.cpp', '.h']:
                    lines = len(file_path.read_text(encoding='utf-8', errors='ignore').splitlines())
                    total_lines += lines
            except Exception:
                continue
        
        code_score = min(total_lines / 1000, 50)  # Cap at 50
        
        return min(base_score + framework_score + pattern_score + diversity_score + code_score, 100)


def main() -> None:
    parser = argparse.ArgumentParser(description="Trading Framework Scanner")
    parser.add_argument("trading_system_bundle", help="Path to trading system bundle or directory")
    parser.add_argument("-o", "--output", help="Optional output JSON file; defaults to stdout")
    parser.add_argument("--detailed", action="store_true", help="Include detailed analysis")
    args = parser.parse_args()

    scanner = TradingFrameworkScanner()
    result = scanner.scan_bundle(args.trading_system_bundle)
    
    if not args.detailed:
        # Simplified output for compatibility with tests
        result = {"frameworks": [f["name"] for f in result["frameworks"]]}

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()