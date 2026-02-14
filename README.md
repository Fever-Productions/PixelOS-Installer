# PixelOS Automated Installer

An automated, GUI-based tool to easily install PixelOS (and other custom ROMs) on supported Android devices. 

![PixelOS Installer Screenshot](https://i.imgur.com/y0faONK.png)

## 🚀 Features
* **Automated Fetching:** Pulls the latest device list and download links directly from the PixelOS GitHub API.
* **Smart Detection:** Automatically detects if the device is in ADB, Bootloader, or FastbootD mode.
* **Dynamic Partition Support:** Handles the complex transition from Bootloader → FastbootD for modern devices (Android 10+).
* **Payload Extraction:** Automatically extracts `payload.bin` using `payload-dumper-go`.
* **Safety Checks:** Verifies file integrity prevents flashing empty files.
* **Manual Mode:** Flash any local `.zip` or `.bin` file.

## 🛠 Prerequisites
* **Windows 10/11**
* **Unlocked Bootloader** on your Android device.
* **USB Drivers** installed (Google/Universal ADB Drivers).

## 📥 Installation
1.  Download the latest release from the [Releases Page](#releases).
2.  Extract the ZIP file.
3.  Run `PixelOS_Installer.exe`.
4.  Ensure your `bin` folder (containing ADB/Fastboot) is in the same directory as the executable.

## ⚠️ Disclaimer
**Use at your own risk.** While this tool includes safety checks, flashing custom firmware always carries a risk of bricking your device. I am not responsible for bricked devices, dead SD cards, thermonuclear war, or you getting fired because the alarm app failed. 
* Always backup your data before flashing.
* Ensure your bootloader is unlocked before using this tool.

## 🏗 Building from Source
If you want to run the python script directly:

1.  Clone the repo:
    ```bash
    git clone [https://github.com/yourusername/PixelOS-Installer.git](https://github.com/yourusername/PixelOS-Installer.git)
    ```
2.  Install dependencies:
    ```bash
    pip install customtkinter requests
    ```
3.  Place `platform-tools` and `payload-dumper-go` in the `bin/` directory.
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
