import json
import subprocess


def analyze_pom_single_repo(repo_path: str, jar_path: str) -> dict[str, list[str]]:
    """
    Run the Java PomAnalyzer in single-repo mode.
    Command: java -jar PomAnalyzer.jar single <repo_path>
    Returns: {repo_path: ["groupId:artifactId", ...]}
    """
    cmd = ["java", "-jar", jar_path, "single", repo_path]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"PomAnalyzer failed: {proc.stderr}")
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON output: {e}\n{proc.stdout[:200]}")
    return data
