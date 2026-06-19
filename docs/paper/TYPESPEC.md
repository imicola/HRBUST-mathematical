# 论文排版规范（TYPESPEC）

> 2026 五一数学建模竞赛（校赛模拟）B 题 · LaTeX 排版约定
> 本文是论文排版的**唯一事实来源**。写正文前请通读；有歧义以本文为准。
> 解题算法/代码不在此文档范围内（见 `solve/code/`）。

---

## 1. 模板与工具链

| 项 | 选定 | 说明 |
|---|---|---|
| 模板类 | **`gmcmthesis.cls`**（vendored，未改动） | 源自 [zhanwen/MathModel](https://github.com/zhanwen/MathModel) 2025 模版；已拷贝至本目录，**勿改** |
| 编译引擎 | **XeLaTeX** | cls 强制 `\RequireXeTeX`，勿用 pdflatex |
| 参考文献 | **biber + biblatex（GB/T 7714-2015 顺序编码制）** | 现代工具链，中英文混排自动处理 |
| 构建命令 | `make` | latexmk 在场则用之，否则回退 `xelatex→biber→xelatex×2` 手动链 |
| 清理 | `make clean` | 删构建中间产物，保留 `main.pdf` |

**本机环境核验结果**（TeX Live 2026 / Arch）：
- ✓ xelatex / lualatex / pdflatex、biber 2.21、bibtex
- ✓ 中文字体：宋体 SimSun、黑体 SimHei、仿宋 FangSong、楷体 KaiTi、思源(Source Han Sans/Serif SC)
- ✗ **缺 MS 与华文字体**：Times New Roman / Arial / Courier New / 华文新魏(STXinwei) / 隶书(LiSu) 本机均无 → 已在 `gmcmthesis.cls` 打补丁改用 TeX Gyre（Times/Helvetica/Courier 兼容，TeX Live 自带）+ 黑体/楷体，**无需额外装字体**
- ✓ biblatex-gb7714-2015 与 -2025、pdfpages、booktabs、listings、**ulem**（`texlive-plaingeneric`）等 cls 全部依赖就位
- ⚠ `latexmk` 未装（pacman 无）：Makefile 已自动回退 `xelatex→biber→xelatex×2` 手动链，不阻塞

---

## 2. 目录结构

```
solve/docs/paper/
├── gmcmthesis.cls      # 模板类（vendored + 本地字体补丁，见文件头注释；排版逻辑勿改）
├── main.tex            # 主文档（元信息 + 封面覆盖 + 摘要 + \input 各节）
├── ref.bib             # 参考文献（biber 读）
├── Makefile            # 构建/清理
├── TYPESPEC.md         # 本文件
├── .gitignore          # 忽略构建中间产物（PDF 入库）
├── figures/            # 全部图片（矢量优先）
└── sections/           # 分节文件（团队并行写作，避免冲突）
    ├── 01_restatement.tex   问题重述
    ├── 02_analysis.tex      问题分析
    ├── 03_assumptions.tex   模型假设
    ├── 04_notation.tex      符号说明
    ├── 05_model.tex         模型建立与求解（Q1–Q4）
    ├── 06_evaluation.tex    模型评价与推广
    └── 07_appendix.tex      附录（代码、补充图表）
```

**协作约定**：每人按节认领 `sections/` 下的文件，**一个文件同一时间只一人编辑**，避免合并冲突。新内容写到独立文件里再 `\input`，不要多人同改 `main.tex`。

---

## 3. 字体（cls 已补丁适配本机，无需手改）

cls 原设的 MS/华文字体本机均无，已在 `gmcmthesis.cls` 文件头标注的补丁里改为可用字体：

| 用途 | 实际字体 | 命令 |
|---|---|---|
| 中文正文 | 宋体 SimSun（原样保留） | `\songti`（默认） |
| 中文标题/强调 | 黑体 SimHei | `\heiti` |
| 中文楷体 | 楷体 KaiTi | `\kaishu` |
| 封面竞赛名 | 黑体 SimHei（原华文新魏 STXinwei，本机无） | `\xinwei` |
| 摘要标题 | 楷体 KaiTi（原隶书 LiSu，本机无） | `\lishu` |
| 西文正文 | TeX Gyre Termes（Times 兼容；原 TNR 本机无） | `\textrm{}` |
| 西文无衬线 | TeX Gyre Heros（Arial 兼容） | `\textsf{}` |
| 西文等宽 | TeX Gyre Cursor（Courier 兼容） | `\texttt{}` |

**不要在正文里 `\setCJKmainfont`/`\setmainfont` 覆盖**——会破坏一致性。需要强调用 `\heiti`/`\textbf{}`。

---

## 4. 文档结构与章节顺序

`main.tex` 已固定如下顺序，**勿调整**：

1. 封面（`\maketitle`）
2. **摘要 + 关键词**（独立成页，cls 自动分页）
3. 目录（`\tableofcontents`）— 若赛方禁止目录，注释此行
4. 一、问题重述
5. 二、问题分析
6. 三、模型假设
7. 四、符号说明
8. 五、模型建立与求解（Q1–Q4 各一 `\subsection`）
9. 六、模型评价与推广
10. 参考文献（`\printbibliography`）
11. 附录（代码、补充图表）

### 摘要规则（硬性）
- **全文完成后最后写**。
- 结构：方法（题目类型+核心算法+创新点）→ 各问一段（思路+关键数值结果）→ 评价。
- 关键词 **3–5 个**，用中文分号 `；` 分隔，**末尾无标点**。
- 摘要**不超过一页**。

### 层级
- `\section{}`（居中、4 号黑体，cls 已配）
- `\subsection{}` / `\subsubsection{}` —— 建模章节按"问题一/模型建立/求解与结果"两级展开。
- 不要用到 `\paragraph` 以下做正文层级。
- **标题要点名具体内容**，禁用"问题X的分析/求解"这类空泛标题；应写成"问题一的分析：单班组单车间——工序链与关键路径"之类。

### 页眉页脚（fancyhdr，`main.tex` 已配）
- **页眉左**：当前章节名（`\leftmark`，随 `\section` 自动更新）。
- **页眉右**：`五一数学建模竞赛（校赛模拟）· B 题`（赛题标识）。
- **页脚中**：页码 `- N -`（小五号）。
- 封面页 `\thispagestyle{empty}`，无页眉页脚。
- 需改页眉内容（如加参赛队号）就改 `main.tex` 里 `\fancyhead` 两行。

---

## 5. 封面（待替换）

当前 `main.tex` 里的 `\renewcommand{\maketitle}` 是**竞赛无关占位封面**（无外部图片依赖，确保可编译）。封面元信息在 `main.tex` 顶部用以下命令填：
```
\title{...}  \baominghao{...}  \schoolname{...}
\membera{...}  \memberb{...}  \memberc{...}
```
**待拿到官方五一赛封面格式后，替换 `\maketitle` 定义**（可能需提供官方 logo 图片到 `figures/`）。在此之前用占位版即可正常写作与编译。

---

## 6. 参考文献

- 用 **biblatex + biber + GB/T 7714-2015 顺序编码制**（`main.tex` 已配好）。
- 条目写入 `ref.bib`，正文用 `\cite{key}` / `\parencite{key}` 引用。
- 中英文条目均可，biber 自动区分；中文条目 `author={张三}` 即可。
- **不要**用 cls 内置的手工 `thebibliography` 环境——已改用 biblatex。

---

## 7. 图与表

| 规则 | 要求 |
|---|---|
| 格式 | **矢量优先**：PDF / EPS（matplotlib 存 `savefig('x.pdf')`）；位图用 PNG ≥300dpi |
| 位置 | 图片放 `figures/`，正文 `\includegraphics{q1_gantt}`（无需写后缀，cls 自动按 pdf/eps/png/jpg 搜索） |
| 编号 | 按节编号 `X-1`（cls+main.tex 已配 `\numberwithin`） |
| 图题 | 在图**下方**；cls 自动用**宋体小四加粗** |
| 表题 | 在表**上方**；字体同上 |
| 三线表 | 用 `booktabs` 的 `\toprule/\midrule/\bottomrule`，**禁用 `\hline` 与竖线** |
| 表宽 | **表格用 `\begin{tabularx}{\textwidth}{...}` 撑满版心**，长内容列用 `X` 自适应；勿用窄 `tabular` 居中留白（参见 `04_notation.tex`） |
| 标签 | `\label{fig:q1-gantt}` / `\label{tab:notation}`，引用 `\ref`/`\autoref` |
| 放置 | `[!htbp]` 优先；大图 `[!h]` 单独居中 |

图表由 `solve/code` 出图后**导出到 `figures/`**（解题区与论文区解耦，互不直接依赖路径）。

---

## 8. 数学

- `amsmath` 已加载：用 `align`/`equation`/`cases`，**不用** `$$...$$`（用 `\[ \]` 或环境）。
- 符号**首次出现须与"符号说明"表一致**；多字母变量用 `\mathit` 或定义算符。
- 定理/定义/引理/假设环境 cls 已配：`\begin{theorem}...\end{theorem}` 等。
- 长公式换行在关系符前断；编号按需。

---

## 9. 代码

- 放**附录**（`sections/07_appendix.tex`）。
- 用 cls 预配置的 `listings`：`\begin{lstlisting}[language=Python] ... \end{lstlisting}`。
- 只贴**关键、可运行**的代码（求解器建模、核心算法），不要整目录倾倒。
- 超长代码可附到外部文件，正文给路径与说明。

---

## 10. 写作规范

- **术语统一**：全文同一概念用同一词（如"工序"不要混用"作业/任务/操作"）。
- **单位**：用国际单位制，数字与单位间空格（`41600\,s` 或 `41600 s`）；表格内可省。
- **有效数字**：结果给出有意义的位数；makespan 等整数给整数。
- **时态**：建模/求解过程用现在时；已做工作可过去时。
- **禁用**：口语化、感叹号、"我们尽量/大概"；用被动或"本文"。
- **量级核对**：写进摘要/正文的数值须与 `solve/results` 一致，禁止臆造。

---

## 11. 边界（与解题区解耦）

- 本目录只做**排版**。求解、数据、算法在 `solve/code/`、`solve/data/`、`solve/results/`。
- 论文需要的结果/图表，由解题区**导出**到 `figures/` 或手工抄录数值，**不在论文目录里跑代码**。
- 不要修改 `gmcmthesis.cls` 的排版逻辑；唯一例外是已做的字体补丁（见文件头）。新宏包/格式调整优先在 `main.tex` 前言做，并在本文档第 12 节登记。

---

## 12. 变更登记

| 日期 | 改动 | 作者 |
|---|---|---|
| 2026-06-19 | 初始排版骨架（gmcmthesis vendored + 占位封面 + biblatex + 分节） | Sisyphus |
| 2026-06-19 | 字体补丁：cls 改 TeX Gyre(Termes/Heros/Cursor)+黑体/楷体替代缺失的 MS/华文字体；`make` 通过出 5 页 PDF | Sisyphus |
| 2026-06-19 | 封面改为「题目版式」单页（无官方封面，仿 cls 原生 \makenametitle） | Sisyphus |
| 2026-06-19 | 排版修订：分析章节标题改描述性、三线表撑满版心（tabularx）、加 fancyhdr 页眉页脚 | Sisyphus |
