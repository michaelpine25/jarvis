# Jarvis - AI Desk Assistant

A voice-activated AI desk assistant built on a Raspberry Pi, powered by the Claude API. Speak to it, and it speaks back.

## Hardware

- Raspberry Pi 4
- USB Microphone
- USB Speaker

## How It Works

1. **Wake Word** — Say "Hey Jarvis" to activate
2. **Speech-to-Text** — Your voice is transcribed locally on the Pi
3. **Claude API** — Transcribed text is sent to Claude and a response is generated
4. **Text-to-Speech** — The response is spoken back through the speaker

## Project Structure

```
jarvis/
├── venv/           # Python virtual environment (not tracked)
├── .env            # API keys (not tracked)
├── .gitignore
├── README.md
└── main.py         # Main assistant logic
```

## Setup

### Prerequisites

- Raspberry Pi 4 running Raspberry Pi OS (64-bit)
- Python 3.9+
- Anthropic API key — get one at [console.anthropic.com](https://console.anthropic.com)

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
   pip install anthropic python-dotenv
   ```

4. Create a `.env` file in the root of the project:
   ```
   ANTHROPIC_API_KEY="your-api-key-here"
   ```

5. Run the assistant:
   ```bash
   python3 main.py
   ```

## Audio Setup

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
| `ANTHROPIC_API_KEY` | Your Anthropic API key |

## Roadmap

- [x] Claude API integration
- [x] Conversation memory
- [x] Jarvis personality via system prompt
- [ ] Speech-to-text (Vosk)
- [ ] Text-to-speech (pyttsx3/espeak)
- [ ] Wake word detection (Porcupine)

