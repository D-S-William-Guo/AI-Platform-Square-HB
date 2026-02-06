from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    resp = client.get('/api/health')
    assert resp.status_code == 200
    assert resp.json()['status'] == 'ok'


def test_list_apps():
    resp = client.get('/api/apps?section=group&status=available')
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]['section'] == 'group'


def test_rankings_have_metric_fields():
    resp = client.get('/api/rankings?ranking_type=excellent')
    assert resp.status_code == 200
    row = resp.json()[0]
    assert 'metric_type' in row
    assert 'value_dimension' in row


def test_submission_flow():
    payload = {
        'app_name': '测试应用',
        'unit_name': '测试单位',
        'contact': '张三',
        'scenario': '该应用用于客服工单智能分发与答案推荐，覆盖一线客服日常工作场景。',
        'embedded_system': '客服工单系统',
        'problem_statement': '人工分发慢且准确率不稳定，影响处理效率。',
        'effectiveness_type': 'efficiency_gain',
        'effectiveness_metric': '工单流转时长下降20%',
        'data_level': 'L2',
        'expected_benefit': '预计每月节省人工排班工时并提升用户满意度。'
    }
    resp = client.post('/api/submissions', json=payload)
    assert resp.status_code == 200
    assert resp.json()['status'] == 'pending'


def test_rules_oa_links():
    resp = client.get('/api/rules')
    assert resp.status_code == 200
    assert resp.json()[0]['href'].startswith('https://')
