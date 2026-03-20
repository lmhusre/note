# 笔记工作区总览

这个工作区收纳了多门课程的学习笔记，既有 LaTeX 项目，也有 Markdown 笔记。后续无论是人工协作还是智能体协作，建议先看本文件，再进入各课程目录查看对应的 `readme.md`。

## 当前笔记目录

- `高分子化学/`
  - 课程主笔记，采用 LaTeX 维护。
  - 已有较完整的协作说明，见 `高分子化学/readme.md`。
- `分析化学/`
  - 课程主笔记，采用 LaTeX 维护。
- `材料成型基础/`
  - 课程主笔记，采用 LaTeX 维护。
- `仪器分析/`
  - 采用 Markdown 维护的章节笔记，目前覆盖第一、二章及光学导论。
- `专英/`
  - 采用 Markdown 维护的专业英语笔记，当前是聚合相关英文材料的整理与精编。

## 顶层脚本

- `run_latex_watch.bat`
  - 用于编译 LaTeX 笔记。
  - 实际调用 `build_tex_watch.py`，输出 PDF 到各项目自己的 `out/` 目录，中间文件进 `auxil/`。
- `run_md_xelatex.bat`
  - 用于把 Markdown 转成 LaTeX 再用 XeLaTeX 编译。
  - 适用于 `仪器分析/`、`专英/` 这类 Markdown 笔记。
- `build_tex_watch.py`
  - LaTeX 构建脚本。
- `main.tex`
  - 当前更像测试或临时 LaTeX 文件，不属于上面几个课程主项目。

## 推荐协作顺序

1. 先确认要修改的是哪一门课程。
2. 再进入对应目录，阅读目录里的 `readme.md`。
3. 只修改正文源文件，不要直接改 `auxil/`、`out/` 等生成目录。
4. 修改完成后再统一编译，并检查生成 PDF。

## 编码与工具提醒

- 中文路径较多，终端操作前建议启用 UTF-8 输出。
- LaTeX 项目默认使用 XeLaTeX。
- Markdown 项目如需导出 PDF，优先走现成批处理脚本，不要手工拼命令。

## 通用协作约定

- 源文件优先级高于导出文件。
  - LaTeX 项目的正文源文件通常是 `<课程名>.tex`。
  - Markdown 项目的正文源文件通常是 `.md`。
- 生成文件不要当作主编辑对象。
  - 如 `out/*.pdf`、`auxil/*.aux`、`auxil/*.toc`、`*_xelatex.tex` 等。
- 若发现图文、公式、章节标题不对应，应优先修正文源文件和资源引用关系。
- 若新增了辅助材料、提取文本或参考 PDF，建议在对应课程目录的 `readme.md` 中同步登记用途。

## 快速入口

- [高分子化学/readme.md](高分子化学/readme.md)
- [分析化学/readme.md](分析化学/readme.md)
- [材料成型基础/readme.md](材料成型基础/readme.md)
- [仪器分析/readme.md](仪器分析/readme.md)
- [专英/readme.md](专英/readme.md)
