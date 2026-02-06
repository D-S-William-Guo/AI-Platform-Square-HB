from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    resp = client.get('/api/health')
    assert resp.status_code == 200
    assert resp.json()['status'] == 'ok'


def test_list_apps():
    resp = client.get('/api/apps?section=group')
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]['section'] == 'group'


def test_submission_flow():
    payload = {'app_name': '测试应用', 'unit_name': '测试单位', 'contact': '张三'}
    resp = client.post('/api/submissions', json=payload)
    assert resp.status_code == 200
    assert resp.json()['status'] == 'pending'
