#!/bin/bash
echo "[+] Installing TermuxPen v3.0..."

# Update packages
pkg update -y

# Install dependencies
pkg install python git qpdf whois traceroute dig -y

# Python packages
pip install --upgrade pip
pip install requests PyPDF2 pillow qrcode

# Optional packages
echo "[?] Install optional packages (SSH bruteforce, etc)?"
echo "    pip install paramiko cryptography"
echo ""
echo "[✓] Installation complete!"
echo "[+] Run: python termuxpen.py"