# Jarvis - AI Desk Assistant

A voice-activated AI desk assistant built on a Raspberry Pi, powered by OpenAI. Say "Hello Jarvis" to wake it up, speak your question, and it speaks back.

## Hardware

- Raspberry Pi 4
- USB Microphone
- USB Speaker

## How It Works

1. **Wake Word** — Say "Hello Jarvis" to activate
2. **Voice Activity Detection** — Automatically detects when you start and stop speaking
3. **Speech-to-Text** — Your voice is transcribed using OpenAI Whisper
4. **LLM** — Transcribed text is sent to GPT-4o and a response is generated
5. **Text-to-Speech** — The response is spoken back through the speaker using OpenAI TTS

## Project Structure

```
jarvis/
├── venv/                             # Python virtual environment (not tracked)
├── .env                              # API keys and config (not tracked)
├── .gitignore
├── README.md
├── Hello-Jarvis_en_mac.ppn           # Porcupine wake word model - Mac (not tracked)
├── Hello-Jarvis_en_raspberry-pi.ppn  # Porcupine wake word model - Pi (not tracked)
└── main.py                           # Main assistant logic
```

## Setup

### Prerequisites

- Raspberry Pi 4 running Raspberry Pi OS (64-bit)
- Python 3.9+
- OpenAI API key — get one at [platform.openai.com](https://platform.openai.com)
- Picovoice access key — get one at [console.picovoice.ai](https://console.picovoice.ai)

### Installation

1. Clone the repo:
   ```bash
   git clone https://github.com/yourusername/jarvis.git
   cd jarvis
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install openai python-dotenv sounddevice scipy webrtcvad numpy pvporcupine pvrecorder pygame
   ```

4. Download your wake word model from [console.picovoice.ai](https://console.picovoice.ai), train it for your platform (Mac or Raspberry Pi), and place the `.ppn` file in the root of the project.

5. Create a `.env` file in the root of the project:
   ```
   OPENAI_API_KEY="your-openai-api-key"
   PICOVOICE_ACCESS_KEY="your-picovoice-access-key"
   AGENT_NAME="Jarvis"
   USER_NAME="Your Name"
   WAKE_WORD_FILE_PATH="Your-.ppn-porcupine-file-path"
   ```

6. Run the assistant:
   ```bash
   python3 main.py
   ```

## Usage

1. Run `python3 main.py`
2. Say **"Hello Jarvis"** to activate
3. Speak your question — it will automatically detect when you start and stop talking
4. Jarvis will respond out loud
6. Press `Ctrl+C` to quit

## Audio Setup (Raspberry Pi)

The USB mic and speaker need to be configured as the default ALSA devices. Add the following to `~/.asoundrc` on the Pi:

```
pcm.!default {
    type asym
    playback.pcm {
        type plug
        slave.pcm "hw:4,0"
    }
    capture.pcm {
        type plug
        slave.pcm "hw:3,0"
    }
}
```

> Note: Your card numbers may differ. Run `aplay -l` and `arecord -l` to find the correct card numbers for your speaker and mic.

## Environment Variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `PICOVOICE_ACCESS_KEY` | Your Picovoice access key for wake word detection |
| `AGENT_NAME` | What the assistant should call itself |
| `USER_NAME` | What the assistant should call you |
| `WAKE_WORD_FILE_PATH` | Path to the .ppn porcupine wake word file |
