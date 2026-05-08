
---

## ⚡ Features

### 🔍 OSINT & Reconnaissance
- Multi-platform username lookup (GitHub, Reddit, Instagram, Twitter/X, TikTok, etc.)
- Email breach checker via HaveIBeenPwned API (k-anonymity)
- DNS lookup, Whois, IP geolocation
- Subdomain scanner with built-in wordlist
- Social media scraper (Instagram, GitHub, Reddit)
- Metadata extractor (PDF, images)
- Google dork generator

### 🔐 Bruteforce & Cracking
- ZIP password cracker
- PDF password cracker (via qpdf)
- Hash cracker (MD5, SHA1, SHA256, SHA512)
- SSH bruteforce (educational - requires paramiko)
- FTP bruteforce (educational)
- Custom wordlist generator with leet speak, numbers, symbols
- Wordlist merger
- Session resume support

### 🔒 Crypto & Encoding
- Base64 Encode/Decode
- Hex Encode/Decode
- Binary Encode
- URL Encode/Decode
- ROT13 Cipher
- XOR Cipher
- Caesar Cipher
- Morse Code Converter

### #️⃣ Hash Tools
- Hash generation (MD5, SHA1, SHA256, SHA512, BLAKE2)
- Hash type identifier
- File hashing
- Hash comparison

### 🌐 Network Tools
- TCP Port scanner
- Ping, Traceroute
- HTTP header analyzer
- Basic WhatWeb/tech detection
- File downloader with progress

### 🛠️ Utilities
- Password generator
- Random string generator
- UUID generator
- QR code generator
- System info viewer
- Result history

### 📦 Module System
- Custom module loader
- Module installer from URL
- Module creation wizard

---

## 📱 Installation

### One-liner (Termux)
```bash
pkg update -y && pkg install git python -y && git clone https://github.com/testlolplz/Termuxpen && cd Termuxpen && bash install.sh