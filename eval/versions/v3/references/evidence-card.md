# 证据卡：来源、计算与生成

需要 Python 3 标准库，无额外依赖。事实从用户要求、diff、工具回执或交付文档摘录；不得用模型之前的总结冒充独立业务验收。

下面是构造教学材料，不是企业业务数据：

```json
{
  "version": 1,
  "title": "规则编排复盘",
  "profile": "constraints",
  "sources": [
    {"id": "s1", "text": "按规则编排方案。构造验收16份方案12份满足全部约束；未采集真实采纳。"}
  ],
  "facts": [
    {"id": "f1", "kind": "change", "source": "s1", "quote": "按规则编排方案"},
    {"id": "f2", "kind": "verification", "source": "s1", "quote": "构造验收16份方案12份满足全部约束"},
    {"id": "f3", "kind": "unknown", "source": "s1", "quote": "未采集真实采纳"}
  ],
  "concepts": [{"term": "constraints", "facts": ["f1"]}],
  "metrics": [{"kind": "rule_rate", "refs": ["f2"], "total": 16, "passed": 12}],
  "brief": false
}
```

`facts.kind` 支持 request、change、verification、status、risk、unknown、contribution。quote 必须逐字存在于指定 source。来源的真实性、完整性以及事实类别仍应由原始记录核对，字符串匹配不是语义真实性证明。

`profile` 和概念键：

| profile | 可用 term |
|---|---|
| async-feedback | receipt、decoupling、ordering |
| constraints | constraints、rules |
| evaluation | regression、historical、gold |
| visual | consistency |
| export | authorization、delivery |
| batch | validation、transaction、idempotency、observability |
| unknown | scope |

每个概念都应引用支持本次映射的事实。选择错误的领域不能只凭格式合法就算通过；新的领域先补有依据的解释资源或选择 unknown。定义保存在 `scripts/worklens.py` 的 PROFILES 中。

## 指标

`rule_rate` 使用 passed/total，固定命名为所给样本规则满足率。`offline_comparison` 使用 baseline、candidate、total，输出两版通过率、百分点差以及基线非零时的相对变化。所用数值必须出现在引用摘录中，负数、布尔值、超过分母或无来源数值会被拒绝。

0 分母不计算比例，0 基线不计算相对提升；使用 Decimal 避免浮点显示误差。数字对应的业务口径由证据卡提供，不能把“所给样本”当全公司效果。

当前不从一段自然语言自动推断任意收益公式；缺少有口径的指标时保留未知。不要为了填写 metrics 改造来源数字。

## 模型计划与错误回退

可选计划仅为：

```json
{"concept_order": ["constraints", "rules"]}
```

必须恰好包含卡中全部概念一次；不能出现 report、收益、测试或个人贡献等自由文本字段。非法计划不会进入最终报告，audit 记录 `rejected_used_grounded_fallback`。没有模型计划也可以生成完整报告。非法卡不会自动“修正”为看似成功的数据。

## 保留的限制

此工具没有持续监听、自动取证或全领域知识推理功能。宿主先将可访问的原始证据整理入卡；当前回归卡由作者按原文构造，测试没有测量自动抽取准确率。工具也不证明使用者已掌握术语，需用报告中的追问与真人复述验证。
