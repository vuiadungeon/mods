#!/usr/bin/env python3
import os
import hashlib
import json
import subprocess
from pathlib import Path

# ================== CONFIG ==================
# Root folder that contains your modpacks
ROOT = Path("/home/scupa/ijm/2.0/")

# Your GitHub repo settings
GITHUB_USER = "vuiadungeon"
GITHUB_REPO = "mods"
BRANCH = "main"

# Base raw URL
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/"
# ============================================


def sha256(file_path: Path) -> str:
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def get_modpacks() -> list[str]:
    """Return list of folders that contain any files (non-empty modpacks)"""
    modpacks = []
    for item in ROOT.iterdir():
        if item.is_dir():
            # Check if directory has any files (recursive)
            if any(item.rglob("*")):
                modpacks.append(item.name)
    return sorted(modpacks)


def scan_modpack(modpack_path: Path, files: list):
    """Recursively scan ALL files in modpack directory"""
    for file_path in sorted(modpack_path.rglob("*")):
        if file_path.is_file():
            # Skip hidden files and common ignore patterns
            if file_path.name.startswith(".") or file_path.name.endswith(".disabled"):
                continue
            # Skip the manifest itself
            if file_path.name == "manifest.json":
                continue
            # Skip image.png (it's downloaded separately by the GUI)
            if file_path.name == "image.png":
                continue

            rel_path = file_path.relative_to(modpack_path)
            rel_name = f"{modpack_path.name}/{rel_path}"
            uri = BASE_URL + rel_name.replace("\\", "/")
            checksum = sha256(file_path)

            files.append({
                "name": str(rel_path).replace("\\", "/"),
                "uri": uri,
                "checksum": checksum
            })
            print(f"  ✓ {rel_path}")


def generate_manifest(modpack: str):
    modpack_path = ROOT / modpack
    output_file = modpack_path / "manifest.json"

    if not modpack_path.exists():
        print(f"❌ Modpack folder not found: {modpack_path}")
        return False

    files = []
    print(f"\nScanning modpack: {modpack} (all files)\n")

    scan_modpack(modpack_path, files)

    manifest = {
        "name": modpack,
        "files": files
    }

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
        print("  /home/scupa/ijm/nafi/ (any files/folders)")
        print("  /home/scupa/ijm/potato/ (any files/folders)")
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
