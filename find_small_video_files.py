import os

# Looks for video files below a certain size. can be useful for decluttering or finding corrupted files.

# Important!
# Run this from the folder you want to search from.
# Edit the path in awk to produce a correct path for VLC.

# Define common video file extensions
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.mpeg', '.mpg'}
# Define size limit (4MB in bytes)
SIZE=4 # size in megabytes
SIZE_LIMIT = SIZE * 1024 * 1024  # SIZE in bytes

def find_video_files():
    video_files = []
    
    # Walk through all directories and subdirectories
    for root, _, files in os.walk('.'):
        for file in files:
            # Check if the file has a video extension
            if os.path.splitext(file)[1].lower() in VIDEO_EXTENSIONS:
                file_path = os.path.join(root, file)
                # Get file size in bytes
                file_size = os.path.getsize(file_path)
                # Check if file size is below 4MB
                if file_size < SIZE_LIMIT:
                    video_files.append((file_path, file_size))
    
    return video_files

def save_to_file(video_files):
    with open('video_files_below_{SIZE}mb.txt', 'w', encoding='utf-8') as f:
        for file_path, file_size in video_files:
            # Convert size to MB for readability
            size_mb = file_size / (1024 * 1024)
            f.write(f"{file_path} ({size_mb:.2f} MB)\n")

def main():
    video_files = find_video_files()
    if video_files:
        save_to_file(video_files)
        print(f"Found {len(video_files)} video files below {SIZE}MB. List saved to 'video_files_below_{SIZE}MB.txt'.")
    else:
        print("No video files below ${SIZE}MB found.")

if __name__ == "__main__":
    main()

# make the list a vlc playlist using awk:
# uncomment to enable or paste awk_command to cli.
#print(f"Run/Edit the follwing command to make a VLC playlist... ")
#input(f"Press Enter to create a vlc playlist, CTRL+C to exit now")
# Edit the print path as required. \\ for windows file paths, j:\\movies\\best_of\\etc
#awk_command=r"""awk '{sub(/ \([0-9.]+ MB\)/, ""); sub(/^\.\//, ""); gsub(/\//, "\\"); print "/mnt/Movies_and_Music/Movies/"  $0}' video_files_below_{SIZE}MB.txt > vlc_playlist.m3u"""
#os.system(awk_command)


