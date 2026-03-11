import sys
import subprocess
import os

def check_gpu():
    print("[CI] Checking GPU Status...")
    try:
        res = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,utilization.gpu", "--format=csv,noheader,nounits"], capture_output=True, text=True)
        if res.returncode == 0:
            print(f"  [PASS] GPU Found: {res.stdout.strip()}")
        else:
            print("  [FAIL] nvidia-smi failed.")
    except Exception as e:
        print(f"  [FAIL] GPU check error: {e}")

def check_environment():
    print("\n[CI] Checking Python Environment & Dependencies...")
    imports = [
        ("numpy", lambda: __import__("numpy").__version__),
        ("scipy", lambda: __import__("scipy").__version__),
        ("jax", lambda: __import__("jax").__version__),
        ("haiku", lambda: __import__("haiku").__version__),
        ("pyrosetta", lambda: "Found"),
        ("colabdesign", lambda: "Found")
    ]
    
    for name, version_fn in imports:
        try:
            ver = version_fn()
            print(f"  [PASS] {name}: {ver}")
            # Specific version conflict checks
            if name == "numpy":
                import numpy
                if int(numpy.__version__.split('.')[0]) >= 2:
                    print(f"    [WARNING] NumPy version is >= 2.0 ({numpy.__version__}). This will crash BindCraft.")
            if name == "scipy":
                import scipy.linalg
                if not hasattr(scipy.linalg, "tril"):
                    print("    [FAIL] scipy.linalg.tril is missing! (Scipy >= 1.13 conflict)")
            if name == "jax":
                import jax
                if not hasattr(jax, "linear_util") and not hasattr(jax, "extend"):
                    print("    [FAIL] jax.linear_util missing (JAX >= 0.4.24 conflict)")
        except ImportError:
            print(f"  [FAIL] {name} is NOT installed.")
        except AttributeError as e:
            print(f"  [FAIL] {name} initialization failed: {e}")
        except Exception as e:
            print(f"  [FAIL] {name} error: {e}")

def check_files():
    print("\n[CI] Checking Critical Files...")
    paths = [
        "/home/shadeform/rbx1_binder_design",
        "/home/shadeform/rbx1_binder_design/BindCraft/bindcraft.py",
        "/home/shadeform/rbx1_binder_design/RFdiffusion/run_inference.py",
        "/home/shadeform/binder_design/run_all.sh"
    ]
    for p in paths:
        if os.path.exists(p):
            print(f"  [PASS] Found: {p}")
        else:
            print(f"  [FAIL] Missing: {p}")

if __name__ == "__main__":
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("       RBX1 PIPELINE SYSTEM CI CHECK")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    check_gpu()
    check_environment()
    check_files()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
