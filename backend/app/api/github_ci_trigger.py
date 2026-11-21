import os
import subprocess
import json
import time
from pathlib import Path

# Simple helper to trigger a GitHub Actions run via repository_dispatch

def trigger_ci(repo: str, event_type: str = "uDos-publish") -> dict:
    token_path = Path(os.getenv('UDOS_HOME', '~/.udos')).expanduser() / '.github' / 'token'
    token = token_path.read_text().strip()
    api = f'https://api.github.com/repos/{repo}/dispatches'
    payload = json.dumps({"event_type": event_type})
    result = subprocess.run([
        'curl', '-X', 'POST',
        '-H', f'Authorization: token {token}',
        '-H', 'Accept: application/vnd.github+json',
        api,
        '-d', payload
    ], capture_output=True, text=True)
    return {"status": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def wait_for_latest_run(repo: str, timeout: int = 600, poll_interval: int = 10) -> dict:
    token_path = Path(os.getenv('UDOS_HOME', '~/.udos')).expanduser() / '.github' / 'token'
    token = token_path.read_text().strip()
    api = f'https://api.github.com/repos/{repo}/actions/runs?per_page=1'
    elapsed = 0
    while elapsed < timeout:
        res = subprocess.run([
            'curl', '-s', '-H', f'Authorization: token {token}', api
        ], capture_output=True, text=True)
        data = json.loads(res.stdout or '{}')
        runs = data.get('workflow_runs', [])
        if runs:
            run = runs[0]
            if run.get('status') == 'completed':
                return {"run": run}
        time.sleep(poll_interval)
        elapsed += poll_interval
    return {"error": f"Timeout after {timeout}s waiting for CI run"}

# Example usage (can be called from a uFlow step or API endpoint)
if __name__ == '__main__':
    repo = 'fredbook/SonicScrewdriver'
    print('Triggering CI...')
    print(trigger_ci(repo))
    print('Waiting for completion...')
    print(wait_for_latest_run(repo))
