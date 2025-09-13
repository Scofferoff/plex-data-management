import os
import shutil
import sys

script_name = os.path.basename(__file__)

# This finds all files and directories in the specified base path
# and moves them into subdirectories based on their starting letter.
# Directories starting with "The " or "The_" are sorted by the 5th letter.
# Existing directories created by this script are ignored to prevent nesting.

# It does not handle name conflicts (e.g., two items named "Avatar").

# It does not make directories for the files themselves as plex likes to use.
# Use make_dirs_for_videos.sh to do that.

# cd to the directory you want to run this from before use
default_base_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

print(f"Default root directory: {default_base_path}")
user_input = input("Is this the desired root directory? (Enter to accept, or enter a new path): ").strip()

base_path = default_base_path if user_input == "" else user_input

base_path = os.path.abspath(base_path) # noramlize the path

# List of names to ignore (case-insensitive)
ignore_list = ["Movies", "Hidden", "Dont_sort"]

# List of potential target directories to skip during processing
created_dirs = set()

# List all items (files and directories) in the base path
items = os.listdir(base_path)

# Filter out ignored names
items = [item for item in items if item.lower() not in [name.lower() for name in ignore_list] and item != script_name]

# First pass to identify directories created by previous runs
for item in items:
    item_path = os.path.join(base_path, item)
    if os.path.isdir(item_path):
        if item.startswith("The ") or item.startswith("The_"):
            target_dir = item[4].upper()  # Use the 5th letter
        else:
            target_dir = item[0].upper()  # Use the 1st letter
        
        # Mark the target directory as created by the script
        created_dirs.add(target_dir)

# Second pass to move directories and files, skipping created directories
for item in items:
    item_path = os.path.join(base_path, item)
    
    # Skip directories that are identified as target directories
    if item in created_dirs:
        continue

    if os.path.isdir(item_path):
        if item.startswith("The ") or item.startswith("The_"):
            target_dir = item[4].upper()  # Use the 5th letter
        else:
            target_dir = item[0].upper()  # Use the 1st letter
        
        target_path = os.path.join(base_path, target_dir)

        # Create the target directory if it doesn't exist
        os.makedirs(target_path, exist_ok=True)

        # Move the directory to the target directory
        shutil.move(item_path, os.path.join(target_path, item))

    elif os.path.isfile(item_path):
        # Handle files similarly to directories
        if item.startswith("The ") or item.startswith("The_"):
            target_dir = item[4].upper()  # Use the 5th letter
        else:
            target_dir = item[0].upper()  # Use the 1st letter
        
        target_path = os.path.join(base_path, target_dir)

        # Create the target directory if it doesn't exist
        os.makedirs(target_path, exist_ok=True)

        # Move the file to the target directory
        shutil.move(item_path, os.path.join(target_path, item))

print("Directories and files sorted and moved.")
