"""Regression coverage with fake courses and temporary state; no LearnHub requests."""
import http.client
import json
import tempfile
import threading
from pathlib import Path
from unittest import mock

import app
import learnhub as lh
import study_tasks


def run():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cfg = {'download_dir': tmp, 'courses': {'1': 'TEST101'}}
        state = {'files': {
            'lab': {'path': 'TEST101/Lab01.zip', 'timemodified': 1},
            'solution': {'path': 'TEST101/PS1_Solutions.pdf', 'timemodified': 1}},
            'assignments': {}, 'upcoming': [
                {'course': 'TEST101', 'name': 'Overdue task', 'due': 1, 'submitted': False, 'url': lh.SITE + '/mod/assign/view.php?id=1'},
                {'course': 'TEST101', 'name': 'Undated task', 'due': 0, 'submitted': True, 'url': lh.SITE + '/mod/assign/view.php?id=2'}],
            'activities': [{'course': 'TEST101', 'id': 3, 'name': 'Turnitin paper', 'activity_type': 'turnitintooltwo', 'due': 0, 'url': None}]}
        with mock.patch.object(lh, 'load_config', return_value=cfg), mock.patch.object(lh, 'load_state', return_value=state), mock.patch.object(lh, 'DATA_DIR', tmp):
            data = study_tasks.build()
            # Only LearnHub coursework: no tasks made from downloaded files.
            assert [t['name'] for t in data['tasks']] == ['Overdue task', 'Turnitin paper', 'Undated task']
            by_name = {t['name']: t for t in data['tasks']}
            assert by_name['Undated task']['submitted'] and by_name['Undated task']['status_known']
            assert not by_name['Turnitin paper']['status_known']
            server = app.LocalServer(('127.0.0.1', 0), app.Handler)
            with mock.patch.object(app, 'PORT', server.server_port), mock.patch.object(app, 'KEY', 'test-only'):
                threading.Thread(target=server.serve_forever, daemon=True).start()
                def request(path, method='GET', body=None, headers=None):
                    conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
                    conn.request(method, path, body, headers or {})
                    result = conn.getresponse()
                    output = result.status, dict(result.getheaders()), result.read()
                    conn.close()
                    return output
                try:
                    assert request('/')[0] == 403
                    code, headers, body = request('/?k=test-only')
                    assert code == 200 and b'Course tasks' in body
                    assert int(headers['Content-Length']) == len(body)
                    assert 'Set-Cookie' not in headers
                    assert request('/', headers={'Cookie': 'study_session=test-only'})[0] == 403  # no cookie auth
                    assert request('/api/tasks')[0] == 403
                    assert request('/api/tasks', headers={'X-Key': 'test-only'})[0] == 200
                    assert request('/api/status', headers={'X-Key': 'test-only', 'Host': 'evil.example'})[0] == 403
                    assert request('/api/tasks', 'POST', '{}', {'X-Key': 'test-only', 'Origin': 'https://evil.example'})[0] == 403
                    assert request('/api/tasks', 'POST', '[]', {'X-Key': 'test-only'})[0] == 400
                    assert request('/api/tasks', 'POST', '{}', {'X-Key': 'test-only'})[0] == 404  # no manual ticks
                    assert request('/api/tasks', 'POST', '{}', {'X-Key': 'test-only', 'Content-Length': '100001'})[0] == 400
                    for path in ('/.local/token', '/app.py', '/%2e%2e/README.md', '/ui.html'):
                        assert request(path, headers={'X-Key': 'test-only'})[0] == 404
                    # The first course save asks where files go; later saves don't.
                    saved = root / 'config.json'
                    chosen = str(root / 'Chosen' / 'Courses')
                    with mock.patch.object(lh, 'CONFIG', str(saved)), mock.patch.object(app, 'start'), \
                         mock.patch.object(app, 'pick_folder', return_value=chosen) as pick:
                        courses = json.dumps({'courses': [{'id': 1, 'short': 'TEST101'}]})
                        for _ in range(2):
                            assert request('/api/courses', 'POST', courses, {'X-Key': 'test-only'})[0] == 200
                        assert pick.call_count == 1
                        assert json.loads(saved.read_text())['download_dir'] == chosen
                finally:
                    server.shutdown()
                    server.server_close()
    print('PASS: standalone UI, LearnHub-only tasks, auth, CSRF, body limits, private paths and first-save folder choice')


if __name__ == '__main__':
    run()
