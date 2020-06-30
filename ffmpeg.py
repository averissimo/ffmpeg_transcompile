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

warnings=[]

existing_files={}

def warn(*args, prefix=""):
    tmp_str = " ".join(args)
    warnings.append(tmp_str)
    print(prefix + 'WARN::', tmp_str)

def print_warnings():
    if len(warnings) == 0:
        return
    print('')
    print('Warnings::')
    for el in warnings:
        print('  * ' + el)

#
# Function to get number of seconds of input
def get_length(filename):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    try:
        return float(result.stdout)
    except ValueError:
        return -1;

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
    try:
        return float(frame_list[0])
    except ValueError:
        return -1;



if os.path.isfile(general_config_path):
    try:
        with open(general_config_path, mode = 'r') as file:
            general_config = yaml.load(file, Loader=yaml.FullLoader)
            # print('loaded general configuration')
    except:
        warn('Could not open general config file ', general_config_path, 'using default options')

        general_config = {
                'flags': '-c:v libx265 -c:a aac -b:a 192k -preset slow -crf 15',
                'lookupMedia': 'MVI_*.MOV',
                'inputExtension': '.MOV',
                'outputExtension': '.mp4',
                'inputFlags': '',
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
            listRaw = yaml.load(file, Loader=yaml.FullLoader)
            list = {}
            for key in listRaw:
                if listRaw[key] is None:
                    list[key] = None
                else:
                    list[key] = {k: v for k, v in listRaw[key].items() if v is not None}
            print('Loaded directory config')
    except:
        print('Error reading config.yml, not really a yml file?')
else:
    fileset = glob.glob(general_config['lookupMedia'])

    list = {}
    for file in fileset:
        list[file] = {'start': None, 'end': None, 'rotate': None, 'options': None, 'suffix': None}

    with open('config.yml', 'w') as outfile:
        yaml.dump(list, outfile, default_flow_style=False)
    print('Writen config.yml, please make the optional changes to the file and run again.')
    print('  files in config.yml:\n    - {}'.format('\n    - '.join(fileset)))
    exit()

for ix in list:
    if not os.path.isfile(ix):
        warn('input file "{0}" doesn\'t exist on this directory'.format(ix))
        continue

    print('')
    print('')
    print('')
    print('')
    print('INFO:: Start of %s' % ix)
    print('')

    print('  INFO:: Metadata:')

    duration = get_length(ix)
    frames = get_frames(ix)
    framerate = frames / duration
    print('    * timestamp: %s' % datetime.utcfromtimestamp(duration).strftime(FMT))
    print('    *   seconds: %s' % duration)
    if frames > 0:
        print('    *    frames: %s' % frames)
        print('    * framerate: %f' % framerate)
    else:
        print('    *    frames: n/a')
        print('    * framerate: n/a')
    print('')


    # print('Processing {0}'.format(ix))
    el = list[ix]
    # output file name
    name = ix.replace(general_config['inputExtension'], '')
    prefix = general_config['inputFlags']
    suffix = ''

    print('  INFO:: Output parameters')
    if el is not None:
        # custom suffix to add to output file
        if 'suffix' in el:
            name = "{0}-{1}".format(name, el['suffix'])

        # Add specific options
        if 'options' in el:
            suffix = '{0} {1}'.format(suffix, el['options'])

        if 'rotate' in el:
            if el['rotate'] == 90:
                suffix = '{0} -vf "transpose=2"'.format(suffix)
            elif el['rotate'] == 180:
                suffix = '{0} -vf "transpose=2,transpose=2"'.format(suffix)
            elif el['rotate'] == 270 or el['rotate'] == -90:
                suffix = '{0} -vf "transpose=1"'.format(suffix)
            else:
                warn('rotate option "%s" not recognized' % el['rotate'])

        # check if it has start/end parameters
        if 'start' in el:
            prefix = '{} -ss {}'.format(prefix, el['start'])
            print('     custom start at: %s' % el['start'])
            # if it also has end parameter, calculate difference in times
            if ('end' in el):
                print('     custom end at: %s' % el['end'])
                tdelta = datetime.strptime(el['end'], FMT) - datetime.strptime(el['start'], FMT)
                # calculate end for ffmpeg based on start
                tdelta_str = str(tdelta)
                suffix = '{0} -t {1}'.format(suffix, tdelta_str)
            else:
                tdelta = datetime.utcfromtimestamp(duration) - datetime.strptime(el['start'], FMT)
                tdelta_str = str(tdelta)

        # when it only has end parameter
        elif ('end' in el):
            print('     custom end at: %s' % el['end'])
            suffix = '{0} -t {1}'.format(suffix, el['end'])

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
    if framerate > 0:
        print('       frames: {0}'.format(tdelta.total_seconds() * framerate))

    # builds ffmpeg command
    cmd = 'ffmpeg {0} {1} -i "{2}" {3} {4} "{5}"'
    cmd = cmd.format(general_config['logLevel'], prefix, ix, general_config['flags'], suffix, name)

    print('')

    # check if file already exists, if so, it skips it
    if os.path.isfile(name):
        print('  INFO:: File %s already exists in directory, skipping...' % name)
        print('')

        duration2 = get_length(name)
        frames2 = get_frames(name)
        framerate2 = frames2 / duration2
        timestamp2 = datetime.utcfromtimestamp(duration2).strftime(FMT)
        if frames2 == -1:
            warn('invalid movie file "%s", can\'t extract metadata' % name, prefix='  ')
        else:
            print('  INFO:: Metadata of existing file:')
            print('    * timestamp: %s' % timestamp2)
            print('    *   seconds: %s' % duration2)
            print('    *    frames: %s' % frames2)
            if framerate > 0:
                print('    * framerate: %f' % framerate2)
            existing_files[name] = {
                'timestamp': str(tdelta_str) + " - " + str(timestamp2),
                'seconds': str(tdelta.total_seconds()) + " - " + str(duration2),
                'framerate': str(framerate) + ' - ' + str(framerate2)
            }
        print('')
    else:
        print('')
        print('  INFO:: ffmpeg command')
        print('')
        print('  $ ', cmd)
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

if len(existing_files) > 0:
    print('')
    print('')
    print('Some output files already existed (%d)' % len(existing_files))
    for key in existing_files:
        print('')
        print('  [{0}]'.format(key))
        print('    * timestamp: {0}'.format(existing_files[key]['timestamp']))
        print('    * seconds: {0}'.format(existing_files[key]['seconds']))
        if framerate > 0:
            print('    * framerate: {0}'.format(existing_files[key]['framerate']))

print_warnings()
