import os
import sys
import subprocess
import datetime
import json
import argparse

# Like new_reencode.py, this script just searches for files that would be converted, giving you an extimate of workload.
# If you benchmark conversion for a video then you should get a very rough estimate of time to do all work.
# Isn't multithreaded.

# Configuration
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.m4v', '.mov', '.flv', '.wmv', '.webm'}
MIN_HEIGHT = 720  # Minimum height threshold (pixels)
BITRATE_THRESHOLD = 1350000  # bits/s, for skipping low-bitrate files

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Count videos to be re-encoded and list them in a file.")
parser.add_argument("search_dir", help="Directory to search for video files")
parser.add_argument("--home-dir", default=None, help="Custom home directory for output file (defaults to current working directory)")
args = parser.parse_args()

# Set search directory and output directory
SEARCH_DIR = args.search_dir
HOME_DIR = args.home_dir if args.home_dir and os.path.isdir(args.home_dir) else os.getcwd()

# Output file for listing videos
OUTPUT_FILE = os.path.join(HOME_DIR, f"videos_to_reencode_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt")

# Check directory exists
if not SEARCH_DIR or not os.path.isdir(SEARCH_DIR):
    print(f"Usage: python3 {sys.argv[0]} /path/to/videos [--home-dir]")
    sys.exit(1)

# Get video metadata
def get_metadata(file_path):
    """
    Use ffprobe to get height and bitrate of the video file.
    Returns (height, bitrate) or (None, None) if error.
    """
    try:
        ffprobe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=bit_rate:stream=height,codec_type', '-of', 'json', file_path]
        result = subprocess.run(
            ffprobe_cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        
        # Parse JSON output
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return None, None
        
        # Get bitrate from format
        bitrate = data.get('format', {}).get('bit_rate')
        if bitrate is not None:
            bitrate = int(bitrate)
        
        # Get height from the first video stream
        streams = [s for s in data.get('streams', []) if s.get('codec_type') == 'video' and s.get('height')]
        height = streams[0].get('height') if streams else None
        return height, bitrate
    except Exception:
        return None, None

# Check if video should be re-encoded
def should_reencode(file_path):
    output_file = os.path.splitext(file_path)[0] + '_720p.mkv'
    height, bitrate = get_metadata(file_path)
    
    if height is None or bitrate is None or os.path.isfile(output_file):
        return False
    if height <= MIN_HEIGHT:
        return False
    if bitrate < BITRATE_THRESHOLD:
        return False
    return True

# Main processing
videos_to_reencode = []
for root, _, files in os.walk(SEARCH_DIR):
    for file in sorted(files):
        if file.lower().endswith(tuple(VIDEO_EXTENSIONS)):
            file_path = os.path.join(root, file)
            if should_reencode(file_path):
                videos_to_reencode.append(file_path)

# Write results to file
with open(OUTPUT_FILE, 'w') as f:
    for video in videos_to_reencode:
        f.write(f"{video}\n")

# Print total count
print(f"Total videos to be re-encoded: {len(videos_to_reencode)}")
print(f"List of videos saved to: {OUTPUT_FILE}")