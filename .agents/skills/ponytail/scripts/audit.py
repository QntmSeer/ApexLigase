import ast
import sys
from pathlib import Path

class PonytailAuditor(ast.NodeVisitor):
    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.issues = []
        try:
            self.code_lines = self.filepath.read_text(encoding='utf-8').splitlines()
        except Exception:
            self.code_lines = []

    def visit_FunctionDef(self, node):
        # 1. Check function line count
        start_line = node.lineno
        end_line = getattr(node, 'end_lineno', start_line + 50)
        func_len = end_line - start_line + 1
        if func_len > 50:
            self.issues.append({
                "line": start_line,
                "type": "Function Length",
                "message": f"Function '{node.name}' is {func_len} lines long (cutoff=50). Split or simplify it."
            })
            
        # 2. Check parameter count
        param_count = len(node.args.args)
        if param_count > 5:
            self.issues.append({
                "line": start_line,
                "type": "Excessive Parameters",
                "message": f"Function '{node.name}' has {param_count} parameters (cutoff=5). Group parameters or refactor."
            })
            
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        # Check if the class is just a namespace (no state, only static/class methods)
        has_init = False
        has_instance_methods = False
        method_count = 0
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_count += 1
                if item.name == '__init__':
                    has_init = True
                
                # Check for @staticmethod or @classmethod decorators
                is_static = False
                for dec in item.decorator_list:
                    if isinstance(dec, ast.Name) and dec.id in ('staticmethod', 'classmethod'):
                        is_static = True
                    elif isinstance(dec, ast.Attribute) and dec.attr in ('staticmethod', 'classmethod'):
                        is_static = True
                
                if not is_static and item.name != '__init__':
                    has_instance_methods = True
                    
        if method_count > 0 and not has_init and not has_instance_methods:
            self.issues.append({
                "line": node.lineno,
                "type": "Static Namespace Class",
                "message": f"Class '{node.name}' contains only static or class methods. Convert it to module-level functions."
            })
            
        self.generic_visit(node)


def audit_file(filepath):
    try:
        content = Path(filepath).read_text(encoding='utf-8')
        tree = ast.parse(content, filename=filepath)
        auditor = PonytailAuditor(filepath)
        auditor.visit(tree)
        return auditor.issues
    except Exception as e:
        return [{"line": 0, "type": "Parser Error", "message": f"Could not parse file: {e}"}]


def main():
    if len(sys.argv) < 2:
        print("Usage: python audit.py <file_or_directory>")
        sys.exit(1)
        
    target = Path(sys.argv[1])
    if not target.exists():
        print(f"Error: Target '{target}' does not exist.")
        sys.exit(1)
        
    files = []
    if target.is_file():
        if target.suffix == '.py':
            files.append(target)
    else:
        files = list(target.glob("**/*.py"))
        
    all_issues = {}
    for f in files:
        issues = audit_file(f)
        if issues:
            all_issues[f] = issues
            
    if not all_issues:
        print("\n[SUCCESS] Ponytail Audit complete: No over-engineering detected!")
        sys.exit(0)
        
    print("\n[WARN] Ponytail Audit Results: Complexity / Over-engineering detected\n")
    print(f"| File | Line | Issue Type | Description |")
    print(f"| --- | --- | --- | --- |")
    for f, issues in all_issues.items():
        rel_path = f.name
        for issue in issues:
            print(f"| {rel_path} | {issue['line']} | {issue['type']} | {issue['message']} |")
    print("")

if __name__ == "__main__":
    main()
