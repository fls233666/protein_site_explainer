import streamlit as st
import pandas as pd
import numpy as np
import requests.exceptions
import json
import os
from src.explain import explain_mutations, explainer
from src.viz import visualizer
from src.cache import clear_cache

# 加载语言文件
def load_translations(language):
    """加载指定语言的翻译文件"""
    lang_file = os.path.join("i18n", f"{language}.json")
    with open(lang_file, "r", encoding="utf-8") as f:
        return json.load(f)

# 初始化语言设置
if "language" not in st.session_state:
    st.session_state["language"] = "en"  # 默认英语

# 加载当前语言的翻译
translations = load_translations(st.session_state["language"])

# 设置页面配置
st.set_page_config(
    page_title=translations["page_title"],
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 添加自定义CSS使内容区域使用完整宽度
st.markdown("""
<style>
    /* 直接移除所有与最大宽度相关的限制 */
    [data-testid="stBlockContainer"] {
        max-width: 100% !important;
        width: 100% !important;
        padding: 2rem 2rem 2rem 2rem;
    }
    
    /* 确保内容区域不被限制 */
    .main {
        width: 100% !important;
    }
    
    /* 确保所有容器元素使用完整宽度 */
    div[data-testid="stBlockContainer"] > div {
        width: 100% !important;
    }
    
    /* 确保表格和图表使用完整宽度 */
    .stDataFrame, .stPlotlyChart, .stPy3Dmol {
        width: 100% !important;
    }
    
    /* 移除应用视图容器的宽度限制 */
    [data-testid="stAppViewContainer"] {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 移除主块容器的宽度限制 */
    [data-testid="stMainBlockContainer"] {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 移除应用主容器的宽度限制 */
    .stApp {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保流式布局的容器使用完整宽度 */
    .css-1d391kg {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保列容器使用完整宽度 */
    [data-testid="column"] {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保容器元素使用完整宽度 */
    .stContainer {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 针对Streamlit 1.28+版本的动态CSS类 */
    .css-18e3th9 {
        padding: 2rem 2rem 2rem 2rem !important;
    }
    
    /* 移除侧边栏和主内容区域的宽度限制 */
    .css-1d90msa {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保内容块使用完整宽度 */
    .css-184tjsw {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保页面容器使用完整宽度 */
    .css-10trblm {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保主页面内容使用完整宽度 */
    .css-1v0mbdj {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保所有卡片容器使用完整宽度 */
    .css-1kyxreq {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保所有内容包装器使用完整宽度 */
    .css-1y4p8pa {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保主内容区域使用完整宽度 */
    .main > .block-container {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保主内容区域不被侧边栏挤压 */
    [data-testid="stSidebar"] + [data-testid="stMain"] {
        width: 100% !important;
    }
    
    /* 确保主内容区域的容器使用完整宽度 */
    [data-testid="stMain"] > div {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保所有内容行使用完整宽度 */
    .row-widget {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保表格容器使用完整宽度 */
    .dataframe-container {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保所有数据框使用完整宽度 */
    table.dataframe {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保所有图表容器使用完整宽度 */
    .plotly-container {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保所有Py3Dmol容器使用完整宽度 */
    .py3dmol-container {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保所有标题容器使用完整宽度 */
    .css-10trblm {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保所有子标题容器使用完整宽度 */
    .css-zt5igj {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保所有文本容器使用完整宽度 */
    .css-qrbaxs {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保所有按钮容器使用完整宽度 */
    .css-1x8cf1d {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 移除所有可能的内容容器最大宽度限制 */
    div[data-testid="stVerticalBlock"] {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保流式布局的内容使用完整宽度 */
    .css-1d391kg {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保内容块使用完整宽度 */
    .css-1v0mbdj {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保侧边栏不会挤压主内容 */
    .css-12oz5g7 {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保所有容器元素使用完整宽度 */
    [data-testid="stBlockContainer"] > div {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保所有元素没有最大宽度限制 */
    * {
        max-width: none !important;
    }
    
    /* 但是保持特定元素的宽度设置 */
    table.dataframe, .plotly-container, .py3dmol-container {
        width: 100% !important;
    }
    
    /* 针对Streamlit 1.30+版本的动态CSS类 */
    .css-1d391kg {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保列容器使用完整宽度 */
    div[data-testid="column"] > div {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保容器内的内容使用完整宽度 */
    .stContainer > div {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保所有垂直块使用完整宽度 */
    [data-testid="stVerticalBlock"] > div {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保所有水平块使用完整宽度 */
    [data-testid="stHorizontalBlock"] {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保所有块容器使用完整宽度 */
    [data-testid="block-container"] {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保所有组件容器使用完整宽度 */
    .streamlit-expander, .streamlit-expander-content {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保绘图容器使用完整宽度 */
    .stPlotlyChart > div {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保Py3Dmol容器使用完整宽度 */
    .stPy3Dmol > div {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保文本区域使用完整宽度 */
    .stTextArea > div {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保所有容器元素使用完整宽度 */
    div[role="main"] > div {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保所有列内容使用完整宽度 */
    .css-1lcbmhc {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 确保所有主内容容器使用完整宽度 */
    .css-1x8cf1d, .css-1b0udgb {
        max-width: 100% !important;
        width: 100% !important;
    }

    /* 移除所有容器的最大宽度限制 */
    [data-testid="stBlockContainer"] > div, 
    [data-testid="stBlockContainer"] > div > div, 
    [data-testid="stBlockContainer"] > div > div > div, 
    [data-testid="stBlockContainer"] > div > div > div > div, 
    [data-testid="stBlockContainer"] > div > div > div > div > div, 
    [data-testid="stBlockContainer"] > div > div > div > div > div > div, 
    [data-testid="stBlockContainer"] > div > div > div > div > div > div > div, 
    [data-testid="stBlockContainer"] > div > div > div > div > div > div > div > div {
        max-width: none !important;
        width: 100% !important;
    }

    /* 确保主内容区域不受侧边栏影响 */
    [data-testid="stMain"] {
        max-width: none !important;
        width: 100% !important;
        flex: 1 1 auto !important;
    }

    /* 确保主内容区域的容器使用完整宽度 */
    [data-testid="stMain"] > div, 
    [data-testid="stMain"] > div > div, 
    [data-testid="stMain"] > div > div > div {
        max-width: none !important;
        width: 100% !important;
        flex: 1 1 auto !important;
    }

    /* 确保块容器使用完整宽度 */
    [data-testid="stBlockContainer"] {
        max-width: none !important;
        width: 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }

    /* 确保侧边栏不会挤压主内容 */
    [data-testid="stSidebar"] + [data-testid="stMain"] {
        margin-left: 0 !important;
        width: 100% !important;
        flex: 1 1 auto !important;
    }

    /* 确保结果部分的所有容器使用完整宽度 */
    [data-testid="stBlockContainer"] > div > div > div > div,
    [data-testid="stBlockContainer"] > div > div > div > div > div,
    [data-testid="stBlockContainer"] > div > div > div > div > div > div,
    [data-testid="stBlockContainer"] > div > div > div > div > div > div > div {
        max-width: none !important;
        width: 100% !important;
    }

    /* 确保所有子标题部分使用完整宽度 */
    [data-testid="stMarkdownContainer"] + div,
    [data-testid="stMarkdownContainer"] + div > div,
    [data-testid="stMarkdownContainer"] + div > div > div,
    [data-testid="stMarkdownContainer"] + div > div > div > div,
    [data-testid="stMarkdownContainer"] + div > div > div > div > div {
        max-width: none !important;
        width: 100% !important;
        flex: 1 1 auto !important;
    }

    /* 确保所有列容器和内容使用完整宽度 */
    [data-testid="column"],
    [data-testid="column"] > div,
    [data-testid="column"] > div > div,
    [data-testid="column"] > div > div > div,
    [data-testid="column"] > div > div > div > div {
        max-width: none !important;
        width: 100% !important;
        flex: 1 1 auto !important;
    }

    /* 确保两列布局中的图表容器使用完整宽度 */
    [data-testid="stVerticalBlock"] {
        max-width: 100% !important;
        width: 100% !important;
    }

    /* 确保两列布局中的内容容器使用完整宽度 */
    [data-testid="stVerticalBlock"] [data-testid="column"] > div {
        max-width: 100% !important;
        width: 100% !important;
    }

    /* 确保所有图表和视图使用完整宽度 */
    .stPlotlyChart,
    .stPlotlyChart > div,
    .stPlotlyChart > div > div,
    .stPlotlyChart > div > div > div,
    .stPy3Dmol,
    .stPy3Dmol > div,
    .stPy3Dmol > div > div,
    .stPy3Dmol > div > div > div,
    .stTextArea,
    .stTextArea > div,
    .stTextArea > div > div,
    .stTextArea > div > div > div {
        max-width: none !important;
        width: 100% !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }

    /* 确保所有容器使用完整宽度 */
    .stContainer,
    .stContainer > div,
    .stContainer > div > div,
    .stContainer > div > div > div,
    .stContainer > div > div > div > div {
        max-width: none !important;
        width: 100% !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }

    /* 确保带有边框的容器使用完整宽度 */
    div[style*="border:"] > div {
        max-width: none !important;
        width: 100% !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }

    /* 确保内容容器使用完整宽度 */
    div[data-testid="stVerticalBlock"] > div > div,
    div[data-testid="stVerticalBlock"] > div > div > div,
    div[data-testid="stHorizontalBlock"] > div > div,
    div[data-testid="stHorizontalBlock"] > div > div > div {
        max-width: none !important;
        width: 100% !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }

    /* 确保结果部分的容器使用完整宽度 */
    [data-testid="stVerticalBlock"] > div > div > div > div {
        max-width: none !important;
        width: 100% !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }

    /* 确保结果部分的所有内容使用完整宽度 */
    [data-testid="stVerticalBlock"] > div > div > div > div > div {
        max-width: none !important;
        width: 100% !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }

    /* 确保所有列的内部元素使用完整宽度 */
    .css-1lcbmhc > div {
        max-width: none !important;
        width: 100% !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }

    /* 确保所有行的元素使用完整宽度 */
    .css-12oz5g7 > div {
        max-width: none !important;
        width: 100% !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }

    /* 确保所有流式布局的元素使用完整宽度 */
    .css-164nlkn > div {
        max-width: none !important;
        width: 100% !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }

    /* 确保所有flex容器使用完整宽度 */
    div[style*="display: flex"] {
        max-width: none !important;
        width: 100% !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }

    /* 确保所有flex项使用完整宽度 */
    div[style*="flex: 1"] {
        max-width: none !important;
        width: 100% !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }

    /* 确保所有带有stVerticalBlock类的元素使用完整宽度 */
    .css-1d391kg {
        max-width: none !important;
        width: 100% !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }

    /* 确保所有带有stHorizontalBlock类的元素使用完整宽度 */
    .css-12oz5g7 {
        max-width: none !important;
        width: 100% !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }

    /* 确保所有带有column类的元素使用完整宽度 */
    .css-1lcbmhc {
        max-width: none !important;
        width: 100% !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }

    /* 确保所有带有block-container类的元素使用完整宽度 */
    .css-164nlkn {
        max-width: none !important;
        width: 100% !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }

    /* 确保所有带有main类的元素使用完整宽度 */
    .css-1d391kg {
        max-width: none !important;
        width: 100% !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }

    /* 确保所有带有block-container类的元素使用完整宽度 */
    .css-1d391kg {
        max-width: none !important;
        width: 100% !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }

    /* 确保所有带有stApp类的元素使用完整宽度 */
    .css-1d391kg {
        max-width: none !important;
        width: 100% !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }
    
    /* 确保侧边栏中的语言选择器显示正常 - 合并两个div模块 */
    [data-testid="stSidebar"] .stSelectbox {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 150px !important;
        position: relative !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* 合并语言选择器的容器和文本区域为一个视觉整体 */
    [data-testid="stSidebar"] .stSelectbox div[role="combobox"] {
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        position: relative !important;
        box-sizing: border-box !important;
        background-color: #ffffff !important;
        border: 1px solid #dfe1e5 !important;
        border-radius: 4px !important;
        padding: 8px 12px !important;
        margin: 0 !important;
    }
    
    /* 合并后的文本区域 */
    [data-testid="stSidebar"] .stSelectbox div[role="textbox"] {
        flex: 1 !important;
        padding-right: 40px !important;
        width: calc(100% - 40px) !important;
        box-sizing: border-box !important;
        background-color: transparent !important;
        border: none !important;
        margin: 0 !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* 将下拉按钮集成到合并后的模块中 */
    [data-testid="stSidebar"] .stSelectbox div[role="button"] {
        position: absolute !important;
        right: 8px !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        margin: 0 !important;
        z-index: 1 !important;
        width: 30px !important;
        height: 30px !important;
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* 移除任何可能的分隔线或额外边框 */
    [data-testid="stSidebar"] .stSelectbox > div {
        border: none !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* 确保选择器在交互时保持视觉统一 */
    [data-testid="stSidebar"] .stSelectbox:focus-within div[role="combobox"] {
        border-color: #165DFF !important;
        box-shadow: 0 0 0 2px rgba(22, 93, 255, 0.2) !important;
    }
    
    /* 取消隐藏第一个div模块，并确保其正确布局 */
    [data-testid="stSidebar"] .stSelectbox .st-ak.st-al.st-as.st-cm.st-bg.st-cn.st-bl {
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        height: auto !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
        position: relative !important;
    }
    
    /* 确保目标div模块具有正确的布局以容纳下拉按钮 */
    [data-testid="stSidebar"] .stSelectbox .st-ak.st-al.st-bd.st-be.st-bf.st-as.st-bg.st-bh.st-ar.st-bi.st-bj.st-bk.st-bl {
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        padding-right: 40px !important;
        position: relative !important;
    }
    
    /* 将下拉按钮移动到目标div中 */
    [data-testid="stSidebar"] .stSelectbox .st-ak.st-al.st-bd.st-be.st-bf.st-as.st-bg.st-bh.st-ar.st-bi.st-bj.st-bk.st-bl div[role="button"] {
        position: absolute !important;
        right: 8px !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        margin: 0 !important;
        z-index: 1 !important;
        width: 30px !important;
        height: 30px !important;
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* 确保侧边栏中的所有表单元素有适当的宽度 */
    [data-testid="stSidebar"] .stTextInput,
    [data-testid="stSidebar"] .stTextArea,
    [data-testid="stSidebar"] .stCheckbox,
    [data-testid="stSidebar"] .stButton {
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

# 页面标题
st.title(translations["page_title_display"])

# 侧边栏
with st.sidebar:
    # 语言选择器
    st.markdown("### Language / 语言")
    language_options = {"English": "en", "简体中文": "zh"}
    selected_language_display = [key for key, value in language_options.items() if value == st.session_state["language"]][0]
    selected_language_display = st.selectbox(
        "Select language",
        options=list(language_options.keys()),
        index=list(language_options.values()).index(st.session_state["language"]),
        label_visibility="collapsed"
    )
    
    # 如果语言变化，更新session_state
    if selected_language_display != [key for key, value in language_options.items() if value == st.session_state["language"]][0]:
        st.session_state["language"] = language_options[selected_language_display]
        st.rerun()
    
    # 输入参数部分
    st.markdown("---")
    st.header(translations["sidebar"]["input_parameters"])
    
    # UniProt ID输入
    uniprot_id = st.text_input(
        translations["sidebar"]["uniprot_id"],
        value="P0DTC2",  # SARS-CoV-2 Spike protein example
        help=translations["sidebar"]["uniprot_id_help"])
    
    # 突变列表输入
    mutation_list_str = st.text_area(
        translations["sidebar"]["mutation_list"],
        value="D614G, A222V, T478K",  # Spike protein examples
        help=translations["sidebar"]["mutation_list_help"],
        height=100)
    
    # 高级选项
    st.markdown("---")
    st.subheader(translations["sidebar"]["advanced_options"])
    
    # 计算敏感度的选项
    calculate_sensitivity = st.checkbox(
        translations["sidebar"]["calculate_sensitivity"],
        value=True,
        help=translations["sidebar"]["calculate_sensitivity_help"])
    
    # 清除缓存按钮
    st.markdown("---")
    if st.button(translations["sidebar"]["clear_cache"], type="secondary"):
        clear_cache()
        st.success(translations["sidebar"]["cache_cleared"])

# 主内容区域
st.header(translations["main"]["results"])

# 提交按钮
submit_col, _ = st.columns([1, 3])
with submit_col:
    if st.button(translations["main"]["explain_mutations"], type="primary", width='stretch'):
        if not uniprot_id.strip():
            st.error(translations["main"]["enter_uniprot_id"])
        elif not mutation_list_str.strip():
            st.error(translations["main"]["enter_mutations"])
        else:
            try:
                # 使用加载状态
                with st.spinner(translations["main"]["processing_mutations"]):
                    # 调用解释函数
                    result = explain_mutations(uniprot_id, mutation_list_str)
                
                # 结果表格区域
                st.subheader(translations["main"]["mutation_analysis_results"])
                results_df = result["results_df"]
                
                # 使用卡片布局显示表格
                with st.container():
                    st.dataframe(results_df, width='stretch', height=300)
                    
                    # 下载CSV按钮居中显示
                    download_col, _, _ = st.columns([1, 2, 1])
                    with download_col:
                        csv = results_df.to_csv(index=False)
                        st.download_button(
                            label=translations["main"]["download_csv"],
                            data=csv,
                            file_name=f"{uniprot_id}_mutations.csv",
                            mime="text/csv",
                            width='stretch'
                        )
                
                # 可视化区域
                st.subheader(translations["main"]["sequence_visualization"])
                
                # 1. 序列特征图
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # 获取pLDDT分布
                    plddt_profile = explainer.get_plddt_profile(result["alphafold_data"])
                    
                    # 绘制序列特征图
                    with st.container(border=True):
                        st.write("**Sequence Profile with Mutations**")
                        fig = visualizer.plot_sequence_profile(results_df, plddt_profile)
                        st.plotly_chart(fig, width='stretch')
                
                with col2:
                    # 绘制pLDDT热图（如果有数据）
                    with st.container(border=True):
                        st.write("**AlphaFold pLDDT**")
                        if plddt_profile is not None:
                            plddt_fig = visualizer.plot_plddt_heatmap(plddt_profile)
                            st.plotly_chart(plddt_fig, width='stretch')
                        else:
                            st.info(translations["main"]["plddt_not_available"])
                
                # 2. 3D结构视图
                st.subheader(translations["main"]["structure_3d"])
                
                try:
                    # 创建3D视图
                    with st.container(border=True):
                        view = visualizer.create_3d_structure(uniprot_id, result["mutations"])
                        st.write("**Interactive 3D Structure (Click to rotate/zoom)**")
                        st.py3Dmol(view, width='stretch')
                except Exception as e:
                    st.info(translations["main"]["structure_not_available"])
                
                # 3. 序列信息
                st.subheader(translations["main"]["sequence_information"])
                
                # 显示序列长度
                st.write(translations["main"]["sequence_length"].format(length=len(result['sequence'])))
                
                # 显示带有突变标记的序列
                with st.container(border=True):
                    st.write("**Protein Sequence with Mutations Highlighted**")
                    marked_sequence = explainer.get_sequence_with_mutations(
                        result["sequence"], result["mutations"])
                    
                    # 序列显示（每100个氨基酸换行）
                    sequence_display = ""
                    for i in range(0, len(marked_sequence), 100):
                        chunk = marked_sequence[i:i+100]
                        # 添加位置标记
                        start_pos = i + 1
                        end_pos = min(i + 100, len(result['sequence']))
                        sequence_display += f"**{start_pos}-{end_pos}:** {chunk}\n\n"
                    
                    st.text_area("Protein sequence", sequence_display, height=200, label_visibility="collapsed", width='stretch')
                
                # 检查是否有AlphaFold数据
                if result["alphafold_data"] is None:
                    st.warning(translations["main"]["alphafold_data_not_available"].format(id=uniprot_id))
                    st.info(translations["main"]["results_without_alphafold"])
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    # 检查错误是否来自UniProt API
                    if "uniprot" in str(e).lower():
                        st.error(translations["main"]["uniprot_id_not_found"].format(id=uniprot_id))
                    else:
                        st.error(translations["main"]["alphafold_not_found"].format(id=uniprot_id))
                else:
                    st.error(translations["main"]["api_error"].format(error=e))
            except ValueError as e:
                st.error(translations["main"]["input_error"].format(error=e))
            except Exception as e:
                st.error(translations["main"]["unexpected_error"].format(error=e))
                st.exception(e)

# 页脚信息
st.sidebar.markdown("---")
st.sidebar.subheader(translations["sidebar"]["about"])
st.sidebar.info(
    translations["sidebar"]["about_content"]
)

# 示例部分
st.sidebar.markdown("---")
st.sidebar.subheader(translations["sidebar"]["examples"])
st.sidebar.markdown(
    f"{translations['sidebar']['example_1']}\n" \
    f"{translations['sidebar']['example_1_uniprot']}\n" \
    f"{translations['sidebar']['example_1_mutations']}\n" \
    "\n" \
    f"{translations['sidebar']['example_2']}\n" \
    f"{translations['sidebar']['example_2_uniprot']}\n" \
    f"{translations['sidebar']['example_2_mutations']}\n" \
    "\n" \
    f"{translations['sidebar']['example_3']}\n" \
    f"{translations['sidebar']['example_3_uniprot']}\n" \
    f"{translations['sidebar']['example_3_mutations']}\n" \
    "\n" \
    f"{translations['sidebar']['example_4']}\n" \
    f"{translations['sidebar']['example_4_uniprot']}\n" \
    f"{translations['sidebar']['example_4_mutations']}\n" \
    "\n" \
    f"{translations['sidebar']['example_5']}\n" \
    f"{translations['sidebar']['example_5_uniprot']}\n" \
    f"{translations['sidebar']['example_5_mutations']}\n" \
    "\n" \
    f"{translations['sidebar']['example_6']}\n" \
    f"{translations['sidebar']['example_6_uniprot']}\n" \
    f"{translations['sidebar']['example_6_mutations']}\n"
)
