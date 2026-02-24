#!/usr/bin/env python3
"""
MeshPi Installation Test Script for RPi Architectures

Tests package installation across different Raspberry Pi architectures:
- arm32v6 (RPi Zero, Zero W)
- arm32v7 (RPi 2, 3, Zero 2 W)  
- arm64v8 (RPi 4, 5)

Usage:
    python test-installation.py --arch arm32v6 --model zero
    python test-installation.py --arch arm64v8 --model pi4
"""

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class InstallationTester:
    def __init__(self, arch: str, model: str, verbose: bool = False):
        self.arch = arch
        self.model = model
        self.verbose = verbose
        self.results = {
            "architecture": arch,
            "rpi_model": model,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "timestamp": time.time(),
            "tests": []
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def run_command(self, cmd: List[str], timeout: int = 300) -> Tuple[int, str, str]:
        """Run command and return exit code, stdout, stderr"""
        if self.verbose:
            self.log(f"Running: {' '.join(cmd)}")
            
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            if self.verbose and result.stdout:
                self.log(f"STDOUT: {result.stdout.strip()}")
            if result.stderr and self.verbose:
                self.log(f"STDERR: {result.stderr.strip()}", "WARNING")
                
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            self.log(f"Command timed out after {timeout}s", "ERROR")
            return 1, "", "Timeout"
        except Exception as e:
            self.log(f"Command failed: {e}", "ERROR")
            return 1, "", str(e)

    def test_pip_version(self) -> Dict:
        """Test pip version and compatibility"""
        self.log("Testing pip version...")
        
        test_result = {
            "name": "pip_version",
            "description": "Check pip version and compatibility",
            "passed": False,
            "details": {}
        }
        
        try:
            # Get pip version
            code, stdout, stderr = self.run_command([sys.executable, "-m", "pip", "--version"])
            if code == 0:
                version_line = stdout.strip()
                test_result["details"]["pip_version"] = version_line
                test_result["passed"] = True
                self.log(f"pip version OK: {version_line}")
            else:
                test_result["details"]["error"] = stderr
                self.log(f"pip version check failed: {stderr}", "ERROR")
                
        except Exception as e:
            test_result["details"]["exception"] = str(e)
            self.log(f"pip version test exception: {e}", "ERROR")
            
        self.results["tests"].append(test_result)
        return test_result

    def test_basic_imports(self) -> Dict:
        """Test basic Python imports"""
        self.log("Testing basic imports...")
        
        test_result = {
            "name": "basic_imports",
            "description": "Test basic Python module imports",
            "passed": False,
            "details": {}
        }
        
        basic_modules = [
            "sys", "os", "json", "subprocess", "platform",
            "pathlib", "time", "datetime", "uuid", "hashlib"
        ]
        
        failed_imports = []
        
        for module in basic_modules:
            try:
                __import__(module)
                test_result["details"][module] = "OK"
            except ImportError as e:
                failed_imports.append(module)
                test_result["details"][module] = f"FAILED: {e}"
                
        if not failed_imports:
            test_result["passed"] = True
            self.log("All basic imports OK")
        else:
            self.log(f"Failed imports: {failed_imports}", "ERROR")
            
        self.results["tests"].append(test_result)
        return test_result

    def test_meshpi_installation_pypi(self) -> Dict:
        """Test MeshPi installation from PyPI"""
        self.log("Testing MeshPi installation from PyPI...")
        
        test_result = {
            "name": "meshpi_installation_pypi",
            "description": "Install MeshPi from PyPI",
            "passed": False,
            "details": {}
        }
        
        try:
            # Clean install
            self.run_command([sys.executable, "-m", "pip", "uninstall", "-y", "meshpi"])
            
            # Install from PyPI
            code, stdout, stderr = self.run_command([
                sys.executable, "-m", "pip", "install", "meshpi"
            ], timeout=600)
            
            test_result["details"]["install_stdout"] = stdout
            test_result["details"]["install_stderr"] = stderr
            
            if code == 0:
                # Test import
                try:
                    import meshpi
                    version = getattr(meshpi, "__version__", "unknown")
                    test_result["details"]["meshpi_version"] = version
                    test_result["passed"] = True
                    self.log(f"MeshPy installation OK, version: {version}")
                except ImportError as e:
                    test_result["details"]["import_error"] = str(e)
                    self.log(f"MeshPi import failed: {e}", "ERROR")
            else:
                test_result["details"]["install_error"] = stderr
                self.log(f"MeshPi installation failed: {stderr}", "ERROR")
                
        except Exception as e:
            test_result["details"]["exception"] = str(e)
            self.log(f"MeshPi installation test exception: {e}", "ERROR")
            
        self.results["tests"].append(test_result)
        return test_result

    def test_meshpi_installation_source(self) -> Dict:
        """Test MeshPi installation from source"""
        self.log("Testing MeshPi installation from source...")
        
        test_result = {
            "name": "meshpi_installation_source",
            "description": "Install MeshPi from source (editable)",
            "passed": False,
            "details": {}
        }
        
        try:
            # Clean install
            self.run_command([sys.executable, "-m", "pip", "uninstall", "-y", "meshpi"])
            
            # Install from source
            code, stdout, stderr = self.run_command([
                sys.executable, "-m", "pip", "install", "-e", "."
            ], timeout=600)
            
            test_result["details"]["install_stdout"] = stdout
            test_result["details"]["install_stderr"] = stderr
            
            if code == 0:
                # Test import
                try:
                    import meshpi
                    version = getattr(meshpi, "__version__", "unknown")
                    test_result["details"]["meshpi_version"] = version
                    test_result["passed"] = True
                    self.log(f"MeshPy source installation OK, version: {version}")
                except ImportError as e:
                    test_result["details"]["import_error"] = str(e)
                    self.log(f"MeshPi import failed: {e}", "ERROR")
            else:
                test_result["details"]["install_error"] = stderr
                self.log(f"MeshPi source installation failed: {stderr}", "ERROR")
                
        except Exception as e:
            test_result["details"]["exception"] = str(e)
            self.log(f"MeshPi source installation test exception: {e}", "ERROR")
            
        self.results["tests"].append(test_result)
        return test_result

    def test_meshpi_optional_deps(self) -> Dict:
        """Test MeshPi installation with optional dependencies"""
        self.log("Testing MeshPi installation with optional dependencies...")
        
        test_result = {
            "name": "meshpi_optional_deps",
            "description": "Install MeshPi with optional dependencies",
            "passed": False,
            "details": {}
        }
        
        try:
            # Clean install
            self.run_command([sys.executable, "-m", "pip", "uninstall", "-y", "meshpi"])
            
            # Install with all extras
            code, stdout, stderr = self.run_command([
                sys.executable, "-m", "pip", "install", "meshpi[all]"
            ], timeout=600)
            
            test_result["details"]["install_stdout"] = stdout
            test_result["details"]["install_stderr"] = stderr
            
            if code == 0:
                # Test imports for optional deps
                optional_imports = {
                    "litellm": "LLM support",
                    "pytest": "Development tools",
                    "websockets": "WebSocket support"
                }
                
                failed_optional = []
                for module, desc in optional_imports.items():
                    try:
                        __import__(module)
                        test_result["details"][module] = "OK"
                    except ImportError as e:
                        failed_optional.append(module)
                        test_result["details"][module] = f"FAILED: {e}"
                
                if not failed_optional:
                    test_result["passed"] = True
                    self.log("All optional dependencies OK")
                else:
                    self.log(f"Failed optional imports: {failed_optional}", "WARNING")
                    # Don't fail the test for optional deps
                    test_result["passed"] = True
            else:
                test_result["details"]["install_error"] = stderr
                self.log(f"MeshPi optional deps installation failed: {stderr}", "ERROR")
                
        except Exception as e:
            test_result["details"]["exception"] = str(e)
            self.log(f"MeshPi optional deps test exception: {e}", "ERROR")
            
        self.results["tests"].append(test_result)
        return test_result

    def test_meshpi_cli(self) -> Dict:
        """Test MeshPi CLI functionality"""
        self.log("Testing MeshPi CLI...")
        
        test_result = {
            "name": "meshpi_cli",
            "description": "Test MeshPi CLI commands",
            "passed": False,
            "details": {}
        }
        
        try:
            # Test meshpi --help
            code, stdout, stderr = self.run_command([sys.executable, "-m", "meshpi", "--help"])
            test_result["details"]["help_exit_code"] = code
            test_result["details"]["help_stdout"] = stdout
            
            if code == 0:
                # Test meshpi info
                code2, stdout2, stderr2 = self.run_command([sys.executable, "-m", "meshpi", "info"])
                test_result["details"]["info_exit_code"] = code2
                test_result["details"]["info_stdout"] = stdout2
                
                if code2 == 0:
                    test_result["passed"] = True
                    self.log("MeshPi CLI tests OK")
                else:
                    test_result["details"]["info_error"] = stderr2
                    self.log(f"meshpi info failed: {stderr2}", "ERROR")
            else:
                test_result["details"]["help_error"] = stderr
                self.log(f"meshpi --help failed: {stderr}", "ERROR")
                
        except Exception as e:
            test_result["details"]["exception"] = str(e)
            self.log(f"MeshPi CLI test exception: {e}", "ERROR")
            
        self.results["tests"].append(test_result)
        return test_result

    def save_results(self, output_dir: str = "/app/test-results"):
        """Save test results to JSON file"""
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"meshpi-test-{self.arch}-{self.model}-{int(time.time())}.json"
        filepath = Path(output_dir) / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
            
        self.log(f"Results saved to: {filepath}")
        return filepath

    def run_all_tests(self) -> bool:
        """Run all installation tests"""
        self.log(f"Starting MeshPi installation tests for {self.arch} ({self.model})")
        
        tests = [
            self.test_pip_version,
            self.test_basic_imports,
            self.test_meshpi_installation_pypi,
            self.test_meshpi_installation_source,
            self.test_meshpi_optional_deps,
            self.test_meshpi_cli
        ]
        
        passed = 0
        failed = 0
        
        for test_func in tests:
            try:
                result = test_func()
                if result["passed"]:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log(f"Test {test_func.__name__} crashed: {e}", "ERROR")
                failed += 1
        
        self.log(f"Test summary: {passed} passed, {failed} failed")
        
        # Save results
        self.save_results()
        
        return failed == 0


def main():
    parser = argparse.ArgumentParser(description="Test MeshPi installation on RPi architectures")
    parser.add_argument("--arch", required=True, choices=["arm32v6", "arm32v7", "arm64v8", "x86_64"],
                       help="Target architecture")
    parser.add_argument("--model", required=True, 
                       choices=["zero", "zero2", "pi2", "pi3", "pi4", "pi5"],
                       help="Raspberry Pi model")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--output-dir", default="/app/test-results", help="Output directory")
    
    args = parser.parse_args()
    
    tester = InstallationTester(args.arch, args.model, args.verbose)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
