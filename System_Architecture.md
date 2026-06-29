# Samaksh System Architecture

This diagram illustrates the high-level architecture of the Samaksh Blind Assistance System. It follows a clean, numbered sequence (1 to 9) showing exactly how data travels through the system and back to the user.

```mermaid
flowchart LR
    %% Custom Styling
    classDef user fill:#f9f,stroke:#333,stroke-width:2px;
    classDef frontend fill:#d4edda,stroke:#28a745,stroke-width:2px;
    classDef cloud fill:#cce5ff,stroke:#007bff,stroke-width:2px;
    classDef backend fill:#fff3cd,stroke:#ffc107,stroke-width:2px;
    classDef external fill:#f8d7da,stroke:#dc3545,stroke-width:2px;

    User((Blind User)):::user

    subgraph Frontend [📱 Mobile React Interface]
        STT([Speech-to-Text]):::frontend
        UI[[App Logic Engine]]:::frontend
        TTS([Text-to-Speech]):::frontend
    end

    subgraph Firebase [☁️ Firebase Cloud DB]
        Session[(Session Commands)]:::cloud
        Msgs[(Chat History)]:::cloud
    end

    subgraph Backend [🍓 Raspberry Pi Edge]
        Cam[Hardware Webcam]:::backend
        AI{{Python Controller}}:::backend
    end
    
    Gemini((✨ Gemini Vision API)):::external

    %% Step-by-Step Sequence Connections
    User -- "1. Voice Command" --> STT
    STT --> UI
    
    UI -- "2. Push Command" --> Session
    Session -- "3. WebSocket Trigger" --> AI
    
    AI -- "4. Capture Image" --> Cam
    Cam -.-> AI
    
    AI -- "5. Send Image" --> Gemini
    Gemini -- "6. Return Text" --> AI
    
    AI -- "7. Write Result" --> Msgs
    Msgs -- "8. Database Sync" --> UI
    
    UI --> TTS
    TTS -- "9. Spoken Audio" --> User
```
