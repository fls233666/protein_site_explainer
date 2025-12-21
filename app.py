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

# 初始化session_state
if "language" not in st.session_state:
    st.session_state["language"] = "en"  # 默认英语
if "result" not in st.session_state:
    st.session_state["result"] = None  # 存储计算结果
if "input_params" not in st.session_state:
    st.session_state["input_params"] = {}  # 存储输入参数

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
    /* 确保内容区域使用完整宽度 */
    [data-testid="stBlockContainer"] {
        max-width: 100% !important;
        width: 100% !important;
        padding: 2rem;
    }
    
    /* 确保表格和图表使用完整宽度 */
    .stDataFrame, .stPlotlyChart, .stPy3Dmol {
        width: 100% !important;
    }
    
    /* 确保侧边栏中的所有表单元素有适当的宽度 */
    [data-testid="stSidebar"] .stTextInput,
    [data-testid="stSidebar"] .stTextArea,
    [data-testid="stSidebar"] .stCheckbox,
    [data-testid="stSidebar"] .stButton,
    [data-testid="stSidebar"] .stSelectbox {
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

# 提交按钮（居中显示）
_, submit_col, _ = st.columns([1, 2, 1])
with submit_col:
    clicked = st.button(translations["main"]["explain_mutations"], type="primary", use_container_width=True)

# 结果渲染（在列作用域外）
if clicked or "last_result" in st.session_state:
    # 检查输入参数
    if clicked:
        if not uniprot_id.strip():
            st.error(translations["main"]["enter_uniprot_id"])
        elif not mutation_list_str.strip():
            st.error(translations["main"]["enter_mutations"])
        else:
            try:
                # 使用加载状态
                with st.spinner(translations["main"]["processing_mutations"]):
                    # 调用解释函数
                    result = explain_mutations(uniprot_id, mutation_list_str, calculate_sensitivity)
                
                # 保存结果到session_state
                st.session_state["last_result"] = result
                st.session_state["input_params"] = {
                    "uniprot_id": uniprot_id,
                    "mutation_list_str": mutation_list_str,
                    "calculate_sensitivity": calculate_sensitivity
                }
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

    # 使用上次结果或新计算结果
    if "last_result" in st.session_state:
        result = st.session_state["last_result"]
        uniprot_id = st.session_state["input_params"]["uniprot_id"]
        
        # 使用标签页组织内容
        tabs = st.tabs([
            translations["main"]["mutation_analysis_results"],
            translations["main"]["sequence_visualization"],
            translations["main"]["structure_3d"],
            translations["main"]["sequence_information"]
        ])
        
        # 1. 结果表格标签页
        with tabs[0]:
            results_df = result["results_df"]
            
            # 使用卡片布局显示表格
            with st.container():
                st.dataframe(results_df, use_container_width=True, height=300)
                
                # 下载CSV按钮居中显示
                _, download_col, _ = st.columns([1, 2, 1])
                with download_col:
                    csv = results_df.to_csv(index=False)
                    st.download_button(
                        label=translations["main"]["download_csv"],
                        data=csv,
                        file_name=f"{uniprot_id}_mutations.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
        
        # 2. 序列可视化标签页
        with tabs[1]:
            # 获取pLDDT分布
            plddt_profile = explainer.get_plddt_profile(result["alphafold_data"])
            
            # 1. 序列特征图
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # 绘制序列特征图
                with st.container(border=True):
                    st.write(translations["main"]["sequence_profile_with_mutations"])
                    fig = visualizer.plot_sequence_profile(results_df, plddt_profile)
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # 绘制pLDDT热图（如果有数据）
                with st.container(border=True):
                    st.write(translations["main"]["alphafold_plddt"])
                    if plddt_profile is not None:
                        plddt_fig = visualizer.plot_plddt_heatmap(plddt_profile)
                        st.plotly_chart(plddt_fig, use_container_width=True)
                    else:
                        st.info(translations["main"]["plddt_not_available"])
        
        # 3. 3D结构视图标签页
        with tabs[2]:
            try:
                # 创建3D视图
                with st.container(border=True):
                    view = visualizer.create_3d_structure(uniprot_id, result["mutations"])
                    st.write(translations["main"]["interactive_3d_structure"])
                    st.py3Dmol(view, use_container_width=True)
            except Exception as e:
                st.info(translations["main"]["structure_not_available"])
        
        # 4. 序列信息标签页
        with tabs[3]:
            # 显示序列长度
            st.write(translations["main"]["sequence_length"].format(length=len(result['sequence'])))
            
            # 显示带有突变标记的序列
            with st.container(border=True):
                st.write(translations["main"]["protein_sequence_with_mutations"])
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
                
                st.text_area(translations["main"]["protein_sequence"], sequence_display, height=200, label_visibility="collapsed")
        
        # 检查是否有AlphaFold数据
        if result["alphafold_data"] is None:
            st.warning(translations["main"]["alphafold_data_not_available"].format(id=uniprot_id))
            st.info(translations["main"]["results_without_alphafold"])

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
