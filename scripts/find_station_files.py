import os
from pathlib import Path

print("="*70)
print("FILE DIAGNOSTIC - Finding Your Station Files")
print("="*70)

# Check multiple directories
search_dirs = [
    "data/raw/stations",
    "data/raw",
    ".",
]

print("\nSearching directories:")
for dir_path in search_dirs:
    print(f"\n📁 {dir_path}:")
    if Path(dir_path).exists():
        files = list(Path(dir_path).glob("*"))
        if files:
            for f in files:
                if f.is_file():
                    print(f"   ✓ {f.name} ({f.stat().st_size} bytes)")
        else:
            print("   (empty)")
    else:
        print("   ✗ Directory does not exist")

print("\n" + "="*70)
print("Looking for files containing:")
print("  - 'Met Stations'")
print("  - 'Parameters'")
print("  - 'Rainfall'")
print("="*70)

# Search recursively
print("\nSearching entire data/ folder:")
if Path("data").exists():
    for root, dirs, files in os.walk("data"):
        for file in files:
            if any(keyword in file for keyword in ['Met', 'Station', 'Parameter', 'Rainfall', 'station']):
                full_path = Path(root) / file
                print(f"   ✓ {full_path}")
else:
    print("   ✗ data/ folder not found")