import os
import sys
import subprocess
import datetime
import shutil
import json

# NOTES:

# When run in ssh [in PuTTY] there seems to be a bug after exiting...
# tty does not output typed text...
# type 'stty sane <ENTER>' to fix it (you won't see it typed)

# Script function.

# searches for video files, gets metadata using ffprobe and down converts the videos using nvenc [CUDA] Then moves the originals.
# Useful for saving disk space and reducing overhead if PLEX is set to deliver content at lower resolutions.

# TODO:
# If moving originals to other drives then ln could be used [after moving] to link files, keeping their location intact so PLEX will see 2 versions to offer.

# Global counter
process_count = 0
#output more messages for debugging
DEBUG=False

# Configuration - Customize these
SEARCH_DIR = sys.argv[1] if len(sys.argv) > 1 else None

CHECK_MOUNT = False  # Set to False to skip mount check

BACKUP_DEV = "/mnt/BACKUP"  # backup drive
# even with backup_dir set; the originals should be stored relative to their original location
BACKUP_DIR = sys.argv[2] if len(sys.argv) > 2 else "originals"  # Subdirectory in backup drive

VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.m4v', '.mov', '.flv', '.wmv', '.webm'}
MIN_HEIGHT = 720  # Minimum height threshold (pixels)
QUALITY_MODE = False  # True for -qp (quality), False for -b:v (bitrate)
QUALITY_VALUE = 23  # For -qp (18-28 typical, lower = better)
BITRATE_THRESHOLD = 1350000  # bits/s, for skipping low-bitrate files
TARGET_BITRATE = 950  # kb/s, for bitrate mode

NUM_THREADS = 4  # Number of parallel threads

# Log file setup
LOG_FILE = os.path.join(os.path.expanduser('~') or os.getcwd(), f"processing_log_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt")
PROCESS_LOG = os.path.join(os.path.expanduser('~') or os.getcwd(), f"current_encoding_files_"+str(datetime.datetime.now().strftime('%H%M%S'))+".txt")

# Check if BACKUP_DIR exists and is mounted, exit if not
def is_drive_mounted(mount_point):
    if CHECK_MOUNT:
        try:
            subprocess.run("mount", BACKUP_DEV, check=True)
            if not is_drive_mounted(BACKUP_DEV):
                print(f"Error: Backup drive '{BACKUP_DEV}' is not mounted.")
                sys.exit(1)
        except subprocess.CalledProcessError as e:
            print(f"Error: Backup drive '{e}' failed.")
            sys.exit(1)

# We need to ensure the backup directory is mounted and try to mount if not
# requires the `user` option to be set in fstab for this to work without password/sudo

# USAGE
# Check directory to work in exists
if not SEARCH_DIR or not os.path.isdir(SEARCH_DIR):
    print(f"Usage: python {sys.argv[0]} /path/to/videos [dir name for originals backup]")
    print(f"-- backup dir should be relative to {BACKUP_DEV}, e.g. 'originals/movies'")
    sys.exit(1)

# Logging function
def log_message(message, level="info"):
    if level == "debug" and not DEBUG:
        return
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry + '\n')

# Create processing file manager
def create_processing_file(num_threads):
    processing_file = PROCESS_LOG
    # Clear old processing file
    if os.path.exists(processing_file):
        os.remove(processing_file)

    processing_files = {}

    def add_file(file_path, output_path):
        processing_files[file_path] = output_path
        with open(processing_file, "a") as f:
            f.write(f"{file_path} -> {output_path}\n")

    def remove_file(file_path):
        if file_path in processing_files:
            del processing_files[file_path]
            with open(processing_file, "w") as f:
                for file_path, output_path in processing_files.items():
                    f.write(f"{file_path} -> {output_path}\n")

    def get_processing_files():
        return processing_files

    return add_file, remove_file, get_processing_files

# File moving function
def move_file_with_relative_path(source_file, source_mount_point, destination_root):
    """
    Move a file to a new location, preserving its relative path from the source mount point.
    
    Args:
        source_file (str): Full path to the source file.
        source_mount_point (str): The base path (mount point) to strip from the source file.
        destination_root (str): The new root directory where the file's relative path will be recreated.
    """
    # Ensure the source file exists
    if not os.path.isfile(source_file):
        log_message(f"Source file does not exist: {source_file}")
        return
    
    # Get the relative path by stripping the source mount point
    if not source_file.startswith(source_mount_point):
        log_message(f"Source file {source_file} is not under mount point {source_mount_point}")
        return
    
    relative_path = os.path.relpath(source_file, source_mount_point)
    
    # Construct the full destination path
    destination_path = os.path.join(destination_root, relative_path)
    
    # Create the destination directory if it doesn't exist
    destination_dir = os.path.dirname(destination_path)
    os.makedirs(destination_dir, exist_ok=True)
    
    # Move the file to the destination
    shutil.move(source_file, destination_path)
    remove_file(source_file)
    log_message(f"Moved: {source_file} => {destination_path}")

# Get video metadata
def get_metadata(file_path):

    """
    Use ffprobe to get height and bitrate of the video file.
    Returns (height, bitrate) or (None, None) if error.
    """
    try:
        # Construct and print the ffprobe command for debugging
        ffprobe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=bit_rate:stream=height,codec_type', '-of', 'json', file_path]
        log_message(f' '.join(ffprobe_cmd), level="debug")
        
        result = subprocess.run(
            ffprobe_cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        
        if result.stderr:
            log_message(f"ffprobe stderr for {file_path}: {result.stderr}")

        ## skipping return code check to handle files with minor issues

        # Parse JSON output
        try:
            data = json.loads(result.stdout)
            log_message(f"ffprobe JSON for {file_path}: {result.stdout}", level="debug")
        except json.JSONDecodeError as e:
            log_message(f"JSON decode error for {file_path}: {e}")
            return None, None
        
        # Get bitrate from format
        bitrate = data.get('format', {}).get('bit_rate')
        if bitrate is not None:
            bitrate = int(bitrate)
        
        # Get height from the first video stream
        streams = [s for s in data.get('streams', []) if s.get('codec_type') == 'video' and s.get('height')]
        height = streams[0].get('height') if streams else None
        log_message(f"Height: {height}, Bitrate: {bitrate} for {file_path}", level="debug")
        return height, bitrate
    except Exception as e:
        log_message(f"Exception in get_video_info for {file_path}: {e}")
        return None, None
        
# Construct FFmpeg command
def run_ffmpeg_cmd(input_path, output_path):
    base_cmd = [
        'ffmpeg', '-hide_banner', '-y', '-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda',
        '-i', input_path, '-vf', 'scale_cuda=-2:720', '-c:a', 'aac', '-b:a', '128k', '-ac', '2'
    ]
    if QUALITY_MODE:
        return base_cmd + ['-c:v', 'h264_nvenc', '-qp', str(QUALITY_VALUE), output_path]
    else:
        base_cmd = base_cmd + ['-c:v', 'h264_nvenc', '-b:v', f'{TARGET_BITRATE}k', output_path]
        log_message(f"FFmpeg command: {' '.join(base_cmd)}", level="debug")
        return base_cmd

# Process a video file
def process_video(file_path):
    #filename = os.path.basename(file_path)
    # suffix of _720p.mkv
    # This also sets the file extension for ffmpegs output.
    output_file = os.path.splitext(file_path)[0] + '_720p.mkv'

    log_message(f"=== Processing: {file_path}", level="debug")

    # Get metadata
    height, bitrate = get_metadata(file_path) 

    # Check criteria to begin conversion
    if height is None or bitrate is None or os.path.isfile(output_file) or height <= MIN_HEIGHT or bitrate < BITRATE_THRESHOLD:
        log_message(f"<> SKIP: {file_path} (criteria not met for conversion => height: {height}. bitrate: {bitrate}).", level="info")
        return
    
    try:
        # log current job
        add_file(file_path, output_file)
        #Show current processing files
        processing_files=get_processing_files()
        print(processing_files)

        result = subprocess.run(
            run_ffmpeg_cmd(file_path, output_file),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, 
            text=True, 
            check=True
        )
        

        try:
            # move original to backup
            move_file_with_relative_path(file_path, '/media/path', os.path.join(BACKUP_DEV, BACKUP_DIR))
        except Exception as e:
            log_message(f"Error moving file {file_path} to backup: {e}")
            return
        # Success point
        log_message(f"+++ SUCCESS: {file_path} re-encoded to {output_file}.")

    except subprocess.CalledProcessError as e:
        log_message(f"FFmpeg error for {file_path}: {e.stderr}")
        if os.path.isfile(output_file):
            os.remove(output_file)
            log_message(f"Removed incomplete output file: {output_file}")

# Main loop
"""
    for root, dirs, files in os.walk(SEARCH_DIR):
        for file in sorted(files):
            if file.lower().endswith(tuple(VIDEO_EXTENSIONS)):
                file_path = os.path.join(root, file)
                process_video(file_path)
"""
# Multithreaded processing
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
    executor.map(process_video, [
        os.path.join(root, file) for root, _, files in os.walk(SEARCH_DIR)
          for file in files 
            if file.lower().endswith(tuple(VIDEO_EXTENSIONS))
        ]
    )

log_message("Processing complete.")

add_file, remove_file, get_processing_files = create_processing_file(NUM_THREADS)