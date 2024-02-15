#!/usr/bin/python3
import discord
import os
import subprocess
import time
import secrets_file
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import speech_recognition as sr 

## file handler

class MyHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        filepath = event.src_path
        filename, file_extension = os.path.splitext(filepath)
        if file_extension.lower() == '.amr':
            time.sleep(10)
            os.remove(filepath)
            print("Removing AMR.")
        if file_extension.lower() == '.mp3':
            print("New MP3!")
            text = ""
            if secrets_file.speech_to_text:
                print("Converting To Text")
                text = convert_to_text(filepath,filename)
            print("Converting to MP4")
            mp4_file = convert_to_mp4(filepath)
            print("Sending to Discord")
            client.loop.create_task(upload_to_discord(mp4_file,text))
        #time.sleep(10)
        print("Removing original file.")
        #os.remove(filepath)

##convert mp3 to mp4
def convert_to_mp4(mp3_file):
    try:
        time.sleep(10)
        mp4_file = os.path.splitext(mp3_file)[0] + '.mp4'
        command = f'ffmpeg -loop 1 -i img/blacksmall.jpg -i "{mp3_file}" -c:a aac -b:a 192k -c:v libx264 -pix_fmt yuv420p -shortest "{mp4_file}"'
        subprocess.run(command, shell=True)
        return mp4_file
    except Exception as e:
        print(f"Error during conversion: {e}")
        return None
  
def convert_to_text(mp3_path,mp3_name):
    print(mp3_path)
    try:
        command = f'ffmpeg -i "{mp3_path}" "{mp3_name}".wav'
        subprocess.run(command, shell=True)
        r = sr.Recognizer() 
        # Load the audio file 
        with sr.AudioFile(f"{mp3_name}.wav") as source: 
            data = r.record(source) 
        # Convert speech to text 
        text = r.recognize_google(data) 
        os.remove(f"{mp3_name}.wav")
        return (text)
    except Exception as e:
        print(f"Error during conversion: {e}")
        return ""



## upload to discord
async def upload_to_discord(mp4_file,text):
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
        if secrets_file.delete_after_upload:
            os.remove(mp4_file)
        ## Send transcribed voice if present.
        if (text != ""):
            await channel.send(f"The following text was transcoded from the recording: \n{text}")
        ## Ping users with the appropriate number
        role_name = filename.split('-', 1)[0].strip()
        role = discord.utils.get(channel.guild.roles, name=role_name)
        if role:
            await channel.send(f"{role.mention} Go get em brothers!")
        else:
            print(f"Role '{role_name}' not found.")
    else:
        print(f"Could not find channel with ID {channel}")

def launch_and_watch(program_path):
    while True:
        process = subprocess.Popen(program_path)
        process.wait()
        if process.returncode != 0:
            print("TTD has crashed. Relaunching...")
        else:
            print("TTD has exited normally.")
            break

        # Wait for a few seconds before relaunching
        time.sleep(5)

if __name__ == "__main__":

    ## initialize watchdogs
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, secrets_file.watch_folder, recursive=False)
    observer.start()

    ## Launch TTD
    launch_and_watch(secrets_file.ttd_path)

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


