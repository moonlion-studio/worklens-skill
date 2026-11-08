# 复跑报告生成测试

测试用例均为脱敏构造材料，不是原企业数据或真人业务收益。检查点保存在 cases.json，但运行器只将 prompt 字段发送给模型，不把检查点作为答案提示。

本次后端为本机 Ollama 的 `qwen2.5:7b`。模型需事先可用；日常使用 Skill 不依赖此模型或 Ollama。

在仓库根目录执行：

```bash
python3 eval/run_eval.py --skill . --cases eval/cases.json --output eval/rerun-results
```

运行器访问本机 `http://127.0.0.1:11434/api/chat`，不会调用公司系统或发布代码。`--endpoint` 可以显式更改目标，输入材料会发送到该目标；默认是本机。输出为每例 JSON，包含原文、结束原因、耗时和 token 数；metadata.json 保存参数和 Skill 内容摘要。

C01、C02 分别运行未加载 Skill 与加载 Skill 的输出，其他用例只运行 Skill。基线仍是具备一般能力的助手，不故意要求它生成错误答案。比较用于观察差异，不能外推为统计效果。

本仓库还保留了初版指令快照，以及修订后的同题回归。要对应复跑两轮，分别使用：

```bash
python3 eval/run_eval.py --skill eval/versions/v1 --cases eval/cases.json --output eval/rerun-v1
python3 eval/run_eval.py --skill . --cases eval/cases-regression.json --output eval/rerun-v2
```

第二轮继续使用首轮用例，是修订后的回归检查，不是独立留出集或泛化效果证明。参数和模型相同，仍可能存在运行环境差异。

人工检查报告按：机制/术语、取舍解释、指标与事实、个人贡献/状态、讲解可用性五个方面核对。发现未经支持的上线、收益或责任归属，不因文字流畅而判通过。截断输出作为不完整样本记录，不能拼成完整成功。

这是小样本、单模型、固定参数测试。评审由任务作者完成，没有独立盲评；不验证真实用户是否学会、不评估录用率，也不验证模型能否通过工具完成原始开发任务。真人理解验证需要另外收集复述与追问结果。
