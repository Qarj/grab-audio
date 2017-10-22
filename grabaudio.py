#!/usr/bin/env python3

version="0.1.0"

import os, sys, time, argparse, stat, subprocess, shlex, codecs, glob
from os.path import splitext

def find_ffmpeg():
    locations = ["C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe", "C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe", "ffmpeg.exe"]
    for l in locations:
        try:
            result = subprocess.run([l, "i"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except FileNotFoundError:
            continue # well, try the next file then
        decoded = result.stdout.decode()
        if decoded.find("the FFmpeg developers"):
            return l
    sys.exit("ffmpeg.exe not found or fails to run")
    return

def splitext_(path):
    return splitext(path)

def file_name(f):
    file_name, extension = splitext_(f)
    return file_name    

def extract_with_cmd(cmd):

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)

    output, errors = proc.communicate()
    decoded = output.decode('cp850')

    if decoded.find("muxing overhead:") > 0:
        print (" ... done!")
        return True

    if decoded.find("already exists") > 0:
        print (" destination file already exists")
        return False

    print ("\n\n\n",file,"UNKNOWN RESPONSE:\n\n",decoded)
    print (decoded,"\n\n")

    return False

def get_extract_method(file):
    file_full = os.path.join(path, file)
    dest_path = os.path.join(path, 'grabaudio')
    dest_no_ext = os.path.join(dest_path, file_name(file))

    cmd = [ffmpeg, "-i", file_full ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
    output, errors = proc.communicate()
    decoded = output.decode('cp850') # western european Windows code page is cp850

    extract = [ffmpeg, "-i", file_full, "-vn", "-acodec", "copy"]

    # we need to find both an audio and video stream to process the file
    if not decoded.find("Video: ") > 0:
        print (" no video stream in file")
        return False, False

    if not decoded.find("Audio: ") > 0:
        print (" no audio stream in file")
        return False, False

    # if multiple audio streams are in the file, the first found will be processed
    # ffmpeg looks at the output file extension to decide which stream to grab
    if decoded.find("Audio: mp3") > 0:
        print (" found mp3 ...", end='')
        return (extract + [dest_no_ext+'.mp3'], dest_path)

    if decoded.find("Audio: aac") > 0:
        print (" found aac ...", end='')
        return (extract + [dest_no_ext+'.m4a'], dest_path)

    if decoded.find("Audio: ac3") > 0:
        print (" found ac3 ...", end='')
        return (extract + [dest_no_ext+'.ac3'], dest_path)

    if decoded.find("Audio: dts") > 0:
        print (" found dts ...", end='')
        return (extract + [dest_no_ext+'.dts'], dest_path)

    print (" did not recognise audio stream\n\n", end='')
    print (decoded,"\n\n")

    return False, False

def process_file(file):
    attempts = 0
    print ("Processing",file,'...', end='')
    command, dest_path = get_extract_method(file)
    if command:
        if not os.path.isdir(dest_path):
            os.makedirs(dest_path)
        success = extract_with_cmd(command)
        if success:
            return 1
        else:
            # file is valid, but some error processing - e.g. destination already exists
            return 0

    # file is not valid - e.g. did not find both an audio and video stream
    return 0

def grabaudio(files):
    ok = 0
    fails = 0
    for f in files:
        if os.path.isdir(os.path.join(path, f)):
            continue
        worked = process_file(f)
        ok += worked
        fails += (1-worked)
    return ok, fails

parser = argparse.ArgumentParser(description='Grab audio from video files.')
parser.add_argument('--path', dest='path', required=False, action='store', help='Folder containing video files, will output in new a subfolder grabaudio')
parser.add_argument('--version', action='version', version=version)
parser.add_argument('--verbose', action='store_true', dest='verbose', default=True, help='Will output extra info ... maybe')
args = parser.parse_args()

if args.path:
    path = args.path
else:
    sys.exit("Must specify target folder path")

if not os.path.isdir(path):
    sys.exit("target folder " + path + " not found")

print ("Grab audio from video files at", path, "\n")

ffmpeg = find_ffmpeg()

files = os.listdir(path)

ok, failed = grabaudio(files)

print ("\n", ok, "video files processed OK [", failed, "failed].")
