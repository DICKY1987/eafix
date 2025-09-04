#!/usr/bin/env python3
"""Trading Issues Detection Tool - Full Implementation

Performs comprehensive static analysis and runtime checks on trading systems
to identify potential issues, vulnerabilities, and optimization opportunities.
"""
import argparse
import json
import os
import re
import ast
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class TradingIssue:
    """Detected trading system issue"""
    issue_id: str
    severity: str  # "critical", "high", "medium", "low", "info"
    category: str
    title: str
    description: str
    file_path: str
    line_number: Optional[int]
    affected_component: str
    recommendation: str
    impact: str
    confidence: float


class TradingIssueDetector:
    """Comprehensive trading system issue detection engine"""
    
    def __init__(self):
        self.issue_patterns = {
            "MQL4_Issues": [
                {
                    "pattern": r"OrderSend\s*\([^)]*\)\s*;?\s*(?!if|while)",
                    "severity": "high",
                    "category": "Error Handling",
                    "title": "OrderSend without error checking",
                    "description": "OrderSend call not followed by error checking",
                    "recommendation": "Add GetLastError() check after OrderSend",
                    "impact": "Failed orders may go unnoticed"
                },
                {
                    "pattern": r"while\s*\(true\)|for\s*\(\s*;\s*;\s*\)",
                    "severity": "critical",
                    "category": "Performance",
                    "title": "Infinite loop detected",
                    "description": "Potential infinite loop without proper exit condition",
                    "recommendation": "Add break condition or timeout mechanism",
                    "impact": "System freeze or high CPU usage"
                },
                {
                    "pattern": r"AccountBalance\(\)\s*[\-\+\*\/]\s*[0-9\.]+\s*(?!;)",
                    "severity": "medium",
                    "category": "Risk Management",
                    "title": "Hardcoded risk calculation",
                    "description": "Risk calculation uses hardcoded values",
                    "recommendation": "Use configurable risk parameters",
                    "impact": "Inflexible risk management"
                },
                {
                    "pattern": r"string\s+\w+\s*=\s*\"[^\"]{100,}\"",
                    "severity": "low",
                    "category": "Memory",
                    "title": "Large string literal",
                    "description": "Very long string literal found",
                    "recommendation": "Consider using external file or breaking into smaller parts",
                    "impact": "Increased memory usage"
                }
            ],
            "Python_Issues": [
                {
                    "pattern": r"except\s*:",
                    "severity": "high",
                    "category": "Error Handling",
                    "title": "Bare except clause",
                    "description": "Catching all exceptions without specific handling",
                    "recommendation": "Specify exception types to catch",
                    "impact": "May hide critical errors"
                },
                {
                    "pattern": r"time\.sleep\(\s*[0-9]+\s*\)",
                    "severity": "medium",
                    "category": "Performance",
                    "title": "Synchronous sleep in main thread",
                    "description": "Using time.sleep() which blocks execution",
                    "recommendation": "Use async/await or threading for delays",
                    "impact": "UI freezing or poor responsiveness"
                },
                {
                    "pattern": r"password\s*=\s*['\"][^'\"]+['\"]|api_key\s*=\s*['\"][^'\"]+['\"]",
                    "severity": "critical",
                    "category": "Security",
                    "title": "Hardcoded credentials",
                    "description": "Credentials or API keys hardcoded in source",
                    "recommendation": "Use environment variables or secure key storage",
                    "impact": "Security vulnerability - credentials exposure"
                },
                {
                    "pattern": r"eval\s*\(|exec\s*\(",
                    "severity": "critical",
                    "category": "Security",
                    "title": "Dynamic code execution",
                    "description": "Using eval() or exec() for dynamic code execution",
                    "recommendation": "Use safer alternatives like ast.literal_eval()",
                    "impact": "Code injection vulnerability"
                }
            ],
            "Architecture_Issues": [
                {
                    "pattern": r"globals?\(\)|locals?\(\)",
                    "severity": "medium",
                    "category": "Code Quality",
                    "title": "Global/local namespace access",
                    "description": "Direct access to global or local namespace",
                    "recommendation": "Use proper parameter passing and return values",
                    "impact": "Harder to debug and maintain"
                },
                {
                    "pattern": r"TODO|FIXME|HACK|XXX",
                    "severity": "low",
                    "category": "Technical Debt",
                    "title": "Technical debt marker",
                    "description": "Code marked for future attention",
                    "recommendation": "Address technical debt items",
                    "impact": "Potential maintenance burden"
                }
            ]
        }
        
        self.risk_patterns = {
            "High_Risk_Operations": [
                r"OrderCloseBy|OrderDelete",  # Order modification without checks
                r"AccountFreeMargin\(\)\s*<\s*[0-9]+",  # Margin checks
                r"MarketInfo\s*\([^)]*MODE_LOTSIZE[^)]*\)",  # Lot size calculations
            ],
            "Memory_Leaks": [
                r"new\s+\w+\[.*?\](?!\s*delete)",  # Array allocation without delete
                r"ObjectCreate\s*\([^)]*\)(?!\s*ObjectDelete)",  # MT4 object creation
            ],
            "Performance_Issues": [
                r"for\s*\([^)]*;\s*\w+\s*<\s*Bars\s*;[^)]*\)",  # Processing all bars
                r"while\s*\([^)]*MarketInfo[^)]*\)",  # Polling market info
            ]
        }

    def detect_issues(self, bundle_path: str) -> Dict[str, Any]:
        """Main issue detection entry point"""
        if not os.path.exists(bundle_path):
            return {
                "issues": [],
                "summary": {"error": "Bundle path not found", "total_issues": 0}
            }
        
        path = Path(bundle_path)
        all_files = self._collect_files(path)
        
        issues = []
        
        # Pattern-based detection
        issues.extend(self._detect_pattern_issues(all_files))
        
        # Syntax and compilation checks
        issues.extend(self._check_syntax_issues(all_files))
        
        # Architecture analysis
        issues.extend(self._analyze_architecture_issues(all_files))
        
        # Security analysis
        issues.extend(self._security_analysis(all_files))
        
        # Performance analysis
        issues.extend(self._performance_analysis(all_files))
        
        # Risk management analysis
        issues.extend(self._risk_analysis(all_files))
        
        # Database issues
        issues.extend(self._database_issues(all_files))
        
        return self._format_results(issues, all_files)

    def _collect_files(self, path: Path) -> List[Path]:
        """Collect all relevant files for analysis"""
        all_files = []
        if path.is_file():
            all_files = [path]
        else:
            extensions = [".py", ".mq4", ".mq5", ".cpp", ".h", ".hpp", ".sql", ".json", ".yaml", ".yml"]
            for ext in extensions:
                all_files.extend(path.rglob(f"*{ext}"))
        
        return all_files

    def _detect_pattern_issues(self, files: List[Path]) -> List[TradingIssue]:
        """Detect issues using pattern matching"""
        issues = []
        issue_counter = 1
        
        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                lines = content.splitlines()
                
                # Determine file type
                if file_path.suffix in ['.mq4', '.mq5']:
                    patterns = self.issue_patterns["MQL4_Issues"]
                elif file_path.suffix == '.py':
                    patterns = self.issue_patterns["Python_Issues"]
                else:
                    patterns = self.issue_patterns["Architecture_Issues"]
                
                for pattern_config in patterns:
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern_config["pattern"], line, re.IGNORECASE):
                            issues.append(TradingIssue(
                                issue_id=f"ISSUE-{issue_counter:04d}",
                                severity=pattern_config["severity"],
                                category=pattern_config["category"],
                                title=pattern_config["title"],
                                description=pattern_config["description"],
                                file_path=str(file_path.name),
                                line_number=line_num,
                                affected_component=self._determine_component(file_path),
                                recommendation=pattern_config["recommendation"],
                                impact=pattern_config["impact"],
                                confidence=0.8
                            ))
                            issue_counter += 1
                
                # Check for additional risk patterns
                for risk_category, risk_patterns in self.risk_patterns.items():
                    for pattern in risk_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            issues.append(TradingIssue(
                                issue_id=f"RISK-{issue_counter:04d}",
                                severity="high",
                                category="Risk Management",
                                title=f"{risk_category.replace('_', ' ')} detected",
                                description=f"Pattern matching {risk_category} found",
                                file_path=str(file_path.name),
                                line_number=None,
                                affected_component=self._determine_component(file_path),
                                recommendation=f"Review {risk_category.lower()} implementation",
                                impact="Potential risk management issue",
                                confidence=0.6
                            ))
                            issue_counter += 1
            
            except Exception as e:
                # Log parsing error as issue
                issues.append(TradingIssue(
                    issue_id=f"PARSE-{issue_counter:04d}",
                    severity="medium",
                    category="File Access",
                    title="File parsing error",
                    description=f"Could not parse file: {str(e)}",
                    file_path=str(file_path.name),
                    line_number=None,
                    affected_component="File System",
                    recommendation="Check file encoding and accessibility",
                    impact="File may not be properly analyzed",
                    confidence=0.9
                ))
                issue_counter += 1
        
        return issues

    def _check_syntax_issues(self, files: List[Path]) -> List[TradingIssue]:
        """Check for syntax and compilation issues"""
        issues = []
        issue_counter = len(issues) + 1000  # Start from 1000 to avoid conflicts
        
        for file_path in files:
            if file_path.suffix == '.py':
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    ast.parse(content)
                except SyntaxError as e:
                    issues.append(TradingIssue(
                        issue_id=f"SYNTAX-{issue_counter:04d}",
                        severity="critical",
                        category="Syntax Error",
                        title="Python syntax error",
                        description=f"Syntax error: {e.msg}",
                        file_path=str(file_path.name),
                        line_number=e.lineno,
                        affected_component="Python Module",
                        recommendation="Fix syntax error before deployment",
                        impact="Code will not execute",
                        confidence=1.0
                    ))
                    issue_counter += 1
                except Exception:
                    pass  # Other parsing issues handled elsewhere
        
        return issues

    def _analyze_architecture_issues(self, files: List[Path]) -> List[TradingIssue]:
        """Analyze architectural issues"""
        issues = []
        issue_counter = 2000
        
        # Check for missing error handling
        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                
                # Count try/except blocks vs risky operations
                try_count = len(re.findall(r'try\s*:', content, re.IGNORECASE))
                risky_ops = len(re.findall(r'(socket\.|requests\.|sqlite3\.|OrderSend|MarketInfo)', content, re.IGNORECASE))
                
                if risky_ops > try_count * 2:  # More than 2 risky ops per try block
                    issues.append(TradingIssue(
                        issue_id=f"ARCH-{issue_counter:04d}",
                        severity="medium",
                        category="Architecture",
                        title="Insufficient error handling",
                        description=f"Found {risky_ops} risky operations but only {try_count} try blocks",
                        file_path=str(file_path.name),
                        line_number=None,
                        affected_component=self._determine_component(file_path),
                        recommendation="Add more comprehensive error handling",
                        impact="Unhandled exceptions may crash system",
                        confidence=0.7
                    ))
                    issue_counter += 1
                
                # Check for code complexity (long functions/methods)
                if file_path.suffix == '.py':
                    functions = re.findall(r'def\s+\w+.*?(?=def|\Z)', content, re.DOTALL)
                    for func in functions:
                        line_count = len(func.splitlines())
                        if line_count > 50:  # Long function threshold
                            issues.append(TradingIssue(
                                issue_id=f"COMPLEX-{issue_counter:04d}",
                                severity="low",
                                category="Code Quality",
                                title="Complex function detected",
                                description=f"Function has {line_count} lines",
                                file_path=str(file_path.name),
                                line_number=None,
                                affected_component="Function",
                                recommendation="Consider breaking into smaller functions",
                                impact="Harder to maintain and debug",
                                confidence=0.8
                            ))
                            issue_counter += 1
            
            except Exception:
                continue
        
        return issues

    def _security_analysis(self, files: List[Path]) -> List[TradingIssue]:
        """Perform security analysis"""
        issues = []
        issue_counter = 3000
        
        security_patterns = [
            {
                "pattern": r"(password|api_key|secret|token)\s*=\s*['\"][^'\"]+['\"]",
                "severity": "critical",
                "title": "Hardcoded credentials",
                "impact": "Credentials may be exposed in source code"
            },
            {
                "pattern": r"http://[^'\"\\s]+",
                "severity": "medium",
                "title": "Unencrypted HTTP connection",
                "impact": "Data transmitted in plaintext"
            },
            {
                "pattern": r"(?:DROP|DELETE|UPDATE)[\s]+.*?(?:WHERE|\;)",
                "severity": "high",
                "title": "Direct SQL operations",
                "impact": "Potential SQL injection vulnerability"
            },
            {
                "pattern": r"os\.system|subprocess\.call",
                "severity": "high",
                "title": "System command execution",
                "impact": "Potential command injection vulnerability"
            }
        ]
        
        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                
                for pattern_config in security_patterns:
                    matches = re.finditer(pattern_config["pattern"], content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append(TradingIssue(
                            issue_id=f"SEC-{issue_counter:04d}",
                            severity=pattern_config["severity"],
                            category="Security",
                            title=pattern_config["title"],
                            description=f"Security issue found: {match.group(0)[:50]}...",
                            file_path=str(file_path.name),
                            line_number=line_num,
                            affected_component="Security Layer",
                            recommendation="Review and secure this implementation",
                            impact=pattern_config["impact"],
                            confidence=0.7
                        ))
                        issue_counter += 1
            
            except Exception:
                continue
        
        return issues

    def _performance_analysis(self, files: List[Path]) -> List[TradingIssue]:
        """Analyze performance issues"""
        issues = []
        issue_counter = 4000
        
        performance_patterns = [
            r'for\s+\w+\s+in\s+range\([0-9]{4,}\)',  # Large range loops
            r'while.*?True.*?:',  # Infinite loops
            r'\.sleep\s*\([^)]*\)',  # Sleep calls
            r'Bars\s*-\s*[0-9]+\s*;\s*\w+\s*>=\s*0',  # Processing all bars
        ]
        
        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                
                for pattern in performance_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append(TradingIssue(
                            issue_id=f"PERF-{issue_counter:04d}",
                            severity="medium",
                            category="Performance",
                            title="Performance concern detected",
                            description=f"Performance issue: {match.group(0)}",
                            file_path=str(file_path.name),
                            line_number=line_num,
                            affected_component="Performance Layer",
                            recommendation="Optimize this operation",
                            impact="May cause performance degradation",
                            confidence=0.6
                        ))
                        issue_counter += 1
            
            except Exception:
                continue
        
        return issues

    def _risk_analysis(self, files: List[Path]) -> List[TradingIssue]:
        """Analyze trading-specific risk issues"""
        issues = []
        issue_counter = 5000
        
        risk_checks = [
            {
                "pattern": r"OrderSend.*?(?:Bid|Ask).*?(?:\+|\-)\s*[0-9]+\s*\*\s*Point",
                "severity": "medium",
                "title": "Hardcoded spread calculation",
                "impact": "Inflexible spread management"
            },
            {
                "pattern": r"AccountBalance\(\)\s*\*\s*[0-9\.]+",
                "severity": "high",
                "title": "Percentage-based position sizing",
                "impact": "May violate risk management rules"
            },
            {
                "pattern": r"Magic\s*=\s*[0-9]+",
                "severity": "low",
                "title": "Hardcoded magic number",
                "impact": "Potential order conflicts"
            }
        ]
        
        for file_path in files:
            if file_path.suffix in ['.mq4', '.mq5']:
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    
                    for risk_config in risk_checks:
                        matches = re.finditer(risk_config["pattern"], content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            issues.append(TradingIssue(
                                issue_id=f"RISK-{issue_counter:04d}",
                                severity=risk_config["severity"],
                                category="Trading Risk",
                                title=risk_config["title"],
                                description=f"Risk issue: {match.group(0)}",
                                file_path=str(file_path.name),
                                line_number=line_num,
                                affected_component="Risk Management",
                                recommendation="Review risk management implementation",
                                impact=risk_config["impact"],
                                confidence=0.7
                            ))
                            issue_counter += 1
                
                except Exception:
                    continue
        
        return issues

    def _database_issues(self, files: List[Path]) -> List[TradingIssue]:
        """Analyze database-related issues"""
        issues = []
        issue_counter = 6000
        
        db_patterns = [
            {
                "pattern": r"SELECT\s+\*\s+FROM",
                "severity": "medium",
                "title": "SELECT * query",
                "impact": "Inefficient database query"
            },
            {
                "pattern": r"(?:execute|cursor\.execute)\s*\([^)]*\%[^)]*\)",
                "severity": "high",
                "title": "String formatting in SQL",
                "impact": "Potential SQL injection vulnerability"
            },
            {
                "pattern": r"\.commit\(\)(?!\s*(?:except|finally))",
                "severity": "medium",
                "title": "Commit without error handling",
                "impact": "Transaction may fail silently"
            }
        ]
        
        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                
                for db_config in db_patterns:
                    matches = re.finditer(db_config["pattern"], content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append(TradingIssue(
                            issue_id=f"DB-{issue_counter:04d}",
                            severity=db_config["severity"],
                            category="Database",
                            title=db_config["title"],
                            description=f"Database issue: {match.group(0)}",
                            file_path=str(file_path.name),
                            line_number=line_num,
                            affected_component="Database Layer",
                            recommendation="Review database operation",
                            impact=db_config["impact"],
                            confidence=0.7
                        ))
                        issue_counter += 1
            
            except Exception:
                continue
        
        return issues

    def _determine_component(self, file_path: Path) -> str:
        """Determine component type based on file path"""
        path_str = str(file_path).lower()
        
        if "core" in path_str:
            return "Core Logic"
        elif "ui" in path_str or "gui" in path_str:
            return "User Interface"
        elif "bridge" in path_str or "connector" in path_str:
            return "Communication Bridge"
        elif "database" in path_str or file_path.suffix == '.db':
            return "Database"
        elif file_path.suffix in ['.mq4', '.mq5']:
            return "Expert Advisor"
        elif "test" in path_str:
            return "Testing Framework"
        else:
            return "General"

    def _format_results(self, issues: List[TradingIssue], files: List[Path]) -> Dict[str, Any]:
        """Format final results"""
        # Sort by severity and confidence
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        issues_sorted = sorted(issues, 
                             key=lambda x: (severity_order.get(x.severity, 5), -x.confidence))
        
        # Create summary statistics
        severity_counts = {}
        category_counts = {}
        component_counts = {}
        
        for issue in issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
            category_counts[issue.category] = category_counts.get(issue.category, 0) + 1
            component_counts[issue.affected_component] = component_counts.get(issue.affected_component, 0) + 1
        
        return {
            "issues": [asdict(issue) for issue in issues_sorted],
            "summary": {
                "total_issues": len(issues),
                "total_files_analyzed": len(files),
                "severity_breakdown": severity_counts,
                "category_breakdown": category_counts,
                "component_breakdown": component_counts,
                "analysis_timestamp": datetime.now().isoformat(),
                "critical_issues": len([i for i in issues if i.severity == "critical"]),
                "high_priority_issues": len([i for i in issues if i.severity in ["critical", "high"]])
            }
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Trading Issues Detection Tool")
    parser.add_argument("trading_system_bundle", help="Path to trading system bundle or directory")
    parser.add_argument("-o", "--output", help="Optional output JSON file; defaults to stdout")
    parser.add_argument("--detailed", action="store_true", help="Include detailed analysis")
    parser.add_argument("--severity", choices=["critical", "high", "medium", "low", "info"], 
                       help="Minimum severity level to report")
    args = parser.parse_args()

    detector = TradingIssueDetector()
    result = detector.detect_issues(args.trading_system_bundle)
    
    # Filter by severity if specified
    if args.severity:
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        min_level = severity_order[args.severity]
        filtered_issues = [
            issue for issue in result["issues"] 
            if severity_order.get(issue["severity"], 5) <= min_level
        ]
        result["issues"] = filtered_issues
        result["summary"]["total_issues"] = len(filtered_issues)
    
    if not args.detailed:
        # Simplified output for compatibility with tests
        result = {"issues": [issue["title"] for issue in result["issues"]]}

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()