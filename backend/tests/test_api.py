import json
import uuid
from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import App, AppDimensionScore, AppRankingSetting, HistoricalRanking, Ranking, RankingConfig, RankingDimension, Submission


client = TestClient(app)
ADMIN_HEADERS = {'X-Admin-Token': settings.admin_token}
DEFAULT_USER_LOGIN = {"username": "zhangsan", "password": settings.user_default_password}


def login_and_get_token(username: str, password: str) -> str:
    client.cookies.clear()
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_health():
    resp = client.get('/api/health')
    assert resp.status_code == 200
    assert resp.json()['status'] == 'ok'


def test_auth_login_me_logout_flow():
    client.cookies.clear()
    login_resp = client.post("/api/auth/login", json=DEFAULT_USER_LOGIN)
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    assert token
    assert login_resp.json()["user"]["username"] == "zhangsan"

    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["user"]["role"] == "user"

    logout_resp = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_resp.status_code == 200

    after_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert after_resp.status_code == 401


def test_auth_login_rejects_invalid_password():
    client.cookies.clear()
    resp = client.post("/api/auth/login", json={"username": "zhangsan", "password": "wrong-password"})
    assert resp.status_code == 401


def test_admin_api_supports_admin_session_token():
    token = login_and_get_token("lisi", settings.admin_default_password)
    resp = client.get("/api/submissions", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})


def test_admin_api_rejects_non_admin_session_token():
    token = login_and_get_token("zhangsan", settings.user_default_password)
    resp = client.get("/api/submissions", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})


def test_submission_records_submitter_user_from_session():
    client.cookies.clear()
    login_resp = client.post("/api/auth/login", json=DEFAULT_USER_LOGIN)
    assert login_resp.status_code == 200
    user_id = login_resp.json()["user"]["id"]
    token = login_resp.json()["access_token"]

    payload = {
        'category': 'group',
        'app_name': f'申报人绑定测试应用-{uuid.uuid4().hex[:8]}',
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
    resp = client.post('/api/submissions', json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()['submitter_user_id'] == user_id

    db = SessionLocal()
    try:
        row = db.query(Submission).filter(Submission.id == resp.json()['id']).first()
        assert row is not None
        assert row.submitter_user_id == user_id
        assert row.updated_at is not None
    finally:
        db.close()


def test_approve_submission_records_admin_actor_fields():
    client.cookies.clear()
    user_login = client.post("/api/auth/login", json=DEFAULT_USER_LOGIN)
    assert user_login.status_code == 200
    user_token = user_login.json()["access_token"]

    payload = {
        'category': 'group',
        'app_name': f'审批人绑定测试应用-{uuid.uuid4().hex[:8]}',
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
    submit_resp = client.post('/api/submissions', json=payload, headers={"Authorization": f"Bearer {user_token}"})
    assert submit_resp.status_code == 200
    submission_id = submit_resp.json()['id']

    admin_login = client.post("/api/auth/login", json={"username": "lisi", "password": settings.admin_default_password})
    assert admin_login.status_code == 200
    admin_id = admin_login.json()["user"]["id"]
    admin_token = admin_login.json()["access_token"]

    approve_resp = client.post(
        f"/api/submissions/{submission_id}/approve-and-create-app",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert approve_resp.status_code == 200
    app_id = approve_resp.json()["app_id"]

    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        app = db.query(App).filter(App.id == app_id).first()
        assert submission is not None
        assert app is not None
        assert submission.approved_by_user_id == admin_id
        assert submission.approved_at is not None
        assert app.approved_by_user_id == admin_id
        assert app.created_from_submission_id == submission_id
    finally:
        db.close()


def test_reject_submission_records_admin_and_reason():
    client.cookies.clear()
    user_login = client.post("/api/auth/login", json=DEFAULT_USER_LOGIN)
    assert user_login.status_code == 200
    user_token = user_login.json()["access_token"]

    payload = {
        'category': 'group',
        'app_name': f'拒绝原因测试应用-{uuid.uuid4().hex[:8]}',
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
    submit_resp = client.post('/api/submissions', json=payload, headers={"Authorization": f"Bearer {user_token}"})
    assert submit_resp.status_code == 200
    submission_id = submit_resp.json()['id']

    admin_login = client.post("/api/auth/login", json={"username": "lisi", "password": settings.admin_default_password})
    assert admin_login.status_code == 200
    admin_id = admin_login.json()["user"]["id"]
    admin_token = admin_login.json()["access_token"]

    reject_resp = client.post(
        f"/api/submissions/{submission_id}/reject",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={'reason': '资料不完整'}
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["reason"] == "资料不完整"

    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        assert submission is not None
        assert submission.rejected_by_user_id == admin_id
        assert submission.rejected_at is not None
        assert submission.rejected_reason == "资料不完整"
    finally:
        db.close()


def test_list_apps():
    seed_payload = {
        'category': 'group',
        'app_name': '种子应用',
        'unit_name': '种子单位',
        'contact': '张三',
        'scenario': '用于验证列表接口的种子场景描述（长度足够）',
        'embedded_system': 'seed',
        'problem_statement': '用于验证问题描述字段长度约束，确保通过',
        'effectiveness_type': 'efficiency_gain',
        'effectiveness_metric': '10',
        'data_level': 'L2',
        'expected_benefit': '用于验证预期收益描述',
        'ranking_enabled': True,
        'ranking_weight': 1.0,
        'ranking_tags': '',
        'ranking_dimensions': ''
    }
    seed_resp = client.post('/api/submissions', json=seed_payload)
    if seed_resp.status_code != 200:
        print("seed_status:", seed_resp.status_code)
        print("seed_body:", seed_resp.text)
    assert seed_resp.status_code == 200

    resp = client.get('/api/apps?section=group&status=available')
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]['section'] == 'group'


def test_rankings_have_metric_fields():
    resp = client.get('/api/rankings?ranking_type=excellent')
    assert resp.status_code == 200
    by_config_resp = client.get('/api/rankings?ranking_config_id=excellent')
    assert by_config_resp.status_code == 200
    data = resp.json()
    if data:
        row = data[0]
        assert 'ranking_config_id' in row
        assert 'metric_type' in row
        assert 'value_dimension' in row
        assert 'updated_at' in row


def test_submission_flow():
    payload = {
            'category': 'group',
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
    assert resp.status_code == 200
    assert resp.json()['status'] == 'pending'
    assert resp.json()['manage_token']


def test_submission_self_manage_flow():
    payload = {
        'category': 'group',
        'app_name': f'申报自助管理测试应用-{uuid.uuid4().hex[:8]}',
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
    create_resp = client.post('/api/submissions', json=payload)
    assert create_resp.status_code == 200
    created = create_resp.json()
    submission_id = created['id']
    manage_token = created['manage_token']
    assert isinstance(manage_token, str)
    assert len(manage_token) >= 16

    self_resp = client.get('/api/submissions/self', params={'manage_token': manage_token})
    assert self_resp.status_code == 200
    assert self_resp.json()['id'] == submission_id

    updated_name = f"{payload['app_name']}-更新"
    update_resp = client.put(
        f'/api/submissions/{submission_id}/self',
        json={
            **payload,
            'app_name': updated_name,
            'manage_token': manage_token,
        },
    )
    assert update_resp.status_code == 200
    assert update_resp.json()['app_name'] == updated_name

    withdraw_resp = client.post(
        f'/api/submissions/{submission_id}/withdraw',
        json={'manage_token': manage_token},
    )
    assert withdraw_resp.status_code == 200

    after_resp = client.get('/api/submissions/self', params={'manage_token': manage_token})
    assert after_resp.status_code == 200
    assert after_resp.json()['status'] == 'withdrawn'

    blocked_update_resp = client.put(
        f'/api/submissions/{submission_id}/self',
        json={
            **payload,
            'manage_token': manage_token,
        },
    )
    assert blocked_update_resp.status_code == 400


def test_rules_oa_links():
    resp = client.get('/api/rules')
    assert resp.status_code == 200
    assert resp.json()[0]['href'].startswith('https://')


def test_reject_submission_changes_status_to_rejected():
    payload = {
        'category': 'group',
        'app_name': '待拒绝测试应用',
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
    create_resp = client.post('/api/submissions', json=payload)
    assert create_resp.status_code == 200
    submission_id = create_resp.json()['id']

    reject_resp = client.post(f'/api/submissions/{submission_id}/reject', headers=ADMIN_HEADERS, json={'reason': '资料不完整'})
    assert reject_resp.status_code == 200

    list_resp = client.get('/api/submissions', headers=ADMIN_HEADERS)
    assert list_resp.status_code == 200
    target = next(item for item in list_resp.json() if item['id'] == submission_id)
    assert target['status'] == 'rejected'


def test_approve_maps_detail_doc_fields_to_app():
    Base.metadata.create_all(bind=engine)

    payload = {
        'category': 'group',
        'app_name': '文档映射测试应用',
        'unit_name': '测试单位',
        'contact': '张三',
        'scenario': '该应用用于客服工单智能分发与答案推荐，覆盖一线客服日常工作场景。',
        'embedded_system': '客服工单系统',
        'problem_statement': '人工分发慢且准确率不稳定，影响处理效率。',
        'effectiveness_type': 'efficiency_gain',
        'effectiveness_metric': '工单流转时长下降20%',
        'data_level': 'L2',
        'expected_benefit': '预计每月节省人工排班工时并提升用户满意度。',
        'cover_image_url': '',
        'detail_doc_url': '/api/static/uploads/docs/demo.pdf',
        'detail_doc_name': 'demo.pdf',
        'ranking_enabled': True,
        'ranking_weight': 1.0,
        'ranking_tags': '',
        'ranking_dimensions': ''
    }
    submit_resp = client.post('/api/submissions', json=payload)
    assert submit_resp.status_code == 200
    submission_id = submit_resp.json()['id']

    approve_resp = client.post(f"/api/submissions/{submission_id}/approve-and-create-app", headers=ADMIN_HEADERS)
    assert approve_resp.status_code == 200
    app_id = approve_resp.json()['app_id']

    app_resp = client.get(f'/api/apps/{app_id}')
    assert app_resp.status_code == 200
    app_data = app_resp.json()
    assert app_data['detail_doc_url'] == payload['detail_doc_url']
    assert app_data['detail_doc_name'] == payload['detail_doc_name']


def test_approve_creates_app_without_placeholder_ranking_setting():
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

        app = db.query(App).filter(App.id == app_id).first()
        assert app is not None
        assert app.status == 'available'
        assert app.target_system == submission.embedded_system

        setting = db.query(AppRankingSetting).filter(AppRankingSetting.app_id == app_id).first()
        assert setting is None
    finally:
        db.close()


def test_update_app_dimension_score_accepts_json_body():
    payload = {
        'category': 'group',
        'app_name': '维度改分测试应用',
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
    submit_resp = client.post('/api/submissions', json=payload)
    assert submit_resp.status_code == 200
    submission_id = submit_resp.json()['id']

    approve_resp = client.post(f"/api/submissions/{submission_id}/approve-and-create-app", headers=ADMIN_HEADERS)
    assert approve_resp.status_code == 200
    app_id = approve_resp.json()['app_id']

    update_resp = client.put(
        f'/api/apps/{app_id}/dimension-scores/1',
        headers=ADMIN_HEADERS,
        json={'score': 88}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()['score'] == 88
    assert update_resp.json()['synced'] >= 0
    assert update_resp.json()['run_id']


def test_delete_ranking_config_cleans_downstream_records():
    unique_suffix = uuid.uuid4().hex[:8]
    config_id = f"cfg-{unique_suffix}"

    payload = {
        'category': 'group',
        'app_name': f'删配置联动测试应用-{unique_suffix}',
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
    submit_resp = client.post('/api/submissions', json=payload)
    assert submit_resp.status_code == 200
    submission_id = submit_resp.json()['id']

    approve_resp = client.post(f"/api/submissions/{submission_id}/approve-and-create-app", headers=ADMIN_HEADERS)
    assert approve_resp.status_code == 200
    app_id = approve_resp.json()['app_id']

    config_resp = client.post(
        '/api/ranking-configs',
        headers=ADMIN_HEADERS,
        json={
            "id": config_id,
            "name": f"测试榜单-{unique_suffix}",
            "description": "删除联动测试",
            "dimensions_config": "[]",
            "calculation_method": "composite",
            "is_active": True,
        },
    )
    assert config_resp.status_code == 200

    setting_resp = client.post(
        f'/api/apps/{app_id}/ranking-settings',
        headers=ADMIN_HEADERS,
        json={
            "ranking_config_id": config_id,
            "is_enabled": True,
            "weight_factor": 1.0,
            "custom_tags": "测试",
        },
    )
    assert setting_resp.status_code == 200

    db = SessionLocal()
    try:
        assert db.query(AppRankingSetting).filter(AppRankingSetting.ranking_config_id == config_id).count() >= 1
        assert db.query(Ranking).filter(Ranking.ranking_config_id == config_id).count() >= 1
        assert db.query(HistoricalRanking).filter(HistoricalRanking.ranking_config_id == config_id).count() >= 1
    finally:
        db.close()

    delete_resp = client.delete(f'/api/ranking-configs/{config_id}', headers=ADMIN_HEADERS)
    assert delete_resp.status_code == 200

    db = SessionLocal()
    try:
        assert db.query(AppRankingSetting).filter(AppRankingSetting.ranking_config_id == config_id).count() == 0
        assert db.query(Ranking).filter(Ranking.ranking_config_id == config_id).count() == 0
        assert db.query(HistoricalRanking).filter(HistoricalRanking.ranking_config_id == config_id).count() == 0
    finally:
        db.close()


def test_delete_ranking_dimension_prunes_config_and_scores():
    unique_suffix = uuid.uuid4().hex[:8]
    config_id = f"cfg-dim-{unique_suffix}"

    payload = {
        'category': 'group',
        'app_name': f'删维度联动测试应用-{unique_suffix}',
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
    submit_resp = client.post('/api/submissions', json=payload)
    assert submit_resp.status_code == 200
    submission_id = submit_resp.json()['id']

    approve_resp = client.post(f"/api/submissions/{submission_id}/approve-and-create-app", headers=ADMIN_HEADERS)
    assert approve_resp.status_code == 200
    app_id = approve_resp.json()['app_id']

    dim_resp = client.post(
        '/api/ranking-dimensions',
        headers=ADMIN_HEADERS,
        json={
            "name": f"删维度测试-{unique_suffix}",
            "description": "用于测试删除维度联动",
            "calculation_method": "默认规则",
            "weight": 1.0,
            "is_active": True,
        },
    )
    assert dim_resp.status_code == 200
    dimension_id = dim_resp.json()['id']

    config_resp = client.post(
        '/api/ranking-configs',
        headers=ADMIN_HEADERS,
        json={
            "id": config_id,
            "name": f"维度联动榜单-{unique_suffix}",
            "description": "维度联动测试",
            "dimensions_config": json.dumps([{"dim_id": dimension_id, "weight": 1.0}], ensure_ascii=False),
            "calculation_method": "composite",
            "is_active": True,
        },
    )
    assert config_resp.status_code == 200

    setting_resp = client.post(
        f'/api/apps/{app_id}/ranking-settings',
        headers=ADMIN_HEADERS,
        json={
            "ranking_config_id": config_id,
            "is_enabled": True,
            "weight_factor": 1.0,
            "custom_tags": "测试",
        },
    )
    assert setting_resp.status_code == 200

    score_resp = client.put(
        f'/api/apps/{app_id}/dimension-scores/{dimension_id}',
        headers=ADMIN_HEADERS,
        json={'score': 90},
    )
    assert score_resp.status_code == 200

    delete_dim_resp = client.delete(f'/api/ranking-dimensions/{dimension_id}', headers=ADMIN_HEADERS)
    assert delete_dim_resp.status_code == 200

    db = SessionLocal()
    try:
        assert db.query(AppDimensionScore).filter(AppDimensionScore.dimension_id == dimension_id).count() == 0
    finally:
        db.close()

    config_after_resp = client.get(f'/api/ranking-configs/{config_id}')
    assert config_after_resp.status_code == 200
    dimensions = json.loads(config_after_resp.json()['dimensions_config'])
    assert all(item.get('dim_id') != dimension_id for item in dimensions)


def test_admin_endpoint_requires_token():
    client.cookies.clear()
    resp = client.post('/api/rankings/sync')
    assert resp.status_code == 401


def test_admin_endpoint_accepts_valid_token():
    Base.metadata.create_all(bind=engine)
    client.cookies.clear()
    resp = client.post('/api/rankings/sync', headers=ADMIN_HEADERS)
    assert resp.status_code == 200


def test_submission_ranking_dimensions_write_is_deprecated():
    payload = {
        'category': 'group',
        'app_name': f'停写维度字段测试-{uuid.uuid4().hex[:8]}',
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
        'ranking_dimensions': 'legacy-dim-1,legacy-dim-2'
    }
    resp = client.post('/api/submissions', json=payload)
    assert resp.status_code == 200
    assert resp.json()['ranking_dimensions'] == ''


def test_save_app_ranking_setting_atomic_success():
    unique = uuid.uuid4().hex[:8]
    app_name = f"原子保存测试应用-{unique}"
    payload = {
        'category': 'group',
        'app_name': app_name,
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
    submit_resp = client.post('/api/submissions', json=payload)
    assert submit_resp.status_code == 200
    submission_id = submit_resp.json()['id']
    approve_resp = client.post(f"/api/submissions/{submission_id}/approve-and-create-app", headers=ADMIN_HEADERS)
    assert approve_resp.status_code == 200
    app_id = approve_resp.json()['app_id']

    db = SessionLocal()
    try:
        dimension = db.query(RankingDimension).filter(RankingDimension.is_active.is_(True)).first()
        assert dimension is not None
        dimension_id = dimension.id
        config_id = f"atomic-{unique}"
        db.add(RankingConfig(
            id=config_id,
            name=f"原子榜单-{unique}",
            description="原子保存测试",
            dimensions_config=json.dumps([{"dim_id": dimension_id, "weight": 1.0}], ensure_ascii=False),
            calculation_method="composite",
            is_active=True,
        ))
        db.commit()
    finally:
        db.close()

    save_resp = client.post(
        f'/api/apps/{app_id}/ranking-settings/save',
        headers=ADMIN_HEADERS,
        json={
            "ranking_config_id": config_id,
            "is_enabled": True,
            "weight_factor": 1.2,
            "custom_tags": "测试",
            "dimension_scores": [{"dimension_id": dimension_id, "score": 91}]
        },
    )
    assert save_resp.status_code == 200
    data = save_resp.json()
    assert data["updated_dimensions"] == 1
    assert data["setting"]["ranking_config_id"] == config_id
    assert data["run_id"]


def test_save_app_ranking_setting_atomic_rollback_on_invalid_dimension():
    unique = uuid.uuid4().hex[:8]
    payload = {
        'category': 'group',
        'app_name': f'原子回滚测试应用-{unique}',
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
    submit_resp = client.post('/api/submissions', json=payload)
    assert submit_resp.status_code == 200
    submission_id = submit_resp.json()['id']
    approve_resp = client.post(f"/api/submissions/{submission_id}/approve-and-create-app", headers=ADMIN_HEADERS)
    assert approve_resp.status_code == 200
    app_id = approve_resp.json()['app_id']

    db = SessionLocal()
    try:
        dimension = db.query(RankingDimension).filter(RankingDimension.is_active.is_(True)).first()
        assert dimension is not None
        config_id = f"atomic-rb-{unique}"
        db.add(RankingConfig(
            id=config_id,
            name=f"原子回滚榜单-{unique}",
            description="原子回滚测试",
            dimensions_config=json.dumps([{"dim_id": dimension.id, "weight": 1.0}], ensure_ascii=False),
            calculation_method="composite",
            is_active=True,
        ))
        db.commit()
        invalid_dimension_id = dimension.id + 99999
    finally:
        db.close()

    save_resp = client.post(
        f'/api/apps/{app_id}/ranking-settings/save',
        headers=ADMIN_HEADERS,
        json={
            "ranking_config_id": config_id,
            "is_enabled": True,
            "weight_factor": 1.1,
            "custom_tags": "测试",
            "dimension_scores": [{"dimension_id": invalid_dimension_id, "score": 80}]
        },
    )
    assert save_resp.status_code == 422
    detail = save_resp.json()["detail"]
    assert detail["code"] == "validation_error"

    db = SessionLocal()
    try:
        setting = db.query(AppRankingSetting).filter(
            AppRankingSetting.app_id == app_id,
            AppRankingSetting.ranking_config_id == config_id
        ).first()
        assert setting is None
        assert db.query(AppDimensionScore).filter(AppDimensionScore.app_id == app_id).count() == 0
    finally:
        db.close()


def test_save_app_ranking_setting_atomic_is_idempotent_for_same_payload():
    unique = uuid.uuid4().hex[:8]
    payload = {
        'category': 'group',
        'app_name': f'原子幂等测试应用-{unique}',
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
    submit_resp = client.post('/api/submissions', json=payload)
    assert submit_resp.status_code == 200
    submission_id = submit_resp.json()['id']
    approve_resp = client.post(f"/api/submissions/{submission_id}/approve-and-create-app", headers=ADMIN_HEADERS)
    assert approve_resp.status_code == 200
    app_id = approve_resp.json()['app_id']

    db = SessionLocal()
    try:
        dimension = db.query(RankingDimension).filter(RankingDimension.is_active.is_(True)).first()
        assert dimension is not None
        dimension_id = dimension.id
        config_id = f"atomic-idem-{unique}"
        db.add(RankingConfig(
            id=config_id,
            name=f"原子幂等榜单-{unique}",
            description="原子幂等测试",
            dimensions_config=json.dumps([{"dim_id": dimension_id, "weight": 1.0}], ensure_ascii=False),
            calculation_method="composite",
            is_active=True,
        ))
        db.commit()
    finally:
        db.close()

    req_payload = {
        "ranking_config_id": config_id,
        "is_enabled": True,
        "weight_factor": 1.3,
        "custom_tags": "幂等",
        "dimension_scores": [{"dimension_id": dimension_id, "score": 87}],
    }
    first_resp = client.post(
        f'/api/apps/{app_id}/ranking-settings/save',
        headers=ADMIN_HEADERS,
        json=req_payload,
    )
    assert first_resp.status_code == 200
    second_resp = client.post(
        f'/api/apps/{app_id}/ranking-settings/save',
        headers=ADMIN_HEADERS,
        json=req_payload,
    )
    assert second_resp.status_code == 200

    db = SessionLocal()
    try:
        setting_count = db.query(AppRankingSetting).filter(
            AppRankingSetting.app_id == app_id,
            AppRankingSetting.ranking_config_id == config_id,
        ).count()
        assert setting_count == 1
        today = datetime.now().date()
        score_count = db.query(AppDimensionScore).filter(
            AppDimensionScore.app_id == app_id,
            AppDimensionScore.dimension_id == dimension_id,
            AppDimensionScore.period_date == today,
        ).count()
        assert score_count == 1
        score_row = db.query(AppDimensionScore).filter(
            AppDimensionScore.app_id == app_id,
            AppDimensionScore.dimension_id == dimension_id,
            AppDimensionScore.period_date == today,
        ).first()
        assert score_row is not None
        assert score_row.score == 87
    finally:
        db.close()


def test_publish_rankings_precheck_requires_enabled_participant():
    unique = uuid.uuid4().hex[:8]
    config_id = f"publish-pre-{unique}"
    db = SessionLocal()
    try:
        dimension = db.query(RankingDimension).filter(RankingDimension.is_active.is_(True)).first()
        assert dimension is not None
        dimension_id = dimension.id
        db.query(AppRankingSetting).update({"is_enabled": False})
        db.commit()
    finally:
        db.close()

    create_resp = client.post(
        '/api/ranking-configs',
        headers=ADMIN_HEADERS,
        json={
            "id": config_id,
            "name": f"发布预检榜单-{unique}",
            "description": "发布预检测试",
            "dimensions_config": json.dumps([{"dim_id": dimension_id, "weight": 1.0}], ensure_ascii=False),
            "calculation_method": "composite",
            "is_active": True,
        },
    )
    assert create_resp.status_code == 200

    publish_resp = client.post('/api/rankings/publish', headers=ADMIN_HEADERS)
    assert publish_resp.status_code == 409
    detail = publish_resp.json()["detail"]
    assert detail["code"] == "publish_precheck_failed"
