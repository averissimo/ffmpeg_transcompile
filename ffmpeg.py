import yaml
import os
import os.path
import glob
from datetime import datetime, timedelta
import subprocess
import time

# Load general configuration
#  should have the ffmpeg_python.yml file in the same directory as this file
#
# Possible options:
#  - flags: ffmpeg codec and other intermediate options
#  - lookupMedia: filter files in directory to be transcoded
#  - inputExtension: extension of input files
#  - outputExtension: extension of output files
#  - logLevel: ffmpeg log level options
general_config_path = os.path.join(os.path.dirname(__file__), 'ffmpeg_python.yml')


# duration in ffmpeg format hours:minutes:seconds
FMT = '%H:%M:%S'

#
# Function to get number of seconds of input
def get_length(filename):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return float(result.stdout)

#
# Function to get number of frames of input
def get_frames(filename):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "stream=nb_frames", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True)
    frame_list = result.stdout.split('\n')
    return float(frame_list[0])



if os.path.isfile(general_config_path):
    try:
        with open(general_config_path, mode = 'r') as file:
            general_config = yaml.load(file, Loader=yaml.FullLoader)
            print('loaded general configuration')
    except:
        print('WARN :: Could not open general config file', general_config_path, 'using default options')
        general_config = {
                'flags': '-c:v libx265 -c:a aac -b:a 192k -preset slow -crf 15',
                'lookupMedia': 'MVI_*.MOV',
                'inputExtension': '.MOV',
                'outputExtension': '.mp4',
                'logLevel': '-loglevel repeat+level+info'
        }

# Folder-level configuration
#  Allows to define which files to convert with
#  start and end times (both absolute)
# 
# Example:
# <file name>:
#   start: <starting time in HH:MM:SS - hours:minutes:seconds>
#   end: <ending time in HH:MM:SS>
#
# note: ending time is absolute, this tool will calcualte ffmpeg
#  -t option relative time
if os.path.isfile('config.yml'):
    try:
        with open(r'./config.yml') as file:
            list = yaml.load(file, Loader=yaml.FullLoader)
            print('Loaded directory config')
    except:
        print('Error reading config.yml, not really a yml file?')
else:
    fileset = glob.glob(general_config['lookupMedia'])
    
    list = {}
    for file in fileset:
        list[file] = None

for ix in list:
    print('')
    print('')
    print('')
    print('')
    print('INFO:: Start of %s' % ix)
    print('')
    print('INFO:: Metadata:')
    print('    Duration of video:')

    duration = get_length(ix)
    frames = get_frames(ix)
    framerate = frames / duration
    print('       *  timestamp: %s' % datetime.utcfromtimestamp(duration).strftime(FMT))
    print('       * in seconds: %s' % duration)
    print('       *  in frames: %s' % frames)
    print('     Framerate: %f' % framerate)
    print('')

    if not os.path.isfile(ix):
        print('WARN :: input file {0} doesn\'t exist on this directory'.format(ix))
        continue
    
    # print('Processing {0}'.format(ix))
    el = list[ix]
    # output file name
    name = ix.replace(general_config['inputExtension'], '')
    prefix = ''
    suffix = ''

    print('INFO:: Output parameters')
    if el is not None:
        # custom suffix to add to output file
        if 'name' in el:
            name = "{0}-{1}".format(name, el['name'])

        # check if it has start/end parameters
        if 'start' in el:
            prefix = '-ss {0}'.format(el['start'])
            print('     custom start at: %s' % el['start'])
            # if it also has end parameter, calculate difference in times
            if ('end' in el):
                print('     custom end at: %s' % el['end'])
                tdelta = datetime.strptime(el['end'], FMT) - datetime.strptime(el['start'], FMT)
                # calculate end for ffmpeg based on start
                tdelta_str = str(tdelta)
                suffix = '-t {0}'.format(tdelta_str)
            else:
                tdelta = datetime.utcfromtimestamp(duration) - datetime.strptime(el['start'], FMT)
                tdelta_str = str(tdelta)
            
        # when it only has end parameter
        elif ('end' in el):
            print('     custom end at: %s' % el['end'])
            suffix = '-t {0}'.format(el['end'])
            
            temp = time.strptime(el['end'], FMT)
            tdelta = timedelta(hours = temp.tm_hour, minutes = temp.tm_min, seconds = temp.tm_sec)
            tdelta_str = str(tdelta)

        # calculate auxiliar info when no custom start or end parameter exist
        else:
            tdelta = datetime.utcfromtimestamp(duration) - datetime.utcfromtimestamp(0)
            tdelta_str = str(tdelta)

    # calculate auxiliar info when no custom start or end parameter exist
    else:
        tdelta = datetime.utcfromtimestamp(duration) - datetime.utcfromtimestamp(0)
        tdelta_str = str(tdelta)

    # adds extension to output file name
    name = '{0}{1}'.format(name, general_config['outputExtension'])
   
    print('     output file will be called: %s' % name)
    print('')
    print('     duration: {0}'.format(tdelta_str))
    print('      seconds: {0}'.format(tdelta.total_seconds()))
    print('       frames: {0}'.format(tdelta.total_seconds() * framerate))
            
    # builds ffmpeg command
    cmd = 'ffmpeg {0} {1} -i "{2}" {3} {4} "{5}"'
    cmd = cmd.format(general_config['logLevel'], prefix, ix, general_config['flags'], suffix, name)
    
    print('')
    print('INFO:: ffmpeg command')
    print('')
    print('$ ', cmd)
    print('')

    # check if file already exists, if so, it skips it
    if os.path.isfile(name):
        print('WARN:: File %s already exists in directory, skipping...' % name)  

        print('WARN:: Metadata of existing file:')
        print('    Duration of video:')

        duration = get_length(name)
        frames = get_frames(name)
        framerate = frames / duration
        print('       *  timestamp: %s' % datetime.utcfromtimestamp(duration).strftime(FMT))
        print('       * in seconds: %s' % duration)
        print('       *  in frames: %s' % frames)
        print('     Framerate: %f' % framerate)
        print('')
    else:
        print('INFO:: output of ffmpeg')
        print('')
        subprocess.run(cmd, shell=True)
        #try:
        #    result
        #    with open("ffmepg_log.txt", 'w') as text_file:
        #        text_file.write(resut.stdout)
        #    with open("ffmepg_error.txt", 'w') as text_file:
        #        text_file.write(resut.stderr)
        #except NameError:
        #    pass
        #    # do nothing
    
    print('')
    print('-- end of %s -----------------------------------------------------------------------------------------' % ix)


