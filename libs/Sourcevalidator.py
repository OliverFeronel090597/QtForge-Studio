
import sys
import ast
import importlib.util
import configparser
from pathlib import Path

from PyQt6.QtCore import (
    pyqtSignal, QThread
)

class SourceValidator(QThread):
    """Background thread for source validation and loading."""
    
    validation_complete = pyqtSignal(bool, str, object)  # success, message, module
    preflight_check = pyqtSignal(bool, str)  # success, message
    progress_update = pyqtSignal(int, str)  # progress, message
    
    def __init__(self, source_path: Path):
        super().__init__()
        self.source_path = source_path
        self.config_path = source_path.parent / f"{source_path.stem}.ini"
        
    def find_dependencies(self, module_path: Path):
        """Find all Python dependencies of a module."""
        dependencies = set()
        
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse AST to find imports
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Get base module name
                        base_module = alias.name.split('.')[0]
                        # Only track local modules (not built-in)
                        if not self.is_builtin_module(base_module):
                            dependencies.add(base_module)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        base_module = node.module.split('.')[0]
                        if not self.is_builtin_module(base_module):
                            dependencies.add(base_module)
                            
        except Exception as e:
            print(f"Error parsing dependencies: {e}")
            
        return dependencies
        
    def is_builtin_module(self, module_name: str) -> bool:
        """Check if a module is built-in."""
        builtin_modules = {
            'sys', 'os', 'math', 'datetime', 'time', 'json', 're',
            'collections', 'itertools', 'functools', 'typing',
            'pathlib', 'configparser', 'traceback', 'ast', 'importlib'
        }
        return module_name in builtin_modules
        
    def run(self):
        """Perform validation and loading in background thread."""
        try:
            self.progress_update.emit(10, "Starting validation...")
            
            # Step 1: Parse configuration
            if not self.config_path.exists():
                self.preflight_check.emit(False, f"Config file not found: {self.config_path}")
                self.validation_complete.emit(False, "Config file missing", None)
                return
                
            self.progress_update.emit(20, "Reading config file...")
            config = configparser.ConfigParser()
            config.read(self.config_path)
            
            if 'source' not in config:
                self.preflight_check.emit(False, "Missing [source] section in config")
                self.validation_complete.emit(False, "Invalid config format", None)
                return
                
            # Step 2: Perform preflight checks
            module_name = config.get('source', 'module', fallback=None)
            entry_point = config.get('source', 'entry_point', fallback='main_widget')
            
            if not module_name:
                self.preflight_check.emit(False, "No module specified in config")
                self.validation_complete.emit(False, "Missing module name", None)
                return
                
            self.progress_update.emit(30, "Checking module file...")
            # Check module exists
            module_path = self.source_path.parent / f"{module_name}.py"
            if not module_path.exists():
                self.preflight_check.emit(False, f"Module file not found: {module_path}")
                self.validation_complete.emit(False, "Module file missing", None)
                return
                
            # Check Python syntax
            self.progress_update.emit(40, "Checking syntax...")
            try:
                with open(module_path, 'r', encoding='utf-8') as f:
                    compile(f.read(), module_path, 'exec')
                self.preflight_check.emit(True, "Syntax check passed")
            except SyntaxError as e:
                self.preflight_check.emit(False, f"Syntax error: {e}")
                self.validation_complete.emit(False, f"Syntax error in module", None)
                return
                
            # Find dependencies
            self.progress_update.emit(50, "Analyzing dependencies...")
            dependencies = self.find_dependencies(module_path)
            
            # Check dependency files exist
            for dep in dependencies:
                dep_path = self.source_path.parent / f"{dep}.py"
                if dep_path.exists():
                    self.progress_update.emit(55, f"Found dependency: {dep}")
                else:
                    # It might be a package or external module
                    pass
                
            # Step 3: Import module
            self.progress_update.emit(60, "Importing module...")
            try:
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                # Step 4: Check entry point
                self.progress_update.emit(80, "Checking entry point...")
                if not hasattr(module, entry_point):
                    self.preflight_check.emit(False, f"Entry point '{entry_point}' not found")
                    self.validation_complete.emit(False, "Missing entry point", None)
                    return
                    
                self.progress_update.emit(100, "Validation complete")
                self.preflight_check.emit(True, "All checks passed")
                self.validation_complete.emit(True, "Source loaded successfully", module)
                
            except ImportError as e:
                self.preflight_check.emit(False, f"Import error: {e}")
                self.validation_complete.emit(False, f"Import failed: {e}", None)
            except Exception as e:
                self.preflight_check.emit(False, f"Unexpected error: {e}")
                self.validation_complete.emit(False, f"Load failed: {e}", None)
                
        except Exception as e:
            self.preflight_check.emit(False, f"Validation error: {e}")
            self.validation_complete.emit(False, f"Validation failed: {e}", None)