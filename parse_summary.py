import sys, json
try:
    content = sys.stdin.read()
    if not content:
        print("No input received")
        sys.exit(0)
    
    # API might return a string that needs secondary parsing, 
    # but Invoke-RestMethod | ConvertTo-Json -Depth 10 should produce valid JSON.
    data = json.loads(content)
    
    # If the API returned a JSON string as the body, data might be a string
    if isinstance(data, str):
        data = json.loads(data)

    print("System Summary:")
    
    routes = data.get('routes', {})
    print(f"  Total routes: {routes.get('total_routes', 'N/A')}")
    
    env = data.get('environment', {})
    print(f"  Python Version: {env.get('python_version', 'N/A')}")
    print(f"  Platform: {env.get('platform', 'N/A')}")
    print(f"  Environment: {env.get('environment', 'N/A')}")
    
    heimdall = data.get('heimdall', {})
    print(f"  Heimdall Alerts Configured: {heimdall.get('alerts', {}).get('configured', 'N/A')}")
    
    # Summary of tags
    by_tag = routes.get('by_tag', {})
    if by_tag:
        print(f"\nTop 10 Route Tags (out of {len(by_tag)}):")
        sorted_tags = sorted(by_tag.items(), key=lambda x: x[1], reverse=True)
        for tag, count in sorted_tags[:10]:
            print(f"  - {tag}: {count}")

except Exception as e:
    print(f"Error parsing: {e}")
    print("Content preview:")
    print(content[:500])
