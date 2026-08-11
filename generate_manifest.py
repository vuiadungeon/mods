#!/usr/bin/env python3
import os
import hashlib
import json
import subprocess
from pathlib import Path

# ================== CONFIG ==================
# Root folder that contains your modpacks
ROOT = Path("/home/scupa/ijm")

# Your GitHub repo settings
GITHUB_USER = "vuiadungeon"
GITHUB_REPO = "mods"
BRANCH = "main"

# Base raw URL
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/"
# ============================================

def md5(file_path: Path) -> str:
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_modpacks() -> list[str]:
    """Return list of folders that contain a 'mods' subfolder"""
    modpacks = []
    for item in ROOT.iterdir():
        if item.is_dir() and (item / "mods").is_dir():
            modpacks.append(item.name)
    return sorted(modpacks)


def generate_manifest(modpack: str):
    mods_folder = ROOT / modpack / "mods"
    output_file = ROOT / modpack / "manifest.json"

    if not mods_folder.exists():
        print(f"❌ Mods folder not found: {mods_folder}")
        return False

    files = []
    print(f"\nScanning mods in → {mods_folder}\n")

    for jar in sorted(mods_folder.glob("*.jar")):
        if jar.name.endswith(".disabled"):
            continue

        rel_name = f"{modpack}/mods/{jar.name}"
        uri = BASE_URL + rel_name
        checksum = md5(jar)

        files.append({
            "name": f"mods/{jar.name}",          # relative to instance .minecraft
            "uri": uri,
            "checksum": checksum
        })
        print(f"  ✓ {jar.name}")

    manifest = {"files": files}

    with open(output_file, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n✅ Generated {output_file} with {len(files)} files")
    return True


def upload_to_github(modpack: str):
    """Add, commit and push the changes"""
    print("\nUploading to GitHub...")

    # We assume the git repo is the ROOT folder
    os.chdir(ROOT)

    try:
        subprocess.run(["git", "add", modpack], check=True)
        subprocess.run(["git", "commit", "-m", f"Update {modpack} modpack"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("✅ Successfully pushed to GitHub!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git error: {e}")
        return False
    return True


def main():
    print("=" * 50)
    print("       Modpack Updater")
    print("=" * 50)

    modpacks = get_modpacks()

    if not modpacks:
        print(f"\nNo modpacks found in {ROOT}")
        print("Expected structure:")
        print("  /home/scupa/ijm/nafi/mods/")
        print("  /home/scupa/ijm/potato/mods/")
        return

    print("\nAvailable modpacks:\n")
    for i, name in enumerate(modpacks, 1):
        print(f"  {i}. {name}")

    print()
    choice = input("Which modpack do you want to update? (number or name): ").strip()

    # Allow choosing by number or by name
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(modpacks):
            selected = modpacks[idx]
        else:
            print("Invalid number")
            return
    else:
        if choice in modpacks:
            selected = choice
        else:
            print("Modpack not found")
            return

    print(f"\n→ Selected: {selected}")

    if generate_manifest(selected):
        upload = input("\nUpload to GitHub now? (Y/n): ").strip().lower()
        if upload in ("", "y", "yes"):
            upload_to_github(selected)
        else:
            print("Skipped upload.")


if __name__ == "__main__":
    main()
