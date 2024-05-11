import os
import time
import sounddevice as sd
import numpy as np
import datetime
import wave
import RPi.GPIO as GPIO 
import simpleaudio as sa
import soundfile as sf

script_dir = os.path.dirname(os.path.realpath(__file__))

# **** List of CAPTURE Hardware Devices ****
# card 3: Headset [Logitech USB Headset], device 0: USB Audio [USB Audio]
#   Subdevices: 1/1
#   Subdevice #0: subdevice #0

# Set the GPIO mode and the pin
GPIO.setmode(GPIO.BCM)
rec_button_pin = 21  # Change this to the GPIO pin you're using
play_button_pin = 20  # Change this to the GPIO pin you're using

# Set up the GPIO pin for input with internal pull-up resistor
GPIO.setup(rec_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(play_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Constants
FORMAT = 'wav'
DEVICE_ID = None  # Use the default audio input device
DEVICE_NAME = "Logitech USB Headset"
SAMPLE_RATE = 44100  # 44.1 kHz
FILENAME_PREFIX = 'recording'
PLAY_FILE = 'hello.wav'
  

def play_audio(file_name, device_name):
    # Load the audio file
    # Directory where you want to search for files

    # Construct the absolute path to the file
    file_path = os.path.join(script_dir, file_name)

    data, fs = sf.read(file_path)

    # Query available audio devices
    devices = sd.query_devices()
    device_index = None
    for i, device in enumerate(devices):
        if device['name'].startswith(device_name):
            device_index = i
            break

    if device_index is not None:
        # Play the audio on the selected device
        sd.play(data, fs, device=device_index)
        #sd.wait()
    else:
        print(f"Device '{device_name}' not found.")


def play_on_keypress():

    directory = script_dir

    # Get a list of files in the directory
    files = os.listdir(directory)

    
    # Filter files that start with "recordig"
    filtered_files = [file for file in files if file.startswith("recording")]

    # Sort the filtered files by filename
    filtered_files.sort(reverse=True)

    # Get the filename of the last file
    if filtered_files:
        last_file = filtered_files[0]
        print("Last file starting with 'recordig':", last_file)
        play_audio(last_file, DEVICE_NAME)
        sd.wait()
    else:
        print("No file starting with 'recordig' found in the directory")




def record_on_keypress():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{FILENAME_PREFIX}_{timestamp}.{FORMAT}"
    print(f"Recording to {filename}")

    # Start recording
    frames_per_buffer = 1024
    stream = sd.InputStream(device=None, channels=1, samplerate=SAMPLE_RATE, dtype=np.int16)
    stream.start()

    recording = True
    audio_data = []

    while recording:
        if GPIO.input(rec_button_pin) == False:  # Change 'esc' to the key you want to use
            audio_chunk, overflowed = stream.read(frames_per_buffer)
            audio_data.append(audio_chunk)

        else:
            recording = False

    stream.stop()
    stream.close()

    print(f"Recording stopped!")

    # Concatenate recorded audio chunks
    full_audio_data = np.concatenate(audio_data, axis=0)

    # Save audio to file using wave module

    file_path = os.path.join(script_dir, filename)
    print(file_path)

    with wave.open(file_path, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(full_audio_data.tobytes())
        print(f"Write completed!")

# Main loop
print (sd.query_devices() )

try:
    if GPIO.input(rec_button_pin) == False:
        print("Hang up first!")
        while GPIO.input(rec_button_pin) == False:
            time.sleep(0.1)
    print("Initalization completed!")
    while True:
        if GPIO.input(rec_button_pin) == False and GPIO.input(play_button_pin) == True:
            print("Recording new message!")
            play_audio(PLAY_FILE, DEVICE_NAME)
            record_on_keypress()
            time.sleep(0.1)
        if GPIO.input(rec_button_pin) == False and GPIO.input(play_button_pin) == False:
            print("Playing back last recording!")
            play_on_keypress()
            time.sleep(0.1)
            print("Hang up to reset state machine!")
            while GPIO.input(rec_button_pin) == False:
                time.sleep(0.1)
            print("Pick up to start recording!")
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nExiting the program.")

finally:
    # Clean up GPIO on program exit
    GPIO.cleanup()
