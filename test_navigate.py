import requests
import json
import time

# Give the server a moment to start
time.sleep(3)

# MCP server URL for SSE transport
server_url = "http://127.0.0.1:8003/sse"

# Tool call payload as query parameters
params = {
    "tool": "navigate",
    "url": "https://news.google.com"
}

print(f"Attempting to call tool '{params['tool']}' on {server_url} with GET")

try:
    response = requests.get(server_url, params=params, stream=True, timeout=60)
    response.raise_for_status()

    print("Request sent successfully. Waiting for response...")

    # Process the streaming response
    for line in response.iter_lines():
        if line:
            # Decode the line and remove the 'data: ' prefix
            data_str = line.decode('utf-8')
            if data_str.startswith('data: '):
                data_str = data_str[6:]
            
            try:
                # Ignore ping messages
                if 'ping' in data_str:
                    continue
                
                # Parse the JSON data
                data_json = json.loads(data_str)
                
                if 'output' in data_json:
                    print(f"Tool output: {data_json['output']}")
                
                if data_json.get('status') == 'complete':
                    print("\nTool execution complete.")
                    break
            except json.JSONDecodeError:
                print(f"Received non-JSON response line: {line.decode('utf-8')}")

except requests.exceptions.RequestException as e:
    print(f"Error calling tool: {e}") 