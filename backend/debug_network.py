import socket

HOSTNAME = "db.tpgeroygxpmbhmrewbpd.supabase.co"
PORT = 5432

print(f"Resolving {HOSTNAME}...")

# Try resolving IPv4
try:
    ipv4 = socket.gethostbyname(HOSTNAME)
    print(f"IPv4 Address: {ipv4}")
except Exception as e:
    print(f"IPv4 Resolution Failed: {e}")
    ipv4 = None

# Try resolving IPv6
try:
    # getaddrinfo returns list of (family, type, proto, canonname, sockaddr)
    info = socket.getaddrinfo(HOSTNAME, PORT, socket.AF_INET6)
    ipv6 = info[0][4][0]
    print(f"IPv6 Address: {ipv6}")
except Exception as e:
    print(f"IPv6 Resolution Failed: {e}")
    ipv6 = None

# Test Connection IPv4
if ipv4:
    print(f"\nTesting TCP Connection to {ipv4}:{PORT}...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((ipv4, PORT))
        print("SUCCESS: Connected via IPv4!")
        s.close()
    except Exception as e:
        print(f"FAILED IPv4: {e}")

# Test Connection IPv6
if ipv6:
    print(f"\nTesting TCP Connection to {ipv6}:{PORT}...")
    try:
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((ipv6, PORT))
        print("SUCCESS: Connected via IPv6!")
        s.close()
    except Exception as e:
        print(f"FAILED IPv6: {e}")
