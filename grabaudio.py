#!/usr/bin/env python3

version="0.2.0"

import os, sys, time, argparse, stat, subprocess, shlex, codecs, glob
from os.path import splitext

def find_ffmpeg():
    locations = ["ffmpeg", "/ffmpeg/bin/ffmpeg","C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe", "C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe"]
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

def file_name_no_ext(f):
    file_name, extension = splitext_(f)
    return file_name    

def path_only(full_path):
    return os.path.dirname(os.path.abspath(full_path))

def extract_with_cmd(cmd):

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)

    output, errors = proc.communicate()
    decoded = output.decode('cp850')

    if decoded.find("muxing overhead:") > 0:
        print (" ... OK!")
        return True

    if decoded.find("already exists") > 0:
        print (" ... destination file already exists")
        return False

    print (" ... \n\n\nUNKNOWN RESPONSE:\n\n",decoded)

    return False

def get_extract_method(file_full):
    #file_full = os.path.join(path, file)
    dest_path = os.path.join(path_only(file_full), 'grabaudio')
    #print ('dest_path', dest_path)
    dest_no_ext = os.path.join(dest_path, file_name_no_ext(os.path.basename(file_full)))
    #print ('dest_no_ext', dest_no_ext)

    cmd = [ffmpeg, "-i", file_full ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
    output, errors = proc.communicate()
    decoded = output.decode('cp850') # western european Windows code page is cp850

    extract = [ffmpeg, "-i", file_full, "-vn", "-acodec", "copy"]

    # we need to find both an audio and video stream to process the file
    if not decoded.find("Video: ") > 0:
        print ("  no video stream in file")
        return False, False

    if not decoded.find("Audio: ") > 0:
        print ("  no audio stream in file")
        return False, False

    # if multiple audio streams are in the file, the first found will be processed
    # ffmpeg looks at the output file extension to decide which stream to grab
    if decoded.find("Audio: mp3") > 0:
        print ("[found mp3]", end='')
        return (extract + [dest_no_ext+'.mp3'], dest_path)

    if decoded.find("Audio: aac") > 0:
        print ("[found aac]", end='')
        return (extract + [dest_no_ext+'.m4a'], dest_path)

    if decoded.find("Audio: ac3") > 0:
        print ("[found ac3]", end='')
        return (extract + [dest_no_ext+'.ac3'], dest_path)

    if decoded.find("Audio: dts") > 0:
        print ("[found dts]...", end='')
        return (extract + [dest_no_ext+'.dts'], dest_path)

    print (" did not recognise audio stream\n\n", end='')
    print (decoded,"\n\n")

    return False, False

def process_file(file_full):
    attempts = 0
    print (" ",file_full,'-> ', end='')
    command, dest_path = get_extract_method(file_full)
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

def grabaudio(dir):
    ok = 0
    fails = 0
    for file_name in os.listdir(dir):
        #print ('file_name',file_name)
        file_full = os.path.join(dir, file_name)
        #print ('file_full',file_full)
        if os.path.isdir(file_full) and not (os.path.basename(file_full) == 'grabaudio'):
            sub_ok, sub_fails = grabaudio(file_full)
            ok += sub_ok
            fails += sub_fails
        if os.path.isdir(file_full):
            continue # mustbe called grabaudio
        worked = process_file(file_full)
        ok += worked
        fails += (1-worked)
    return ok, fails

parser = argparse.ArgumentParser(description='Grab audio from video files.')
parser.add_argument('path', metavar='PATH', help='Folder containing video files, will output in new a subfolder grabaudio')
parser.add_argument('--version', action='version', version=version)
parser.add_argument('--verbose', action='store_true', dest='verbose', default=True, help='Will output extra info ... maybe')
args = parser.parse_args()

if not os.path.isdir(args.path):
    sys.exit("target folder " + args.path + " not found")

print ("Grab audio from video files in", args.path, "\n")

ffmpeg = find_ffmpeg()

ok, failed = grabaudio(args.path)

print ("\n", ok, "video files processed OK [", failed, "files failed].")
