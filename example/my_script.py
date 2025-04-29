# import slurm_longrun
import json
import os
import time


def load_state():
    try:
        with open("./state.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_state(state):
    with open("./state.json", "w") as f:
        json.dump(state, f)


print(os.getenv("SLURM_LONGRUN_INITIAL_JOB_ID"), flush=True)
state = load_state()
print(state)


def main():
    for i in range(state.get("i", 0), 3):
        state["i"] = i
        save_state(state)
        print(i + 1, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), flush=True)
        time.sleep(60)


main()
