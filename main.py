from dotenv import load_dotenv
from openai import OpenAI
import sounddevice as sd
import scipy.io.wavfile as wav
import webrtcvad
import numpy as np
import collections
import os
import pygame
import io
import pvporcupine
import pvrecorder

load_dotenv()

client = OpenAI()
conversation_history = []

user_name = os.getenv("USER_NAME")
PORCUPINE_ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY")

system_prompt = f"""You are Jarvis, a helpful and intelligent personal desk assistant for {user_name}.
You are concise, friendly, and professional like the Jarvis from Iron Man.
Always address him as {user_name}. Keep responses brief and conversational
since they will be spoken out loud."""

SAMPLE_RATE = 16000
FRAME_DURATION = 30
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION / 1000)

START_SPEECH_FRAMES = 5
STOP_SILENCE_FRAMES = 30
PRE_BUFFER_FRAMES = 10

def wait_for_wake_word():
    porcupine = pvporcupine.create(
        access_key=PORCUPINE_ACCESS_KEY,
        keyword_paths=["hello-jarvis-porcupine.ppn"]
    )
    recorder = pvrecorder.PvRecorder(frame_length=porcupine.frame_length)
    recorder.start()
    print("🟢 Waiting for 'Hello Jarvis'...")
    try:
        while True:
            pcm = recorder.read()
            result = porcupine.process(pcm)
            if result >= 0:
                print("👋 Wake word detected!")
                break
    finally:
        recorder.stop()
        recorder.delete()
        porcupine.delete()

def record_audio():
    vad = webrtcvad.Vad(3) # 3 is the most aggressive mode
    print("👂 Listening...")
    triggered = False
    speech_frames = []
    pre_buffer = collections.deque(maxlen=PRE_BUFFER_FRAMES)
    silence_buffer = collections.deque(maxlen=STOP_SILENCE_FRAMES)
    speech_counter = 0

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype='int16',
        blocksize=FRAME_SIZE
    ) as stream:

        while True:
            frame, _ = stream.read(FRAME_SIZE)
            frame_bytes = bytes(frame)
            is_speech = vad.is_speech(frame_bytes, SAMPLE_RATE)
            if not triggered:
                pre_buffer.append(frame_bytes)
                if is_speech:
                    speech_counter += 1
                else:
                    speech_counter = 0
                if speech_counter >= START_SPEECH_FRAMES:
                    print("🎙️ Speech detected")
                    triggered = True
                    silence_buffer.clear()
                    speech_frames.extend(pre_buffer)
            else:
                speech_frames.append(frame_bytes)
                silence_buffer.append(is_speech)
                if len(silence_buffer) == STOP_SILENCE_FRAMES and not any(silence_buffer):
                    print("✅ Silence detected, stopping")
                    break

    audio = np.frombuffer(b''.join(speech_frames), dtype=np.int16)

    if len(audio) < SAMPLE_RATE:
        print("⚠️ Too short, ignoring")
        return None

    wav.write("input.wav", SAMPLE_RATE, audio)
    print("💾 Saved input.wav")
    return True

def transcribe():
    with open("input.wav", "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )
    return transcript.text

def ask_gpt(user_input):
    conversation_history.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt}] + conversation_history
    )
    assistant_message = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": assistant_message})
    return assistant_message

def speak(text):
    response = client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=text
    )
    pygame.mixer.init()
    audio_data = io.BytesIO(response.content)
    pygame.mixer.music.load(audio_data)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

wait_for_wake_word()

while True:
    if record_audio():
        text = transcribe()
        if text:
            print(f"You said: {text}")
            response = ask_gpt(text)
            print(f"Jarvis: {response}")
            speak(response)
