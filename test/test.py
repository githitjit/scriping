import requests

# Configure requests to use Tor
proxies = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}

def get_ip():
    response = requests.get('http://httpbin.org/ip')
    return response.json()['origin']

def get_tor_ip():
    response = requests.get('http://httpbin.org/ip', proxies=proxies)
    return response.json()['origin']

if __name__ == "__main__":
    try:
        ip_address = get_tor_ip()
        print(f"Connected to Tor. IP address: {ip_address}")
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Tor: {e}")
    
    ip_address = get_ip()
    print(f"Not using Tor. IP address: {ip_address}")
    
    target_url = 'https://bakufu.jp/archives/1046884'
    print(target_url.split('/', 2)[2])