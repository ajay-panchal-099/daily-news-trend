import os
import base64
import subprocess
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# === Configuration ===
KEY_DIR = Path("/opt/render/project/.ssh")
KEY_PATH = KEY_DIR / "temp_id_ed25519"
REPO_URL = "git@github.com:ajay-panchal-099/daily-news-trend.git"
BRANCH_NAME = "main"


def format_ist_datetime():
    """Return current IST time as formatted string."""
    ist_time = datetime.now(ZoneInfo("Asia/Kolkata"))
    return ist_time.strftime('%Y-%m-%d %H:%M:%S IST')

def get_private_key():
    """Retrieve and decode the SSH private key from environment variables."""
    base64_key = os.getenv("SSH_PRIVATE_KEY_BASE64")
    plain_key = os.getenv("SSH_PRIVATE_KEY")

    if base64_key:
        print("🔐  Decoding base64 private key...")
        decoded = base64.b64decode(base64_key).decode("utf-8")
        return normalize_key(decoded)
    elif plain_key:
        print("🔐  Using plain SSH private key from environment...")
        return normalize_key(plain_key)
    else:
        raise EnvironmentError("❌  No SSH key found in environment variables.")

def normalize_key(key: str) -> str:
    """Ensure the SSH key format is valid."""
    lines = key.strip().splitlines()
    if not lines[0].startswith("-----BEGIN") or not lines[-1].startswith("-----END"):
        raise ValueError("❌  Invalid SSH key format")
    return "\n".join(lines) + "\n"

def write_temp_key(private_key: str):
    """Write the SSH key to the .ssh directory with secure permissions."""
    print("✅  Writing private key to project .ssh directory...")
    KEY_DIR.mkdir(parents=True, exist_ok=True)
    if KEY_PATH.exists():
        KEY_PATH.chmod(0o600)
        KEY_PATH.unlink()
    KEY_PATH.write_text(private_key)
    KEY_PATH.chmod(0o400)
    print(f"🔑  Temp SSH key saved at {KEY_PATH}")

def setup_ssh_agent_and_add_key():
    """Start ssh-agent, add key, and configure known_hosts for GitHub."""
    print("🚀  Starting ssh-agent and adding key...")
    agent_output = subprocess.check_output("ssh-agent -s", shell=True, executable="/bin/bash").decode()
    for line in agent_output.splitlines():
        if "SSH_AUTH_SOCK" in line or "SSH_AGENT_PID" in line:
            key, value = line.split(";")[0].split("=")
            os.environ[key] = value

    result = subprocess.run(["ssh-add", str(KEY_PATH)], capture_output=True, text=True)
    if result.returncode != 0:
        print("❌  ssh-add failed:\n", result.stderr)
        raise RuntimeError("ssh-add failed")

    subprocess.run("mkdir -p ~/.ssh && touch ~/.ssh/known_hosts", shell=True, executable="/bin/bash")
    subprocess.run("ssh-keyscan github.com >> ~/.ssh/known_hosts", shell=True, executable="/bin/bash")
    print("✅  SSH agent setup complete, key added, known_hosts updated.")

# === Git Functions ===

def git_commit_and_push():
    """Set up Git identity, commit changes in data/, and push to GitHub."""
    try:
        print("⚙️  Setting Git identity...")
        subprocess.run(["git", "config", "--global", "user.name", "ajay-panchal-099"], check=True)
        subprocess.run(["git", "config", "--global", "user.email", "akpanchal099@gmail.com"], check=True)

        print("🔍  Checking Git remote...")
        remote_output = subprocess.run(["git", "remote"], capture_output=True, text=True)
        if "origin" not in remote_output.stdout:
            subprocess.run(["git", "remote", "add", "origin", REPO_URL], check=True)
        else:
            print("✅  Git remote already set.")

        # Check current branch
        current_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
        if current_branch != BRANCH_NAME:
            print(f"🔁  Switching from '{current_branch}' to '{BRANCH_NAME}'...")
            subprocess.run(["git", "stash", "--include-untracked"], check=True)
            subprocess.run(["git", "checkout", BRANCH_NAME], check=True)
            subprocess.run(["git", "stash", "pop"], check=True)

        print("📦  Staging 'data/' directory...")
        subprocess.run(["git", "add", "data/"], check=True)

        # Check if there are changes to commit
        if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode == 0:
            print("📭  No changes to commit.")
            return

        commit_msg = f"📈  Auto-update: Trend data refreshed at {format_ist_datetime()} by cron job"
        print(f"📝  Committing changes...")
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)

        print("🚚  Pushing to GitHub...")
        subprocess.run(["git", "push", "origin", BRANCH_NAME], check=True)

        print("✅  Push completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌  Git error: {e}")
        return False

# === Main ===

def setup_git():
    """Main function to set up Git and push changes."""
    key = get_private_key()
    write_temp_key(key)
    setup_ssh_agent_and_add_key()
    git_commit_and_push()

setup_git()