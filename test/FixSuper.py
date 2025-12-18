import re
import os

def fix_init_super(file_path: str):
    """
    Ensure that each __init__ method has exactly one super().__init__() directly after the def line.
    Removes extra blank lines or duplicate super calls.
    """
    if not os.path.exists(file_path):
        print(f"[WARN] File does not exist: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    fixed_lines = []
    inside_init = False
    init_indent = None
    super_added = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Detect __init__
        if re.match(r"def __init__\s*\(.*\)\s*:", stripped):
            inside_init = True
            init_indent = len(line) - len(line.lstrip())
            super_added = False
            fixed_lines.append(line.rstrip() + "\n")
            continue

        if inside_init:
            current_indent = len(line) - len(line.lstrip())

            # Skip empty lines immediately after def
            if not super_added and stripped == "":
                continue

            # Insert super if not added yet
            if not super_added:
                fixed_lines.append(" " * (init_indent + 4) + "super().__init__()\n")
                super_added = True

            # Remove extra super() lines
            if stripped.startswith("super()") and ".__init__" not in stripped:
                continue

            # Detect end of __init__
            if stripped and current_indent <= init_indent:
                inside_init = False

        fixed_lines.append(line)

    # Ensure super added at EOF if inside __init__
    if inside_init and not super_added:
        fixed_lines.append(" " * (init_indent + 4) + "super().__init__()\n")

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(fixed_lines)

    print(f"[INFO] Fixed __init__ in {file_path}")

# ---------------- Example Usage ----------------
if __name__ == "__main__":
    path = "main.py"
    fix_init_super(path)
