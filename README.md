# PyMoodle-JKU Linz

A python client for accessing the jku moodle page. 

## Features

- List all courses
    - query a specific course
    - download data from a course (PDFS/Zips...)
    - download streams (you need ffmpeg installed locally and added to your PATH)
    - get all Links on a page (with the [Link Type](pymoodle_jku/Classes/course_data.py))
    - get all html from a section
- Get [information about courses](pymoodle_jku/Classes/course.py)
    - startdate/enddate
    - fullname/shortname
    - id
    - etc


## Unsupported

- Downloading of Zoom streams of jku.zoom.us isn't supported for now. If somebody get it working please feel free to do a merge request.


## Support

If you want to add something, create an issue and do a pull request. 
