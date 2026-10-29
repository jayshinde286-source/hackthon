"""Script: Verify DBGuard runtime environment and installed capabilities."""

import importlib
import sys

PACKAGES = [
    ("streamlit", "Streamlit Web Dashboard"),
    ("pandas", "Pandas Data Analysis"),
    ("numpy", "NumPy Scientific Computing"),
    ("plotly", "Plotly Visualization Engine"),
    ("pytest", "Pytest Test Suite"),
    ("reportlab", "ReportLab PDF Publishing"),
    ("zstandard", "Zstandard Decompression"),
]


def check():
    print("=" * 60)
    print(" DBGuard Runtime Environment Check")
    print("=" * 60)
    print(f"Python Version: {sys.version.split()[0]} ({sys.platform})")
    print(f"Executable:     {sys.executable}")
    print("-" * 60)

    all_ok = True
    for mod_name, label in PACKAGES:
        try:
            m = importlib.import_module(mod_name)
            ver = getattr(m, "__version__", "installed")
            print(f" [PASS] {label:<30} v{ver}")
        except ImportError as e:
            print(f" [FAIL] {label:<30} NOT FOUND ({e})")
            all_ok = False

    print("=" * 60)
    if all_ok:
        print(">> All required libraries and optional engines are ready.")
        sys.exit(0)
    else:
        print(">> Some packages are missing. Run: pip install -r requirements.txt")
        sys.exit(1)


if __name__ == "__main__":
    check()

