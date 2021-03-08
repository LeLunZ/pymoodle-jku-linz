# PyMoodle-JKU Linz

A local python client for accessing the jku moodle page. No Passwords are sent anywhere except
to https://moodle.jku.at/jku/login/index.php!

## Overview

What can you do with PyMoodle? A Short Overview.

You can do all this from the commandline and much more:

- Download files from moodle videos/pdf/folder/etc. and even **Exams** as markdown
- List all your grades without needing to open the browser and search moodle
- List your timetable from moodle.
- Password of moodle can be stored in the local system keyring. No need to enter it every time!

## Install

`pip3 install -U pymoodle-jku `

To get autocompletion working add this to your bash .bashrc/.zshrc/....:

`eval "$(register-python-argcomplete pymoodle)"`

If you are using fish/Tcsh or another shell, have a closer
look [here](https://github.com/kislyuk/argcomplete#zsh-support).

## Requirements

To Download streams, you need [ffmpeg](https://ffmpeg.org/download.html) installed.

## Usage Commandline Script

The commandline script is called **pymoodle**.

With **pymoodle** you can call these Utilities:

- download
- grades
- timeline
- config

You will find everything you need if you call:
`pymoodle --help` or `pymoodle {Utility} --help`

### Config

With the config utility you can configure your environment. You can either specify arguments that should be changed (
see `pymoodle config --help`) or launch the config in interactive mode like this: `pymoodle config`

Its **recommended** to configure your environment once if you want. You can also set a default download Path. (which
needs to exist before downloading.)

### Download

With the download utility you can download files and exams from moodle. There are multiple ways to select a course. If
nothing is specified it will download everything. But you can also launch Download in interactive mode like
this: `pymoodle download -i`

Or it's possible to search and download courses, which includes the word "Logic" or "Daten" like
this: `pymoodle download -s Logic -s Daten`

To download stuff from old courses specify the `-o` option, else only running courses will be considered. In interactive
mode you can press *m* to load old courses.

**Only for people who used PyMoodle before**

**Exams** are now downloaded too. To force a redownload of only exams use the `-e` option. This future will be removed
later. Its currently only implemented so that you don't have to download everything else again.

### Grades

Grades will launch automatically in interactive mode. Just like {download} it's also possible to use `-o` for old
courses or `-s` to search for courses.

### Timeline 

Timeline 

## Examples

There are two examples:

### Downloading

Open the [downloading.py](pymoodle_jku/Utils/downloading.py) and run it. It will download all possible files to your
disk.

It will also store a txt file with all downloaded urls. So you can run it multiple times, and it will only download
stuff once.

### Timeline

Run [timetable.py](pymoodle_jku/Utils/timetable.py) and get the full json response from your timetable. (In a next
release this will be a object, with type hints not a json)

## Features

- Login to your personal moodle account
    - passwords don't get stored anywhere, only send to the moodle (actually sso) server
- List all courses
    - query a specific course
    - download data from a course (PDFS/Zips...)
    - download streams (you need ffmpeg installed locally and added to your PATH)
    - get all Links on a page (with the [Link Type](pymoodle_jku/Classes/course_data.py))
    - get all html from a section of a course
- Get [information about courses](pymoodle_jku/Classes/course.py)
    - startdate/enddate
    - fullname/shortname
    - id
    - etc.
- Downloads are streamed
    - that means pymoodle take chunks of the request and writes it to the filesystem (which means less RAM usage)
        - to compare that: downloading: 4 x 2GB Videos into memory uses 8 GB. Streaming it and chunking it onto the
          filesystem takes not more than a few hundred MB.
- Get your Timeline
- Exception is thrown if you get logged out. (So catch it and call login again...)
- Every request I implemented is directly from the official moodle page. (Took a very long time to debug)

## Unsupported

- Downloading of Zoom streams of jku.zoom.us isn't supported for now. If somebody get it working please feel free to do
  a merge request.

## Support/Community

If you want to add something, create an issue and do a pull request.

### Install for testing

* clones this repo
* `pip3 install -r requirements.txt`

### Unittests

### Examples