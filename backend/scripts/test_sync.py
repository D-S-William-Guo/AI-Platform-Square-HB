import os

import requests

# 测试同步排行榜
backend_port = os.getenv("BACKEND_DEV_PORT", "8000")
base_url = os.getenv("SYNC_BASE_URL", f"http://127.0.0.1:{backend_port}")
response = requests.post(f"{base_url.rstrip('/')}/api/rankings/sync")
print(f"状态码: {response.status_code}")
print(f"响应: {response.text}")
