# Purpose
mlt-video-grid works on an almost empty MLT file as created by the [Shotcut](https://github.com/mltframework/shotcut) video editor.
It adds all video streams as provided on the command line and arranges them into a video grid.
This will commonly be required when editing videos for virtual choirs:

![Example output](https://raw.githubusercontent.com/hoffie/mlt-video-grid/master/example_output.png)

You specify the input MLT file (`-i`), the output MLT file (`-o`), the number of columns (`-c`) and, optionally, if videos should only start after some seconds of time which may be used for displaying the title (`-b`).
Besides that, you will specify all the videos you want to add.
You can use the special video path `FILL` before a video which is supposed to fit into two columns.
The number of rows will be calculated automatically.
If you've got less than `rows x columns` videos, the remaining space will be empty.

This tool drastically reduces the required manual steps when producing such videos.
Manual editing will still be required, e.g. when adjusting the individual videos' visible area within Shotcut.

For performance reasons (within Shotcut, not within this tool), it makes sense to downscale the input videos to the minimum required resolution, maybe even in a format which is fast to decode.

# Requirements
## Dependencies
The tool is built with Python 3 and does not require any dependencies besides the standard library.

## Assumptions
The tool works on an almost empty MLT file.
The file should contain two tracks:
- Track 0 (i.e. the first added track) should be the main audio-only track.
- Track 1 (= second track from bottom in Shotcut's UI) should be the main video track.

# Development
This project is considered feature-complete at the moment. New features will only be added as needed.

## Assumptions
- Existing .mlt file as created by shotcut
- Track 0 (bottom) is the main audio-only track
- Track 1 (second from bottom) is the main video-only track
