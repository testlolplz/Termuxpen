# TermuxPen v3.0 🛡️

Mobile Penetration Testing Framework for Termux

[![Version](https://img.shields.io/badge/version-3.0.0-blue)]()
[![Python](https://img.shields.io/badge/python-3.8+-green)]()
[![License](https://img.shields.io/badge/license-MIT-red)]()

## ⚡ Features

- 🔍 **OSINT** - Username lookup, email breach check, DNS/Whois, social scraping
- 🔐 **Bruteforce** - ZIP/PDF cracking, hash cracking, SSH/FTP (educational)
- 🔒 **Crypto** - Base64, Hex, XOR, Caesar, ROT13, Morse
- 🌐 **Network** - Port scanner, HTTP analysis, pinger
- 📝 **Reporting** - Professional pentest reports
- 📦 **Modules** - Custom module system

## 📱 Installation

```bash
# Clone repo
git clone https://github.com/testlolplz/Termuxpen
cd Termuxpen

# Install dependencies
pkg install python qpdf whois dig
pip install requests PyPDF2 paramiko Pillow qrcode

# Run
python termuxpen.py