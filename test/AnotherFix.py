import re
from pathlib import Path

def fix_pyqt_init(file_path: str):
    """
    Fix all classes inheriting from QWidget or QMainWindow in a Python file.
    Ensures `super().__init__()` is present and properly indented inside __init__.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"[ERROR] File not found: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    fixed_lines = []
    inside_class = False
    inside_init = False
    init_indent = None
    super_called = False
    class_inherits = False

    class_pattern = re.compile(r"class\s+\w+\s*\(\s*(QWidget|QMainWindow)\s*\)\s*:")
    init_pattern = re.compile(r"def\s+__init__\s*\(.*\):")

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Detect class inheritance
        if class_pattern.match(stripped):
            inside_class = True
            class_inherits = True
            fixed_lines.append(line)
            continue

        # Detect __init__ method
        if inside_class and init_pattern.match(stripped):
            inside_init = True
            init_indent = len(line) - len(line.lstrip())
            super_called = False
            fixed_lines.append(line)
            continue

        if inside_init:
            current_indent = len(line) - len(line.lstrip())
            # Detect end of __init__ by indentation
            if stripped and current_indent <= init_indent:
                if not super_called:
                    fixed_lines.append(" " * (init_indent + 4) + "super().__init__()\n")
                inside_init = False

            # Check if super() already called
            if "super().__init__" in stripped:
                super_called = True

        fixed_lines.append(line)

    # If file ends while still inside __init__ and super not called
    if inside_init and not super_called:
        fixed_lines.append(" " * (init_indent + 4) + "super().__init__()\n")

    # Write back fixed file
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(fixed_lines)

    print(f"[INFO] Fixed all PyQt __init__ inheritance in {file_path}")

# Usage example
fix_pyqt_init("main.py")
