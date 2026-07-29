"""Project Manager — One-Click Setup Wizard.

Auto-detects the user's environment and generates config.json.
Also updates SKILL.md with the user's actual paths.
Run once after cloning the repository.

Usage: python setup.py
       (or double-click setup.bat)
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# ── Colors (ANSI escape codes for Windows 10+ / terminal) ──
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

CHECK = f"{GREEN}✓{RESET}"
WARN = f"{YELLOW}⚠{RESET}"
CROSS = f"{RED}✗{RESET}"

PROJECT_DIR = Path(__file__).parent.resolve()


def print_banner():
    print()
    print(f"{CYAN}{BOLD}  ╔══════════════════════════════════════════╗")
    print(f"  ║     Project Manager · 项目管家           ║")
    print(f"  ║     One-Click Setup · 一键配置            ║")
    print(f"  ╚══════════════════════════════════════════╝{RESET}")
    print()
    print("  This wizard will auto-detect your environment")
    print("  and configure everything needed to run Project Manager.")
    print("  本向导将自动检测您的环境，完成所有必要配置。")
    print()


def detect_claude_cmd():
    """Detect the Claude Code CLI location. Multi-level fallback."""
    print(f"  {CYAN}[1/4]{RESET} Detecting Claude Code CLI...")

    # Method 1: %APPDATA%\npm\claude.cmd (npm global install)
    appdata = os.environ.get("APPDATA", "")
    npm_claude = Path(appdata) / "npm" / "claude.cmd"
    if npm_claude.exists():
        print(f"       {CHECK} Found: {npm_claude}")
        return str(npm_claude)

    # Method 2: Check PATH via shutil.which
    claude_in_path = shutil.which("claude") or shutil.which("claude.cmd")
    if claude_in_path:
        print(f"       {CHECK} Found in PATH: {claude_in_path}")
        return claude_in_path

    # Method 3: Common npm prefix locations
    for prefix in [
        Path.home() / "AppData" / "Roaming" / "npm" / "claude.cmd",
        Path.home() / "AppData" / "Local" / "npm" / "claude.cmd",
        Path("C:/Program Files/nodejs/claude.cmd"),
    ]:
        if prefix.exists():
            print(f"       {CHECK} Found: {prefix}")
            return str(prefix)

    # Not found — ask user
    print(f"       {WARN} Claude CLI not auto-detected.")
    print(f"       {YELLOW}If you haven't installed Claude Code yet, visit:{RESET}")
    print(f"       https://docs.anthropic.com/en/docs/claude-code/overview")
    print()
    manual = input(f"       Enter path to claude.cmd (or press Enter to skip): ").strip()
    if manual:
        if os.path.isfile(manual):
            print(f"       {CHECK} Using: {manual}")
            return manual
        else:
            print(f"       {CROSS} File not found. Continuing without Claude CLI.")
            return ""
    else:
        print(f"       {YELLOW} Skipped. You can configure this later in config.json.{RESET}")
        return ""


def detect_default_project_dir():
    """Suggest and configure the default project directory."""
    print()
    print(f"  {CYAN}[2/4]{RESET} Default project directory")

    # Check if D:\Claude program exists
    d_claude = Path("D:/Claude program")
    home_projects = Path.home() / "Claude Projects"

    suggestions = []
    if d_claude.exists():
        suggestions.append(str(d_claude))
    suggestions.append(str(home_projects))

    print(f"       Where should new Claude Code projects be stored?")
    for i, s in enumerate(suggestions, 1):
        exists = "(exists)" if Path(s).exists() else "(will be created)"
        print(f"       [{i}] {s} {exists}")
    print(f"       [0] Enter a custom path")

    choice = input(f"       Choose [{len(suggestions)}]: ").strip()
    if choice == "0":
        custom = input(f"       Enter custom path: ").strip()
        if custom:
            selected = custom
        else:
            selected = suggestions[-1]
    elif choice.isdigit() and 1 <= int(choice) <= len(suggestions):
        selected = suggestions[int(choice) - 1]
    else:
        selected = suggestions[-1] if suggestions else str(home_projects)

    # Ensure directory exists
    p = Path(selected)
    if not p.exists():
        try:
            p.mkdir(parents=True, exist_ok=True)
            print(f"       {CHECK} Created: {p}")
        except Exception:
            print(f"       {CROSS} Could not create {p}. Continuing anyway.")
    else:
        print(f"       {CHECK} Directory: {p}")
    return str(p)


def detect_obsidian_vault():
    """Optionally detect Obsidian vault location."""
    print()
    print(f"  {CYAN}[3/4]{RESET} Obsidian vault (optional)")

    use_obsidian = input(f"       Enable Obsidian backup sync? [y/N]: ").strip().lower()
    if use_obsidian != "y":
        print(f"       {YELLOW} Skipped. Obsidian backup disabled.{RESET}")
        return ""

    # Search for Obsidian vaults
    docs = Path.home() / "Documents"
    candidates = []
    if docs.exists():
        for item in docs.iterdir():
            if item.is_dir() and "obsidian" in item.name.lower():
                candidates.append(item)
            elif item.is_dir():
                # Check if contains .obsidian folder
                if (item / ".obsidian").is_dir():
                    candidates.append(item)

    if candidates:
        print(f"       Found {len(candidates)} Obsidian vault(s):")
        for i, c in enumerate(candidates, 1):
            print(f"       [{i}] {c}")
        print(f"       [0] Enter custom path")
        print(f"       [s] Skip")
        choice = input(f"       Choose: ").strip()
        if choice == "0":
            custom = input(f"       Enter vault path: ").strip()
            if custom and Path(custom).is_dir():
                print(f"       {CHECK} Using: {custom}")
                return custom
            else:
                print(f"       {WARN} Invalid path. Skipping.")
                return ""
        elif choice.isdigit() and 1 <= int(choice) <= len(candidates):
            selected = str(candidates[int(choice) - 1])
            print(f"       {CHECK} Using: {selected}")
            return selected
        else:
            print(f"       {YELLOW} Skipped.{RESET}")
            return ""
    else:
        manual = input(f"       No vaults found. Enter path (or Enter to skip): ").strip()
        if manual:
            print(f"       {CHECK} Using: {manual}")
            return manual
        else:
            print(f"       {YELLOW} Skipped.{RESET}")
            return ""


def show_summary(claude_cmd, project_dir, obsidian_vault):
    """Show configuration summary and get user confirmation."""
    print()
    print(f"  {CYAN}[4/4]{RESET} Configuration Summary")
    print(f"  {'─' * 46}")
    print(f"  Project Manager dir : {PROJECT_DIR}")
    print(f"  Claude CLI          : {claude_cmd or '(not configured)'}")
    print(f"  Default project dir : {project_dir}")
    print(f"  Obsidian vault      : {obsidian_vault or '(disabled)'}")
    print(f"  Port                : 8765")
    print(f"  {'─' * 46}")
    print()

    ok = input(f"  {BOLD}Apply this configuration? [Y/n]:{RESET} ").strip().lower()
    return ok != "n"


def write_config(claude_cmd, project_dir, obsidian_vault):
    """Write config.json to the project directory."""
    config = {
        "port": 8765,
        "defaultProjectDir": project_dir,
        "claudeCmd": claude_cmd,
        "obsidianVault": obsidian_vault,
        "projectManagerDir": str(PROJECT_DIR),
    }
    config_path = PROJECT_DIR / "config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"  {CHECK} config.json written")


def update_skill_md(claude_cmd, project_dir, obsidian_vault):
    """Replace placeholders in SKILL.md with actual paths."""
    skill_path = PROJECT_DIR / ".claude" / "skills" / "project-manager" / "SKILL.md"
    if not skill_path.exists():
        print(f"  {WARN} SKILL.md not found, skipping update.")
        return

    content = skill_path.read_text(encoding="utf-8")

    # Apply replacements
    content = content.replace("{projectManagerDir}", str(PROJECT_DIR))
    content = content.replace("{defaultProjectDir}", project_dir)
    content = content.replace("{obsidianVault}", obsidian_vault)

    # Only replace Claude path examples if we found one
    if claude_cmd:
        content = content.replace("{claudeCmd}", claude_cmd)

    skill_path.write_text(content, encoding="utf-8")
    print(f"  {CHECK} SKILL.md updated")

    # Protect personalized SKILL.md from accidental git commit
    try:
        subprocess.run(
            ["git", "update-index", "--skip-worktree", str(skill_path)],
            cwd=str(PROJECT_DIR), capture_output=True, timeout=5
        )
        print(f"  {CHECK} SKILL.md protected from accidental git commit")
    except Exception:
        pass  # Not in a git repo — no problem


def test_server():
    """Try starting the server briefly to verify everything works."""
    print()
    print(f"  Testing server...", end=" ", flush=True)

    server_py = PROJECT_DIR / "server.py"
    try:
        proc = subprocess.Popen(
            [sys.executable, str(server_py)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=str(PROJECT_DIR),
            creationflags=0x08000000 if sys.platform == "win32" else 0,
        )
        time.sleep(2)

        # Check if it started
        if proc.poll() is None:
            # Still running — good!
            import urllib.request
            try:
                resp = urllib.request.urlopen("http://localhost:8765/api/status", timeout=2)
                if resp.status == 200:
                    print(f"{CHECK} Server started successfully!")
                else:
                    print(f"{WARN} Server started but returned status {resp.status}")
            except Exception:
                print(f"{WARN} Server process started but API not responding.")
                print(f"       Check http://localhost:8765/web-ui/index.html manually.")

            proc.terminate()
            proc.wait(timeout=5)
        else:
            stdout, stderr = proc.communicate()
            print(f"{CROSS} Server failed to start.")
            if stderr:
                print(f"       Error: {stderr.decode('utf-8', errors='replace')[:300]}")
    except Exception as e:
        print(f"{CROSS} Could not test server: {e}")


def print_done():
    print()
    print(f"  {GREEN}{BOLD}╔══════════════════════════════════════════╗")
    print(f"  ║         Setup Complete! · 配置完成！    ║")
    print(f"  ╚══════════════════════════════════════════╝{RESET}")
    print()
    print(f"  {BOLD}To start using Project Manager:{RESET}")
    print()
    print(f"    {CYAN}python server.py{RESET}")
    print()
    print(f"  Then open: {CYAN}http://localhost:8765/web-ui/index.html{RESET}")
    print()
    print(f"  {YELLOW}Tip:{RESET} Double-click {CYAN}web-ui/index.html{RESET} for offline (read-only) access.")
    print()


def main():
    print_banner()

    claude_cmd = detect_claude_cmd()
    project_dir = detect_default_project_dir()
    obsidian_vault = detect_obsidian_vault()

    if not show_summary(claude_cmd, project_dir, obsidian_vault):
        print(f"\n  {YELLOW}Setup cancelled. Run again anytime with: python setup.py{RESET}\n")
        return

    print()
    print(f"  Applying configuration...")
    write_config(claude_cmd, project_dir, obsidian_vault)
    update_skill_md(claude_cmd, project_dir, obsidian_vault)
    test_server()
    print_done()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {YELLOW}Setup cancelled.{RESET}\n")
    except Exception as e:
        print(f"\n  {RED}Unexpected error: {e}{RESET}\n")
