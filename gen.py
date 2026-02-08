import requests
import random
import string
import threading
import time
import os
import sys

from colorama import init, Fore

init()

def load_proxies():
    try:
        with open("data/proxies.txt", "r") as f:
            proxies = [line.strip() for line in f if line.strip()]
            if proxies:
                print(Fore.YELLOW + f"[*] Loaded {len(proxies)} proxies")
            return proxies
    except:
        return []

def get_proxy(proxies, index):
    if not proxies:
        return None
    return proxies[index % len(proxies)]

def setup_session_proxy(session, proxy_str, use_proxies):
    if use_proxies and proxy_str:
        try:
            session.proxies.update({
                'http': f'socks5://{proxy_str}',
                'https': f'socks5://{proxy_str}'
            })
        except:
            pass
    return session

def create_temp_inbox(session):
    try:
        url = 'https://api.internal.temp-mail.io/api/v3/email/new'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        payload = {"min_name_length": 10, "max_name_length": 10}
        response = session.post(url, headers=headers, json=payload, timeout=15)

        if response.status_code != 200:
            return None

        data = response.json()
        email = data.get('email')

        if not email:
            return None

        return {'address': email, 'token': data.get('token')}
    except:
        return None

def generate_password():
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(12))

def create_account(proxies, target_accounts, accounts_created, lock, running, proxy_index_counter, use_proxies):
    while running[0]:
        with lock:
            if accounts_created[0] >= target_accounts:
                break
            proxy_index = proxy_index_counter[0]
            proxy_index_counter[0] += 1

        proxy = get_proxy(proxies, proxy_index) if use_proxies else None
        session = requests.Session()
        session = setup_session_proxy(session, proxy, use_proxies)

        try:
            temp_mail = create_temp_inbox(session)
            if not temp_mail or 'address' not in temp_mail:
                continue

            email = temp_mail['address']
            print(Fore.GREEN + "[*] (mail made) " + Fore.LIGHTMAGENTA_EX + f"({email})")

            password = generate_password()
            country = random.choice(["United Kingdom", "United States"])

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                #'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Content-Type': 'application/json',
                'Origin': 'https://vibegames.com',
                'Referer': 'https://vibegames.com/register',
                'X-Requested-With': 'XMLHttpRequest'
            }

            olddata = { # not needed anymore - feel free to remove
                'email': email,
                'password1': password,
                'password2': password,
                'country': country,
                'terms': 'on',
                'action': 'Register',
                'controller': 'Auth'
            }

            data = {
                "0": {
                    'country': "US",
                    'email': email,
                    'name': "Oneshot Niko",
                    'password': password
                }
            }

            response = session.post('https://vibegames.com/api/trpc/register?batch=1',  # replaced from https://vibegames.com/Data/DataController (old api)
                                  headers=headers, 
                                  json=data, # changed from data=data to json=data
                                  timeout=15)

            if response.status_code == 429:
                print(Fore.RED + "[-] (rate limited) 429 - without using proxies, this error is common. use less threads or use proxies")
                time.sleep(5)
                continue

            if response.status_code == 200:
                with lock:
                    if accounts_created[0] < target_accounts:
                        accounts_created[0] += 1
                        with open("output/accs.txt", "a") as f:
                            f.write(f"{email}:{password}\n")
                        print(Fore.CYAN + "[+] (created) " + Fore.LIGHTMAGENTA_EX + f"({email}:{password})")
                    else:
                        running[0] = False
            else:
                print(Fore.RED + f"[-] (failed) {response.status_code}")
                print(Fore.YELLOW + f"[DEBUG] Response: {response.text}")

        except Exception as e:
            print(Fore.RED + f"[!] Exception: {e}")
            continue

def main():
    os.system('cls' if os.name == 'nt' else 'clear')

    print(Fore.LIGHTYELLOW_EX + "VibeGames Account Generator")

    proxies = []
    use_proxies = False

    use_proxy_input = input(Fore.LIGHTCYAN_EX + "Use proxies? (y/n): " + Fore.WHITE).lower()
    if use_proxy_input == 'y':
        proxies = load_proxies()
        if not proxies:
            print(Fore.RED + "[!] No proxies found in data/proxies.txt")
            return
        use_proxies = True
        print(Fore.GREEN + "[+] Using proxies")
    else:
        print(Fore.YELLOW + "[*] Running without proxies")

    try:
        target_accounts = int(input(Fore.LIGHTCYAN_EX + "Accounts to make: " + Fore.WHITE))
        threads_count = int(input(Fore.LIGHTCYAN_EX + "Threads: " + Fore.WHITE))
    except:
        return

    accounts_created = [0]
    running = [True]
    lock = threading.Lock()
    proxy_index_counter = [0]
    threads = []

    for i in range(threads_count):
        thread = threading.Thread(target=create_account, args=(proxies, target_accounts, accounts_created, lock, running, proxy_index_counter, use_proxies))
        thread.daemon = True
        threads.append(thread)
        thread.start()

    try:
        while any(t.is_alive() for t in threads):
            time.sleep(0.5)
            if accounts_created[0] >= target_accounts:
                running[0] = False
                break
    except KeyboardInterrupt:
        running[0] = False
        print(Fore.RED + "\n🛑 Exiting...")
        sys.exit(0)

    for thread in threads:
        thread.join()

    print(Fore.LIGHTGREEN_EX + f"\nCreated {accounts_created[0]} accounts")
    print(Fore.LIGHTBLUE_EX + "[*] Saved to output/accs.txt")

if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    main()

