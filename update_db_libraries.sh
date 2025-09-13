#!/bin/bash

# INFO
# Alphabetically organised files/folders sometimes confuses plex and adding all those paths in the gui is SO tedious.
# This appends {0-9 A-Z} folder paths to you main path e.g. /plexlibrary/Movies/A
# This allows you to better organise Titles Alphabetically.

# Related scripts:
#
# make_dirs_for_videos.sh - Puts files into folders matching their filename
# sort_dirs.py - Moves files/folders to their alphabetical folder e.g. Avatar -> A/Avatar


# db found in "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db"
# library_section ID is found in table `library_sections`


# Arrays for LIBRARY_SECTION_ID and ROOT_PATH
LIBRARY_SECTION_IDS=(9 7 6)  # 6=TV, 7=Movies, 9=Music
ROOT_PATHS=("/media/Movies" "/media/Music" "/media/TV")  # Add corresponding root paths here

#Save the sql to:
SAVE_FILE="plex_db_library_update.txt"

# Fixed values from the provided row
AVAILABLE=1
# May not be needed:
SCANNED_AT=1757372629
CREATED_AT=1757371171
UPDATED_AT=1757372629

# Generate SQL INSERT statements
echo "INSERT INTO section_locations (library_section_id, root_path, available, scanned_at, created_at, updated_at) VALUES" > $SAVE_FILE

# Loop through the arrays
for ((i=0; i<${#LIBRARY_SECTION_IDS[@]}; i++)); do
    LIBRARY_SECTION_ID=${LIBRARY_SECTION_IDS[$i]}
    ROOT_PATH=${ROOT_PATHS[$i]}
	
	# Loop through 0-9 and A-Z
	for char in {0..9} {A..Z}; do
		# Construct the new path
		NEW_PATH="${ROOT_PATH}/${char}"
		# Print the SQL row, with a comma unless it's the last row
		if [ $i -eq $((${#LIBRARY_SECTION_IDS[@]}-1)) ] && [ "$char" == "Z" ]; then
			echo "($LIBRARY_SECTION_ID, '$NEW_PATH', $AVAILABLE, $SCANNED_AT, $CREATED_AT, $UPDATED_AT);" >> $SAVE_FILE
		else
			echo "($LIBRARY_SECTION_ID, '$NEW_PATH', $AVAILABLE, $SCANNED_AT, $CREATED_AT, $UPDATED_AT)," >> $SAVE_FILE
		fi
	done
done
