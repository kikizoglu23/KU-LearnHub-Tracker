"""Coursework from LearnHub: assignments with their official submission status, plus quizzes and Turnitin."""
import learnhub as lh


def build():
    cfg, state = lh.load_config(), lh.load_state()
    selected = set(cfg['courses'].values())
    tasks = []
    for a in state.get('upcoming', []):
        if a['course'] in selected:
            tasks.append(dict(course=a['course'], name=a['name'], kind='Assignments', due=a.get('due', 0),
                              url=a.get('url'), submitted=bool(a.get('submitted')), status_known=True))
    for a in state.get('activities', []):
        if a['course'] in selected:
            tasks.append(dict(course=a['course'], name=a['name'],
                              kind='Assignments' if a['activity_type'] == 'turnitintooltwo' else 'Quizzes & surveys',
                              due=a.get('due', 0), url=a.get('url'), submitted=False, status_known=False))
    tasks.sort(key=lambda task: (task['due'] or float('inf'), task['name'].casefold()))
    return {'tasks': tasks, 'courses': sorted(selected)}
