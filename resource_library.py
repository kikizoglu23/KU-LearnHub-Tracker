"""Searchable metadata for already downloaded LearnHub files; no extra Moodle calls."""
import re
from pathlib import Path
import learnhub as lh

def resources():
    cfg, state = lh.load_config(), lh.load_state()
    course_ids = {lh.safe_name(short):str(cid) for cid,short in cfg['courses'].items()}
    names = {lh.safe_name(short):short for short in cfg['courses'].values()}
    result=[]
    for key,item in state['files'].items():
        rel=item['path'];parts=re.split(r'[/\\]',rel)
        if not parts or not parts[-1]: continue
        cid=course_ids.get(parts[0])
        if cid is None: continue
        short = names[parts[0]]
        coverage=state.get('coverage',{}).get(short,{})
        current=(key in coverage.get('expected',{})) if coverage.get('checked_at') and not coverage.get('error') else None
        result.append({'path':rel,'name':parts[-1],'course':short,
                       'current':current,
                       'section':' / '.join(parts[1:-1]),
                       'at':item.get('at',item.get('timemodified',0)),
                       'course_url':f'{lh.SITE}/course/view.php?id={int(cid)}' if cid else None})
    return sorted(result,key=lambda r:(-r['at'],r['path']))

def resource_path(rel):
    # Serve only files present in our download index, inside the download root.
    if not isinstance(rel,str) or not any(v['path']==rel for v in lh.load_state()['files'].values()): return None
    root=Path(lh.load_config()['download_dir']).expanduser().resolve()
    target=(root / rel).resolve()
    return target if target.is_relative_to(root) and target.is_file() else None
