#!/usr/bin/env python3
"""
Process Analysis and Optimization Tools
Advanced analytics for process documentation and optimization
"""

import json
import yaml
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import statistics

from atomic_process_framework import ProcessFlow, ProcessStep, SubProcess, AtomicProcessFramework

@dataclass
class PerformanceMetrics:
    """Performance analysis results"""
    total_estimated_time_ms: int
    critical_path_time_ms: int
    average_step_time_ms: float
    max_step_time_ms: int
    bottleneck_steps: List[Dict]
    parallel_potential: float
    actor_utilization: Dict[str, float]

@dataclass
class ComplexityMetrics:
    """Process complexity analysis"""
    total_steps: int
    total_branches: int
    cyclomatic_complexity: int
    subprocess_coupling: float
    actor_diversity: int
    max_section_depth: int
    maintainability_score: float

@dataclass
class QualityMetrics:
    """Process quality assessment"""
    documentation_completeness: float
    validation_coverage: float
    error_handling_coverage: float
    sla_completeness: float
    dependency_health: float
    overall_quality_score: float

class ProcessAnalyzer:
    """Comprehensive process analysis and optimization tool"""
    
    def __init__(self, framework: AtomicProcessFramework = None):
        self.framework = framework or AtomicProcessFramework()
        self.graph = None
        self.analysis_results = {}
    
    def load_process_flow(self, file_path: str, format_type: str = "yaml") -> ProcessFlow:
        """Load process flow from file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        flow = self.framework.load_machine_readable(content, format_type)
        self.framework.process_flow = flow
        return flow
    
    def build_process_graph(self, flow: ProcessFlow) -> nx.DiGraph:
        """Build NetworkX graph representation of the process"""
        graph = nx.DiGraph()
        
        # Add nodes for each step
        for section in flow.sections:
            for step in section.steps:
                graph.add_node(step.step_id, 
                              actor=step.actor,
                              description=step.description,
                              sla_ms=step.sla_ms or 0,
                              section=section.section_id,
                              subprocess_calls=len(step.subprocess_calls))
        
        # Add edges based on dependencies and flow
        for section in flow.sections:
            steps = section.steps
            for i, step in enumerate(steps):
                # Sequential flow within section
                if i < len(steps) - 1:
                    graph.add_edge(step.step_id, steps[i + 1].step_id, edge_type="sequential")
                
                # Explicit dependencies
                for dep in step.dependencies:
                    if graph.has_node(dep):
                        graph.add_edge(dep, step.step_id, edge_type="dependency")
                
                # GOTO targets
                for target in step.goto_targets:
                    if graph.has_node(target):
                        graph.add_edge(step.step_id, target, edge_type="goto")
        
        self.graph = graph
        return graph
    
    def analyze_performance(self, flow: ProcessFlow) -> PerformanceMetrics:
        """Comprehensive performance analysis"""
        
        if not self.graph:
            self.build_process_graph(flow)
        
        # Calculate basic metrics
        all_slas = []
        actor_times = defaultdict(list)
        bottlenecks = []
        
        for section in flow.sections:
            for step in section.steps:
                sla = step.sla_ms or 0
                all_slas.append(sla)
                actor_times[step.actor].append(sla)
                
                # Identify bottlenecks (steps taking >2 seconds)
                if sla > 2000:
                    bottlenecks.append({
                        "step_id": step.step_id,
                        "actor": step.actor,
                        "sla_ms": sla,
                        "description": step.description,
                        "severity": "critical" if sla > 10000 else "high" if sla > 5000 else "medium"
                    })
        
        # Critical path analysis
        critical_path_time = self._calculate_critical_path()
        
        # Parallel potential analysis
        parallel_potential = self._analyze_parallel_potential()
        
        # Actor utilization
        total_time = sum(all_slas)
        actor_utilization = {}
        for actor, times in actor_times.items():
            actor_utilization[actor] = sum(times) / total_time if total_time > 0 else 0
        
        return PerformanceMetrics(
            total_estimated_time_ms=sum(all_slas),
            critical_path_time_ms=critical_path_time,
            average_step_time_ms=statistics.mean(all_slas) if all_slas else 0,
            max_step_time_ms=max(all_slas) if all_slas else 0,
            bottleneck_steps=bottlenecks,
            parallel_potential=parallel_potential,
            actor_utilization=actor_utilization
        )
    
    def analyze_complexity(self, flow: ProcessFlow) -> ComplexityMetrics:
        """Analyze process complexity metrics"""
        
        if not self.graph:
            self.build_process_graph(flow)
        
        total_steps = sum(len(section.steps) for section in flow.sections)
        total_branches = 0
        subprocess_calls = 0
        max_section_depth = 0
        
        # Count branches and subprocess coupling
        for section in flow.sections:
            max_section_depth = max(max_section_depth, len(section.steps))
            for step in section.steps:
                total_branches += len(step.goto_targets)
                subprocess_calls += len(step.subprocess_calls)
        
        # Cyclomatic complexity (simplified)
        cyclomatic_complexity = total_branches - total_steps + 2
        
        # Subprocess coupling
        subprocess_coupling = subprocess_calls / total_steps if total_steps > 0 else 0
        
        # Actor diversity
        actors = set()
        for section in flow.sections:
            for step in section.steps:
                actors.add(step.actor)
        
        # Maintainability score (0-10 scale)
        maintainability_score = self._calculate_maintainability_score(flow)
        
        return ComplexityMetrics(
            total_steps=total_steps,
            total_branches=total_branches,
            cyclomatic_complexity=cyclomatic_complexity,
            subprocess_coupling=subprocess_coupling,
            actor_diversity=len(actors),
            max_section_depth=max_section_depth,
            maintainability_score=maintainability_score
        )
    
    def analyze_quality(self, flow: ProcessFlow) -> QualityMetrics:
        """Analyze process quality metrics"""
        
        total_steps = sum(len(section.steps) for section in flow.sections)
        
        # Documentation completeness
        documented_steps = 0
        for section in flow.sections:
            for step in section.steps:
                score = 0
                if step.description and len(step.description) > 10:
                    score += 1
                if step.notes:
                    score += 0.5
                if step.validation_rules:
                    score += 0.5
                documented_steps += min(score, 1.0)
        
        doc_completeness = documented_steps / total_steps if total_steps > 0 else 0
        
        # Validation coverage
        validated_steps = sum(1 for section in flow.sections 
                            for step in section.steps 
                            if step.validation_rules)
        validation_coverage = validated_steps / total_steps if total_steps > 0 else 0
        
        # Error handling coverage
        error_handled_steps = sum(1 for section in flow.sections 
                                for step in section.steps 
                                if step.error_codes or step.goto_targets)
        error_handling_coverage = error_handled_steps / total_steps if total_steps > 0 else 0
        
        # SLA completeness
        sla_steps = sum(1 for section in flow.sections 
                       for step in section.steps 
                       if step.sla_ms is not None)
        sla_completeness = sla_steps / total_steps if total_steps > 0 else 0
        
        # Dependency health
        dependency_health = self._analyze_dependency_health(flow)
        
        # Overall quality score
        overall_quality = (doc_completeness + validation_coverage + 
                         error_handling_coverage + sla_completeness + 
                         dependency_health) / 5
        
        return QualityMetrics(
            documentation_completeness=doc_completeness,
            validation_coverage=validation_coverage,
            error_handling_coverage=error_handling_coverage,
            sla_completeness=sla_completeness,
            dependency_health=dependency_health,
            overall_quality_score=overall_quality
        )
    
    def _calculate_critical_path(self) -> int:
        """Calculate critical path through the process"""
        if not self.graph:
            return 0
        
        try:
            # Find longest path using topological sort
            topo_order = list(nx.topological_sort(self.graph))
            distances = {node: 0 for node in self.graph.nodes()}
            
            for node in topo_order:
                node_time = self.graph.nodes[node].get('sla_ms', 0)
                for successor in self.graph.successors(node):
                    distances[successor] = max(distances[successor], 
                                             distances[node] + node_time)
            
            return max(distances.values()) if distances else 0
            
        except nx.NetworkXError:
            # If graph has cycles, use approximation
            return sum(self.graph.nodes[node].get('sla_ms', 0) 
                      for node in self.graph.nodes())
    
    def _analyze_parallel_potential(self) -> float:
        """Analyze how much of the process could run in parallel"""
        if not self.graph:
            return 0.0
        
        try:
            # Find strongly connected components
            strongly_connected = list(nx.strongly_connected_components(self.graph))
            
            # Calculate parallelizable portions
            total_time = sum(self.graph.nodes[node].get('sla_ms', 0) 
                           for node in self.graph.nodes())
            
            if total_time == 0:
                return 0.0
            
            # Estimate parallel potential based on graph structure
            sequential_components = len(strongly_connected)
            total_nodes = len(self.graph.nodes())
            
            # Higher parallelization potential with more independent components
            parallel_potential = min(0.8, (total_nodes - sequential_components) / total_nodes)
            
            return parallel_potential
            
        except Exception:
            return 0.0
    
    def _calculate_maintainability_score(self, flow: ProcessFlow) -> float:
        """Calculate maintainability score (0-10)"""
        score = 10.0
        
        # Penalize high complexity
        total_steps = sum(len(section.steps) for section in flow.sections)
        if total_steps > 100:
            score -= 2.0
        elif total_steps > 50:
            score -= 1.0
        
        # Penalize many actors (coordination complexity)
        actors = set(step.actor for section in flow.sections for step in section.steps)
        if len(actors) > 10:
            score -= 1.5
        elif len(actors) > 5:
            score -= 0.5
        
        # Reward good documentation
        documented_ratio = sum(1 for section in flow.sections 
                             for step in section.steps 
                             if step.description and len(step.description) > 10) / total_steps
        score += documented_ratio * 2.0
        
        # Reward subprocess usage (modularity)
        subprocess_ratio = len(flow.subprocesses) / max(1, total_steps // 10)
        score += min(1.0, subprocess_ratio)
        
        return max(0.0, min(10.0, score))
    
    def _analyze_dependency_health(self, flow: ProcessFlow) -> float:
        """Analyze health of dependencies and flow"""
        if not self.graph:
            return 0.0
        
        try:
            # Check for cycles
            has_cycles = not nx.is_directed_acyclic_graph(self.graph)
            
            # Check for isolated nodes
            isolated_nodes = list(nx.isolates(self.graph))
            
            # Check for unreachable nodes
            if self.graph.nodes():
                # Find weakly connected components
                weak_components = list(nx.weakly_connected_components(self.graph))
                is_connected = len(weak_components) == 1
            else:
                is_connected = True
            
            # Calculate health score
            health_score = 1.0
            
            if has_cycles:
                health_score -= 0.3
            
            if isolated_nodes:
                health_score -= 0.2 * len(isolated_nodes) / len(self.graph.nodes())
            
            if not is_connected:
                health_score -= 0.3
            
            return max(0.0, health_score)
            
        except Exception:
            return 0.5  # Default to medium health if analysis fails
    
    def generate_optimization_recommendations(self, flow: ProcessFlow) -> List[Dict]:
        """Generate recommendations for process optimization"""
        
        recommendations = []
        
        # Analyze performance
        perf_metrics = self.analyze_performance(flow)
        complexity_metrics = self.analyze_complexity(flow)
        quality_metrics = self.analyze_quality(flow)
        
        # Performance recommendations
        if perf_metrics.bottleneck_steps:
            recommendations.append({
                "category": "Performance",
                "priority": "High",
                "title": "Address Performance Bottlenecks",
                "description": f"Found {len(perf_metrics.bottleneck_steps)} bottleneck steps",
                "details": perf_metrics.bottleneck_steps[:3],  # Top 3
                "action": "Review and optimize slow steps, consider caching or parallel execution"
            })
        
        if perf_metrics.parallel_potential > 0.3:
            recommendations.append({
                "category": "Performance", 
                "priority": "Medium",
                "title": "Parallelization Opportunity",
                "description": f"Process has {perf_metrics.parallel_potential:.1%} parallelization potential",
                "action": "Identify independent steps that can run concurrently"
            })
        
        # Complexity recommendations
        if complexity_metrics.cyclomatic_complexity > 20:
            recommendations.append({
                "category": "Complexity",
                "priority": "High", 
                "title": "High Cyclomatic Complexity",
                "description": f"Complexity score: {complexity_metrics.cyclomatic_complexity}",
                "action": "Consider breaking down complex sections into sub-processes"
            })
        
        if complexity_metrics.subprocess_coupling < 0.1:
            recommendations.append({
                "category": "Modularity",
                "priority": "Medium",
                "title": "Low Sub-process Usage",
                "description": "Process could benefit from more modular design",
                "action": "Extract common patterns into reusable sub-processes"
            })
        
        # Quality recommendations
        if quality_metrics.documentation_completeness < 0.8:
            recommendations.append({
                "category": "Quality",
                "priority": "Medium",
                "title": "Improve Documentation",
                "description": f"Documentation completeness: {quality_metrics.documentation_completeness:.1%}",
                "action": "Add descriptions, notes, and validation rules to steps"
            })
        
        if quality_metrics.error_handling_coverage < 0.5:
            recommendations.append({
                "category": "Reliability",
                "priority": "High",
                "title": "Insufficient Error Handling",
                "description": f"Error handling coverage: {quality_metrics.error_handling_coverage:.1%}",
                "action": "Add error codes and GOTO targets for failure scenarios"
            })
        
        # Sort by priority
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        return recommendations
    
    def visualize_process_graph(self, flow: ProcessFlow, output_file: str = "process_graph.png"):
        """Generate visual representation of the process graph"""
        
        if not self.graph:
            self.build_process_graph(flow)
        
        plt.figure(figsize=(16, 12))
        
        # Create layout
        try:
            pos = nx.spring_layout(self.graph, k=2, iterations=50)
        except:
            pos = nx.random_layout(self.graph)
        
        # Color nodes by actor
        actors = set(self.graph.nodes[node]['actor'] for node in self.graph.nodes())
        colors = plt.cm.Set3(range(len(actors)))
        actor_colors = dict(zip(actors, colors))
        
        node_colors = [actor_colors[self.graph.nodes[node]['actor']] for node in self.graph.nodes()]
        
        # Size nodes by SLA time
        node_sizes = [max(100, self.graph.nodes[node]['sla_ms'] // 10) for node in self.graph.nodes()]
        
        # Draw the graph
        nx.draw(self.graph, pos, 
                node_color=node_colors,
                node_size=node_sizes,
                with_labels=True,
                labels={node: node for node in self.graph.nodes()},
                font_size=8,
                font_weight='bold',
                arrows=True,
                edge_color='gray',
                alpha=0.7)
        
        # Add legend
        legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                                    markerfacecolor=actor_colors[actor], 
                                    markersize=10, label=actor)
                         for actor in actors]
        plt.legend(handles=legend_elements, loc='upper right')
        
        plt.title(f"Process Flow Graph: {flow.title}", fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Process graph saved to {output_file}")
    
    def generate_comprehensive_report(self, flow: ProcessFlow, output_dir: str = "analysis_reports"):
        """Generate comprehensive analysis report"""
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Run all analyses
        perf_metrics = self.analyze_performance(flow)
        complexity_metrics = self.analyze_complexity(flow)
        quality_metrics = self.analyze_quality(flow)
        recommendations = self.generate_optimization_recommendations(flow)
        
        # Create comprehensive report
        report = {
            "analysis_timestamp": datetime.now().isoformat(),
            "process_info": {
                "title": flow.title,
                "version": flow.version,
                "date": flow.date,
                "sections": len(flow.sections),
                "subprocesses": len(flow.subprocesses)
            },
            "performance_metrics": asdict(perf_metrics),
            "complexity_metrics": asdict(complexity_metrics),
            "quality_metrics": asdict(quality_metrics),
            "recommendations": recommendations
        }
        
        # Save JSON report
        with open(output_path / "analysis_report.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate visualizations
        self.visualize_process_graph(flow, str(output_path / "process_graph.png"))
        
        # Generate summary report
        self._generate_markdown_report(report, output_path / "analysis_summary.md")
        
        print(f"Comprehensive analysis report generated in {output_path}")
        return report
    
    def _generate_markdown_report(self, report: Dict, output_file: Path):
        """Generate markdown summary report"""
        
        md_content = f"""# Process Analysis Report

Generated on: {report['analysis_timestamp']}

## Process Overview

- **Title**: {report['process_info']['title']}
- **Version**: {report['process_info']['version']}
- **Date**: {report['process_info']['date']}
- **Sections**: {report['process_info']['sections']}
- **Sub-processes**: {report['process_info']['subprocesses']}

## Performance Metrics

- **Total Estimated Time**: {report['performance_metrics']['total_estimated_time_ms']:,} ms
- **Critical Path Time**: {report['performance_metrics']['critical_path_time_ms']:,} ms
- **Average Step Time**: {report['performance_metrics']['average_step_time_ms']:.1f} ms
- **Parallel Potential**: {report['performance_metrics']['parallel_potential']:.1%}

### Bottlenecks
"""
        
        for bottleneck in report['performance_metrics']['bottleneck_steps'][:5]:
            md_content += f"- **{bottleneck['step_id']}** ({bottleneck['severity']}): {bottleneck['sla_ms']:,} ms\n"
        
        md_content += f"""
## Complexity Metrics

- **Total Steps**: {report['complexity_metrics']['total_steps']}
- **Cyclomatic Complexity**: {report['complexity_metrics']['cyclomatic_complexity']}
- **Sub-process Coupling**: {report['complexity_metrics']['subprocess_coupling']:.2f}
- **Actor Diversity**: {report['complexity_metrics']['actor_diversity']}
- **Maintainability Score**: {report['complexity_metrics']['maintainability_score']:.1f}/10

## Quality Metrics

- **Documentation Completeness**: {report['quality_metrics']['documentation_completeness']:.1%}
- **Validation Coverage**: {report['quality_metrics']['validation_coverage']:.1%}
- **Error Handling Coverage**: {report['quality_metrics']['error_handling_coverage']:.1%}
- **SLA Completeness**: {report['quality_metrics']['sla_completeness']:.1%}
- **Overall Quality Score**: {report['quality_metrics']['overall_quality_score']:.1%}

## Recommendations

"""
        
        for i, rec in enumerate(report['recommendations'][:10], 1):
            md_content += f"### {i}. {rec['title']} ({rec['priority']} Priority)\n\n"
            md_content += f"**Category**: {rec['category']}\n\n"
            md_content += f"**Description**: {rec['description']}\n\n"
            md_content += f"**Action**: {rec['action']}\n\n"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

def main():
    """CLI interface for process analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process Analysis and Optimization Tool")
    parser.add_argument("input_file", help="Path to process flow file (YAML or JSON)")
    parser.add_argument("--format", choices=["yaml", "json"], default="yaml", help="Input file format")
    parser.add_argument("--output-dir", "-o", default="analysis_reports", help="Output directory for reports")
    parser.add_argument("--performance", action="store_true", help="Run performance analysis only")
    parser.add_argument("--complexity", action="store_true", help="Run complexity analysis only")
    parser.add_argument("--quality", action="store_true", help="Run quality analysis only")
    parser.add_argument("--graph", action="store_true", help="Generate process graph visualization")
    
    args = parser.parse_args()
    
    # Load and analyze process
    analyzer = ProcessAnalyzer()
    flow = analyzer.load_process_flow(args.input_file, args.format)
    
    print(f"🔍 Analyzing process: {flow.title}")
    
    if args.performance or not any([args.performance, args.complexity, args.quality]):
        print("\n📊 Performance Analysis:")
        perf_metrics = analyzer.analyze_performance(flow)
        print(f"   • Total time: {perf_metrics.total_estimated_time_ms:,} ms")
        print(f"   • Critical path: {perf_metrics.critical_path_time_ms:,} ms")
        print(f"   • Bottlenecks: {len(perf_metrics.bottleneck_steps)}")
    
    if args.complexity or not any([args.performance, args.complexity, args.quality]):
        print("\n🧩 Complexity Analysis:")
        complexity_metrics = analyzer.analyze_complexity(flow)
        print(f"   • Total steps: {complexity_metrics.total_steps}")
        print(f"   • Cyclomatic complexity: {complexity_metrics.cyclomatic_complexity}")
        print(f"   • Maintainability: {complexity_metrics.maintainability_score:.1f}/10")
    
    if args.quality or not any([args.performance, args.complexity, args.quality]):
        print("\n⭐ Quality Analysis:")
        quality_metrics = analyzer.analyze_quality(flow)
        print(f"   • Documentation: {quality_metrics.documentation_completeness:.1%}")
        print(f"   • Error handling: {quality_metrics.error_handling_coverage:.1%}")
        print(f"   • Overall quality: {quality_metrics.overall_quality_score:.1%}")
    
    if args.graph:
        print("\n🎨 Generating process graph...")
        analyzer.visualize_process_graph(flow, f"{args.output_dir}/process_graph.png")
    
    # Generate comprehensive report if no specific analysis requested
    if not any([args.performance, args.complexity, args.quality, args.graph]):
        print(f"\n📑 Generating comprehensive report...")
        analyzer.generate_comprehensive_report(flow, args.output_dir)
    
    print("\n✅ Analysis complete!")

if __name__ == "__main__":
    main()