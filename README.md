# PageBot

PageBot is a discord bot written in python using the discord.py library, which watches a folder for audio clips output from the TwoToneDetect (TTD) software. It takes the audio clips, uses ffmpeg to convert them to mp4 for embedding purposes, and uploads them to discord. If your TTD configuration uses numbers at the beginning of the name, it will ping a role with the appropriate numbers, and can be used as a rudimentary method to get dispatch notes (SEE TOS BELOW). You must supply your own copy of TwoToneDetect and ffmpeg.

# Installation

1. Install the latest version of python3
2. Download and Decompress PageBot
3. Download [ffmpeg.exe](https://www.ffmpeg.org/download.html) and drop it into the PageBot directory
4. Run the following from the PageBot directory ```pip install requirements.txt```
5. Rename ```sample-secrets_file.py``` to ```secrets_file.py``` and fill in required information
6. Run the bot with ```python pagebot.py```

# Configuration
|             | ttd_path                                      | key                | watch_folder                         | notify_text                                          | channel_id                                     | delete_after_upload                           | speech_to_text                                                          |
|-------------|-----------------------------------------------|--------------------|--------------------------------------|------------------------------------------------------|------------------------------------------------|-----------------------------------------------|-------------------------------------------------------------------------|
| Required    | NO                                            | YES                | YES                                  | NO                                                   | YES                                            | YES                                           | YES                                                                     |
| Description | Path to launch TTD from, leave "" to disable. | Discord bot token. | Folder to watch for new audio clips. | Can be blank, send a message when notfied of a page. | Discord Channel ID to send page notifications. | Delete *.mp4 file after uploading to Discord. | Enable/Disable Speech to Text. It does not work well, and is very slow. |



# TOS

PageBot is NOT meant to replace a county-approved pager or mobile dispatching application in any way whatsoever. It is solely meant as a record of recent dispatch notes, to be kept in an easy place to access. PageBot and its authors are not liable for any injuries caused by people utilizing this application. We are not affilaited with the two tone detect software in any way. 
