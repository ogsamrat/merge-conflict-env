"""
Baseline inference script for the Merge Conflict Resolution Environment.

Uses the OpenAI API client to evaluate an LLM on all three tasks.
Outputs [START]/[STEP]/[END] lines per the OpenEnv hackathon format.
"""

from __future__ import annotations

import json
import os
import sys
import traceback

from openai import OpenAI

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")
HF_TOKEN = os.getenv("HF_TOKEN")

if HF_TOKEN is None:
    raise ValueError("HF_TOKEN environment variable is required")

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

ENV_BASE_URL = os.getenv(
    "ENV_BASE_URL",
    "https://xamrat-merge-conflict-env.hf.space",
)

TASKS = ["easy_simple_text", "medium_code_logic", "hard_multi_file"]

SYSTEM_PROMPT = """\
You are an expert software developer resolving git merge conflicts.

You interact with a merge conflict environment by outputting JSON actions.
Available actions:
- {"action_type": "list_conflicts"} - List files with conflicts
- {"action_type": "view_file", "file_path": "<path>"} - View a file's content
- {"action_type": "view_context"} - View git log and branch info
- {"action_type": "resolve_file", "file_path": "<path>", "content": "<resolved>"} - Submit resolved file content
- {"action_type": "run_tests"} - Run tests to verify your resolution
- {"action_type": "submit"} - Submit your final resolution

Strategy:
1. First, list_conflicts to see which files need resolving
2. view_context to understand what each branch intended
3. For each conflicted file, view_file to see the conflicts
4. resolve_file with the correctly merged content
5. run_tests to verify
6. submit when done

When resolving conflicts:
- Remove ALL conflict markers (<<<<<<< , =======, >>>>>>>)
- Keep changes from BOTH branches where possible
- Ensure code is syntactically valid
- Maintain consistency across files

Respond with ONLY a JSON action object. No explanation text."""


def make_observation_prompt(observation: dict) -> str:
    """Convert an observation dict into a prompt for the LLM."""
    parts = []

    if observation.get("message"):
        parts.append(f"Status: {observation['message']}")

    if observation.get("conflict_files"):
        parts.append(f"Conflicted files: {observation['conflict_files']}")

    if observation.get("resolution_status"):
        parts.append(f"Resolution status: {observation['resolution_status']}")

    if observation.get("file_content"):
        parts.append(f"File content:\n```\n{observation['file_content']}\n```")

    if observation.get("git_context"):
        parts.append(f"Git context:\n{observation['git_context']}")

    if observation.get("test_output"):
        output = observation["test_output"][:2000]
        parts.append(f"Test output:\n{output}")

    if observation.get("error"):
        parts.append(f"Error: {observation['error']}")

    if observation.get("conflicts_remaining") is not None:
        parts.append(f"Conflicts remaining: {observation['conflicts_remaining']}")

    return "\n\n".join(parts)


def parse_action(response_text: str) -> dict:
    """Parse the LLM response into an action dict."""
    text = response_text.strip()

    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        action = json.loads(text)
        if "action_type" in action:
            return action
    except json.JSONDecodeError:
        pass

    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("{"):
            try:
                action = json.loads(line)
                if "action_type" in action:
                    return action
            except json.JSONDecodeError:
                continue

    return {"action_type": "submit"}


def call_env(endpoint: str, method: str = "GET", payload: dict | None = None) -> dict:
    """Call the environment server API."""
    import urllib.request
    import urllib.error

    url = f"{ENV_BASE_URL}{endpoint}"
    data = json.dumps(payload).encode() if payload else None
    headers = {"Content-Type": "application/json"} if payload else {}

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return {"error": f"HTTP {e.code}: {body}"}
    except Exception as e:
        return {"error": str(e)}


SCORE_MIN = 0.01
SCORE_MAX = 0.99


def strict_score(value: float) -> float:
    """Clamp to strictly (0, 1) range."""
    return round(max(SCORE_MIN, min(SCORE_MAX, float(value))), 2)


def run_task(task_name: str) -> float:
    """Run a single task episode. Returns the final task score."""
    print(f"[START] task={task_name} env=merge_conflict model={MODEL_NAME}", flush=True)

    rewards: list[float] = []
    step_num = 0
    is_success = False
    final_score = SCORE_MIN
    max_steps = 25

    try:
        reset_resp = call_env("/reset", method="POST", payload={"task_id": task_name})
        observation = reset_resp.get("observation", reset_resp)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": make_observation_prompt(observation)},
        ]

        done = observation.get("done", False)

        while not done and step_num < max_steps:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.1,
                max_tokens=4096,
            )
            assistant_text = response.choices[0].message.content or ""
            action = parse_action(assistant_text)

            step_resp = call_env("/step", method="POST", payload={"action": action})
            observation = step_resp.get("observation", step_resp)
            raw_reward = step_resp.get("reward")
            if raw_reward is None or raw_reward == 0:
                raw_reward = observation.get("reward")
            if raw_reward is None or raw_reward == 0:
                raw_reward = SCORE_MIN
            reward = strict_score(float(raw_reward))
            done = step_resp.get("done", observation.get("done", False))
            raw_error = observation.get("error") or "null"
            error = str(raw_error).replace("\n", " ").replace("\r", " ")[:200]

            step_num += 1
            rewards.append(reward)

            action_str = json.dumps(action, separators=(",", ":"))
            print(
                f"[STEP] step={step_num} "
                f"action={action_str} "
                f"reward={reward:.2f} "
                f"done={'true' if done else 'false'} "
                f"error={error}",
                flush=True,
            )

            # Update running score from info if available
            info = observation.get("info", {})
            if isinstance(info, dict) and "task_score" in info:
                final_score = strict_score(float(info["task_score"]))
            elif done:
                final_score = reward

            messages.append({"role": "assistant", "content": assistant_text})
            messages.append({"role": "user", "content": make_observation_prompt(observation)})

        is_success = observation.get("success", False) and observation.get("conflicts_remaining", 1) == 0

        # Use last task_score from info if available, else last reward
        info = observation.get("info", {})
        if isinstance(info, dict) and "task_score" in info:
            final_score = strict_score(float(info["task_score"]))
        elif rewards:
            final_score = strict_score(rewards[-1])

    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        safe_error = str(e).replace("\n", " ").replace("\r", " ")[:200]
        print(
            f"[STEP] step={step_num + 1} "
            f"action=error "
            f"reward={SCORE_MIN:.2f} "
            f"done=true "
            f"error={safe_error}",
            flush=True,
        )
        rewards.append(SCORE_MIN)
        final_score = SCORE_MIN

    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={'true' if is_success else 'false'} "
        f"steps={step_num} "
        f"score={final_score:.2f} "
        f"rewards={rewards_str}",
        flush=True,
    )
    return final_score


def main():
    sys.stderr.write(f"Merge Conflict Resolver - Baseline Inference\n")
    sys.stderr.write(f"Model: {MODEL_NAME}\n")
    sys.stderr.write(f"API: {API_BASE_URL}\n")
    sys.stderr.write(f"Env: {ENV_BASE_URL}\n")

    scores = []
    for task in TASKS:
        scores.append(run_task(task))
    return scores


if __name__ == "__main__":
    main()
