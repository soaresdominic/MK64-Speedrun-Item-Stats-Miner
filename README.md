# MK64 Speedrun Item Stats Miner
Mario Kart 64 speedrun item stats miner. Collect stats on item distribution from recorded speedruns of the game Mario Kart 64.

\
Requirements:
* python3 64 bit
* at least 4 GB RAM Free - closer to 10GB+ reccommended
* opencv-python (cv2)
* psutil

Before Running:
* Create videoRanges file videoRanges.csv in root folder, using format below. minutes are integers and can be 0 or after video ends. put a 1 minute buffer to each time 5,10 -> 4,11

video filename, start minute of video to process, end minute of video to process,  start minute of video to process, end minute of video to process, etc.\
e.g.  
`2021-07-17 17-44-28.mkv,4,8,43,50`\
`2021-08-09 17-23-59.mkv,0,150`

Notes:
* Developed in Python 3.7.2
* Originally made for videos from https://www.twitch.tv/abney317

