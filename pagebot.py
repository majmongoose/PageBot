#!/usr/bin/python3
import discord
import os
import subprocess
import time
import secrets_file
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

## file handler

class MyHandler(FileSystemEventHandler):
    def on_created(self, event):
        print("New Created!")
        if event.is_directory:
            print("Was a directory")
            return
        filepath = event.src_path
        filename, file_extension = os.path.splitext(filepath)
        if file_extension.lower() == '.mp3':
            print("Was an MP3!")
            mp4_file = convert_to_mp4(filepath)
            client.loop.create_task(upload_to_discord(mp4_file))

##convert mp3 to mp4
def convert_to_mp4(mp3_file):
    try:
        mp4_file = os.path.splitext(mp3_file)[0] + '.mp4'
        command = f'./ffmpeg -loop 1 -i img/blacksmall.jpg -i "{mp3_file}" -c:a aac -b:a 192k -c:v libx264 -pix_fmt yuv420p -shortest "{mp4_file}"'
        subprocess.run(command, shell=True)
        os.remove(mp3_file)
        return mp4_file
    except Exception as e:
        print(f"Error during conversion: {e}")
        return None

## upload to discord
async def upload_to_discord(mp4_file):
    ## Check to make sure conversion worked.
    if mp4_file is None:
        print("Conversion failed. Skipping upload.")
        return
    ## Get channel to send in
    channel = client.get_channel(secrets_file.channel_id)
    if channel:
        filename = os.path.basename(mp4_file)
        ## Send Video with name
        with open(mp4_file, 'rb') as f:
            await channel.send(filename,file=discord.File(f))

        ## Ping users with the appropriate number
        role_name = filename.split('-', 1)[0].strip()
        role = discord.utils.get(channel.guild.roles, name=role_name)
        if role:
            await channel.send(f"{role.mention} Go get em brothers!")
        else:
            print(f"Role '{role_name}' not found.")
    else:
        print(f"Could not find channel with ID {channel}")

if __name__ == "__main__":

    ## initialize watchdogs
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, secrets_file.watch_folder, recursive=False)
    observer.start()

    ## initialize discord 
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    client.run(secrets_file.key)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

##discord stuffs
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


