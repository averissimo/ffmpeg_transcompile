#!/usr/bin/python3

import transcode
import argparse

parser = argparse.ArgumentParser(description='Trancompile video files in current directory.')
parser.add_argument('--copy', help='Use copy codec', action='store_const', const=True)

args = parser.parse_args()

t = transcode.Transcode()
if args.copy:
    t.set_copy()

t.run_cmd()
