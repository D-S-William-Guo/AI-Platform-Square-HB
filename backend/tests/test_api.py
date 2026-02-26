from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import AppRankingSetting, Submission


client = TestClient(app)
ADMIN_HEADERS = {'X-Admin-Token': settings.admin_token}


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
    data = resp.json()
    if data:
        row = data[0]
        assert 'ranking_config_id' in row
        assert 'metric_type' in row
        assert 'value_dimension' in row
        assert 'updated_at' in row


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
        'expected_benefit': '预计每月节省人工排班工时并提升用户满意度。',
        'ranking_enabled': True,
        'ranking_weight': 1.0,
        'ranking_tags': '',
        'ranking_dimensions': ''
    }
    resp = client.post('/api/submissions', json=payload)
    print("status:", resp.status_code)
    print("body:", resp.text)
    assert resp.status_code == 200
    assert resp.json()['status'] == 'pending'


def test_rules_oa_links():
    resp = client.get('/api/rules')
    assert resp.status_code == 200
    assert resp.json()[0]['href'].startswith('https://')


def test_approve_creates_disabled_ranking_setting():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        submission = Submission(
            app_name='测试应用-审批设置初始化',
            unit_name='测试单位',
            contact='李四',
            category='assistant',
            scenario='该应用用于客服工单智能分发与答案推荐，覆盖一线客服日常工作场景。',
            embedded_system='测试系统',
            problem_statement='人工分发慢且准确率不稳定，影响处理效率。',
            effectiveness_type='efficiency_gain',
            effectiveness_metric='工单流转时长下降20%',
            data_level='L2',
            expected_benefit='预计每月节省人工排班工时并提升用户满意度。',
            status='pending',
            ranking_enabled=True,
            ranking_weight=1.0,
            ranking_tags='',
            ranking_dimensions='',
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)

        approve_resp = client.post(f"/api/submissions/{submission.id}/approve-and-create-app", headers=ADMIN_HEADERS)
        assert approve_resp.status_code == 200
        app_id = approve_resp.json()['app_id']

        setting = db.query(AppRankingSetting).filter(AppRankingSetting.app_id == app_id).first()
        assert setting is not None
        assert setting.is_enabled is False
    finally:
        db.close()


def test_admin_endpoint_requires_token():
    resp = client.post('/api/rankings/sync')
    assert resp.status_code == 401


def test_admin_endpoint_accepts_valid_token():
    Base.metadata.create_all(bind=engine)
    resp = client.post('/api/rankings/sync', headers=ADMIN_HEADERS)
    assert resp.status_code == 200
