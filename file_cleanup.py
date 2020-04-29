import sys
import os
import argparse
import time
import logging as log

# this script looks in the directory and deletes any files older than 8 days (691200 seconds)

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-f", "--folder", required=True, type=str, help="Path to folder to be cleaned up")
ap.add_argument("-d", "--days", required=True, type=int, help="Files modified before DAYS ago will be deleted from FOLDER")
args = vars(ap.parse_args())

# set up logging
log.basicConfig(level=log.INFO, format='%(asctime)s  :%(levelname)s:  %(message)s')
log.info("%s starting.  Folder: %s  Days: %s", sys.argv[0], args["folder"], args["days"])

directory = args["folder"]
now = time.time()

# find files that are outside the time window
files_to_remove = []
for f in os.listdir(directory):
    age = now - os.path.getmtime(directory + "/" + f)
    if age > (args["days"] * 24 * 60 * 60):  # change days to seconds
        files_to_remove.append(directory + "/" + f)

for v in sorted(files_to_remove):
    os.unlink(v)
    # log.info("Removed: %s", v)

log.info("%s completed.  %s files removed", sys.argv[0], len(files_to_remove))
