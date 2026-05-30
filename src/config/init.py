# Create empty __init__.py files
from pathlib import Path

init_files = [
	"src/__init__.py",
	"src/config/__init__.py",
	"src/data/__init__.py",
	"src/features/__init__.py",
	"src/models/__init__.py",
	"src/training/__init__.py",
	"src/prediction/__init__.py",
	"src/utils/__init__.py",
]

for file_path in init_files:
	Path(file_path).touch()
