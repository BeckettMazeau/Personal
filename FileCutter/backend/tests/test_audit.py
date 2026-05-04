import os
import re

def test_no_forbidden_functions():
    forbidden_pattern = re.compile(
        r"(?<!`)\b(os\.remove|os\.unlink|shutil\.rmtree)\b(?!`)"
    )
    backend_dir = os.path.join(os.path.dirname(__file__), "..")

    for root, dirs, files in os.walk(backend_dir):
        if "__pycache__" in root or "venv" in root or ".git" in root or "tests" in root: # ignore tests where we mock them
            continue

        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    matches = forbidden_pattern.findall(content)
                    assert (
                        not matches
                    ), f"Forbidden function(s) found in {filepath}: {matches}"


if __name__ == "__main__":
    test_no_forbidden_functions()
    print("Audit passed.")
