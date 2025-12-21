# Protein Site Explainer

Protein Site Explainer 是一个基于 Streamlit 的交互式工具，用于分析蛋白质突变的影响。它结合了多种生物信息学资源和深度学习模型，提供全面的突变分析结果。

## 功能特性

### 核心功能

- **ESM-2 评分**：
  - 计算突变的对数似然比 (LLR)，评估突变的影响
  - 使用准确的 ESM 字母表索引，确保评分正确性
  - 批处理优化：按位置分组突变，大幅减少计算时间
  - 矢量化计算：使用 PyTorch 张量优化性能

- **位点敏感度**：计算位点对所有可能突变的平均敏感度，评估位点保守性

- **AlphaFold 结构分析**：
  - 获取 pLDDT 分数，评估结构置信度
  - 下载完整的 PDB 结构文件
  - 3D 结构可视化，高亮突变位置

- **UniProt 特征映射**：
  - 将 UniProt 注释的功能域映射到突变位置
  - 支持多种特征类型（如功能域、结合位点、修饰位点等）
  - 增强的 XML 解析，支持多种位置格式

### 性能优化

- **模型复用**：使用 `st.cache_resource` 复用 ESM 模型，避免重复加载
- **批处理**：按位置分组突变，计算时间从 O(n) 降至 O(1) 每位置
- **设备管理**：
  - 自动检测 CUDA GPU 并使用 GPU 加速
  - GPU 内存不足时自动回退到 CPU
  - 支持手动选择计算设备

### 网络与解析稳健性

- **统一请求会话**：使用增强的 `requests.Session` 配置
  - 超时控制和重试机制
  - 详细的错误处理和恢复
  - 安全的文件下载（临时文件 + 原子重命名）

- **兼容性解析**：
  - 支持 UniProt XML 中多种特征位置格式
  - AlphaFold PDB 文件的安全解析
  - 多种突变输入格式支持

### 缓存系统增强

- **版本控制**：避免使用过期缓存
- **并发安全**：支持多进程访问
- **配置灵活**：可配置缓存目录和大小限制
- **智能清理**：基于最大大小和 TTL 的 LRU 清理策略

### 可视化与用户体验

- **交互式图表**：使用 Plotly 实现丰富的可视化
  - 序列特征曲线图（LLR、敏感度、pLDDT）
  - pLDDT 热图
  - 突变位置高亮显示

- **3D 结构可视化**：
  - 使用 py3Dmol 实现交互式 3D 结构视图
  - 突变位置自动高亮
  - 支持旋转、缩放和选择

- **结果导出**：支持将分析结果导出为 CSV 文件

- **多语言支持**：提供英文和中文界面

### 跨平台兼容性

- 支持 Windows 10/11、Linux (Ubuntu 20.04+) 和 MacOS 11+
- 统一的代码结构和依赖管理
- 优化的文件路径处理
- 一致的用户体验 across all platforms

## 安装方法

### 1. 克隆仓库

```bash
git clone <repository-url>
cd protein_site_explainer
```

### 2. 创建虚拟环境（可选但推荐）

#### Linux/Mac
```bash
# 使用 conda
conda create -n protein_explainer python=3.8
conda activate protein_explainer

# 或者使用 venv
python -m venv venv
source venv/bin/activate
```

#### Windows
```bash
# 使用 conda
conda create -n protein_explainer python=3.8
conda activate protein_explainer

# 或者使用 venv
python -m venv venv
venv\Scripts\activate
```

### 3. 安装依赖

#### 核心依赖
```bash
pip install -r requirements.txt
```

#### 开发依赖（用于测试和开发）
```bash
pip install -r requirements-dev.txt
```

#### 可选：CPU版本安装（无NVIDIA GPU时）

如果您没有NVIDIA GPU，可以安装PyTorch的CPU版本：

```bash
# Linux/Mac
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# Windows
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

#### 可编辑安装（开发时推荐）

```bash
pip install -e .
```

## 运行方法

### Linux/Mac
```bash
python -m streamlit run app.py
```

### Windows
```bash
python -m streamlit run app.py
```

**注意**：在 Windows 系统上，推荐使用 `python -m streamlit` 格式而不是直接使用 `streamlit` 命令，因为后者可能会因为 PATH 环境变量配置问题导致 "streamlit: command not found" 错误。

应用将在浏览器中打开，默认地址为 `http://localhost:8501`。

### 设备选择

应用会自动检测可用的计算设备：
- 如果检测到 NVIDIA GPU 并安装了 CUDA，将使用 GPU 进行 ESM 模型计算
- 如果 GPU 内存不足或未检测到 GPU，将自动回退到 CPU

您可以在应用界面中手动选择计算设备。

## 使用示例

### 基本用法

1. 在左侧边栏输入：
   - **UniProt ID**：例如 `P0DTC2`（SARS-CoV-2 Spike 蛋白）
   - **Mutation List**：例如 `D614G, A222V, T478K`

2. 点击 "Explain Mutations" 按钮

3. 查看结果：
   - 突变分析表格
   - 序列特征曲线图
   - 3D 结构视图
   - 蛋白质序列信息

### 示例 1：SARS-CoV-2 Spike 蛋白

- **UniProt ID**: `P0DTC2`
- **Mutations**: `D614G, A222V, T478K`

### 示例 2：人类 p53 蛋白

- **UniProt ID**: `P04637`
- **Mutations**: `R175H, R248Q, R273H`

## 项目结构

```
protein_site_explainer/
├── app.py                      # Streamlit 应用主文件
├── requirements.txt            # 核心依赖列表
├── requirements-dev.txt        # 开发依赖列表（测试和开发工具）
├── setup.py                    # 项目配置文件
├── pytest.ini                  # pytest 配置
├── .gitignore                  # Git 忽略文件配置
├── .gitattributes              # Git 属性配置
├── README.md                   # 项目说明文档
├── i18n/                       # 国际化资源文件
│   ├── en.json                 # 英文翻译
│   └── zh.json                 # 中文翻译
├── src/                        # 源代码目录
│   ├── __init__.py             # 包初始化文件
│   ├── cache.py                # 磁盘缓存实现（带版本控制和并发安全）
│   ├── parsing.py              # 突变解析模块
│   ├── uniprot.py              # UniProt API 交互（增强的错误处理）
│   ├── alphafold.py            # AlphaFold 数据获取
│   ├── esm_scoring.py          # ESM 评分计算（批处理和矢量化）
│   ├── explain.py              # 核心解释逻辑
│   └── viz.py                  # 可视化功能
└── tests/                      # 测试目录
    ├── test_parsing.py         # 解析模块测试
    ├── test_uniprot.py         # UniProt 模块测试
    ├── test_alphafold.py       # AlphaFold 模块测试
    ├── test_esm_scoring.py     # ESM 评分测试
    └── test_full_flow.py       # 完整流程测试
```

## 模块说明

- **cache.py**: 实现磁盘缓存机制，包含：
  - 版本控制：避免使用过期缓存
  - 并发安全：支持多进程访问
  - 清理策略：基于最大大小和 TTL 的 LRU 清理
  - 跨平台兼容：支持 Windows 和 Linux/Mac

- **parsing.py**: 解析和验证突变字符串（格式：A123T），支持多种输入格式

- **uniprot.py**: 通过 UniProt REST API 获取蛋白质序列和功能特征：
  - 增强的错误处理：支持超时、重试和错误恢复
  - 统一的 `requests.Session`：提高性能和可靠性
  - 安全的文件下载：使用临时文件和原子重命名

- **alphafold.py**: 从 AlphaFold 数据库获取 pLDDT 数据和结构文件：
  - 与 `uniprot.py` 共享请求会话配置
  - 详细的错误处理和状态报告

- **esm_scoring.py**: 使用 ESM-2 模型计算 LLR 和位点敏感度：
  - 批处理：按位置分组突变，减少计算时间
  - 矢量化：使用 PyTorch 张量优化计算
  - 设备自动选择：GPU（优先）/CPU 切换
  - 增强的错误处理：处理 GPU 内存不足等情况

- **explain.py**: 整合所有模块，提供统一的解释接口

- **viz.py**: 实现可视化功能：
  - 序列特征曲线图（包含 LLR、敏感度和 pLDDT）
  - pLDDT 热图
  - 3D 结构视图（高亮突变位置）

- **app.py**: Streamlit 应用界面和用户交互逻辑：
  - 多语言支持（英文/中文）
  - 设备选择界面
  - 统一的结果导出
  - 增强的用户体验

## 技术栈

- **Streamlit**: Web 应用框架，提供交互式用户界面
- **PyTorch**: 深度学习框架，支持 ESM-2 模型（提供 CPU 和 GPU 版本）
- **ESM-2**: 蛋白质语言模型（用于突变评分），来自 Meta AI
- **AlphaFold**: 蛋白质结构预测数据库（用于 pLDDT 分析和结构可视化）
- **UniProt**: 蛋白质数据库（用于序列和功能信息）
- **requests**: 网络请求库（增强的错误处理和会话管理）
- **lxml**: XML 解析库（用于处理 UniProt XML 响应）
- **joblib**: 用于缓存和并行计算
- **plotly**: 交互式图表库（用于序列特征曲线图和热图）
- **py3Dmol**: 3D 结构可视化库（用于蛋白质结构展示）
- **pytest**: 测试框架（用于单元测试和集成测试）
- **black/flake8/isort**: 代码格式化和质量检查工具
- **mypy**: 静态类型检查工具

### 跨平台兼容性

所有依赖均支持 Windows、Linux 和 Mac 系统，确保在不同操作系统上都能正常运行。

## 测试

### 运行所有测试

```bash
# Linux/Mac
pytest

# Windows
pytest
```

### 运行特定测试文件

```bash
# Linux/Mac
pytest tests/test_esm_scoring.py -v
pytest tests/test_full_flow.py -v

# Windows
pytest tests/test_esm_scoring.py -v
pytest tests/test_full_flow.py -v
```

### 运行测试并生成覆盖率报告

```bash
# Linux/Mac
pytest --cov=src tests/

# Windows
pytest --cov=src tests/
```

### 测试内容

- **单元测试**：测试各个模块的核心功能
  - `test_parsing.py`: 突变解析和验证
  - `test_esm_scoring.py`: ESM 评分计算和批处理
  - `test_uniprot.py`: UniProt API 交互和错误处理
  - `test_alphafold.py`: AlphaFold 数据获取

- **集成测试**：测试完整的工作流程
  - `test_full_flow.py`: 端到端测试，包括从输入到结果输出

所有测试均在 Windows 和 Linux 系统上验证通过。

## 注意事项

### 系统要求

- **操作系统**：Windows 10/11, Linux (Ubuntu 20.04+), MacOS 11+
- **Python 版本**：3.8 或更高
- **内存**：建议至少 8GB RAM
- **存储**：建议至少 5GB 可用磁盘空间（用于缓存和模型）
- **GPU**：可选，NVIDIA GPU 需支持 CUDA 11.7+（可加速 ESM 模型计算）

### 常见问题

1. **API 限制**：UniProt 和 AlphaFold 数据库可能有访问限制，应用会自动处理重试和错误恢复

2. **计算资源**：
   - ESM 模型首次运行需要下载模型权重（约 3GB）
   - GPU 加速需要正确安装 CUDA 和 PyTorch
   - 如遇到 GPU 内存不足，应用会自动回退到 CPU

3. **缓存机制**：
   - 结果会自动缓存，提高重复查询速度
   - 缓存目录默认为应用运行目录下的 `.cache` 文件夹
   - 支持手动清理缓存（在应用界面中）

4. **数据验证**：
   - 请确保输入的 UniProt ID 格式正确
   - 突变格式应为 "A123T"（野生型氨基酸+位置+突变型氨基酸）
   - 支持多种输入格式（如 "A123T,A456V" 或 "A123T A456V"）

5. **跨平台注意事项**：
   - Windows：使用 `python -m streamlit` 启动应用
   - Linux/Mac：可以使用 `streamlit run` 或 `python -m streamlit run`
   - 文件路径处理已优化，确保在所有平台上正常工作

## 联系方式

如有问题或建议，请通过以下方式联系：

- Email: <1300311091@qq.com>
- GitHub: <https://github.com/fls233666/protein_site_explainer>
