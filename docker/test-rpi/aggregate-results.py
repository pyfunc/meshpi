#!/usr/bin/env python3
"""
Aggregate test results from multiple RPi architecture tests

Combines JSON result files from different architecture tests into a summary report.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


class ResultAggregator:
    def __init__(self, results_dir: str = "/app/test-results"):
        self.results_dir = Path(results_dir)
        self.summary = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": 0,
            "architectures": {},
            "overall_status": "unknown",
            "issues": [],
            "recommendations": []
        }

    def load_result_files(self) -> List[Dict]:
        """Load all JSON result files"""
        results = []
        
        if not self.results_dir.exists():
            print(f"Results directory not found: {self.results_dir}")
            return results
            
        for json_file in self.results_dir.glob("meshpi-test-*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    results.append(data)
                    print(f"Loaded: {json_file.name}")
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
                
        return results

    def analyze_results(self, results: List[Dict]) -> Dict:
        """Analyze test results and generate summary"""
        if not results:
            self.summary["overall_status"] = "no_results"
            return self.summary
            
        total_passed = 0
        total_failed = 0
        
        for result in results:
            arch = result.get("architecture", "unknown")
            model = result.get("rpi_model", "unknown")
            key = f"{arch}_{model}"
            
            arch_summary = {
                "architecture": arch,
                "model": model,
                "python_version": result.get("python_version"),
                "platform": result.get("platform"),
                "tests": result.get("tests", []),
                "passed": 0,
                "failed": 0,
                "status": "unknown"
            }
            
            # Analyze individual tests
            for test in result.get("tests", []):
                self.summary["total_tests"] += 1
                if test.get("passed", False):
                    arch_summary["passed"] += 1
                    total_passed += 1
                else:
                    arch_summary["failed"] += 1
                    total_failed += 1
                    
                    # Collect issues
                    issue = {
                        "architecture": arch,
                        "model": model,
                        "test": test.get("name"),
                        "description": test.get("description"),
                        "error": test.get("details", {}).get("error") or test.get("details", {}).get("exception")
                    }
                    self.summary["issues"].append(issue)
            
            # Determine architecture status
            if arch_summary["failed"] == 0:
                arch_summary["status"] = "passed"
            elif arch_summary["passed"] > arch_summary["failed"]:
                arch_summary["status"] = "partial"
            else:
                arch_summary["status"] = "failed"
                
            self.summary["architectures"][key] = arch_summary
        
        # Determine overall status
        if total_failed == 0:
            self.summary["overall_status"] = "all_passed"
        elif total_passed > total_failed:
            self.summary["overall_status"] = "mostly_passed"
        else:
            self.summary["overall_status"] = "mostly_failed"
            
        # Generate recommendations
        self._generate_recommendations()
        
        return self.summary

    def _generate_recommendations(self):
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check for common issues
        issue_patterns = {}
        for issue in self.summary["issues"]:
            error = issue.get("error", "")
            if "pip" in error.lower():
                issue_patterns["pip_issues"] = issue_patterns.get("pip_issues", 0) + 1
            if "import" in error.lower():
                issue_patterns["import_issues"] = issue_patterns.get("import_issues", 0) + 1
            if "timeout" in error.lower():
                issue_patterns["timeout_issues"] = issue_patterns.get("timeout_issues", 0) + 1
        
        # Architecture-specific recommendations
        for arch_key, arch_data in self.summary["architectures"].items():
            if arch_data["status"] == "failed":
                recommendations.append({
                    "type": "architecture_specific",
                    "architecture": arch_data["architecture"],
                    "model": arch_data["model"],
                    "message": f"Consider architecture-specific fixes for {arch_key}"
                })
        
        # General recommendations
        if issue_patterns.get("pip_issues", 0) > 0:
            recommendations.append({
                "type": "general",
                "message": "Consider updating pip installation process or using different pip version"
            })
            
        if issue_patterns.get("timeout_issues", 0) > 0:
            recommendations.append({
                "type": "general", 
                "message": "Consider increasing timeout values for slower architectures"
            })
            
        self.summary["recommendations"] = recommendations

    def print_summary(self):
        """Print formatted summary to console"""
        print("\n" + "="*60)
        print("MESHPI MULTI-ARCHITECTURE TEST SUMMARY")
        print("="*60)
        
        print(f"Timestamp: {self.summary['timestamp']}")
        print(f"Overall Status: {self.summary['overall_status']}")
        print(f"Total Tests: {self.summary['total_tests']}")
        
        print("\n" + "-"*40)
        print("ARCHITECTURE RESULTS:")
        print("-"*40)
        
        for arch_key, arch_data in self.summary["architectures"].items():
            status_symbol = "✓" if arch_data["status"] == "passed" else "✗" if arch_data["status"] == "failed" else "⚠"
            print(f"{status_symbol} {arch_key}: {arch_data['passed']} passed, {arch_data['failed']} failed")
            print(f"   Python: {arch_data['python_version']}")
            print(f"   Platform: {arch_data['platform']}")
        
        if self.summary["issues"]:
            print("\n" + "-"*40)
            print("ISSUES FOUND:")
            print("-"*40)
            
            for i, issue in enumerate(self.summary["issues"][:10], 1):  # Show first 10 issues
                print(f"{i}. {issue['architecture']} ({issue['model']}) - {issue['test']}")
                if issue.get("error"):
                    error_msg = issue['error'][:100] + "..." if len(issue['error']) > 100 else issue['error']
                    print(f"   Error: {error_msg}")
        
        if self.summary["recommendations"]:
            print("\n" + "-"*40)
            print("RECOMMENDATIONS:")
            print("-"*40)
            
            for i, rec in enumerate(self.summary["recommendations"], 1):
                print(f"{i}. {rec['message']}")
        
        print("\n" + "="*60)

    def save_summary(self, filename: str = "test-summary.json"):
        """Save summary to file"""
        summary_path = self.results_dir / filename
        
        with open(summary_path, 'w') as f:
            json.dump(self.summary, f, indent=2, default=str)
            
        print(f"Summary saved to: {summary_path}")
        return summary_path

    def run(self):
        """Run the aggregation process"""
        print("Loading test results...")
        results = self.load_result_files()
        
        if not results:
            print("No test results found!")
            return False
            
        print(f"Found {len(results)} result files")
        
        print("Analyzing results...")
        self.analyze_results(results)
        
        print("Generating summary...")
        self.print_summary()
        self.save_summary()
        
        return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Aggregate MeshPi test results")
    parser.add_argument("--results-dir", default="/app/test-results", 
                       help="Directory containing test result files")
    
    args = parser.parse_args()
    
    aggregator = ResultAggregator(args.results_dir)
    success = aggregator.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
