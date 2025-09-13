#!/bin/bash

# This makes directories for each found file and moves them there.

# /media/user/movies/A/Avatar.mp4
# moves to:
# /media/user/movies/A/Avatar/Avatar.mp4

# Check if root directory is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <root_directory> [--debug]"
    exit 1
fi

root_dir="$1"
debug_mode=false

# Check for debug flag
if [ "$2" = "--debug" ]; then
    debug_mode=true
fi

# Check if root directory exists
if [ ! -d "$root_dir" ]; then
    echo "Error: Directory '$root_dir' does not exist."
    exit 1
fi

# Use find to locate files in immediate subdirectories (e.g., A, B, C, 0)
find "$root_dir" -maxdepth 2 -mindepth 2 -type f | while read -r file; do
    # Get filename and extension
    filename=$(basename "$file")
    name="${filename%.*}"

    # Get the subdirectory (e.g., A, B, C)
    subdir=$(dirname "$file")

    # Define target directory in the same subdirectory
    target_dir="$subdir/$name"

    if [ "$debug_mode" = true ]; then
        # In debug mode, show the file and where it would be moved
        echo "Found: '$file' -> Would move to: '$target_dir/$filename'"
    else
        # Create target directory in the same subdirectory
        mkdir -p "$target_dir"

        # Move file to target directory
        mv "$file" "$target_dir/"
        echo "Moved '$file' to '$target_dir/$filename'"
    fi
done
