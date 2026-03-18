from dotenv import load_dotenv
from openai import OpenAI
import sounddevice as sd
import webrtcvad
import numpy as np
import collections
import os
import pygame
import io
import pvporcupine
import pvrecorder
import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
import re

load_dotenv()

client = OpenAI()
conversation_history = []

user_name = os.getenv("USER_NAME")
agent_name = os.getenv("AGENT_NAME")
PORCUPINE_ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY")
WAKE_WORD_FILE_PATH = os.getenv("WAKE_WORD_FILE_PATH")

system_prompt = f"""You are {agent_name}, a helpful and intelligent personal desk assistant for {user_name}.
You are concise, friendly, and professional like the Jarvis from Iron Man.
Always address him as {user_name}. Keep responses brief and conversational
since they will be spoken out loud.
When {user_name} is clearly saying goodbye or ending the conversation, end your response with the exact token: <END_CONVERSATION>"""


SAMPLE_RATE = 16000
FRAME_DURATION = 30
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION / 1000)

START_SPEECH_FRAMES = 5
STOP_SILENCE_FRAMES = 30
PRE_BUFFER_FRAMES = 10

whisper_model = WhisperModel("base", device="cpu", compute_type="int8")

def wait_for_wake_word():
    porcupine = pvporcupine.create(
        access_key=PORCUPINE_ACCESS_KEY,
        keyword_paths=[WAKE_WORD_FILE_PATH]
    )
    recorder = pvrecorder.PvRecorder(frame_length=porcupine.frame_length)
    recorder.start()
    print("Waiting for 'Hello Jarvis'...")
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
    vad = webrtcvad.Vad(3)
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

    # Convert to float32 normalized between -1 and 1 for faster-whisper
    audio_float32 = audio.astype(np.float32) / 32768.0
    return audio_float32

def transcribe(audio):
    print("Transcribing...")
    segments, _ = whisper_model.transcribe(audio, beam_size=1)
    text = " ".join([segment.text for segment in segments])
    return text.strip()

def ask_gpt_stream(user_input):
    print("Asking GPT...")
    conversation_history.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt}] + conversation_history
    )
    assistant_message = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": assistant_message})
    return assistant_message

def speak(text):
    SAMPLE_RATE = 24000
    
    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="onyx",
        input=text,
        response_format="pcm"
    ) as response:
        with sd.RawOutputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16') as stream:
            for chunk in response.iter_bytes(chunk_size=4096):
                stream.write(chunk)

def speak_into_stream(text, stream):
    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="onyx",
        input=text,
        response_format="pcm"
    ) as response:
        for chunk in response.iter_bytes(chunk_size=4096):
            stream.write(chunk)

def write_silence(stream, duration_ms=100, sample_rate=24000):
    silence = b'\x00' * int(sample_rate * duration_ms / 1000) * 2
    stream.write(silence)

while True:
    wait_for_wake_word()
    speak(f"Yes {user_name}?")
    silence_count = 0
    MAX_SILENCE = 3

    while True:
        audio = record_audio()
        if audio is not None:
            silence_count = 0
            text = transcribe(audio)
            if text:
                print(f"You said: {text}")
                token_stream = ask_gpt_stream(text)
                buffer = ""
                full_response = ""
                sentence_endings = re.compile(r'(?<=[.!?])\s+')

                with sd.RawOutputStream(samplerate=24000, channels=1, dtype='int16') as stream:
                    for token in token_stream:
                        full_response += token
                        buffer += token
                        print(token, end="", flush=True)

                        parts = sentence_endings.split(buffer)
                        for sentence in parts[:-1]:
                            clean = sentence.replace("<END_CONVERSATION>", "").strip()
                            if clean:
                                speak_into_stream(clean, stream)
                        buffer = parts[-1]

                    if buffer.strip():
                        clean = buffer.replace("<END_CONVERSATION>", "").strip()
                        if clean:
                            speak_into_stream(clean, stream)

                    write_silence(stream)
                print()

                if "<END_CONVERSATION>" in full_response:
                    break
        else:
            silence_count += 1
            if silence_count >= MAX_SILENCE:
                print("💤 Going back to sleep...")
                speak("Going to sleep, say Hello Jarvis to wake me up.")
                break