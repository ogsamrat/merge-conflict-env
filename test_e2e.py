"""End-to-end test of the live HuggingFace Space."""

import json
import urllib.request
from pathlib import Path

BASE = "https://xamrat-merge-conflict-env.hf.space"


def call(endpoint, method="GET", payload=None):
    url = f"{BASE}{endpoint}"
    data = json.dumps(payload).encode() if payload else None
    headers = {"Content-Type": "application/json"} if payload else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read().decode())


def test_easy_task():
    print("=" * 60)
    print("FULL E2E TEST: easy_simple_text")
    print("=" * 60)

    # 1. Reset
    r = call("/reset", "POST", {"task_id": "easy_simple_text"})
    obs = r["observation"]
    print(f"[RESET]   success={obs['success']}  conflicts={obs['conflict_files']}")
    assert obs["success"], "Reset failed"
    assert "README.md" in obs["conflict_files"], "No conflicts found"

    # 2. List conflicts
    r = call("/step", "POST", {"action": {"action_type": "list_conflicts"}})
    obs = r["observation"]
    print(f"[LIST]    conflicts={obs['conflict_files']}  reward={r['reward']}")
    assert len(obs["conflict_files"]) > 0, "No conflicts listed"

    # 3. View file
    r = call("/step", "POST", {"action": {"action_type": "view_file", "file_path": "README.md"}})
    obs = r["observation"]
    content = obs["file_content"]
    has_markers = "<<<<<<< " in content
    print(f"[VIEW]    has_markers={has_markers}  length={len(content)}  reward={r['reward']}")
    assert has_markers, "File should have conflict markers"

    # 4. View context
    r = call("/step", "POST", {"action": {"action_type": "view_context"}})
    obs = r["observation"]
    ctx = obs["git_context"]
    print(f"[CONTEXT] length={len(ctx)}  reward={r['reward']}")
    assert len(ctx) > 0, "Git context should not be empty"
    print(f"          preview: {ctx[:150]}")

    # 5. Resolve with gold standard
    gold = Path("tasks/easy_simple_text/gold_resolution/README.md").read_text(encoding="utf-8")
    r = call("/step", "POST", {"action": {"action_type": "resolve_file", "file_path": "README.md", "content": gold}})
    obs = r["observation"]
    reward = r["reward"]
    print(f"[RESOLVE] message={obs['message']}  reward={reward}  remaining={obs['conflicts_remaining']}")
    breakdown = obs.get("info", {}).get("grading_breakdown", {})
    print(f"          breakdown={breakdown}")
    assert reward > 0.5, f"Gold resolution should score high, got {reward}"

    # 6. Run tests
    r = call("/step", "POST", {"action": {"action_type": "run_tests"}})
    obs = r["observation"]
    print(f"[TESTS]   success={obs['success']}  reward={r['reward']}")
    if obs.get("test_output"):
        lines = obs["test_output"].splitlines()
        for line in lines:
            if "passed" in line or "failed" in line or "error" in line.lower():
                print(f"          {line.strip()}")

    # 7. Submit
    r = call("/step", "POST", {"action": {"action_type": "submit"}})
    obs = r["observation"]
    print(f"[SUBMIT]  done={r['done']}  success={obs['success']}  message={obs['message']}")
    assert r["done"], "Submit should set done=True"

    # 8. State
    r = call("/state")
    print(f"[STATE]   task={r.get('task_id')}  steps={r.get('step_count')}  total_reward={r.get('total_reward')}")

    print("\n>>> EASY TASK: ALL CHECKS PASSED <<<\n")


def test_medium_task():
    print("=" * 60)
    print("FULL E2E TEST: medium_code_logic")
    print("=" * 60)

    r = call("/reset", "POST", {"task_id": "medium_code_logic"})
    obs = r["observation"]
    print(f"[RESET]   success={obs['success']}  conflicts={obs['conflict_files']}")
    assert obs["success"], "Reset failed"

    # Resolve utils.py
    gold_utils = Path("tasks/medium_code_logic/gold_resolution/utils.py").read_text(encoding="utf-8")
    r = call("/step", "POST", {"action": {"action_type": "resolve_file", "file_path": "utils.py", "content": gold_utils}})
    print(f"[RESOLVE] utils.py  reward={r['reward']}  remaining={r['observation']['conflicts_remaining']}")

    # Resolve main.py
    gold_main = Path("tasks/medium_code_logic/gold_resolution/main.py").read_text(encoding="utf-8")
    r = call("/step", "POST", {"action": {"action_type": "resolve_file", "file_path": "main.py", "content": gold_main}})
    print(f"[RESOLVE] main.py  reward={r['reward']}  remaining={r['observation']['conflicts_remaining']}")

    # Submit
    r = call("/step", "POST", {"action": {"action_type": "submit"}})
    print(f"[SUBMIT]  done={r['done']}  success={r['observation']['success']}")

    r = call("/state")
    print(f"[STATE]   steps={r.get('step_count')}  total_reward={r.get('total_reward')}")
    print("\n>>> MEDIUM TASK: CHECKS PASSED <<<\n")


def test_hard_task():
    print("=" * 60)
    print("FULL E2E TEST: hard_multi_file")
    print("=" * 60)

    r = call("/reset", "POST", {"task_id": "hard_multi_file"})
    obs = r["observation"]
    print(f"[RESET]   success={obs['success']}  conflicts={obs['conflict_files']}")
    assert obs["success"], "Reset failed"

    for fname in ["config.py", "models.py", "utils.py", "api.py"]:
        gold_path = Path(f"tasks/hard_multi_file/gold_resolution/{fname}")
        if gold_path.exists():
            gold = gold_path.read_text(encoding="utf-8")
            r = call("/step", "POST", {"action": {"action_type": "resolve_file", "file_path": fname, "content": gold}})
            print(f"[RESOLVE] {fname}  reward={r['reward']}  remaining={r['observation']['conflicts_remaining']}")

    r = call("/step", "POST", {"action": {"action_type": "submit"}})
    print(f"[SUBMIT]  done={r['done']}  success={r['observation']['success']}")

    r = call("/state")
    print(f"[STATE]   steps={r.get('step_count')}  total_reward={r.get('total_reward')}")
    print("\n>>> HARD TASK: CHECKS PASSED <<<\n")


if __name__ == "__main__":
    test_easy_task()
    test_medium_task()
    test_hard_task()
    print("=" * 60)
    print("ALL 3 TASKS VERIFIED SUCCESSFULLY")
    print("=" * 60)
