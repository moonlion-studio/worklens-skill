# WorkLens｜工作价值解读器

**事情做完，也能讲清楚。**

### 一键复制安装

点击下方代码块右上角的复制按钮，把命令发给你的 Agent 安装，或直接在终端运行：

```bash
npx skills add moonlion-studio/worklens-skill --skill work-impact-debrief
```

按提示选择 Agent 与安装位置。命令需要 Node.js / npx 环境；也可以让支持 Skill 安装的 Agent 根据本仓库完成安装。

**WorkLens 是一款面向 AI 编程与知识工作的专业复盘 Skill，帮助你把实际完成的任务，沉淀成能够理解、复述，并用于面试和工作汇报的项目经验。**

当你通过自然语言让 AI 写代码、增加功能、排查 Bug、优化业务流程，或搭建 RAG、Agent 与 Workflow 应用时，项目可以不断推进，但面试和汇报仍然需要回答：这是什么领域的问题？为什么采用这个方案？有哪些取舍？实际验证了什么？你本人负责了哪些判断？

WorkLens 将这些解释接到日常任务交付之后。AI 会结合本次对话、实际改动和已有验证材料，把具体工作连接到技术概念、产品决策、数据口径与个人贡献，再整理成适合 AI 应用工程师、产品经理或项目交付岗位的讲法。它也能帮助你回顾已有项目，为技术面试、简历项目经历、项目复盘、周报与阶段汇报准备素材。

使用方式保持简单：**小任务直接在对话里几句话讲清；大任务自动形成报告，并在宿主支持且已授权时保存结论与文件索引。** 你照常交代任务，材料整理、事实核对和已有数据的计算由 AI 完成。没有验证的效果会明确保留，不把功能完成直接写成业务收益。

## 谁会用到 WorkLens

- **AI 编程与 Vibe Coding 使用者**：能推动功能实现，希望进一步理解代码背后的机制，并讲清做了什么、为什么这样做。
- **AI 应用工程师与开发者**：把功能开发、接口排查、数据处理和 AI 评测整理成有依据的技术解释与面试故事。
- **产品经理与业务系统负责人**：从需求、角色、流程和方案取舍出发，解释交付与验证，形成可继续积累的项目记录。
- **准备求职或需要定期汇报的人**：减少临时翻聊天记录、回忆改动的负担，让日常工作留下可用于简历、面试、周报和述职的素材。

### English overview

WorkLens is an **Agent Skill for AI-assisted development, Vibe Coding, project retrospectives, interview preparation, and work reporting**. It connects real tasks with technical concepts, product decisions, verified outcomes, and personal contributions. Small tasks get a concise chat debrief; larger tasks become saved reports, with memory indexes when the host supports them. It helps you explain the work you actually did without inventing metrics or results.

## 就两种处理

| 任务 | 完成后怎么交付 |
|---|---|
| 小任务：修一个问题、加一个小功能、改样式 | 直接在对话里用几句话讲清专业做法和实际变化。默认不写文件。 |
| 大任务：多个模块协作、完整流程、重要方案或阶段交付 | 对话里先给结果，自动写一份复盘文件，并把结论和文件位置存入可用的长期记忆。 |

任务大小由 AI 按实际工作判断。你说“简单讲”“详细写”或“别存文件”，就按你的要求做。

## 怎么用

照常说任务即可，也可以明确加一句：

> 使用 `$work-impact-debrief` 完成这个任务。小任务直接讲，大任务写报告并记住。

复盘已经做过的工作，也可以直接说：

> 帮我把刚才的改动讲清楚，告诉我面试或汇报时怎么说。

**你不需要填写表格、整理证据卡、准备 JSON、安装 Python 或运行命令。** AI 自己阅读当前任务的材料，核对事实、计算已有数据，再决定如何交付。

## 会讲清什么

这属于什么问题、用到什么专业做法、为什么这样处理、实际验证到了哪一步、你负责什么，以及面试或汇报时怎样表达。没有的数据简短标明，不编造业务提升。

小任务例如“预约保存成功后还在等历史同步”，可以直接讲：

> 这涉及异步同步与交互反馈。改动将本次保存结果与历史刷新分开，以保存回执决定成功提示。实际耗时改善还要看已有采样；面试时可以解释为关键操作链路与后台同步解耦。

大任务把这些内容展开为一份可读报告。长期记忆只保留简短结论、文件索引和待跟进项，方便以后继续使用；不支持记忆的助手会保存本地索引并说明情况，不假装已记住。

## 安装与适配

把仓库链接交给支持 Skill 的助手，让它安装并启用 `work-impact-debrief`。本机已经安装的用户更新后即可继续用。

支持持久记忆的宿主按已有授权和存储约定写入；其他宿主保留本地索引。报告和内部材料不自动上传。

<details>
<summary>手动安装（可选）</summary>

将 `SKILL.md`、`agents/`、`references/` 和 `scripts/` 放到助手的 `work-impact-debrief` 技能目录。Codex 默认目录是 `~/.codex/skills/work-impact-debrief/`。安装操作也可以交给助手完成。

</details>

## 后台核对

来源、指标和贡献仍要准确。AI 可按需使用仓库内的校验与计算工具，默认交互不要求用户了解这些细节。

[测试与适用范围](EVALUATION.md)记录了当前交付方式与既有后台回归；[报告样例](eval/v3/results/C03.md)是严格生成模式的示例，普通对话不需要照着它的格式写。

<details>
<summary>开发与测试（可选）</summary>

后台脚本仅在需要程序化校验时使用，依赖 Python 3 标准库。18 项回归覆盖来源引用、比例/百分点、失败状态和责任归属；它们不代表所有自然语言讲解都已经过自动验证。

```bash
python3 -m unittest discover -s tests -v
```

严格模式的[证据卡说明](references/evidence-card.md)、[历史评测](eval/history/EVALUATION-0.2.md)和[本机联调结果](eval/v3/results/)供开发者检查，不是使用前置步骤。

</details>
