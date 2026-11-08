#!/usr/bin/env python3
"""Render professional debriefs from quoted evidence; model plans cannot add facts."""
import argparse
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import html
import json
from pathlib import Path


PROFILES = {
    'async-feedback': {
        'domain': '异步数据交互与操作反馈',
        'terms': {
            'receipt': ('写入回执', '用本次写入的确认结果判断是否保存；历史刷新是另一项操作。'),
            'decoupling': ('关键链路解耦', '将本单必须等待的结果与后台同步分开；await 本身不等于阻塞 JavaScript 主线程。'),
            'ordering': ('异步响应顺序保护', '识别新旧响应，避免迟到旧快照覆盖较新的状态；异步执行本身不能提供这项保证。'),
        },
        'question': '如果保存请求超时，为什么不能直接认定未保存并重新创建？',
        'answer': '先核对实际保存结果或已有幂等机制，避免重复业务；不能假定具体保护已经实现。',
        'next': '核对手机端保存反馈与后台刷新失败路径；没有可比前测时先建立当前耗时基线。',
    },
    'constraints': {
        'domain': '规则驱动的多约束辅助决策',
        'terms': {
            'constraints': ('约束编排', '将禁用条件、候选筛选和偏好评分分开；候选不足时保留人工决策入口。'),
            'rules': ('规则驱动决策', '规则与打分可以独立运行；用 AI 写代码不等于运行时调用语言模型。'),
        },
        'question': '规则满足率与真实采纳率为什么不同？',
        'answer': '前者评价规则检查，后者评价实际使用选择；构造样本通过不能推出用户采纳。',
        'next': '核对未满足样本的失败原因，再采集真实采纳与人工修改记录。',
    },
    'evaluation': {
        'domain': 'AI 离线评测、回归分析与风险准入',
        'terms': {
            'regression': ('逐题回归', '比较同题改善、持平和退化；总分增加不能抵消高风险错误。'),
            'historical': ('历史基线比较', '同一题库不等于同条件随机 A/B；方案版本不自动代表模型发生变化。'),
            'gold': ('评分复核与金标准', 'AI 评分与业务方独立复核分开记录；开发集结果不直接代表生产表现。'),
        },
        'question': '总通过率提高后，权限退化为什么还要单独处理？',
        'answer': '权限错误可能产生不允许的业务结论；应单列严重程度、复核与准入判断，不能用平均数掩盖。',
        'next': '优先复核严重退化和评分依据，再决定准入；扩大题数本身不能保证统计显著或业务代表性。',
    },
    'visual': {
        'domain': '界面视觉一致性',
        'terms': {
            'consistency': ('视觉一致性', '统一颜色与间距；点击区域、误触或转化变化需要另外验证。'),
        },
        'question': '样式变化能否证明误触减少？',
        'answer': '不能，需要明确事件区域或实际可用性观测。',
        'next': '核对适用页面和布局；实际可用性效果另行观察。',
    },
    'export': {
        'domain': '文件导出交付与权限排查',
        'terms': {
            'authorization': ('授权排查', '403 是权限拒绝响应，不足以定位配置错误或其他根因。'),
            'delivery': ('交付状态分层', '代码存在、联调成功、文件生成和正式发布是不同阶段。'),
        },
        'question': '为什么收到 403 不能说导出联调已经通过？',
        'answer': '需要根据实际身份、策略、接口日志和文件结果核对；错误响应不能替代成功证据。',
        'next': '在原授权内核对调用身份、权限策略及响应记录；文件生成和验收有凭证后再更新状态。',
    },
    'batch': {
        'domain': '批次数据处理与可靠性交付',
        'terms': {
            'validation': ('输入校验', '在写入前识别错误行，并保留可定位的错误记录。'),
            'transaction': ('事务原子性', '事务范围内的写入中断时回滚；不能据此推定所有系统级一致性。'),
            'idempotency': ('幂等与唯一标识', '区分业务对象唯一键与请求批次标识，避免重试重复创建。'),
            'observability': ('批次可观测性', '通过批次编号、状态和计数解释处理结果，支持追踪与重试。'),
        },
        'question': '唯一键和批次幂等分别解决什么？',
        'answer': '对象唯一性与重复请求结果是不同约束；结合已实现机制解释，不能只凭日志推定幂等。',
        'next': '核对事务边界、重复批次和失败结果；真实人工耗时另行采样。',
    },
    'unknown': {
        'domain': '需求与验证信息待补充',
        'terms': {
            'scope': ('需求边界', '先明确角色、操作对象、输入条件和完成标准，再选择适用的专业机制。'),
        },
        'question': '还需要哪几项材料才能解释这次改动？',
        'answer': '操作对象或页面、关键改动，以及一次实际验证结果；不要补造原系统行为。',
        'next': '补充操作对象/页面、改动和一次验证结果；当前只形成事实范围内的初稿。',
    },
}
KINDS = {'request', 'change', 'verification', 'status', 'risk', 'unknown', 'contribution'}
TRADEOFFS = {
    'async-feedback': '及时反馈与后台刷新可靠性需要分别设计；改变等待路径后仍要验证刷新失败恢复和旧响应保护。',
    'constraints': '不可放宽的约束与可调整偏好应分开；候选不足时解释缺口并交给人确认，不强行凑齐。',
    'evaluation': '整体分数与严重退化应分别判断；对照条件、评分复核和风险门槛缺一项都应明确保留。',
    'visual': '统一样式时核对适用页面，不从局部视觉变化推导整体业务收益。',
    'export': '生成位置的选择应结合实际数据量、权限和交付方式；仅知道服务端方案不足以推定安全或性能收益。',
    'batch': '批次事务范围、失败隔离和重试成本需要权衡；先说明当前边界，再比较其他方案。',
    'unknown': '操作对象和验证缺失时暂不比较架构方案；先补最少的事实材料。',
}


class EvidenceError(ValueError):
    pass


def exact_keys(value, allowed, required, label):
    if not isinstance(value, dict) or not required <= value.keys() or value.keys() - allowed:
        raise EvidenceError(label + ': missing or unexpected fields')


def number(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EvidenceError('counts must be non-negative integers')
    return value


def percentage(n, d):
    return None if not d else Decimal(n) * 100 / Decimal(d)


def fmt(value):
    return format(value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), 'f').rstrip('0').rstrip('.') if value else '0'


def check_card(card):
    exact_keys(card, {'version', 'title', 'profile', 'sources', 'facts', 'concepts', 'metrics', 'brief'},
               {'version', 'title', 'profile', 'sources', 'facts', 'concepts'}, 'card')
    if card['version'] != 1 or card['profile'] not in PROFILES:
        raise EvidenceError('unsupported card version or profile')
    if not isinstance(card['title'], str) or not card['title'].strip():
        raise EvidenceError('title required')
    for key in ['sources', 'facts', 'concepts', 'metrics']:
        if not isinstance(card.get(key, []), list):
            raise EvidenceError(key + ' must be an array')
    if not isinstance(card.get('brief', False), bool):
        raise EvidenceError('brief must be boolean')
    sources = {}
    for source in card['sources']:
        exact_keys(source, {'id', 'text'}, {'id', 'text'}, 'source')
        if not isinstance(source['id'], str) or source['id'] in sources or not isinstance(source['text'], str):
            raise EvidenceError('invalid or duplicate source')
        sources[source['id']] = source['text']
    facts = {}
    for fact in card['facts']:
        exact_keys(fact, {'id', 'kind', 'source', 'quote'}, {'id', 'kind', 'source', 'quote'}, 'fact')
        if not isinstance(fact['id'], str) or fact['id'] in facts or fact['kind'] not in KINDS:
            raise EvidenceError('invalid or duplicate fact')
        text = sources.get(fact['source'])
        if not isinstance(fact['quote'], str) or not fact['quote'] or text is None or fact['quote'] not in text:
            raise EvidenceError('fact is not an exact excerpt of its source')
        facts[fact['id']] = fact
    if not facts:
        raise EvidenceError('at least one sourced fact required')
    for concept in card['concepts']:
        exact_keys(concept, {'term', 'facts'}, {'term', 'facts'}, 'concept')
        if (not isinstance(concept['term'], str) or concept['term'] not in PROFILES[card['profile']]['terms']
                or not isinstance(concept['facts'], list) or not concept['facts']
                or any(not isinstance(ref, str) for ref in concept['facts'])):
            raise EvidenceError('unsupported or unsourced concept')
        if any(ref not in facts for ref in concept['facts']):
            raise EvidenceError('unknown concept evidence')
    for metric in card.get('metrics', []):
        exact_keys(metric, {'kind', 'refs', 'total', 'passed', 'baseline', 'candidate'}, {'kind', 'refs', 'total'}, 'metric')
        if (metric['kind'] not in {'rule_rate', 'offline_comparison'} or not isinstance(metric['refs'], list)
                or not metric['refs'] or any(not isinstance(x, str) or x not in facts for x in metric['refs'])):
            raise EvidenceError('invalid metric evidence or kind')
        if metric['kind'] == 'rule_rate' and card['profile'] != 'constraints':
            raise EvidenceError('rule rate requires rule profile')
        if metric['kind'] == 'offline_comparison' and card['profile'] != 'evaluation':
            raise EvidenceError('offline comparison requires evaluation profile')
        numeric_fields = ['total', 'passed'] if metric['kind'] == 'rule_rate' else ['total', 'baseline', 'candidate']
        if set(numeric_fields) != (metric.keys() - {'kind', 'refs'}):
            raise EvidenceError('unexpected metric numeric fields')
        text = ' '.join(facts[x]['quote'] for x in metric['refs'])
        import re
        present = {int(x) for x in re.findall(r'(?<![\d.])\d+(?![\d.])', text)}
        for key in numeric_fields:
            value = number(metric[key])
            if value not in present:
                raise EvidenceError('metric count absent from quoted evidence')
            if key != 'total' and value > metric['total']:
                raise EvidenceError('passed count exceeds total')
    return facts


def check_plan(card, plan):
    exact_keys(plan, {'concept_order'}, {'concept_order'}, 'model plan')
    order = plan['concept_order']
    allowed = [x['term'] for x in card['concepts']]
    if not isinstance(order, list) or any(not isinstance(x, str) for x in order):
        raise EvidenceError('concept_order must contain strings')
    if len(set(order)) != len(order) or set(order) != set(allowed):
        raise EvidenceError('plan must preserve every grounded concept exactly once')
    return order


def metric_lines(card):
    lines = []
    for metric in card.get('metrics', []):
        total = metric['total']
        if not total:
            lines.append('所给样本分母为 0，不计算通过率。')
        elif metric['kind'] == 'rule_rate':
            lines.append(f"所给样本规则满足率：{metric['passed']}/{total} = {fmt(percentage(metric['passed'], total))}%；不代表 LLM 准确率或真实采纳率。")
        else:
            old, new = percentage(metric['baseline'], total), percentage(metric['candidate'], total)
            delta = new - old
            lines.append(f"所给离线样本通过率：{fmt(old)}% → {fmt(new)}%，变化 {fmt(delta)} 个百分点。")
            lines.append('基线通过率为 0，不计算相对提升。' if not old else f'相对变化：{fmt(delta / old * 100)}%；不称为同期随机 A/B 或生产准确率。')
    return lines or ['未提交可计算的指标；不生成效率、质量或业务收益数字。']


def render(card, plan=None):
    facts = check_card(card)
    order = [x['term'] for x in card['concepts']]
    audit = {'plan_status': 'not_requested', 'rejected_reason': None}
    if plan is not None:
        try:
            order = check_plan(card, plan)
            audit['plan_status'] = 'accepted'
        except EvidenceError as exc:
            audit.update(plan_status='rejected_used_grounded_fallback', rejected_reason=str(exc))
    profile = PROFILES[card['profile']]
    groups = {kind: [f for f in facts.values() if f['kind'] == kind] for kind in KINDS}
    def quoted(group):
        return '；'.join('「' + html.escape(f['quote']) + '」[' + f['id'] + ']' for f in groups[group])
    changes = quoted('change') or '未提交具体改动材料'
    verification = quoted('verification') or '未提交实际验证结论'
    status = quoted('status') or '运行/发布状态未确认'
    contribution = quoted('contribution') or '个人职责未确认，不自动认领设计、编码或验收'
    risk = quoted('risk') or '未提交额外风险记录'
    unknown = quoted('unknown') or '实际业务效果及独立理解仍需按任务核实'
    metrics = metric_lines(card)
    if card.get('brief'):
        report = f"# {html.escape(card['title'])}\n\n领域：{profile['domain']}。\n\n改动记录：{changes}。\n\n验证：{verification}；未知：{unknown}。\n\n面试/汇报：本次属于视觉一致性调整，采用记录中的改动；不从样式变化推导效率或转化提升。个人职责与实际效果按来源核实。\n"
    else:
        rows = ['# ' + html.escape(card['title']), '', '**来源事实**',
                '需求：' + (quoted('request') or '需求来源待确认'), '改动：' + changes,
                '验证：' + verification, '状态：' + status,
                '风险：' + risk, '未知：' + unknown, '贡献：' + contribution, '',
                '**专业解释**', '领域：' + profile['domain'] + '。']
        for key in order:
            term, definition = profile['terms'][key]
            refs = next(x['facts'] for x in card['concepts'] if x['term'] == key)
            rows.append(f'- {term}：{definition} 对应材料：' + '、'.join('[' + ref + ']' for ref in refs))
        rows += ['', '**取舍分析（不冒充历史评审）**', TRADEOFFS[card['profile']]]
        rows += ['', '**指标口径**'] + metrics
        names = '、'.join(profile['terms'][key][0] for key in order)
        story = f'本次任务涉及{profile["domain"]}，可用{names}解释。记录中的做法是{changes}。验证记录为{verification}，交付状态为{status}。'
        # Every output form reuses the same source-backed facts and calculated metrics.
        tail = ' '.join(metrics) + ' 风险记录：' + risk + '。待确认：' + unknown + '。职责记录：' + contribution + '。'
        update = f'进展：{changes}。验证：{verification}。交付状态：{status}。' + tail + ' 下一步：' + profile['next']
        rows += ['', '**面试讲法**', story + tail, '', '**工作汇报**', update,
                 '', '**理解追问**', profile['question'], '回答要点：' + profile['answer'],
                 '', '**下一步**', profile['next'], '', '**证据索引**']
        for fid, fact in facts.items():
            rows.append(f'- [{fid}] {fact["source"]}：{html.escape(fact["quote"])}')
        report = '\n\n'.join(row for row in rows if row) + '\n'
    audit.update(source_hashes={s['id']: hashlib.sha256(s['text'].encode()).hexdigest() for s in card['sources']},
                 facts=len(facts), metrics=metrics, renderer='worklens-0.3')
    return report, audit


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--card', required=True)
    ap.add_argument('--plan')
    ap.add_argument('--output', required=True)
    ap.add_argument('--audit')
    args = ap.parse_args()
    try:
        card = json.loads(Path(args.card).read_text())
        plan = json.loads(Path(args.plan).read_text()) if args.plan else None
        report, audit = render(card, plan)
    except (EvidenceError, json.JSONDecodeError) as exc:
        ap.exit(2, 'Evidence validation failed: ' + str(exc) + '\n')
    Path(args.output).write_text(report)
    if args.audit:
        Path(args.audit).write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
