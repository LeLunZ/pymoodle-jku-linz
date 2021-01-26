# PyMoodle-JKU Linz

A python client for accessing the jku moodle page. 



## Examples

There are two examples:

### Downloading

Open the [downloading.py](pymoodle_jku/Tests/downloading.py) and run it. It will download all possible files to your disk.

It will also store a txt file with all downloaded urls. So you can run it multiple times, and it will only download stuff once.

### Timeline

Run [timetable.py](pymoodle_jku/Tests/timetable.py) and get the full json response from your timetable. (In a next release this will be a object, with type hints not a json)

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
        - to compare that: downloading: 4 x 2GB Videos into memory uses 8 GB. Streaming it and chunking it onto the filesystem takes not more than a few hundred MB.
- Get your Timeline
- Exception is thrown if you get logged out. (So catch it and call login again...)
- Every request I implemented is directly from the official moodle page. (Took a very long time to debug)


## Unsupported

- Downloading of Zoom streams of jku.zoom.us isn't supported for now. If somebody get it working please feel free to do a merge request.


## Support

If you want to add something, create an issue and do a pull request. 
