#!/usr/bin/python3

import transcode
import argparse

parser = argparse.ArgumentParser(description='Trancompile video files in current directory.')
parser.add_argument('--copy', help='Use copy codec', action='store_const', const=True)

parser.add_argument('--prores', help='Use prores codec', action='store_const', const=True)
parser.add_argument('--dnx', help='Use DNxhr codec', action='store_const', const=True)
parser.add_argument('--vp9', help='Use vp9 codec', action='store_const', const=True)

args = parser.parse_args()

t = transcode.Transcode()
if args.copy:
    t.set_copy()
elif args.prores:
    t.set_codec('-c:v prores_ks -profile:v 3 -qscale:v 9 -vendor ap10 -pix_fmt yuv422p10le', '-c:a pcm_s24le')
    t.set_suffix('-converted.mov')
elif args.vp9:
    t.set_codec('-c:v libvpx-vp9 -crf 25 -b:v 0')
elif args.dnx:
    t.set_codec('-c:v dnxhd -profile:v dnxhr_hq', '-c:a pcm_s16le')
    t.set_suffix('-converted.mov')


t.run_cmd()
