import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def load_proxies(filename='proxies.txt'):
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def test_proxy(proxy):
    proxies = {'http': proxy, 'https': proxy}
    try:
        response = requests.get('https://www.google.com', proxies=proxies, timeout=5)
        if response.status_code == 200:
            return (proxy, True)
    except Exception:
        pass
    return (proxy, False)

def main():
    proxies = load_proxies()
    results = []
    with ThreadPoolExecutor(max_workers=200) as executor:
        future_to_proxy = {executor.submit(test_proxy, proxy): proxy for proxy in proxies}
        for future in as_completed(future_to_proxy):
            proxy, is_working = future.result()
            status = "WORKING" if is_working else "FAILED"
            print(f"{proxy}: {status}")

if __name__ == "__main__":
    main()