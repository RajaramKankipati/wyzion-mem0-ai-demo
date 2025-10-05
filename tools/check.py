import subprocess


def run():
    cmds = [
        ["black", "--check", "."],
        ["isort", "--check-only", "."],
        ["flake8", "--ignore=E501", "."],
        ["mypy", "/wyzion_mem0_ai_demo/app/"],
    ]
    for cmd in cmds:
        print(f"\n▶ Running: {' '.join(cmd)}")
        subprocess.run(["poetry", "run"] + cmd, check=False)
