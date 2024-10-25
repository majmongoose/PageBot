#!/usr/bin/python3
import discord
import os
import subprocess
import time
import secrets_file
import threading
import psutil
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import speech_recognition as sr 

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
            client.loop.create_task(upload_to_discord(mp4_file,text))

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
            await channel.send(f"{role.mention} {secrets_file.notify_text}")
        else:
            print(f"Role '{role_name}' not found.")
    else:
        print(f"Could not find channel with ID {channel}")


def kill_existing_ttd_instances():
    """Terminate all running instances of TTD."""
    for proc in psutil.process_iter(['name', 'exe', 'cmdline']):
        try:
            if 'ttd' in proc.name().lower() or 'ttd' in ' '.join(proc.cmdline()).lower():
                print("Terminating an existing instance of TTD...")
                proc.terminate()  # Send SIGTERM
                proc.wait()  # Wait for the process to terminate
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def launch_and_watch(program_path):
    program_directory = os.path.dirname(program_path)
    restart_time = secrets_file.restart_time  # Format: "HH:MM" or None

    if restart_time:
        restart_hour, restart_minute = map(int, restart_time.split(":"))
    
    restart_triggered = False  # Flag to prevent multiple restarts within the same minute

    while True:
        # Terminate any existing TTD processes before starting a new one
        kill_existing_ttd_instances()

        # Launch the TTD program
        print("Starting TTD program...")
        process = subprocess.Popen(program_path, cwd=program_directory)

        while True:
            if restart_time:
                current_time = datetime.now()
                
                # Check if it's the restart time and restart hasn't been triggered in the current minute
                if (current_time.hour == restart_hour and current_time.minute == restart_minute and not restart_triggered):
                    print(f"Scheduled restart time reached ({restart_time}). Restarting TTD...")
                    process.terminate()
                    process.wait()
                    restart_triggered = True  # Set flag to prevent multiple restarts in the same minute
                    break  # Exit inner loop to relaunch TTD
                
                # Reset the flag once we're past the restart minute
                if current_time.minute != restart_minute:
                    restart_triggered = False

            # Check if TTD has crashed
            if process.poll() is not None:
                print("TTD has crashed. Relaunching...")
                break  # Exit inner loop to relaunch TTD

            # Sleep for a short interval before checking again
            time.sleep(60)  # Check once every minute

        # Wait for a few seconds before relaunching after crash or scheduled restart
        print("Waiting before relaunching TTD...")
        time.sleep(2)

if __name__ == "__main__":

    ## initialize watchdogs
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, secrets_file.watch_folder, recursive=False)
    observer.start()

    ## Launch TTD
    if (secrets_file.ttd_path != ""):
        watchdog_thread = threading.Thread(target=launch_and_watch, args=(secrets_file.ttd_path,))
        watchdog_thread.start()

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


