"""Exercise the optional model plan and the grounded renderer on seven cases."""
import importlib.util
import json
from pathlib import Path
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('worklens', ROOT / 'scripts/worklens.py')
wl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wl)


def main():
    output = ROOT / 'eval/v3/results'
    output.mkdir(exist_ok=True)
    all_results = []
    for file in sorted((ROOT / 'eval/v3/cards').glob('C*.json')):
        card = json.loads(file.read_text())
        terms = [x['term'] for x in card['concepts']]
        schema = {'type': 'object', 'properties': {'concept_order': {'type': 'array', 'items': {'type': 'string', 'enum': terms}, 'minItems': len(terms), 'maxItems': len(terms)}}, 'required': ['concept_order'], 'additionalProperties': False}
        request = {
            'model': 'qwen2.5:7b', 'stream': False, 'format': schema,
            'messages': [
                {'role': 'system', 'content': '只选择术语讲解顺序。输出一个JSON对象，仅含concept_order。必须使用每个给定键且恰好一次，不写事实、报告或额外字段。'},
                {'role': 'user', 'content': json.dumps({'task': card['title'], 'domain': wl.PROFILES[card['profile']]['domain'], 'terms': terms}, ensure_ascii=False)},
            ],
            'options': {'temperature': 0.2, 'seed': 42, 'num_ctx': 4096, 'num_predict': 300},
        }
        start = time.monotonic()
        transport_error = None
        response = None
        try:
            req = urllib.request.Request('http://127.0.0.1:11434/api/chat', data=json.dumps(request).encode(), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=90) as result:
                response = json.load(result)
            raw = response.get('message', {}).get('content', '')
            try:
                plan = json.loads(raw)
            except json.JSONDecodeError:
                plan = {'invalid_response': raw}
        except Exception as exc:
            transport_error = str(exc)
            raw = ''
            plan = {'transport_error': type(exc).__name__}
        report, audit = wl.render(card, plan)
        record = {'case': file.stem, 'model': request['model'], 'model_role': 'bounded concept ordering only; facts and narratives rendered by code',
                  'options': request['options'], 'raw_plan': raw, 'transport_error': transport_error,
                  'model_done_reason': response.get('done_reason') if response else None,
                  'seconds': round(time.monotonic() - start, 3), 'audit': audit}
        (output / (file.stem + '.md')).write_text(report)
        (output / (file.stem + '.json')).write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
        all_results.append(record)
        print(json.dumps({'case': file.stem, 'seconds': record['seconds'], 'plan_status': audit['plan_status']}, ensure_ascii=False), flush=True)
    # Three unseen numerical/missing-information fixtures require no model call.
    for file in sorted((ROOT / 'eval/v3/cards').glob('H*.json')):
        report, audit = wl.render(json.loads(file.read_text()))
        (output / (file.stem + '.md')).write_text(report)
        (output / (file.stem + '.json')).write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n')
    summary = {'model_calls': len(all_results), 'accepted_plans': sum(x['audit']['plan_status'] == 'accepted' for x in all_results),
               'guarded_fallbacks': sum(x['audit']['plan_status'] != 'accepted' for x in all_results),
               'reports': 10, 'cards': 'curated exact-source excerpts, not model extraction accuracy',
               'scope': 'code-enforced report invariants; not unbounded model writing or human interview efficacy'}
    (output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
