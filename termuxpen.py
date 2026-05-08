
#!/usr/bin/env python3
"""
TermuxPen v3.0 - Mobile Penetration Testing Framework
GitHub: https://github.com/testlolplz/Termuxpen
Educational use only. Always get proper authorization before testing.
"""

import os
import sys
import hashlib
import zipfile
import subprocess
import base64
import json
import logging
import shutil
import time
import re
import socket
import random
import string
from datetime import datetime
from pathlib import Path
from io import StringIO, BytesIO
from urllib.parse import urlparse

# ─── CONFIGURATION ───
VERSION = "3.0.0"
GITHUB_REPO = "https://github.com/testlolplz/Termuxpen"
RAW_URL = "https://raw.githubusercontent.com/testlolplz/Termuxpen/main"
CONFIG_DIR = Path.home() / ".termuxpen"
CONFIG_FILE = CONFIG_DIR / "config.json"
LOG_FILE = CONFIG_DIR / "termuxpen.log"
SESSION_FILE = CONFIG_DIR / "session.json"
WORDLIST_DIR = CONFIG_DIR / "wordlists"
MODULES_DIR = CONFIG_DIR / "modules"

# ─── COLORS (Termux compatible) ───
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    RESET = '\033[0m'

# ─── LOGGING SETUP ───
def setup_logging():
    CONFIG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

# ─── DATABASE ───
class Database:
    """Simple JSON-based database for storing results"""
    
    @staticmethod
    def save_result(category, data):
        db_file = CONFIG_DIR / f"{category}_results.json"
        try:
            existing = []
            if db_file.exists():
                with open(db_file, 'r') as f:
                    existing = json.load(f)
            
            data['timestamp'] = datetime.now().isoformat()
            data['id'] = len(existing) + 1
            existing.append(data)
            
            temp = db_file.with_suffix('.tmp')
            with open(temp, 'w') as f:
                json.dump(existing[-100:], f, indent=2)  # Keep last 100
                f.flush()
                os.fsync(f.fileno())
            temp.replace(db_file)
        except Exception as e:
            logging.error(f"Database error: {e}")
    
    @staticmethod
    def get_results(category, limit=10):
        db_file = CONFIG_DIR / f"{category}_results.json"
        if db_file.exists():
            try:
                with open(db_file, 'r') as f:
                    data = json.load(f)
                return data[-limit:]
            except:
                pass
        return []

# ─── MODULE LOADER ───
class ModuleLoader:
    """Dynamic module loading system"""
    
    @staticmethod
    def load_external_modules():
        """Load custom modules from modules directory"""
        modules = {}
        MODULES_DIR.mkdir(exist_ok=True)
        
        for module_file in MODULES_DIR.glob("*.py"):
            if module_file.name.startswith('_'):
                continue
            try:
                module_name = module_file.stem
                spec = __import__(f"modules.{module_name}", fromlist=[module_name])
                if hasattr(spec, 'run'):
                    modules[module_name] = spec
            except Exception as e:
                logging.warning(f"Failed to load module {module_file}: {e}")
        
        return modules

# ─── NETWORK TOOLS ───
class NetworkTools:
    """Network utilities"""
    
    @staticmethod
    def check_internet():
        """Check if internet is available"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except:
            return False
    
    @staticmethod
    def get_ip_info():
        """Get public IP info"""
        import requests
        try:
            resp = requests.get("http://ip-api.com/json/", timeout=5)
            return resp.json()
        except:
            return None
    
    @staticmethod
    def port_scan(host, ports=None):
        """Simple TCP port scanner"""
        if ports is None:
            ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 
                    3306, 3389, 8080, 8443]
        
        open_ports = []
        print(f"\n[+] Scanning {host}...")
        
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((host, port))
                if result == 0:
                    service = socket.getservbyport(port) if port <= 1024 else "unknown"
                    print(f"    {Colors.GREEN}[OPEN]{Colors.RESET} Port {port} ({service})")
                    open_ports.append(port)
                sock.close()
            except:
                pass
        
        return open_ports

# ─── MAIN FRAMEWORK ───
class TermuxPen:
    def __init__(self):
        self.version = VERSION
        self.config = self.load_config()
        self.external_modules = ModuleLoader.load_external_modules()
        self.net = NetworkTools()
        
        self.main_modules = {
            "1": ("🔍 OSINT & Recon", self.osint_menu),
            "2": ("🔐 Bruteforce & Cracking", self.bruteforce_menu),
            "3": ("🔒 Crypto & Encoding", self.crypto_menu),
            "4": ("#️⃣  Hash Tools", self.hash_menu),
            "5": ("🌐 Network Tools", self.network_menu),
            "6": ("📝 Report Generator", self.generate_report),
            "7": ("🛠️  Utilities", self.utils_menu),
            "8": ("📦 Module Manager", self.module_manager),
        }
        
        if self.config.get("first_run", True):
            self.first_run_setup()
    
    def load_config(self):
        """Load or create config"""
        default_config = {
            "version": VERSION,
            "first_run": True,
            "wordlist_path": str(WORDLIST_DIR),
            "max_threads": 4,
            "timeout": 10,
            "user_agent": f"TermuxPen/{VERSION}",
            "auto_update_check": True,
            "save_sessions": True,
            "theme": "default",
            "history_size": 100,
            "stealth_mode": False,
        }
        
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                # Update with any new defaults
                for key, value in default_config.items():
                    config.setdefault(key, value)
                return config
        except:
            pass
        
        return default_config
    
    def save_config(self):
        """Save config safely"""
        try:
            CONFIG_DIR.mkdir(exist_ok=True)
            temp = CONFIG_FILE.with_suffix('.tmp')
            with open(temp, 'w') as f:
                json.dump(self.config, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            temp.replace(CONFIG_FILE)
        except Exception as e:
            logging.error(f"Config save error: {e}")
    
    def first_run_setup(self):
        """Initial framework setup"""
        self.clear_screen()
        print(f"""{Colors.CYAN}
    ╔══════════════════════════════════════╗
    ║                                      ║
    ║     🚀 FIRST TIME SETUP WIZARD      ║
    ║                                      ║
    ╚══════════════════════════════════════╝{Colors.RESET}
        """)
        
        # Create directories
        for directory in [CONFIG_DIR, WORDLIST_DIR, MODULES_DIR]:
            directory.mkdir(exist_ok=True)
        
        # Create default wordlists
        self.create_default_wordlists()
        
        # Test internet
        print("[+] Checking internet connectivity...")
        if self.net.check_internet():
            print(f"    {Colors.GREEN}[✓] Internet connected{Colors.RESET}")
        else:
            print(f"    {Colors.YELLOW}[!] No internet (offline mode){Colors.RESET}")
        
        self.config["first_run"] = False
        self.save_config()
        
        print(f"\n{Colors.GREEN}[✓] Setup complete!{Colors.RESET}")
        time.sleep(2)
    
    def create_default_wordlists(self):
        """Create bundled wordlists"""
        wordlists = {
            "common_passwords.txt": [
                "123456", "password", "12345678", "qwerty", "123456789",
                "12345", "1234", "111111", "1234567", "sunshine",
                "qwerty123", "iloveyou", "admin", "root", "test123",
                "password123", "admin123", "letmein", "welcome", "monkey",
                "dragon", "master", "abc123", "123123", "football",
            ],
            "common_usernames.txt": [
                "admin", "root", "user", "test", "guest",
                "info", "adm", "mysql", "oracle", "ftp",
                "pi", "postgres", "git", "jenkins", "deploy",
            ],
            "subdomains.txt": [
                "www", "mail", "ftp", "localhost", "webmail",
                "smtp", "pop", "ns1", "webdisk", "ns2",
                "cpanel", "whm", "autodiscover", "blog", "shop",
                "dev", "staging", "api", "admin", "portal",
                "cdn", "media", "static", "app", "m",
            ]
        }
        
        for filename, words in wordlists.items():
            filepath = WORDLIST_DIR / filename
            if not filepath.exists():
                with open(filepath, 'w') as f:
                    f.write('\n'.join(words))
    
    def clear_screen(self):
        """Cross-platform screen clear"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def show_banner(self):
        """Display main banner"""
        banner = f"""
{Colors.CYAN}{Colors.BOLD}
    ╔══════════════════════════════════════════╗
    ║                                          ║
    ║          TERMUXPEN FRAMEWORK             ║
    ║          Mobile Pentesting Tool          ║
    ║                                          ║
    ║     {Colors.WHITE}Version: {VERSION}{Colors.CYAN}                    ║
    ║     {Colors.WHITE}Author: testlolplz{Colors.CYAN}                 ║
    ║     {Colors.WHITE}GitHub: github.com/testlolplz/Termuxpen{Colors.CYAN} ║
    ║                                          ║
    ╚══════════════════════════════════════════╝
{Colors.RESET}
{Colors.YELLOW}[!] For authorized security testing only{Colors.RESET}
{Colors.YELLOW}[!] Educational purposes - use responsibly{Colors.RESET}
        """
        return banner
    
    # ─── UPDATE SYSTEM ───
    def check_for_updates(self):
        """Check GitHub for latest release"""
        if not self.config.get("auto_update_check", True):
            return
        
        import requests
        
        try:
            api_url = "https://api.github.com/repos/testlolplz/Termuxpen/releases/latest"
            resp = requests.get(api_url, timeout=5)
            
            if resp.status_code == 200:
                release = resp.json()
                latest_version = release.get("tag_name", "").lstrip('v')
                
                if latest_version and latest_version != VERSION:
                    print(f"\n{Colors.YELLOW}[!] New version available: v{latest_version}{Colors.RESET}")
                    print(f"[+] Run 'Update Framework' to install")
        except:
            pass
    
    def update_framework(self):
        """Update framework from GitHub"""
        import requests
        
        print(f"\n{Colors.CYAN}[ Update Framework ]{Colors.RESET}")
        print(f"Current version: {VERSION}")
        print(f"Repo: {GITHUB_REPO}")
        
        if not self.net.check_internet():
            print(f"{Colors.RED}[!] No internet connection{Colors.RESET}")
            return
        
        print("[+] Checking GitHub for updates...")
        
        try:
            # Get latest release
            api_url = "https://api.github.com/repos/testlolplz/Termuxpen/releases/latest"
            resp = requests.get(api_url, timeout=10)
            
            if resp.status_code == 200:
                release = resp.json()
                latest = release.get("tag_name", "").lstrip('v')
                
                if latest == VERSION:
                    print(f"{Colors.GREEN}[✓] Already up to date{Colors.RESET}")
                    return
                
                print(f"{Colors.YELLOW}[!] Update available: v{latest}{Colors.RESET}")
                print(f"\nRelease notes:")
                print(f"  {release.get('body', 'No notes')[:200]}")
                
                if input(f"\n{Colors.BOLD}Download and install? (y/n): {Colors.RESET}").lower() != 'y':
                    return
                
                # Download new version
                download_url = f"{RAW_URL}/termuxpen.py"
                print("[+] Downloading update...")
                
                response = requests.get(download_url, timeout=30)
                
                if response.status_code == 200:
                    # Backup current
                    current_file = Path(__file__) if '__file__' in dir() else Path(sys.argv[0])
                    backup = current_file.with_suffix('.backup')
                    shutil.copy2(current_file, backup)
                    
                    # Save new version
                    temp_file = current_file.with_suffix('.new')
                    with open(temp_file, 'w') as f:
                        f.write(response.text)
                        f.flush()
                        os.fsync(f.fileno())
                    
                    os.replace(temp_file, current_file)
                    
                    print(f"{Colors.GREEN}[✓] Updated to v{latest}!{Colors.RESET}")
                    print("[+] Restart framework to apply update")
                    
                    # Update config version
                    self.config["version"] = latest
                    self.save_config()
                    
                    if input("Restart now? (y/n): ").lower() == 'y':
                        os.execv(sys.executable, ['python'] + sys.argv)
                else:
                    print(f"{Colors.RED}[!] Download failed: {response.status_code}{Colors.RESET}")
            else:
                print(f"{Colors.RED}[!] Cannot check updates: {resp.status_code}{Colors.RESET}")
        
        except Exception as e:
            print(f"{Colors.RED}[!] Update error: {e}{Colors.RESET}")
            logging.error(f"Update error: {e}")
    
    # ─── MODULE MANAGER ───
    def module_manager(self):
        """Manage external modules"""
        print(f"\n{Colors.CYAN}[ Module Manager ]{Colors.RESET}")
        print("1. List installed modules")
        print("2. Install module from URL")
        print("3. Create new module")
        print("4. Remove module")
        
        choice = input("\n> Select: ").strip()
        
        if choice == "1":
            modules = list(MODULES_DIR.glob("*.py"))
            if modules:
                print("\n[ Installed Modules ]")
                for mod in modules:
                    size = os.path.getsize(mod)
                    print(f"  📦 {mod.stem} ({size} bytes)")
            else:
                print("[!] No modules installed")
        
        elif choice == "2":
            url = input("Module URL: ").strip()
            name = input("Module name: ").strip()
            if url and name:
                import requests
                try:
                    resp = requests.get(url, timeout=10)
                    if resp.status_code == 200:
                        mod_file = MODULES_DIR / f"{name}.py"
                        with open(mod_file, 'w') as f:
                            f.write(resp.text)
                        print(f"{Colors.GREEN}[✓] Module installed: {name}{Colors.RESET}")
                    else:
                        print(f"{Colors.RED}[!] Download failed{Colors.RESET}")
                except Exception as e:
                    print(f"{Colors.RED}[!] Error: {e}{Colors.RESET}")
        
        elif choice == "3":
            name = input("Module name: ").strip()
            if name:
                template = f'''#!/usr/bin/env python3
"""
Module: {name}
Author: 
Description: 
"""

def run():
    """Main module entry point"""
    print("[{name}] Module loaded!")
    # Your code here

if __name__ == "__main__":
    run()
'''
                mod_file = MODULES_DIR / f"{name}.py"
                with open(mod_file, 'w') as f:
                    f.write(template)
                print(f"{Colors.GREEN}[✓] Module created: {name}{Colors.RESET}")
        
        elif choice == "4":
            name = input("Module name to remove: ").strip()
            mod_file = MODULES_DIR / f"{name}.py"
            if mod_file.exists():
                mod_file.unlink()
                print(f"{Colors.GREEN}[✓] Module removed{Colors.RESET}")
            else:
                print("[!] Module not found")
    
    # ─── OSINT MODULE ───
    def osint_menu(self):
        """OSINT and reconnaissance tools"""
        print(f"\n{Colors.CYAN}[ OSINT & Reconnaissance ]{Colors.RESET}")
        print("1.  Username lookup (multi-platform)")
        print("2.  Email breach checker")
        print("3.  Email info (format, domain)")
        print("4.  IP Geolocation")
        print("5.  DNS Lookup")
        print("6.  Whois Lookup")
        print("7.  Subdomain Scanner")
        print("8.  Social Media Scraper")
        print("9.  Metadata Extractor")
        print("10. Google Dork Generator")
        
        choice = input("\n> Select: ").strip()
        
        osint_actions = {
            "1": self.username_lookup,
            "2": self.email_breach_check,
            "3": self.email_info,
            "4": self.ip_geolocation,
            "5": self.dns_lookup,
            "6": self.whois_lookup,
            "7": self.subdomain_scanner,
            "8": self.social_scraper,
            "9": self.metadata_extractor,
            "10": self.dork_generator,
        }
        
        if choice in osint_actions:
            osint_actions[choice]()
    
    def username_lookup(self):
        """Check username across platforms"""
        import requests
        
        username = input("Username: ").strip()
        if not username:
            return
        
        platforms = {
            "GitHub": f"https://api.github.com/users/{username}",
            "Reddit": f"https://www.reddit.com/user/{username}/about.json",
            "Instagram": f"https://www.instagram.com/{username}/",
            "Twitter/X": f"https://twitter.com/{username}",
            "TikTok": f"https://www.tiktok.com/@{username}",
            "Pinterest": f"https://www.pinterest.com/{username}/",
            "Steam": f"https://steamcommunity.com/id/{username}/",
            "Keybase": f"https://keybase.io/{username}",
        }
        
        print(f"\n[+] Searching '{username}' across {len(platforms)} platforms...\n")
        
        results = {"username": username, "found_on": [], "not_found_on": []}
        
        for platform, url in platforms.items():
            try:
                headers = {"User-Agent": self.config["user_agent"]}
                resp = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
                
                if resp.status_code == 200:
                    print(f"  {Colors.GREEN}[✓]{Colors.RESET} {platform}: Found")
                    results["found_on"].append(platform)
                elif resp.status_code == 404:
                    print(f"  {Colors.RED}[✗]{Colors.RESET} {platform}: Not found")
                    results["not_found_on"].append(platform)
                else:
                    print(f"  {Colors.YELLOW}[?]{Colors.RESET} {platform}: {resp.status_code}")
            except:
                print(f"  {Colors.RED}[!]{Colors.RESET} {platform}: Error")
        
        Database.save_result("osint", results)
    
    def email_breach_check(self):
        """Check email in breaches via HIBP"""
        import requests
        
        email = input("Email: ").strip()
        if '@' not in email:
            print(f"{Colors.RED}[!] Invalid email{Colors.RESET}")
            return
        
        sha1 = hashlib.sha1(email.lower().encode()).hexdigest().upper()
        prefix, suffix = sha1[:5], sha1[5:]
        
        try:
            resp = requests.get(
                f"https://api.pwnedpasswords.com/range/{prefix}",
                headers={"User-Agent": "TermuxPen-HIBP"},
                timeout=10
            )
            
            if resp.status_code == 200:
                for line in resp.text.splitlines():
                    if line.startswith(suffix):
                        count = line.split(':')[1].strip()
                        print(f"\n{Colors.RED}[!] BREACHED{Colors.RESET}")
                        print(f"    Found in {count} data breaches!")
                        print(f"    Email: {email}")
                        print(f"    Hash: {sha1}")
                        Database.save_result("breach", {"email": email, "count": count, "hash": sha1})
                        return
                
                print(f"\n{Colors.GREEN}[✓] No breaches found{Colors.RESET}")
            else:
                print(f"{Colors.RED}[!] API error: {resp.status_code}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}[!] Error: {e}{Colors.RESET}")
    
    def email_info(self):
        """Analyze email address"""
        email = input("Email: ").strip()
        if '@' not in email:
            print(f"{Colors.RED}[!] Invalid email{Colors.RESET}")
            return
        
        local, domain = email.split('@', 1)
        
        print(f"\n[ Email Analysis ]")
        print(f"  Full: {email}")
        print(f"  Local part: {local}")
        print(f"  Domain: {domain}")
        print(f"  Length: {len(email)}")
        print(f"  Common provider: ", end="")
        
        common_providers = {
            "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
            "protonmail.com", "icloud.com", "aol.com", "mail.com"
        }
        print(f"{'Yes' if domain.lower() in common_providers else 'No'}")
    
    def ip_geolocation(self):
        """Get IP geolocation info"""
        import requests
        
        target = input("IP (leave blank for your IP): ").strip()
        
        try:
            url = f"http://ip-api.com/json/{target}" if target else "http://ip-api.com/json/"
            resp = requests.get(url, timeout=5)
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"\n[ IP Geolocation ]")
                for key, value in data.items():
                    if value:
                        print(f"  {key}: {value}")
        except Exception as e:
            print(f"{Colors.RED}[!] Error: {e}{Colors.RESET}")
    
    def dns_lookup(self):
        """DNS record lookup"""
        domain = input("Domain: ").strip()
        if not domain:
            return
        
        print(f"\n[ DNS Lookup: {domain} ]\n")
        
        record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA']
        
        for rtype in record_types:
            try:
                result = subprocess.run(
                    ['dig', '+short', rtype, domain],
                    capture_output=True, text=True, timeout=5
                )
                if result.stdout.strip():
                    print(f"  {Colors.GREEN}[{rtype}]{Colors.RESET}")
                    for line in result.stdout.strip().split('\n'):
                        print(f"    {line}")
            except:
                pass
    
    def whois_lookup(self):
        """Whois lookup"""
        domain = input("Domain: ").strip()
        if not domain:
            return
        
        print(f"\n[ Whois: {domain} ]\n")
        
        try:
            result = subprocess.run(
                ['whois', domain],
                capture_output=True, text=True, timeout=15
            )
            
            # Show key info
            for line in result.stdout.split('\n'):
                lower = line.lower()
                if any(key in lower for key in ['registrar', 'creation', 'expir', 'name server', 'registrant', 'country']):
                    print(f"  {line.strip()}")
        except FileNotFoundError:
            print(f"{Colors.YELLOW}[!] Install whois: pkg install whois{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}[!] Error: {e}{Colors.RESET}")
    
    def subdomain_scanner(self):
        """Scan for subdomains"""
        import requests
        
        domain = input("Domain (e.g., example.com): ").strip()
        if not domain:
            return
        
        wordlist = WORDLIST_DIR / "subdomains.txt"
        
        if not wordlist.exists():
            print(f"{Colors.RED}[!] Subdomain wordlist not found{Colors.RESET}")
            return
        
        with open(wordlist) as f:
            subdomains = [line.strip() for line in f if line.strip()]
        
        print(f"\n[+] Scanning {domain} ({len(subdomains)} subdomains)...\n")
        
        found = []
        for sub in subdomains:
            url = f"https://{sub}.{domain}"
            try:
                resp = requests.get(url, timeout=5, allow_redirects=True,
                                   headers={"User-Agent": self.config["user_agent"]})
                if resp.status_code < 500:
                    print(f"  {Colors.GREEN}[✓]{Colors.RESET} {sub}.{domain} ({resp.status_code})")
                    found.append({"subdomain": f"{sub}.{domain}", "status": resp.status_code})
            except:
                pass
        
        if found:
            Database.save_result("subdomains", {"domain": domain, "found": found})
    
    def social_scraper(self):
        """Basic social media info gathering"""
        import requests
        
        platform = input("Platform (instagram/github/reddit): ").strip().lower()
        username = input("Username: ").strip()
        
        if not username:
            return
        
        urls = {
            "instagram": f"https://www.instagram.com/{username}/?__a=1",
            "github": f"https://api.github.com/users/{username}",
            "reddit": f"https://www.reddit.com/user/{username}/about.json",
        }
        
        if platform not in urls:
            print(f"{Colors.RED}[!] Unsupported platform{Colors.RESET}")
            return
        
        try:
            headers = {"User-Agent": self.config["user_agent"]}
            resp = requests.get(urls[platform], headers=headers, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"\n[ {platform.upper()} Info ]")
                
                if platform == "github":
                    print(f"  Username: {data.get('login')}")
                    print(f"  Name: {data.get('name')}")
                    print(f"  Bio: {data.get('bio')}")
                    print(f"  Repos: {data.get('public_repos')}")
                    print(f"  Followers: {data.get('followers')}")
                    print(f"  Following: {data.get('following')}")
                    print(f"  Created: {data.get('created_at')}")
                
                elif platform == "reddit":
                    user_data = data.get('data', {})
                    print(f"  Username: {user_data.get('name')}")
                    print(f"  Karma: {user_data.get('total_karma')}")
                    print(f"  Created: {datetime.fromtimestamp(user_data.get('created_utc', 0))}")
                
                elif platform == "instagram":
                    user = data.get('graphql', {}).get('user', {})
                    print(f"  Username: {user.get('username')}")
                    print(f"  Full Name: {user.get('full_name')}")
                    print(f"  Bio: {user.get('biography')}")
                    print(f"  Posts: {user.get('edge_owner_to_timeline_media', {}).get('count')}")
                    print(f"  Followers: {user.get('edge_followed_by', {}).get('count')}")
                    print(f"  Following: {user.get('edge_follow', {}).get('count')}")
                    print(f"  Private: {user.get('is_private')}")
            else:
                print(f"{Colors.RED}[!] Not found or private{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}[!] Error: {e}{Colors.RESET}")
    
    def metadata_extractor(self):
        """Extract metadata from files"""
        filepath = input("File path: ").strip()
        
        if not os.path.exists(filepath):
            print(f"{Colors.RED}[!] File not found{Colors.RESET}")
            return
        
        print(f"\n[ File Analysis: {filepath} ]")
        stat = os.stat(filepath)
        print(f"  Size: {stat.st_size:,} bytes")
        print(f"  Created: {datetime.fromtimestamp(stat.st_ctime)}")
        print(f"  Modified: {datetime.fromtimestamp(stat.st_mtime)}")
        print(f"  Permissions: {oct(stat.st_mode)[-3:]}")
        
        # PDF
        if filepath.lower().endswith('.pdf'):
            try:
                from PyPDF2 import PdfReader
                with open(filepath, 'rb') as f:
                    reader = PdfReader(f)
                    if reader.metadata:
                        print(f"\n  [ PDF Metadata ]")
                        for k, v in reader.metadata.items():
                            print(f"    {k}: {v}")
                    print(f"  Pages: {len(reader.pages)}")
            except ImportError:
                print(f"  {Colors.YELLOW}[!] pip install PyPDF2{Colors.RESET}")
            except Exception as e:
                print(f"  {Colors.RED}[!] {e}{Colors.RESET}")
        
        # Image (basic)
        elif filepath.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            try:
                from PIL import Image
                with Image.open(filepath) as img:
                    print(f"\n  [ Image Info ]")
                    print(f"    Format: {img.format}")
                    print(f"    Size: {img.size}")
                    print(f"    Mode: {img.mode}")
                    if hasattr(img, 'info'):
                        for k, v in img.info.items():
                            if isinstance(v, (str, int, float)):
                                print(f"    {k}: {v}")
            except ImportError:
                print(f"  {Colors.YELLOW}[!] pip install Pillow{Colors.RESET}")
    
    def dork_generator(self):
        """Generate Google dorks for a target"""
        target = input("Target domain/name: ").strip()
        if not target:
            return
        
        dorks = [
            f'site:{target} filetype:pdf',
            f'site:{target} filetype:doc',
            f'site:{target} filetype:xls',
            f'site:{target} inurl:admin',
            f'site:{target} inurl:login',
            f'site:{target} intitle:"index of"',
            f'site:{target} intext:"password"',
            f'site:{target} intext:"confidential"',
            f'site:{target} ext:sql',
            f'site:{target} ext:log',
            f'site:pastebin.com "{target}"',
        ]
        
        print(f"\n[ Google Dorks for {target} ]\n")
        for i, dork in enumerate(dorks, 1):
            print(f"  {i}. {dork}")
        
        # Save
        with open(f"dorks_{target}.txt", 'w') as f:
            f.write('\n'.join(dorks))
        print(f"\n{Colors.GREEN}[✓] Saved to dorks_{target}.txt{Colors.RESET}")
    
    # ─── BRUTEFORCE MODULE ───
    def bruteforce_menu(self):
        """Password cracking tools"""
        print(f"\n{Colors.CYAN}[ Bruteforce & Cracking ]{Colors.RESET}")
        print("1. ZIP Password Cracker")
        print("2. PDF Password Cracker")
        print("3. Hash Cracker (MD5/SHA1/SHA256)")
        print("4. SSH Bruteforce")
        print("5. FTP Bruteforce")
        print("6. Wordlist Generator")
        print("7. Wordlist Merger")
        print("8. Resume Session")
        
        choice = input("\n> Select: ").strip()
        
        actions = {
            "1": self.zip_cracker,
            "2": self.pdf_cracker,
            "3": self.hash_cracker,
            "4": self.ssh_bruteforce,
            "5": self.ftp_bruteforce,
            "6": self.wordlist_generator,
            "7": self.wordlist_merger,
            "8": self.resume_session,
        }
        
        if choice in actions:
            actions[choice]()
    
    def zip_cracker(self):
        """ZIP password cracking"""
        zip_path = input("ZIP file path: ").strip()
        if not os.path.exists(zip_path):
            print(f"{Colors.RED}[!] File not found{Colors.RESET}")
            return
        
        wordlist_path = input("Wordlist path (enter for default): ").strip()
        if not wordlist_path:
            wordlist_path = str(WORDLIST_DIR / "common_passwords.txt")
        
        if not os.path.exists(wordlist_path):
            print(f"{Colors.RED}[!] Wordlist not found{Colors.RESET}")
            return
        
        with open(wordlist_path, 'r', errors='ignore') as f:
            passwords = [line.strip() for line in f if line.strip()]
        
        print(f"\n[+] Cracking: {zip_path}")
        print(f"[+] Wordlist: {len(passwords)} passwords\n")
        
        start_time = time.time()
        
        try:
            with zipfile.ZipFile(zip_path) as zf:
                for i, password in enumerate(passwords, 1):
                    if i % 100 == 0:
                        elapsed = time.time() - start_time
                        rate = i / elapsed if elapsed > 0 else 0
                        print(f"    [{i}/{len(passwords)}] {rate:.0f} pwd/sec")
                    
                    try:
                        zf.extractall(pwd=password.encode())
                        elapsed = time.time() - start_time
                        print(f"\n{Colors.GREEN}[✓] PASSWORD FOUND: {password}{Colors.RESET}")
                        print(f"    Time: {elapsed:.1f}s")
                        print(f"    Attempts: {i}")
                        return
                    except RuntimeError:
                        continue
                    except zipfile.BadZipFile:
                        print(f"{Colors.RED}[!] Corrupt ZIP{Colors.RESET}")
                        return
            
            print(f"\n{Colors.RED}[✗] Password not found{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}[!] Error: {e}{Colors.RESET}")
    
    def pdf_cracker(self):
        """PDF password cracking with qpdf"""
        pdf_path = input("PDF file path: ").strip()
        if not os.path.exists(pdf_path):
            print(f"{Colors.RED}[!] File not found{Colors.RESET}")
            return
        
        wordlist_path = input("Wordlist path: ").strip()
        if not os.path.exists(wordlist_path):
            print(f"{Colors.RED}[!] Wordlist not found{Colors.RESET}")
            return
        
        try:
            subprocess.run(['qpdf', '--version'], capture_output=True)
        except FileNotFoundError:
            print(f"{Colors.RED}[!] Install qpdf: pkg install qpdf{Colors.RESET}")
            return
        
        with open(wordlist_path, 'r', errors='ignore') as f:
            passwords = [line.strip() for line in f if line.strip()]
        
        print(f"\n[+] Cracking PDF: {pdf_path}")
        print(f"[+] Trying {len(passwords)} passwords...\n")
        
        for i, password in enumerate(passwords, 1):
            if i % 50 == 0:
                print(f"    [{i}/{len(passwords)}]")
            
            try:
                result = subprocess.run(
                    ['qpdf', f'--password={password}', '--decrypt', pdf_path, '/dev/null'],
                    capture_output=True, timeout=10
                )
                if result.returncode == 0:
                    print(f"\n{Colors.GREEN}[✓] PASSWORD: {password}{Colors.RESET}")
                    return
            except:
                continue
        
        print(f"\n{Colors.RED}[✗] Not found{Colors.RESET}")
    
    def hash_cracker(self):
        """Hash cracking"""
        hash_value = input("Hash: ").strip()
        print("Types: md5, sha1, sha256, sha512")
        hash_type = input("Hash type: ").strip().lower()
        wordlist_path = input("Wordlist: ").strip()
        
        if not os.path.exists(wordlist_path):
            print(f"{Colors.RED}[!] Wordlist not found{Colors.RESET}")
            return
        
        hash_funcs = {
            "md5": hashlib.md5,
            "sha1": hashlib.sha1,
            "sha256": hashlib.sha256,
            "sha512": hashlib.sha512,
        }
        
        if hash_type not in hash_funcs:
            print(f"{Colors.RED}[!] Invalid type{Colors.RESET}")
            return
        
        with open(wordlist_path, 'r', errors='ignore') as f:
            passwords = [line.strip() for line in f if line.strip()]
        
        print(f"\n[+] Cracking {hash_type} hash...")
        print(f"[+] {len(passwords)} passwords\n")
        
        target = hash_value.lower()
        
        for i, password in enumerate(passwords, 1):
            if i % 1000 == 0:
                print(f"    [{i}/{len(passwords)}]")
            
            hashed = hash_funcs[hash_type](password.encode()).hexdigest()
            
            if hashed == target:
                print(f"\n{Colors.GREEN}[✓] CRACKED: {password}{Colors.RESET}")
                return
        
        print(f"\n{Colors.RED}[✗] Not cracked{Colors.RESET}")
    
    def ssh_bruteforce(self):
        """SSH bruteforce (educational)"""
        try:
            import paramiko
        except ImportError:
            print(f"{Colors.RED}[!] Install: pip install paramiko{Colors.RESET}")
            return
        
        host = input("Target host: ").strip()
        port = int(input("Port (22): ") or "22")
        username = input("Username: ").strip()
        wordlist = input("Password wordlist: ").strip()
        
        if not os.path.exists(wordlist):
            print(f"{Colors.RED}[!] Wordlist not found{Colors.RESET}")
            return
        
        print(f"{Colors.YELLOW}[!] USE ONLY ON AUTHORIZED SYSTEMS{Colors.RESET}")
        confirm = input("Continue? (y/n): ").lower()
        if confirm != 'y':
            return
        
        with open(wordlist, 'r', errors='ignore') as f:
            passwords = [line.strip() for line in f if line.strip()]
        
        print(f"\n[+] Targeting: {username}@{host}:{port}")
        print(f"[+] {len(passwords)} passwords\n")
        
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        for i, password in enumerate(passwords, 1):
            if i % 10 == 0:
                print(f"    [{i}/{len(passwords)}]")
            
            try:
                client.connect(host, port=port, username=username,
                             password=password, timeout=5, banner_timeout=5)
                print(f"\n{Colors.GREEN}[✓] LOGIN: {username}:{password}{Colors.RESET}")
                client.close()
                return
            except paramiko.AuthenticationException:
                continue
            except Exception:
                time.sleep(0.5)  # Rate limiting
                continue
        
        print(f"\n{Colors.RED}[✗] No valid password{Colors.RESET}")
        client.close()
    
    def ftp_bruteforce(self):
        """FTP bruteforce"""
        from ftplib import FTP
        
        host = input("FTP host: ").strip()
        username = input("Username: ").strip()
        wordlist = input("Password wordlist: ").strip()
        
        if not os.path.exists(wordlist):
            print(f"{Colors.RED}[!] Wordlist not found{Colors.RESET}")
            return
        
        print(f"{Colors.YELLOW}[!] Authorized testing only!{Colors.RESET}")
        if input("Continue? (y/n): ").lower() != 'y':
            return
        
        with open(wordlist, 'r', errors='ignore') as f:
            passwords = [line.strip() for line in f if line.strip()]
        
        print(f"\n[+] Target: {username}@{host}")
        print(f"[+] {len(passwords)} passwords\n")
        
        for password in passwords:
            try:
                ftp = FTP(host, timeout=10)
                ftp.login(username, password)
                print(f"\n{Colors.GREEN}[✓] LOGIN: {username}:{password}{Colors.RESET}")
                ftp.quit()
                return
            except Exception:
                continue
        
        print(f"\n{Colors.RED}[✗] No valid login{Colors.RESET}")
    
    def wordlist_generator(self):
        """Generate custom wordlists"""
        print(f"\n{Colors.CYAN}[ Wordlist Generator ]{Colors.RESET}")
        
        base = input("Base words (comma-separated): ").strip()
        if not base:
            return
        
        words = [w.strip() for w in base.split(',') if w.strip()]
        
        print("\nOptions:")
        add_numbers = input("  Add numbers 0-99? (y/n): ").lower() == 'y'
        add_symbols = input("  Add symbols (!@#$)? (y/n): ").lower() == 'y'
        add_years = input("  Add years 2000-2024? (y/n): ").lower() == 'y'
        leet_mode = input("  Leet speak variations? (y/n): ").lower() == 'y'
        
        output = input("Output file: ").strip() or "generated_wordlist.txt"
        
        generated = set()
        
        leet_map = {'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '5', 't': '7'}
        
        for word in words:
            # Base variations
            generated.add(word)
            generated.add(word.lower())
            generated.add(word.upper())
            generated.add(word.capitalize())
            generated.add(word[::-1])  # Reverse
            
            # Number suffixes
            if add_numbers:
                for i in range(100):
                    generated.add(f"{word}{i}")
                    generated.add(f"{word}{i:02d}")
            
            # Symbol suffixes
            if add_symbols:
                for sym in ['!', '@', '#', '$']:
                    generated.add(f"{word}{sym}")
                    generated.add(f"{sym}{word}")
            
            # Year suffixes
            if add_years:
                for year in range(2000, 2025):
                    generated.add(f"{word}{year}")
                    generated.add(f"{word}{str(year)[-2:]}")
            
            # Leet speak
            if leet_mode:
                leet_word = ''.join(leet_map.get(c.lower(), c) for c in word)
                generated.add(leet_word)
        
        # Write with atomic operation
        temp = output + '.tmp'
        with open(temp, 'w') as f:
            for item in sorted(generated):
                f.write(f"{item}\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, output)
        
        print(f"\n{Colors.GREEN}[✓] Generated {len(generated):,} entries")
        print(f"[✓] Saved to: {output}{Colors.RESET}")
    
    def wordlist_merger(self):
        """Merge multiple wordlists"""
        files = input("Wordlist files (space-separated): ").strip().split()
        output = input("Output file: ").strip()
        
        if not files or not output:
            return
        
        all_words = set()
        for filepath in files:
            if os.path.exists(filepath):
                with open(filepath, 'r', errors='ignore') as f:
                    words = {line.strip() for line in f if line.strip()}
                    all_words.update(words)
                    print(f"  [+] {filepath}: {len(words):,} words")
        
        with open(output, 'w') as f:
            for word in sorted(all_words):
                f.write(f"{word}\n")
        
        print(f"\n{Colors.GREEN}[✓] Merged {len(all_words):,} unique words -> {output}{Colors.RESET}")
    
    def resume_session(self):
        """Resume interrupted session"""
        if SESSION_FILE.exists():
            with open(SESSION_FILE, 'r') as f:
                session = json.load(f)
            
            print(f"\n[ Resume Session ]")
            for key, value in session.items():
                print(f"  {key}: {value}")
            
            if input("\nResume? (y/n): ").lower() == 'y':
                session_type = session.get('type')
                if session_type == 'zip':
                    self.zip_cracker()
                elif session_type == 'pdf':
                    self.pdf_cracker()
        else:
            print(f"{Colors.YELLOW}[!] No saved session{Colors.RESET}")
    
    # ─── CRYPTO MODULE ───
    def crypto_menu(self):
        """Encryption and encoding tools"""
        print(f"\n{Colors.CYAN}[ Crypto & Encoding ]{Colors.RESET}")
        print("1. Base64 Encode/Decode")
        print("2. Hex Encode/Decode")
        print("3. Binary Encode/Decode")
        print("4. URL Encode/Decode")
        print("5. ROT13 Cipher")
        print("6. XOR Cipher")
        print("7. Caesar Cipher")
        print("8. Morse Code")
        
        choice = input("\n> Select: ").strip()
        
        if choice == "1":
            text = input("Text: ").strip()
            if text:
                enc = base64.b64encode(text.encode()).decode()
                print(f"Base64: {enc}")
                try:
                    dec = base64.b64decode(text).decode()
                    print(f"Decoded: {dec} (from input)")
                except:
                    pass
        elif choice == "2":
            text = input("Text: ").strip()
            if text:
                print(f"Hex: {text.encode().hex()}")
                try:
                    dec = bytes.fromhex(text).decode()
                    print(f"Decoded: {dec} (from input)")
                except:
                    pass
        elif choice == "3":
            text = input("Text: ").strip()
            if text:
                binary = ' '.join(format(ord(c), '08b') for c in text)
                print(f"Binary: {binary}")
        elif choice == "4":
            from urllib.parse import quote, unquote
            text = input("Text: ").strip()
            if text:
                print(f"URL Encoded: {quote(text)}")
                print(f"URL Decoded: {unquote(text)}")
        elif choice == "5":
            text = input("Text: ").strip()
            if text:
                rot13 = str.maketrans(
                    'ABCDEFGHIJKLMabcdefghijklmNOPQRSTUVWXYZnopqrstuvwxyz',
                    'NOPQRSTUVWXYZnopqrstuvwxyzABCDEFGHIJKLMabcdefghijklm'
                )
                print(f"ROT13: {text.translate(rot13)}")
        elif choice == "6":
            text = input("Text: ").strip()
            key = input("Key (1-255): ").strip()
            if text and key.isdigit():
                key = int(key)
                result = ''.join(chr(ord(c) ^ key) for c in text)
                print(f"XOR (hex): {result.encode().hex()}")
        elif choice == "7":
            text = input("Text: ").strip()
            shift = int(input("Shift: ") or "3")
            result = ''.join(
                chr((ord(c) - 65 + shift) % 26 + 65) if c.isupper()
                else chr((ord(c) - 97 + shift) % 26 + 97) if c.islower()
                else c for c in text
            )
            print(f"Caesar({shift}): {result}")
        elif choice == "8":
            text = input("Text: ").strip().upper()
            morse = {
                'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
                'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
                'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
                'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
                'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
                'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
                '3': '...--', '4': '....-', '5': '.....', '6': '-....',
                '7': '--...', '8': '---..', '9': '----.', ' ': '/'
            }
            result = ' '.join(morse.get(c, '?') for c in text)
            print(f"Morse: {result}")
    
    # ─── HASH MODULE ───
    def hash_menu(self):
        """Hash tools"""
        print(f"\n{Colors.CYAN}[ Hash Tools ]{Colors.RESET}")
        print("1. Generate Hashes")
        print("2. Hash Identifier")
        print("3. File Hash")
        print("4. Compare Hashes")
        
        choice = input("\n> Select: ").strip()
        
        if choice == "1":
            text = input("Text: ").strip()
            if text:
                print(f"\n{'='*50}")
                print(f"Text: {text[:30]}")
                print(f"{'='*50}")
                print(f"MD5:    {hashlib.md5(text.encode()).hexdigest()}")
                print(f"SHA1:   {hashlib.sha1(text.encode()).hexdigest()}")
                print(f"SHA256: {hashlib.sha256(text.encode()).hexdigest()}")
                print(f"SHA512: {hashlib.sha512(text.encode()).hexdigest()}")
                print(f"BLAKE2: {hashlib.blake2b(text.encode()).hexdigest()[:64]}")
                print(f"{'='*50}")
        elif choice == "2":
            h = input("Hash: ").strip()
            length = len(h)
            types = {32: "MD5/MD4/NTLM", 40: "SHA1", 56: "SHA224",
                    64: "SHA256/SHA3-256/BLAKE2", 96: "SHA384", 128: "SHA512"}
            print(f"\n  Length: {length}")
            print(f"  Likely: {types.get(length, 'Unknown')}")
        elif choice == "3":
            filepath = input("File: ").strip()
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    content = f.read()
                print(f"\n  MD5:    {hashlib.md5(content).hexdigest()}")
                print(f"  SHA256: {hashlib.sha256(content).hexdigest()}")
        elif choice == "4":
            h1 = input("Hash 1: ").strip()
            h2 = input("Hash 2: ").strip()
            if h1 == h2:
                print(f"\n{Colors.GREEN}[✓] Hashes match{Colors.RESET}")
            else:
                print(f"\n{Colors.RED}[✗] Hashes differ{Colors.RESET}")
    
    # ─── NETWORK MODULE ───
    def network_menu(self):
        """Network tools"""
        print(f"\n{Colors.CYAN}[ Network Tools ]{Colors.RESET}")
        print("1. Port Scanner")
        print("2. Ping Host")
        print("3. Traceroute")
        print("4. HTTP Headers")
        print("5. WhatWeb (basic)")
        print("6. Download File")
        
        choice = input("\n> Select: ").strip()
        
        if choice == "1":
            host = input("Host/IP: ").strip()
            ports = input("Ports (comma-separated, enter for common): ").strip()
            port_list = [int(p) for p in ports.split(',')] if ports else None
            self.net.port_scan(host, port_list)
        
        elif choice == "2":
            host = input("Host: ").strip()
            try:
                result = subprocess.run(['ping', '-c', '4', host],
                                      capture_output=True, text=True, timeout=15)
                print(result.stdout)
            except:
                print(f"{Colors.RED}[!] Ping failed{Colors.RESET}")
        
        elif choice == "3":
            host = input("Host: ").strip()
            try:
                result = subprocess.run(['traceroute', host],
                                      capture_output=True, text=True, timeout=30)
                print(result.stdout)
            except FileNotFoundError:
                print(f"{Colors.YELLOW}[!] Install: pkg install traceroute{Colors.RESET}")
        
        elif choice == "4":
            import requests
            url = input("URL: ").strip()
            if not url.startswith('http'):
                url = 'https://' + url
            try:
                resp = requests.get(url, timeout=10)
                print(f"\n[ HTTP Headers ]")
                for key, value in resp.headers.items():
                    print(f"  {key}: {value}")
            except Exception as e:
                print(f"{Colors.RED}[!] {e}{Colors.RESET}")
        
        elif choice == "5":
            import requests
            url = input("URL: ").strip()
            if not url.startswith('http'):
                url = 'https://' + url
            try:
                resp = requests.get(url, timeout=10)
                print(f"\n[ Tech Detection ]")
                print(f"  Server: {resp.headers.get('Server', 'Unknown')}")
                print(f"  Powered-By: {resp.headers.get('X-Powered-By', 'Unknown')}")
                print(f"  Cookies: {resp.headers.get('Set-Cookie', 'None')}")
            except Exception as e:
                print(f"{Colors.RED}[!] {e}{Colors.RESET}")
        
        elif choice == "6":
            import requests
            url = input("File URL: ").strip()
            filename = input("Save as: ").strip()
            if url and filename:
                try:
                    resp = requests.get(url, stream=True, timeout=30)
                    total = int(resp.headers.get('content-length', 0))
                    downloaded = 0
                    with open(filename, 'wb') as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total:
                                pct = (downloaded / total) * 100
                                print(f"\r  Downloading... {pct:.0f}%", end='')
                    print(f"\n{Colors.GREEN}[✓] Downloaded: {filename}{Colors.RESET}")
                except Exception as e:
                    print(f"{Colors.RED}[!] {e}{Colors.RESET}")
    
    # ─── REPORT ───
    def generate_report(self):
        """Generate penetration test report"""
        print(f"\n{Colors.CYAN}[ Report Generator ]{Colors.RESET}")
        
        target = input("Target: ").strip()
        tester = input("Tester name: ").strip()
        
        report = f"""
{'='*60}
PENETRATION TEST REPORT
{'='*60}

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Target: {target}
Tester: {tester}
Tool: TermuxPen v{VERSION}

{'='*60}
1. EXECUTIVE SUMMARY
{'='*60}
[Provide brief overview of findings]

{'='*60}
2. METHODOLOGY
{'='*60}
Testing performed using TermuxPen mobile pentesting framework.
Tests conducted: [list test types]

{'='*60}
3. FINDINGS
{'='*60}
[List vulnerabilities with severity ratings]

Severity Legend:
  Critical | High | Medium | Low | Info

{'='*60}
4. RECOMMENDATIONS
{'='*60}
[Provide remediation steps]

{'='*60}
5. DISCLAIMER
{'='*60}
This test was performed with proper authorization.
Unauthorized testing is illegal and unethical.

Report generated by TermuxPen v{VERSION}
GitHub: {GITHUB_REPO}
"""
        
        filename = f"pentest_report_{target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            f.write(report)
        
        print(f"\n{Colors.GREEN}[✓] Report saved: {filename}{Colors.RESET}")
    
    # ─── UTILITIES ───
    def utils_menu(self):
        """Utility tools"""
        print(f"\n{Colors.CYAN}[ Utilities ]{Colors.RESET}")
        print("1. Password Generator")
        print("2. Random String Generator")
        print("3. UUID Generator")
        print("4. QR Code Generator")
        print("5. Text to File")
        print("6. File Info")
        print("7. System Info")
        print("8. View History")
        
        choice = input("\n> Select: ").strip()
        
        if choice == "1":
            length = int(input("Length: ") or "16")
            chars = input("Special chars? (y/n): ").lower() == 'y'
            if chars:
                all_chars = string.ascii_letters + string.digits + "!@#$%^&*"
            else:
                all_chars = string.ascii_letters + string.digits
            password = ''.join(random.choice(all_chars) for _ in range(length))
            print(f"\nPassword: {password}")
        
        elif choice == "2":
            length = int(input("Length: ") or "10")
            print(f"\nHex:    {''.join(random.choice(string.hexdigits) for _ in range(length))}")
            print(f"Alpha:  {''.join(random.choice(string.ascii_letters) for _ in range(length))}")
            print(f"Num:    {''.join(random.choice(string.digits) for _ in range(length))}")
        
        elif choice == "3":
            import uuid
            print(f"\nUUID4: {uuid.uuid4()}")
            print(f"UUID1: {uuid.uuid1()}")
        
        elif choice == "4":
            text = input("Text/URL: ").strip()
            try:
                import qrcode
                qr = qrcode.QRCode()
                qr.add_data(text)
                qr.print_ascii()
            except ImportError:
                print(f"{Colors.YELLOW}[!] pip install qrcode{Colors.RESET}")
        
        elif choice == "5":
            text = input("Text: ").strip()
            filename = input("Save as: ").strip()
            if text and filename:
                with open(filename, 'w') as f:
                    f.write(text)
                print(f"{Colors.GREEN}[✓] Saved{Colors.RESET}")
        
        elif choice == "6":
            filepath = input("File path: ").strip()
            if os.path.exists(filepath):
                stat = os.stat(filepath)
                print(f"\n  Name: {os.path.basename(filepath)}")
                print(f"  Size: {stat.st_size:,} bytes")
                print(f"  Type: {os.path.splitext(filepath)[1]}")
                print(f"  Permissions: {oct(stat.st_mode)[-3:]}")
        
        elif choice == "7":
            print(f"\n[ System Info ]")
            print(f"  Termux: {os.path.exists('/data/data/com.termux')}")
            print(f"  Python: {sys.version}")
            print(f"  Platform: {sys.platform}")
            print(f"  Config: {CONFIG_DIR}")
        
        elif choice == "8":
            results = Database.get_results("osint", 5)
            if results:
                print(f"\n[ Recent OSINT Results ]")
                for r in results:
                    print(f"  - {r.get('username', 'N/A')} ({r.get('timestamp', '')})")
            else:
                print("[!] No saved results")
    
    # ─── MAIN LOOP ───
    def run(self):
        """Main program loop"""
        self.clear_screen()
        print(self.show_banner())
        
        # Check for updates (silent)
        self.check_for_updates()
        
        while True:
            try:
                print(f"\n{Colors.BLUE}{'─'*50}{Colors.RESET}")
                for key, (name, _) in self.main_modules.items():
                    print(f"  {Colors.BOLD}{key}{Colors.RESET}. {name}")
                print(f"  {Colors.BOLD}0{Colors.RESET}. 🚪 Exit")
                print(f"  {Colors.BOLD}U{Colors.RESET}. 🔄 Update Framework")
                print(f"{Colors.BLUE}{'─'*50}{Colors.RESET}")
                
                choice = input(f"\n{Colors.BOLD}TermuxPen{Colors.RESET}> ").strip()
                
                if choice == "0":
                    print(f"\n{Colors.GREEN}[+] Shutting down. Stay ethical!{Colors.RESET}")
                    print(f"[+] GitHub: {GITHUB_REPO}")
                    logging.info("Framework shutdown")
                    sys.exit(0)
                
                elif choice.upper() == "U":
                    self.update_framework()
                
                elif choice in self.main_modules:
                    _, func = self.main_modules[choice]
                    print()
                    func()
                    input(f"\n{Colors.DIM}[Press Enter to continue...]{Colors.RESET}")
                    self.clear_screen()
                    print(self.show_banner())
                
                else:
                    print(f"{Colors.RED}[!] Invalid option{Colors.RESET}")
            
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}[!] Use '0' to exit{Colors.RESET}")
            except EOFError:
                print(f"\n{Colors.YELLOW}[!] EOF detected - restart script{Colors.RESET}")
                break
            except Exception as e:
                print(f"{Colors.RED}[!] Error: {e}{Colors.RESET}")
                logging.error(f"Runtime error: {e}", exc_info=True)

# ─── ENTRY POINT ───
if __name__ == "__main__":
    setup_logging()
    
    is_termux = os.path.exists("/data/data/com.termux")
    
    if is_termux:
        print(f"{Colors.GREEN}[✓] Termux environment detected{Colors.RESET}\n")
    else:
        print(f"{Colors.YELLOW}[!] Not running in Termux - limited features{Colors.RESET}\n")
    
    try:
        framework = TermuxPen()
        framework.run()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.GREEN}[+] Goodbye!{Colors.RESET}")
        sys.exit(0)