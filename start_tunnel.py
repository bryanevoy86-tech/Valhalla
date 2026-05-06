"""
Setup tunnel to expose backend on public URL
"""
from pyngrok import ngrok
import time

print("=" * 70)
print("STARTING TUNNEL")
print("=" * 70)

try:
    # Connect ngrok to port 4000
    public_url = ngrok.connect(4000, "http")
    print(f"\n✓ Tunnel started!")
    print(f"\n  Public URL: {public_url}")
    print(f"\n  Share this URL with WeWeb or other services")
    print(f"\n  Local:  http://127.0.0.1:4000")
    print(f"  Public: {public_url}")
    
    print("\n" + "=" * 70)
    print("Tunnel is running. Press Ctrl+C to stop.")
    print("=" * 70 + "\n")
    
    # Keep tunnel running
    while True:
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\n\nShutting down tunnel...")
    ngrok.kill()
    print("Tunnel stopped.")
except Exception as e:
    print(f"\n✗ Error: {str(e)}")
