import requests

# 测试同步排行榜
response = requests.post('http://localhost:8000/api/rankings/sync')
print(f"状态码: {response.status_code}")
print(f"响应: {response.text}")
