# PixelOS Automated Installer & ROM Manager

An automated, AI-powered tool to easily install PixelOS (and other custom ROMs) on supported Android devices. It combines an official PixelOS installer, a universal ROM search engine, and a **Gemini-powered AI Hunter** into one professional dashboard.

![PixelOS Installer Screenshot](https://i.imgur.com/y0faONK.png)

## 🚀 Features

### 🤖 Gemini AI ROM Hunter (NEW)
* **Smart Search:** Uses Google's Gemini AI to find the latest custom ROMs (LineageOS, Evolution X, CrDroid, etc.) for *any* Android device.
* **Model Selector:** Choose between **Gemini 1.5 Flash** (Fast) or **Gemini 1.5 Pro** (Detailed) directly from the UI.
* **Direct Links:** AI generates clickable download buttons instantly.

### 📱 Official PixelOS Installer
* **Automated Fetching:** Pulls the latest device list and download links directly from the PixelOS GitHub API.
* **One-Click Install:** Handles download, payload extraction, and flashing automatically.

### 🔍 Universal Database
* **Offline Database:** Instantly maps over 400+ device names (e.g., "OnePlus 7") to their codenames (e.g., "guacamole").
* **Smart Links:** Provides quick search links for XDA Forums, SourceForge, and Telegram updates.

### ⚡ Intelligent Flasher
* **Smart Detection:** Automatically detects if the device is in ADB, Bootloader, or FastbootD mode.
* **Dynamic Partition Support:** Handles the complex transition from Bootloader → FastbootD for modern devices (Android 10+).
* **Payload Extraction:** Automatically extracts `payload.bin` using embedded `payload-dumper-go`.
* **Safety Checks:** Verifies file integrity to prevent flashing empty or corrupt files.
* **Manual Mode:** Flash any local `.zip` or `.bin` file via the Manual Flasher tab.

## 🛠 Prerequisites
* **Windows 10/11**
* **Unlocked Bootloader** on your Android device.
* **USB Drivers** installed (Google/Universal ADB Drivers).
* *(Optional)* **Gemini API Key** for AI features (Get it free at [aistudio.google.com](https://aistudio.google.com)).

## 📥 Installation
1.  Download the latest release from the [Releases Page](https://github.com/Fever-Productions/PixelOS-Installer/releases).
2.  Extract the ZIP file.
3.  Run `PixelOS_Installer.exe`.
4.  **Important:** Ensure your `bin` folder (containing ADB/Fastboot) is in the same directory as the executable.

## ⚠️ Disclaimer
**Use at your own risk.** While this tool includes safety checks, flashing custom firmware always carries a risk of bricking your device. I am not responsible for bricked devices, dead SD cards, thermonuclear war, or you getting fired because the alarm app failed. 
* Always backup your data before flashing.
* Ensure your bootloader is unlocked before using this tool.

## 🏗 Building from Source
If you want to run the python script directly or build your own EXE:

1.  Clone the repo:
    ```bash
    git clone https://github.com/Fever-Productions/PixelOS-Installer.git
    ```
2.  Install dependencies (Updated for AI features):
    ```bash
    pip install customtkinter requests google-generativeai
    ```
3.  Place `platform-tools` (ADB/Fastboot) and `payload-dumper-go` in the `bin/` directory.
4.  Run:
    ```bash
    python main.py
    ```

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Credits
* [PixelOS Team](https://pixelos.net/) for the amazing ROM and API.
* [ssut](https://github.com/ssut/payload-dumper-go) for the Payload Dumper tool.
* [Google](https://developer.android.com/studio/releases/platform-tools) for ADB & Fastboot.
