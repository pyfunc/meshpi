#!/usr/bin/env python3
"""
Test utilities for RPi architecture testing

Common utilities and helper functions for installation testing.
"""

import os
import sys
import time
import json
import platform
import subprocess
from typing import Dict, List, Optional, Tuple
from pathlib import Path


def get_system_info() -> Dict:
    """Collect comprehensive system information"""
    info = {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "architecture": platform.architecture(),
        "uname": platform.uname()._asdict(),
        "timestamp": time.time()
    }
    
    # Get additional system info
    try:
        # Memory info (Linux)
        if Path("/proc/meminfo").exists():
            with open("/proc/meminfo") as f:
                meminfo = {}
                for line in f:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        meminfo[key.strip()] = value.strip()
                info["memory"] = meminfo
    except Exception:
        pass
    
    try:
        # CPU info (Linux)
        if Path("/proc/cpuinfo").exists():
            with open("/proc/cpuinfo") as f:
                cpuinfo = []
                current_cpu = {}
                for line in f:
                    if line.strip() == "":
                        if current_cpu:
                            cpuinfo.append(current_cpu)
                            current_cpu = {}
                    elif ":" in line:
                        key, value = line.split(":", 1)
                        current_cpu[key.strip()] = value.strip()
                if current_cpu:
                    cpuinfo.append(current_cpu)
                info["cpu"] = cpuinfo
    except Exception:
        pass
    
    return info


def check_package_compatibility(package_name: str, version: Optional[str] = None) -> Dict:
    """Check if a package is compatible with current architecture"""
    result = {
        "package": package_name,
        "version": version,
        "compatible": False,
        "available_versions": [],
        "error": None
    }
    
    try:
        # Check if package is available
        cmd = [sys.executable, "-m", "pip", "index", "versions", package_name]
        process = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if process.returncode == 0:
            result["compatible"] = True
            # Parse versions from output
            output = process.stdout
            if "Available versions:" in output:
                versions_line = output.split("Available versions:")[1].strip()
                result["available_versions"] = [v.strip() for v in versions_line.split(",")]
        else:
            result["error"] = process.stderr
            
    except subprocess.TimeoutExpired:
        result["error"] = "Timeout checking package availability"
    except Exception as e:
        result["error"] = str(e)
    
    return result


def test_wheel_compatibility(wheel_path: str) -> Dict:
    """Test if a wheel file is compatible with current architecture"""
    result = {
        "wheel_path": wheel_path,
        "compatible": False,
        "wheel_info": {},
        "error": None
    }
    
    try:
        # Use pip wheel inspector
        cmd = [sys.executable, "-m", "pip", "show", "-f", wheel_path]
        process = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if process.returncode == 0:
            result["compatible"] = True
            result["wheel_info"] = {
                "stdout": process.stdout,
                "stderr": process.stderr
            }
        else:
            result["error"] = process.stderr
            
    except Exception as e:
        result["error"] = str(e)
    
    return result


def benchmark_installation_time(package_spec: str, iterations: int = 3) -> Dict:
    """Benchmark package installation time"""
    times = []
    errors = []
    
    for i in range(iterations):
        try:
            start_time = time.time()
            
            # Uninstall first
            subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", package_spec], 
                         capture_output=True, timeout=60)
            
            # Install
            process = subprocess.run([sys.executable, "-m", "pip", "install", package_spec],
                                   capture_output=True, text=True, timeout=300)
            
            end_time = time.time()
            
            if process.returncode == 0:
                times.append(end_time - start_time)
            else:
                errors.append(process.stderr)
                
        except subprocess.TimeoutExpired:
            errors.append("Installation timeout")
        except Exception as e:
            errors.append(str(e))
    
    result = {
        "package_spec": package_spec,
        "iterations": iterations,
        "times": times,
        "errors": errors,
        "avg_time": sum(times) / len(times) if times else None,
        "min_time": min(times) if times else None,
        "max_time": max(times) if times else None,
        "success_rate": len(times) / iterations
    }
    
    return result


def create_test_report(results: List[Dict], output_path: str) -> str:
    """Create a comprehensive test report"""
    report = {
        "timestamp": time.time(),
        "system_info": get_system_info(),
        "test_results": results,
        "summary": {
            "total_tests": len(results),
            "passed": sum(1 for r in results if r.get("passed", False)),
            "failed": sum(1 for r in results if not r.get("passed", False)),
        }
    }
    
    # Add architecture-specific analysis
    arch_results = {}
    for result in results:
        arch = result.get("architecture", "unknown")
        if arch not in arch_results:
            arch_results[arch] = {"passed": 0, "failed": 0, "issues": []}
        
        if result.get("passed", False):
            arch_results[arch]["passed"] += 1
        else:
            arch_results[arch]["failed"] += 1
            arch_results[arch]["issues"].append({
                "test": result.get("name", "unknown"),
                "error": result.get("error", "unknown")
            })
    
    report["architecture_analysis"] = arch_results
    
    # Write report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    return output_path


def validate_environment() -> Dict:
    """Validate that the testing environment is properly set up"""
    validation = {
        "valid": True,
        "issues": [],
        "warnings": []
    }
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 9):
        validation["valid"] = False
        validation["issues"].append(f"Python {python_version.major}.{python_version.minor} is not supported (requires 3.9+)")
    
    # Check pip
    try:
        import pip
        validation["pip_version"] = pip.__version__
    except ImportError:
        validation["valid"] = False
        validation["issues"].append("pip is not available")
    
    # Check network connectivity (for PyPI access)
    try:
        import urllib.request
        urllib.request.urlopen("https://pypi.org", timeout=10)
        validation["network_ok"] = True
    except Exception:
        validation["network_ok"] = False
        validation["warnings"].append("Cannot reach PyPI - installation tests may fail")
    
    # Check disk space
    try:
        stat = os.statvfs(".")
        free_space_mb = (stat.f_bavail * stat.f_frsize) // (1024 * 1024)
        if free_space_mb < 500:  # Less than 500MB
            validation["warnings"].append(f"Low disk space: {free_space_mb}MB available")
        validation["free_space_mb"] = free_space_mb
    except Exception:
        validation["warnings"].append("Cannot check disk space")
    
    return validation


if __name__ == "__main__":
    # Test the utilities
    print("System Info:")
    print(json.dumps(get_system_info(), indent=2, default=str))
    
    print("\nEnvironment Validation:")
    validation = validate_environment()
    print(json.dumps(validation, indent=2, default=str))
