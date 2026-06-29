# Raspberry Pi Embedded Systems: Technical Q&A
**Samaksh - Blind Assistance System**

This document serves as a preparation guide for technical viva and embedded system design questions specifically tailored to the Raspberry Pi hardware used in the Samaksh project.

---

## 1. Boot Sequence: Power-On to Linux
**Q: How does the Raspberry Pi boot from the moment power is applied?**
Unlike traditional PCs with a BIOS, the Raspberry Pi's boot process is driven entirely by the VideoCore GPU before the ARM CPU is even turned on.

1. **Power On:** The PMIC (Power Management IC) receives 5V and distributes regulated voltages to the SoC (System on Chip) and RAM.
2. **Stage 1 (BootROM):** A small piece of code hardwired into the SoC silicon executes. It wakes up the VideoCore GPU. The ARM CPU remains held in a reset state.
3. **Stage 2 (`bootcode.bin`):** The GPU reads the FAT32 partition of the MicroSD card, finds `bootcode.bin`, and executes it. This initializes the LPDDR SDRAM.
4. **Stage 3 (`start.elf`):** The GPU loads the main firmware (`start.elf`). It reads `config.txt` (hardware config) and sets up the base hardware parameters.
5. **Stage 4 (`kernel.img`):** The GPU loads the Linux Kernel into the newly initialized SDRAM. Finally, it releases the ARM CPU from reset, pointing it at the kernel.
6. **Init/Systemd:** The ARM CPU takes over, boots the Linux OS, mounts the root filesystem, and starts background services (like our Python AI script).

---

## 2. Power Consumption
**Q: What is the power consumption of this embedded system?**
- **Input:** Requires a 5V DC supply via USB-C (Pi 4) or Micro-USB (Pi 3).
- **Idle State:** The board consumes roughly ~2.5W to 3.0W.
- **Under Load (Camera + Wi-Fi):** When running `ai.py`, capturing webcam frames, and transmitting over Wi-Fi, it draws around **5.0W to 6.5W** (1.0A to 1.3A at 5V).
- **Webcam:** A standard USB webcam draws approximately 500mA (2.5W) maximum from the USB controller.

---

## 3. Video Streaming & Drivers
**Q: How does the Raspberry Pi read the video stream from the webcam?**
The system uses the **UVC (USB Video Class)** protocol. 
1. The webcam sends frames over the USB 2.0 bus.
2. The Raspberry Pi OS uses the **V4L2 (Video4Linux2)** kernel driver to interface with the camera hardware.
3. We configured OpenCV in our Python script (`cv2.VideoCapture(0, cv2.CAP_V4L2)`) to bypass high-level multimedia frameworks (like GStreamer) and talk *directly* to the V4L2 driver, ensuring maximum stability and preventing pipeline crashes.

---

## 4. Hardware Block Diagram Components
**Q: What are the key internal hardware blocks of the Raspberry Pi utilized in this project?**
- **SoC (System on Chip - Broadcom BCM2711/BCM2837):** Contains both the ARM Cortex CPU (runs Python, Firebase SDK) and the VideoCore GPU (handles booting).
- **SDRAM (Synchronous Dynamic RAM):** LPDDR4 memory. It holds the Linux Kernel, our Python environment, and temporarily buffers the JPEG images captured from the webcam before they are sent to Gemini.
- **Wi-Fi Module (Cypress/Broadcom):** Connects via the internal SDIO bus to the SoC. It handles the WebSocket TCP/IP connection to Firebase and REST API calls to Google.
- **USB Controller:** Handles the physical layer communication with the external USB webcam.
- **PMIC (Power Management IC):** Steps down the 5V input to 3.3V, 1.8V, and 1.2V required by the SoC and RAM.
