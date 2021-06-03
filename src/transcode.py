import glob
import yaml
import os.path
import subprocess
from datetime import datetime
import time
import re


class Video:
    def __init__(self, path):
        self._path = path

    @property
    def path(self):
        return self._path

    def get_duration(self, duration=0):
        if duration == 0:
            duration = self.get_length()

        duration_str = self.parse_seconds(duration).strftime(Transcode.FMT)

        return duration_str

    def get_length(self):
        result = self.ffprobe('duration', self.path)
        values = result.stdout.split('\n')
        try:
            return float(values[0])
        except ValueError:
            return -1;

    def get_frames(self):
        result = self.ffprobe('nb_frames', self.path)
        values = result.stdout.split('\n')
        try:
            return float(values[0])
        except ValueError:
            return -1;

    @staticmethod
    def parse_duration(duration_str: str):
        duration_str = duration_str.strip()

        if re.match(r"^\d\d:\d\d:\d\d\.\d{1,6}$", duration_str):
            result = datetime.strptime(duration_str, Transcode.FMT)
        elif re.match(r"^\d\d:\d\d:\d\d$", duration_str):
            result = datetime.strptime(duration_str, Transcode.FMT.replace(".%f", ""))
        elif re.match(r"^\d\d:\d\d:\d\d\.\d+$", duration_str):
            duration_str = re.sub(r'(\d\d:\d\d:\d\d\.\d{1,6})\d+', '\\1', duration_str)
            result = datetime.strptime(duration_str, Transcode.FMT)
        elif re.match(r"^\d\d:\d\d:\d\d\.$", duration_str):
            duration_str = re.sub(r'(\d\d:\d\d:\d\d)\.', '\\1', duration_str)
            result = datetime.strptime(duration_str, Transcode.FMT)
        else:
            raise Exception("Unknown duration, please use HH:MM:SS, HH:MM:SS.MS or a number representing seconds.")
        result = result.replace(year=1970)
        return (result - Video.parse_seconds(0)).total_seconds()

    @staticmethod
    def strftime(seconds):
        result = datetime.utcfromtimestamp(seconds)
        return datetime.strftime(result, Transcode.FMT)

    @staticmethod
    def parse_seconds(seconds):
        result = datetime.utcfromtimestamp(seconds)

        return result

    @staticmethod
    def ffprobe(stream, path):
        cmd = ["ffprobe", "-v", "error",
               "-select_streams", "v:0",
               "-show_entries", f"stream={stream}",
               "-of", "default=noprint_wrappers=1:nokey=1",
               path]
        return subprocess.run(cmd,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,
                              text=True)


class VideoConfig(Video):
    def __init__(self, path: str, options: dict, config: dict = None):
        self._path = path
        if config is None:
            self._opts = {
                'name': path,
                'start': 0,
                'end': self.get_length(),
                'rotate': 0,
                'options': '',
                'suffix': options['outputExtension'],
                'codec_video': options['codec_video'],
                'codec_audio': options['codec_audio']
            }
        else:
            if "start" in config:
                config["start"] = Video.parse_duration(config["start"])
            if "end" in config:
                config["end"] = Video.parse_duration(config["end"])
            self._opts = config

        self._path = path
        self._name = re.sub(options['inputExtension'], '', path)

    def set_codecs(self, video="-c:v copy", audio="-c:a copy"):
        self._opts["codec_video"] = video
        self._opts["codec_audio"] = audio

    @property
    def video(self):
        if "codec_video" in self._opts:
            return self._opts["codec_video"]
        else:
            return "-c:v copy"

    @property
    def audio(self):
        if "codec_audio" in self._opts:
            return self._opts["codec_audio"]
        else:
            return "-c:a copy"

    @property
    def opts(self):
        tmp_opts = self._opts
        if self.start == 0:
            tmp_opts["start"] = "00:00:00"
        else:
            tmp_opts["start"] = Video.strftime(self.start)
        tmp_opts["end"] = Video.strftime(self.end)
        return tmp_opts

    @property
    def options(self):
        if "options" in self._opts:
            return self._opts["options"]
        else:
            return ""

    @property
    def start(self):
        if "start" in self._opts:
            return self._opts["start"]
        else:
            return 0

    @property
    def rotate(self):
        if "rotate" in self._opts:
            return self._opts["rotate"]
        else:
            return 0

    @property
    def tdelta(self):
        return self.end - self.start

    @property
    def end(self):
        if "end" in self._opts:
            return self._opts["end"]
        else:
           return self.get_length()

    def __repr__(self):
        return f"VideoConfig(path: {self.path}, opts: {self._opts})"

    @property
    def name(self):
        if "suffix" in self._opts and self._opts['suffix'].strip() != "":
            return f"{self._name}{self._opts['suffix'].strip()}"
        else:
            return self._name

    @property
    def path(self):
        return self._path

    def set_suffix(self, new_suffix):
        self._opts["suffix"] = new_suffix

    @property
    def suffix(self):
        if "suffix" in self._opts:
            return self._opts["suffix"]
        else:
            return Transcode.OPTS["outputExtension"]


class Transcode:
    """
    Class to build commands from config.yml file or from files in directory
    """
    OPTS = {
        'codec_video': '-c:v libx265 -preset slow -crf 15',
        'codec_audio': '-c:a aac -b:a 192k',
        'lookupMedia': '*.mp4',
        'inputExtension': '.mp4$',
        'outputExtension': '-converted.mp4',
        'additionFlags': '-hwaccel cuda',
        'logLevel': '-loglevel repeat+level+info'
    }

    CONFIG_FILE = "./config.yml"
    GENERAL_CONFIG_FILE = "ffmpeg_python.yml"
    FMT = '%H:%M:%S.%f'

    def __init__(self, opts=None):
        if opts is None:
            general_config_path = os.path.join(os.path.dirname(__file__), '..', 'etc', self.GENERAL_CONFIG_FILE)
            if os.path.isfile(general_config_path):
                with open(general_config_path, 'r') as file:
                    default_opts = yaml.load(file, Loader=yaml.FullLoader)
                self._opts = default_opts
            else:
                self._opts = self.OPTS
        else:
            self._opts = opts

        self._force_copy = False
        self._force_suffix = False

        self._warnings = []

    def set_suffix(self, new_suffix):
        self._opts["outputExtension"] = new_suffix
        self._force_suffix = True

    def set_codec(self, video=None, audio=None):
        if video is not None:
            self._opts["codec_video"] = video

        if audio is not None:
            self._opts["codec_audio"] = audio

        self._force_copy = True

    def set_copy(self):
        self._force_copy = True
        self.set_codec()

    def print_warnings(self):
        if len(self._warnings) == 0:
            return
        print('')
        print('Warnings::')
        for el in self._warnings:
            print('  * ' + el)

    def warn(self, *args, prefix=""):
        tmp_str = " ".join(args)
        self._warnings.append(tmp_str)
        print(prefix + 'WARN::', tmp_str)

    def build_config_from_scratch(self):
        fileset = glob.glob(self._opts['lookupMedia'])

        print(f'Building "config.yml" from {len(fileset)} files. It can take a bit...')

        files = []
        for file in fileset:
            v: VideoConfig = VideoConfig(file, self._opts)
            files.append(v.opts)
        with open(self.CONFIG_FILE, 'w') as outfile:
            yaml.dump(files, outfile, default_flow_style=False, Dumper=yaml.CDumper, allow_unicode=True, sort_keys=False)
        print('')
        print('Writen config.yml, please make the optional changes to the file and run again.')
        print('  files in config.yml:\n    - {}'.format('\n    - '.join(fileset)))
        return files

    def build_config(self):
        files: list[VideoConfig] = []
        if os.path.isfile(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as file:
                    files_raw = yaml.load(file, Loader=yaml.FullLoader)
                    for el in files_raw:
                        v: VideoConfig = VideoConfig(el["name"], self._opts, el)
                        files.append(v)
                    print('Loaded directory config')
            except Exception as e:
                print('Error reading config.yml, not really a yml file?')
        else:
            files = self.build_config_from_scratch()
            exit(0)
        return files

    def run_cmd(self):
        files = self.build_config()

        existing_files = {}

        if self._force_copy:
            print("")
            print("")
            print(f"WARNING:: Force codec was activated (--copy or --prores), all operations will overwrite codecs")
            print(f"         video: {self._opts['codec_video']}")
            print(f"         audio: {self._opts['codec_audio']}")
            print(f"        suffix: {self._opts['outputExtension']}")
            print('')
            print(f"        waiting 5 seconds before advancing, press ctrl+c to stop.")
            for ix in range(5):
                print(f"{5 - ix}")
                time.sleep(1)
            print(f"Starting...")

        v: VideoConfig
        for v in files:
            if not os.path.isfile(v.path):
                self.warn(f"input file \"{v.name}\" doesn't exist on this directory")
                continue

            if self._force_copy:
                v.set_codecs(self._opts['codec_video'], self._opts['codec_audio'])

            if self._force_suffix:
                v.set_suffix(self._opts['outputExtension'])

            print('')
            print('')
            print('')
            print('')
            print(f'INFO:: Start of {v.name}')
            print('')

            print('  INFO:: Metadata:')

            duration = v.get_length()
            frames = v.get_frames()
            frame_rate = frames / duration
            print('    * timestamp: %s' % v.get_duration(duration))
            print('    *   seconds: %s' % duration)
            if frames > 0:
                print('    *    frames: %s' % frames)
                print('    * framerate: %f' % frame_rate)
            else:
                print('    *    frames: n/a')
                print('    * framerate: n/a')
            print('')

            # print('Processing {0}'.format(ix))
            # output file name
            name = v.name
            prefix = [self._opts['additionFlags'], v.options]
            suffix = []

            print('  INFO:: Output parameters')
            tdelta = v.tdelta
            tdelta_str = str(Video.parse_seconds(v.tdelta).strftime(self.FMT))

            if v.rotate == 0:
                pass
            elif v.rotate == 90:
                suffix.append('-vf "transpose=2"')
            elif v.rotate == 180:
                suffix.append('-vf "transpose=2,transpose=2"')
            elif v.rotate == 270 or v.rotate == -90:
                suffix.append('-vf "transpose=1"')
            else:
                self.warn('rotate option "%s" not recognized' % el['rotate'])

            # check if it has start/end parameters
            prefix.append(f'-ss {v.start}')
            if v.start != 0:
                print(f'     custom start at: {v.start}')
            suffix.append(f'-t {tdelta}')

            print('     output file will be called: %s' % name)
            print('')
            print('     duration: {0}'.format(tdelta_str))
            print('      seconds: {0}'.format(tdelta))
            if frame_rate > 0:
                print('       frames: {0}'.format(tdelta * frame_rate))

            prefix_str: str = " ".join(prefix)
            suffix_str: str = " ".join(suffix)
            # builds ffmpeg command
            cmd = f'ffmpeg {self._opts["logLevel"]} {prefix_str} -i "{v.path}" {v.video} {v.audio} {suffix_str} "{name}"'

            # check if file already exists, if so, it skips it
            if os.path.isfile(name):
                print('')
                print('  INFO:: File %s already exists in directory, skipping...' % name)
                print('')
                v2 = Video(v.path)
                duration2 = v2.get_length()
                frames2 = v2.get_frames()
                frame_rate2 = frames2 / duration2
                timestamp2 = Video.parse_seconds(duration2).strftime(self.FMT)
                if frames2 == -1:
                    self.warn('invalid movie file "%s", can\'t extract metadata' % v.path, prefix='  ')
                else:
                    print('  INFO:: Metadata of existing file:')
                    print('    * timestamp: %s' % timestamp2)
                    print('    *   seconds: %s' % duration2)
                    print('    *    frames: %s' % frames2)
                    if frame_rate > 0:
                        print('    * framerate: %f' % frame_rate2)
                    existing_files[name] = {
                        'timestamp': str(tdelta_str) + " - " + str(timestamp2),
                        'seconds': str(tdelta) + " - " + str(duration2),
                        'framerate': str(frame_rate) + ' - ' + str(frame_rate2)
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
            print(f'-- end of {v.name} -------------------------------------------------------------------------------')

        if len(existing_files) > 0:
            print('')
            print('')
            print('Some output files already existed (%d)' % len(existing_files))
            for key in existing_files:
                print('')
                print('  [{0}]'.format(key))
                print('    * timestamp: {0}'.format(existing_files[key]['timestamp']))
                print('    * seconds: {0}'.format(existing_files[key]['seconds']))
                if frame_rate > 0:
                    print('    * framerate: {0}'.format(existing_files[key]['framerate']))

        self.print_warnings()




