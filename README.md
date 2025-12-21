# Protein Site Explainer

Protein Site Explainer 是一个基于 Streamlit 的交互式工具，用于分析蛋白质突变的影响。它结合了多种生物信息学资源和深度学习模型，提供全面的突变分析结果。

## 功能特性

- **ESM-2 评分**：计算突变的对数似然比 (LLR)，评估突变的影响
- **位点敏感度**：计算位点对所有可能突变的平均敏感度
- **AlphaFold 结构分析**：获取 pLDDT 分数，评估结构置信度
- **UniProt 特征映射**：将 UniProt 注释的功能域映射到突变位置
- **可视化展示**：
  - 序列特征曲线图（包含 LLR、敏感度和 pLDDT）
  - pLDDT 热图
  - 3D 结构视图（高亮突变位置）
- **结果导出**：支持将分析结果导出为 CSV 文件
- **磁盘缓存**：缓存结果以提高性能

## 安装方法

### 1. 克隆仓库

```bash
git clone <repository-url>
cd protein_site_explainer
```

### 2. 创建虚拟环境（可选但推荐）

```bash
# 使用 conda
conda create -n protein_explainer python=3.8
conda activate protein_explainer

# 或者使用 venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

## 运行方法

使用以下命令启动 Streamlit 应用：

```bash
streamlit run app.py
```

应用将在浏览器中打开，默认地址为 `http://localhost:8501`。

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
├── app.py              # Streamlit 应用主文件
├── requirements.txt    # 依赖列表
├── setup.py            # 项目配置
├── pytest.ini          # pytest 配置
├── README.md           # 项目说明文档
├── src/
│   ├── cache.py        # 磁盘缓存实现
│   ├── parsing.py      # 突变解析模块
│   ├── uniprot.py      # UniProt API 交互
│   ├── alphafold.py    # AlphaFold 数据获取
│   ├── esm_scoring.py  # ESM 评分计算
│   ├── explain.py      # 核心解释逻辑
│   └── viz.py          # 可视化功能
└── tests/
    ├── test_parsing.py # 解析模块测试
    ├── test_uniprot.py # UniProt 模块测试
    ├── test_alphafold.py # AlphaFold 模块测试
    └── test_full_flow.py # 完整流程测试
```

## 模块说明

- **cache.py**: 实现磁盘缓存机制，减少重复 API 请求和模型计算
- **parsing.py**: 解析和验证突变字符串（格式：A123T）
- **uniprot.py**: 通过 UniProt REST API 获取蛋白质序列和功能特征
- **alphafold.py**: 从 AlphaFold 数据库获取 pLDDT 数据
- **esm_scoring.py**: 使用 ESM-2 模型计算 LLR 和位点敏感度
- **explain.py**: 整合所有模块，提供统一的解释接口
- **viz.py**: 实现可视化功能，包括序列曲线图和 3D 结构视图
- **app.py**: Streamlit 应用界面和用户交互逻辑

## 技术栈

- **Streamlit**: Web 应用框架
- **ESM-2**: 蛋白质语言模型（用于突变评分）
- **AlphaFold**: 蛋白质结构预测（用于 pLDDT 分析）
- **UniProt**: 蛋白质数据库（用于序列和功能信息）
- **plotly**: 交互式图表库
- **py3Dmol**: 3D 结构可视化
- **pytest**: 测试框架

## 测试

运行以下命令执行测试：

```bash
pytest
```

运行特定测试文件：

```bash
pytest tests/test_full_flow.py -v
```

## 注意事项

1. **API 限制**：UniProt 和 AlphaFold 数据库可能有访问限制
2. **计算资源**：ESM 模型需要一定的计算资源，首次运行可能较慢
3. **缓存机制**：结果会自动缓存，提高重复查询的速度
4. **数据验证**：请确保输入的 UniProt ID 和突变格式正确

## 联系方式

如有问题或建议，请通过以下方式联系：

- Email: <1300311091@qq.com>
- GitHub: <https://github.com/fls233666/protein_site_explainer>
