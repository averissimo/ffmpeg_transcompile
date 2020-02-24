import yaml
import os
import os.path
import glob
from datetime import datetime
import subprocess

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
    if not os.path.isfile(ix):
        print('WARN :: file {0} doesn\'t exist on this directory'.format(ix))
        continue
    # print('Processing {0}'.format(ix))
    el = list[ix]
    # output file name
    name = ix.replace(general_config['inputExtension'], general_config['outputExtension'])
    prefix = ''
    suffix = ''
    if el is not None:
        if 'name' in el:
            name = "{1}-{0}".format(el['name'], name)
        if 'start' in el:
            prefix = '-ss {0}'.format(el['start'])
            if ('end' in el):
                FMT = '%H:%M:%S'
                tdelta = datetime.strptime(el['end'], FMT) - datetime.strptime(el['start'], FMT)
                # calculate end for ffmpeg based on start
                suffix = '-t {0}'.format(tdelta)
        elif ('end' in el):
            suffix = '-t {0}'.format(el['end'])
    cmd = 'ffmpeg {0} {1} -i {2} {3} {4} {5}'
    cmd = cmd.format(general_config['logLevel'], prefix, ix, general_config['flags'], suffix, name)
    if os.path.isfile(name):
        print('INFO:: File %s already exists in directory, skipping...' % name)
    else:
        print('$ ffmpeg', cmd)
        print('')
        print('(output of ffmpeg)')
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
    print('-- end of ffmpeg -----------------------------------------------------------------------------------------')


