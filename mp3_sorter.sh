#!/bin/bash

# Gathers mp3 metadata [in current dir] and attempts to sort by Artist, Album.


# Check if eyeD3 is installed
if ! command -v eyeD3 &> /dev/null; then
    echo "eyeD3 is not installed. Please install it first."
    exit 1
fi

# Loop through all MP3 files in the current directory
for file in *.mp3; do
    # Skip if no MP3 files are found
    [[ -f "$file" ]] || continue

    # Extract metadata using eyeD3
    track_raw=$(eyeD3 --no-color "$file" | grep '^track: ' | awk '{print $2}')
    # Check if track_raw starts with a digit
    if [[ $track_raw =~ ^[0-9]+ ]]; then
        track=$(echo "$track_raw" | cut -d'/' -f1 | sed 's/^0*//' ) #| tr -d '[:punct:]' | tr ' ' '_')
    else
        track="0"
    fi
    album=$(eyeD3 --no-color "$file" | grep '^album: ' | awk '{for (i=2; i<=NF; i++) print $i}' | tr '\n\r' ' ' | tr -d '[:punct:]' | tr ' ' '_' | sed 's/_*$//')
    artist=$(eyeD3 --no-color "$file" | grep '^artist: ' | awk '{for (i=2; i<=NF; i++) print $i}' | tr '\n\r' ' ' | tr -d '[:punct:]' | tr ' ' '_' | sed 's/_*$//')
    title=$(eyeD3 --no-color "$file" | grep '^title: ' | awk '{for (i=2; i<=NF; i++) print $i}' | tr '\n\r' ' ' | tr -d '[:punct:]' | tr ' ' '_' | sed 's/_*$//')

    # Handle missing metadata
    track=${track:-"0"}
    album=${album:-"UnknownAlbum"}
    artist=${artist:-"UnknownArtist"}
    title=${title:-"UnknownTitle"}

    # Construct new filename
	# if it's set to the meta title then we can get "unknownTitle.mp3" and ruin things.
    newname="${track}_${file}.mp3"

    # Rename the file
    if [[ "$file" != "$newname" ]]; then
		mkdir -p "$artist/$album"
        mv -i "$file" "$artist/$album/$newname"
        echo "Renamed: $file to '$artist/$album/$newname'"
    else
        echo "No rename needed for: $file"
    fi
done