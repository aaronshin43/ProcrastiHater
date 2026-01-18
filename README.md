# Procrasti-Hater

**"I see you scrolling your phone instead of working."**

Procrasti-Hater is an AI-powered surveillance agent that forces you to be productive. It monitors your screen process and webcam activity in real-time, detecting distractions like sleeping, using your phone, or launching games. When you slack off, a personalized AI persona (e.g., Gigachad, Gordon Ramsey) verbally roasts you.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LiveKit](https://img.shields.io/badge/LiveKit-Realtime-orange)
![PyQt6](https://img.shields.io/badge/UI-PyQt6-green)
![OpenAI](https://img.shields.io/badge/AI-OpenAI%20%2F%20ElevenLabs-purple)

## 🔥 Key Features

-   **👀 Real-time Vision Monitoring**: Detects if you are sleeping, looking at your phone, absent, or looking away (gazing elsewhere) using MediaPipe.
-   **🖥️ Process & Window Tracking**: Instantly detects distraction apps (Games, Netflix, Social Media) based on active window titles.
-   **🗣️ Verbal Abuse (TTS)**: Uses ElevenLabs to generate voice responses. The AI interrupts you immediately when a violation is detected.
-   **🎭 Multiple Personas**: Choose your supervisor - form the supportive "Anime Girl" to the ruthless "Drill Sergeant" or "Gordon Ramsey".
-   **🎙️ Interactive Excuses**: You can talk back to the agent via microphone. The AI judges if your excuse is valid or scolds you harder (LLM-based).
-   **📊 Session Report**: At the end of a work session, get a ruthless "Session Review" with a score and a detailed breakdown of your sins.

## 🛠️ Tech Stack

### Client
-   **Framework**: Python, PyQt6
-   **Vision**: MediaPipe (Face Landmarkers, Pose Detection)
-   **Audio**: SoundDevice (Push-to-Talk)
-   **Communication**: LiveKit Client SDK (Data Channels for real-time packets)
-   **UI Design**: Custom "Pip-Boy" style retro interface.

### Agent 
-   **Framework**: LiveKit Agents
-   **Intelligence**: Google Gemini (Reasoning & Persona)
-   **Voice**: ElevenLabs TTS (Streaming Audio)
-   **Logic**: Asyncio-based event loop handling detection packets and managing conversation state.

## 📂 Project Structure

```
ProcrastiHater/
│
├── 📂 agent/                 # [Backend] The AI logic running on the server
│   ├── main.py               # Entry point. Handles LiveKit events & orchestration.
│   ├── llm.py                # Interacts with OpenAI for generating scolding text.
│   ├── memory.py             # Manages session history & cooldowns.
│   └── prompts.py            # System prompts defining the Personas.
│
├── 📂 client/                # [Frontend] The desktop application
│   ├── main.py               # Entry point. Launches UI & Background Services.
│   ├── config.py             # Configuration loader (.env).
│   │
│   ├── 📂 services/          # Background worker threads
│   │   ├── vision.py         # Webcam analysis (Sleep/Phone/Absence detection).
│   │   ├── screen.py         # Active window monitoring.
│   │   ├── livekit_client.py # Network storage for sending packets.
│   │   └── stats.py          # Local session statistics tracking.
│   │
│   └── 📂 ui/                # PyQt6 Widgets
│       ├── main_window.py    # Dashboard (Personality selection, Stats).
│       ├── floating_widget.py# Always-on-top character overlay.
│       └── stats_view.py     # End-of-session report card.
│
└── 📂 shared/                # Shared types & protocols
    ├── protocol.py           # JSON Packet structure.
    └── constants.py          # Event definitions (WINDOW_CHANGE, SLEEPING, etc).
```

## 🚀 Getting Started

### Prerequisites
1.  **Python 3.10+**
2.  **LiveKit Cloud Project** (Url & Secret)
3.  **OpenAI API Key**
4.  **ElevenLabs API Key**

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/procrastihater.git
    cd procrastihater
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment**
    Create a `.env` file in the root directory:
    ```ini
    LIVEKIT_URL=wss://your-project.livekit.cloud
    LIVEKIT_API_KEY=your_api_key
    LIVEKIT_API_SECRET=your_api_secret
    OPENAI_API_KEY=sk-proj-...
    ELEVEN_API_KEY=...
    ```

### Usage

1.  **Start the Agent**
    ```bash
    python agent/main.py start
    ```
    *The agent will connect to the room and wait for a user.*

2.  **Start the Client**
    ```bash
    python client/main.py
    ```
    *The GUI will launch. Select a persona and click START.*

## 🎮 Controls

-   **Alt+S**: Toggle Microphone (Push-to-Talk)
-   **Alt+B**: Toggle Debug Window (View webcam feed & vision landmarks)

## 📜 License
MIT License
