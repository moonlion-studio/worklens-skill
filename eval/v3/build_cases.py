"""Construct quoted evidence fixtures; extraction is curated, not model-tested."""
import json
from pathlib import Path


def make_card(key, text, profile, pieces, concepts, metrics=None, brief=False):
    facts = []
    for i, (kind, quote) in enumerate(pieces, 1):
        assert quote in text, (key, quote)
        facts.append({'id': f'f{i}', 'kind': kind, 'source': 's1', 'quote': quote})
    return {'version': 1, 'title': key, 'profile': profile,
            'sources': [{'id': 's1', 'text': text}], 'facts': facts,
            'concepts': [{'term': term, 'facts': refs} for term, refs in concepts],
            'metrics': metrics or [], 'brief': brief}


def build(root):
    source = {c['id']: c['prompt'] for c in json.loads((root / 'eval/cases.json').read_text())}
    specs = [
        ('C01', 'async-feedback', [
            ('request', '预约保存了还一直转圈，改好'),
            ('change', 'const receipt=await saveBooking(); applyReceipt(receipt); showSuccess(); syncAllHistoryInBackground()'),
            ('change', '旧响应不能覆盖较新的预约'),
            ('verification', '重复提交和时段冲突检查通过'),
            ('status', '开发包已上传，未正式发布'),
            ('unknown', '没有真实手机耗时前测和后测'),
        ], [('receipt', ['f2']), ('decoupling', ['f2']), ('ordering', ['f3'])], []),
        ('C02', 'constraints', [
            ('request', '给我的菜单功能做专业复盘'),
            ('contribution', '我用AI写代码'),
            ('change', '菜品结构化标签→过滤忌口和下架菜→按预算与菜式打分补齐→用户换菜确认'),
            ('change', '没有调用语言模型'),
            ('verification', '构造验收中35份方案有28份满足预先标注的全部规则'),
            ('unknown', '没有采集真实采纳和耗时数据'),
        ], [('constraints', ['f3']), ('rules', ['f3', 'f4'])],
         [{'kind': 'rule_rate', 'refs': ['f5'], 'total': 35, 'passed': 28}]),
        ('C03', 'evaluation', [
            ('request', '帮我把复测结果写成专业报告'),
            ('verification', '构造开发集25题，历史基线14题通过，今天候选18题通过'),
            ('status', '条件不同时间运行，没有随机分流'),
            ('change', '5题从未通过变通过，1题从通过变未通过，其余状态不变'),
            ('risk', '退化题把无权限角色说成可下载'),
            ('unknown', '评分是AI助手完成，业务方和我没有独立复核'),
        ], [('regression', ['f4', 'f5']), ('historical', ['f2', 'f3']), ('gold', ['f6'])],
         [{'kind': 'offline_comparison', 'refs': ['f2'], 'total': 25, 'baseline': 14, 'candidate': 18}]),
        ('C04', 'visual', [
            ('request', '我想写汇报和面试素材'),
            ('change', '按钮颜色改成统一蓝色，左右间距从8px改成12px'),
            ('verification', '只查看了一个本地页面'),
            ('unknown', '未做用户测试，没改流程和接口'),
        ], [('consistency', ['f2'])], []),
        ('C05', 'export', [
            ('request', '我要求增加导出'),
            ('contribution', 'AI提出服务端生成文件的方案并写了代码'),
            ('contribution', '我只确认需求，还没有评审方案或验收'),
            ('status', '接口联调返回403权限拒绝，未生成文件，未发布'),
            ('change', 'AI提出服务端生成文件的方案并写了代码'),
        ], [('authorization', ['f4']), ('delivery', ['f2', 'f4'])], []),
        ('C06', 'batch', [
            ('request', '导入供应商CSV时别一条失败就不知道哪些写进去了'),
            ('change', '先逐行校验并生成错误行报告，合法批次在事务里写入'),
            ('change', '用外部供应商编码做唯一键，重复请求返回同一批次状态'),
            ('change', '日志记录批次号和成功/失败数量'),
            ('verification', '构造数据验证了重复批次不新增记录，写入中断会回滚'),
            ('status', '只在本地验证'),
            ('unknown', '没有生产文件和真实人工耗时'),
        ], [('validation', ['f2']), ('transaction', ['f2', 'f5']), ('idempotency', ['f3']), ('observability', ['f4'])], []),
        ('C07', 'unknown', [
            ('request', '我今天加了个筛选功能'),
            ('unknown', '没有提供页面、角色、筛选字段、代码或验证材料'),
            ('unknown', '别写数字，也别替我改东西'),
        ], [('scope', ['f2'])], []),
    ]
    cards = [make_card(key, source[key], profile, pieces, terms, metrics, key == 'C04')
             for key, profile, pieces, terms, metrics in specs]
    # New fixtures not used to write the original seven-case prompts.
    heldout = [
        ('H01', '构造规则测试16份方案12份满足全部约束；没有生产采纳记录。', 'constraints',
         [('verification', '构造规则测试16份方案12份满足全部约束'), ('unknown', '没有生产采纳记录')],
         [('constraints', ['f1'])], [{'kind': 'rule_rate', 'refs': ['f1'], 'total': 16, 'passed': 12}]),
        ('H02', '构造开发集12题，历史基线0题通过，候选3题通过；不同时间比较；评分未独立复核。', 'evaluation',
         [('verification', '构造开发集12题，历史基线0题通过，候选3题通过'), ('status', '不同时间比较'), ('unknown', '评分未独立复核')],
         [('historical', ['f1', 'f2']), ('gold', ['f3'])], [{'kind': 'offline_comparison', 'refs': ['f1'], 'total': 12, 'baseline': 0, 'candidate': 3}]),
        ('H03', '想优化导出权限，还没有改动、测试或发布记录。', 'unknown',
         [('request', '想优化导出权限'), ('unknown', '还没有改动、测试或发布记录')],
         [('scope', ['f1', 'f2'])], []),
    ]
    cards += [make_card(*row) for row in heldout]
    return cards


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[2]
    out = root / 'eval/v3/cards'
    out.mkdir(exist_ok=True)
    for card in build(root):
        (out / (card['title'] + '.json')).write_text(json.dumps(card, ensure_ascii=False, indent=2) + '\n')
