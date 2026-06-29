# Hybrid Block Diagram (Hardware & Software)

This block diagram provides a balanced view of the system, showing how the physical hardware components of the Raspberry Pi interact with the software stack and external cloud services.

```mermaid
flowchart TD
    %% External Hardware
    subgraph Peripherals [External Hardware]
        Webcam[USB Webcam]
        Power[5V Power Supply]
    end

    %% Raspberry Pi
    subgraph Pi [Raspberry Pi Edge Device]
        direction TB
        
        subgraph HW [Internal Hardware]
            SoC[ARM Cortex Processor]
            WiFI[Wireless / Network Module]
        end
        
        subgraph SW [Software Stack]
            OS[Raspberry Pi OS & V4L2 Drivers]
            OpenCV[OpenCV Image Engine]
            App[Python AI Controller]
        end
        
        %% Internal Architecture Links
        SoC ~~~ SW
        SoC <-->|Data Bus| WiFI
        OS <-->|Hardware Access| SoC
        OpenCV <-->|Driver Access| OS
        App <-->|Frame Requests| OpenCV
    end

    %% Cloud APIs
    subgraph Services [Cloud Infrastructure]
        Firebase[(Firebase Realtime Database)]
        Gemini((Google Gemini Vision API))
    end

    %% Connections
    Power ==>|Power Delivery| Pi
    Webcam <-->|USB Video Stream| OS
    
    App <-->|WebSocket Commands| Firebase
    App <-->|Image + Prompt Request| Gemini
    
    WiFI <-->|Internet Routing| Services
```
