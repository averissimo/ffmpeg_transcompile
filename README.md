# FFMPEG transcompile

> batch trancompile video files based on a per-directory configuration

This tool will transcode the media in the directory where you run it as long as it has a `config.yml` file.

When running without `config.yml` file in the directory, the tool will generate a default one with all files that are follow the `lookupMedia` search and all available options are blank _(and ignored if not changed)_.

### Options

General options for the tool are defined in `ffmpeg_python.yml` file available in the repository. with possible options:

* `codec_video`: ffmpeg video codec and other intermediate options
* `code_audio`: ffmpeg audio codec and other intermediate options
* `lookupMedia`: filter files in directory to be transcoded
* `inputExtension`: extension of input files
* `outputExtension`: extension of output files
* `logLevel`: ffmpeg log level options
* `inputFlags`: ffmpeg options before input

Allows to have per-directory options when a `config.yml` file is present. When it's present it will only convert the files declared in it. Possible options are

* `suffix`: output name, it will show as `<original name>-<name>.mp4`
* `options`: additional options
* `start`: starting position, if not supplied, the same start of input will be used
* `end`: end position in `HH:MM:SS` *(hours:minutes:seconds)* as absolute values, not relative to the start position *(when supplied)*.
    * This is different from `-t` option in ffmepg as the tool will calculate the relative time when `start` is also supplied.
    * It can also be `HH:MM:SS.ms`, where ms is the microsecond or an number representing the absolute seconds _(61 would be `00:01:01`)_.
* `rotate`: rotation of video. Available options are: `90`, `180`, `270` _(or `-90`)_
    * Use right hand to figure out rotation or think of it as counter clockwise

### Example

Example of a valid `config.yml` file with all combinations:

```
- name: one.mp4
  start: 00:00:00
  end: '00:00:16.454922'
  rotate: 0
  options: ''
  suffix: ''
  codec_video: -c:v copy
  codec_audio: -c:a copy
- name: two.mp4
  start: 00:00:00
  end: '00:00:44.111978'
  rotate: 0
  options: ''
  suffix: ''
  codec_video: -c:v copy
  codec_audio: -c:a copy
- name: third movie.mp4
  start: 00:00:00
  end: '00:00:06'
  rotate: 0
  options: ''
  suffix: ''
  codec_video: -c:v copy
  codec_audio: -c:a copy
```
