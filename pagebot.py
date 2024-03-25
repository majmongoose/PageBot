import discord
from discord.ext import commands
import os
import subprocess
import time
import secrets_file
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import speech_recognition as sr 

## Initialize the bot with command prefix
bot = commands.Bot(command_prefix='!')

## New File Handler
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
            bot.loop.create_task(upload_to_discord(mp4_file,text))

## Convert MP3 to MP4
def convert_to_mp4(mp3_file):
    try:
        time.sleep(10)
        mp4_file = os.path.splitext(mp3_file)[0] + '.mp4'
        command = f'ffmpeg -loop 1 -i "{secrets_file.image_path}" -i "{mp3_file}" -c:a aac -b:a 192k -c:v libx264 -pix_fmt yuv420p -shortest "{mp4_file}"'
        subprocess.run(command, shell=True)
        os.remove(mp3_file)
        return mp4_file
    except Exception as e:
        print(f"Error during conversion: {e}")
        return None

## Send audio to interpreter
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
    channel = bot.get_channel(secrets_file.channel_id)
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
            await channel.send(f"{role.mention} {secrets_file.notify_text}")
        else:
            print(f"Role '{role_name}' not found.")
    else:
        print(f"Could not find channel with ID {channel}")

## Command to restart TTD software manually
@bot.command()
async def restart_ttd(ctx):
    if secrets_file.ttd_path:
        await ctx.send("Restarting TTD software...")
        restart_ttd_process(secrets_file.ttd_path)
    else:
        await ctx.send("TTD path not configured.")

## Function to restart TTD software
def restart_ttd_process(program_path):
    program_directory = os.path.dirname(program_path)
    process = subprocess.Popen(program_path, cwd=program_directory)
    process.wait()
    if process.returncode != 0:
        print("TTD has crashed. Relaunching...")
    else:
        print("TTD has exited normally.")

## Launch and watch TTD
def launch_and_watch_ttd():
    while True:
        process = subprocess.Popen(secrets_file.ttd_path)
        process.wait()
        if process.returncode != 0:
            print("TTD has crashed. Relaunching...")
        else:
            print("TTD has exited normally.")
            break
        # Wait for a few seconds before relaunching
        time.sleep(2)

if __name__ == "__main__":
    ## Initialize watchdogs
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, secrets_file.watch_folder, recursive=False)
    observer.start()

    ## Start watching TTD
    if secrets_file.ttd_path:
        ttd_thread = threading.Thread(target=launch_and_watch_ttd)
        ttd_thread.start()

    ## Initialize Discord bot
    bot.run(secrets_file.key)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

## Discord event
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
