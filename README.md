# FFMPEG transcompile

> batch trancompile video files based on a per-directory configuration

This tool will transcode the media in the directory where you run it as long as it has a `config.yml` file.

When running without `config.yml` file in the directory, the tool will generate a default one with all files that are follow the `lookupMedia` search and all available options are blank _(and ignored if not changed)_.

### Options

General options for the tool are defined in `ffmpeg_python.yml` file available in the repository. with possible options:

* `flags`: ffmpeg codec and other intermediate options
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
* `rotate`: rotation of video. Available options are: `90`, `180`, `270` _(or `-90`)_
    * Use right hand to figure out rotation or think of it as counter clockwise

### Example

Example of a valid `config.yml` file with all combinations:

```
MVI_5086.MOV:
  start: 00:07:32
  suffix: 'whatever'
  rotate: 90
  options: '-nostats'
MVI_5090.MOV:
  end: "00:04:47"
MVI_5115.MOV:
  start: "00:03:18"
  end: "00:05:51"
```
