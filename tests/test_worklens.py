import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('worklens', ROOT / 'scripts/worklens.py')
wl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wl)
fixtures_spec = importlib.util.spec_from_file_location('fixtures', ROOT / 'eval/v3/build_cases.py')
fixtures = importlib.util.module_from_spec(fixtures_spec)
fixtures_spec.loader.exec_module(fixtures)
CARDS = {c['title']: c for c in fixtures.build(ROOT)}


class EvidenceGateTests(unittest.TestCase):
    def test_all_original_and_new_cards_render(self):
        for key, card in CARDS.items():
            with self.subTest(key=key):
                report, audit = wl.render(card)
                self.assertEqual(audit['facts'], len(card['facts']))
                self.assertTrue(report)

    def test_source_excerpts_required(self):
        card = copy.deepcopy(CARDS['C01'])
        card['facts'][0]['quote'] = '已完成集成测试'
        with self.assertRaises(wl.EvidenceError):
            wl.render(card)

    def test_extra_card_assertion_rejected(self):
        card = copy.deepcopy(CARDS['C01'])
        card['business_gain'] = '效率提高80%'
        with self.assertRaises(wl.EvidenceError):
            wl.render(card)

    def test_model_cannot_inject_test_or_ownership_claim(self):
        for payload in [{'concept_order': ['receipt', 'decoupling', 'ordering'], 'report': '我独立设计并完成集成测试'},
                        {'concept_order': ['不存在的Agent架构']}, {'concept_order': []}, '我负责全部实现']:
            with self.subTest(payload=payload):
                expected, _ = wl.render(CARDS['C01'])
                actual, audit = wl.render(CARDS['C01'], payload)
                self.assertEqual(actual, expected)
                self.assertEqual(audit['plan_status'], 'rejected_used_grounded_fallback')

    def test_model_order_preserves_grounded_concepts(self):
        report, audit = wl.render(CARDS['C01'], {'concept_order': ['ordering', 'receipt', 'decoupling']})
        self.assertEqual(audit['plan_status'], 'accepted')
        self.assertLess(report.index('- 异步响应顺序保护'), report.index('- 写入回执'))

    def test_ratio_not_llm_accuracy(self):
        values = wl.metric_lines(CARDS['C02'])
        self.assertIn('28/35 = 80%', values[0])
        self.assertTrue(values[0].startswith('所给样本规则满足率'))

    def test_percentage_points_and_relative_change(self):
        values = wl.metric_lines(CARDS['C03'])
        self.assertIn('56% → 72%，变化 16 个百分点', values[0])
        self.assertIn('28.57%', values[1])

    def test_metrics_are_repeated_without_changing_counts(self):
        report, _ = wl.render(CARDS['C02'])
        for section in ['**指标口径**', '**面试讲法**', '**工作汇报**']:
            part = report.split(section)[1].split('\n\n**')[0]
            self.assertIn('28/35 = 80%', part)
        self.assertNotIn('所有方案满足', report)

    def test_permission_regression_and_review_gap_survive_both_narratives(self):
        report, _ = wl.render(CARDS['C03'])
        for section in ['**面试讲法**', '**工作汇报**']:
            part = report.split(section)[1].split('\n\n**')[0]
            self.assertIn('退化题把无权限角色说成可下载', part)
            self.assertIn('业务方和我没有独立复核', part)
            self.assertIn('没有随机分流', part)

    def test_403_is_not_success_and_roles_remain_separate(self):
        report, _ = wl.render(CARDS['C05'])
        self.assertNotIn('接口联调通过', report)
        self.assertIn('未生成文件，未发布', report)
        self.assertIn('AI提出服务端生成文件的方案并写了代码', report)
        self.assertIn('我只确认需求，还没有评审方案或验收', report)
        self.assertIn('不足以定位配置错误', report)

    def test_missing_information_does_not_create_completion(self):
        report, _ = wl.render(CARDS['C07'])
        self.assertIn('未提交具体改动材料', report)
        self.assertIn('未提交实际验证结论', report)
        self.assertIn('运行/发布状态未确认', report)
        self.assertIn('个人职责未确认', report)
        for invented in ['已完成本地测试', '用户反馈显示', '我负责设计', '单元测试通过']:
            self.assertNotIn(invented, report)

    def test_simple_style_does_not_claim_measured_effect(self):
        report, _ = wl.render(CARDS['C04'])
        self.assertIn('未做用户测试', report)
        self.assertNotIn('减少误触', report)
        self.assertNotIn('中台', report)
        self.assertLess(len(report), 280)

    def test_new_ratio_is_calculated_not_filled_from_example(self):
        self.assertIn('12/16 = 75%', wl.metric_lines(CARDS['H01'])[0])

    def test_zero_baseline_does_not_divide(self):
        values = wl.metric_lines(CARDS['H02'])
        self.assertIn('0% → 25%', values[0])
        self.assertIn('基线通过率为 0，不计算相对提升', values[1])

    def test_zero_total_is_explicit(self):
        card = copy.deepcopy(CARDS['H01'])
        card['sources'][0]['text'] = '构造样本0题0通过'
        card['facts'] = [{'id': 'f1', 'kind': 'verification', 'source': 's1', 'quote': '构造样本0题0通过'}]
        card['metrics'][0].update(total=0, passed=0)
        report, _ = wl.render(card)
        self.assertIn('分母为 0，不计算通过率', report)

    def test_invalid_counts_and_missing_numeric_evidence(self):
        for change in [{'passed': 36}, {'passed': -1}, {'passed': True}, {'passed': 27}, {'total': 0.5}]:
            card = copy.deepcopy(CARDS['C02'])
            card['metrics'][0].update(change)
            with self.subTest(change=change), self.assertRaises(wl.EvidenceError):
                wl.render(card)

    def test_model_cannot_change_metric_name(self):
        card = copy.deepcopy(CARDS['C02'])
        card['metrics'][0]['label'] = 'AI准确率'
        with self.assertRaises(wl.EvidenceError):
            wl.render(card)

    def test_missing_or_duplicate_sources_and_evidence(self):
        for kind in ['source', 'duplicate', 'concept']:
            card = copy.deepcopy(CARDS['C01'])
            if kind == 'source':
                card['facts'][0]['source'] = 'missing'
            elif kind == 'duplicate':
                card['facts'].append(copy.deepcopy(card['facts'][0]))
            else:
                card['concepts'][0]['facts'] = ['missing']
            with self.subTest(kind=kind), self.assertRaises(wl.EvidenceError):
                wl.render(card)


if __name__ == '__main__':
    unittest.main()
