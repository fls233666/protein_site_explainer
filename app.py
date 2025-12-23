import streamlit as st
import pandas as pd
import numpy as np
import requests.exceptions
import json
import os
from src.explain import explain_mutations, explainer
from src.viz import visualizer
from src.cache import clear_cache
from src.sequence_view import render_sequence_html, apply_mutations, generate_fasta, merge_windows
from src.parsing import Mutation
from stmol import showmol

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
    
    /* 蛋白质序列显示样式 */
    .seq-view pre {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        font-size: 12px;
        line-height: 1.35;
        white-space: pre-wrap;
        word-wrap: break-word;
        margin: 0;
    }
    
    .seq-view .mut {
        background-color: #ffe08a;
        border: 1px solid #d4a017;
        border-radius: 3px;
        padding: 0 1px;
        cursor: help;
    }
    
    /* 行首标记样式 */
    .seq-view strong {
        color: #666;
        font-weight: bold;
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
                # 使用getattr安全地获取status_code，避免e.response为None导致的二次异常
                status_code = getattr(e.response, "status_code", None)
                if status_code == 404:
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
            # 添加debug开关
            debug_mode = st.checkbox(translations["main"]["debug_mode"], value=False)
            
            try:
                # 创建3D视图
                with st.container(border=True):
                    view = visualizer.create_3d_structure(uniprot_id, result["mutations"])
                    
                    if view is None:
                        # 如果没有3D结构可用，显示友好提示
                        st.write(translations["main"]["no_structure_available"])
                        st.info(translations["main"]["alphaFold_404"].format(id=uniprot_id))
                        st.info(translations["main"]["local_file_option"])
                        
                        # debug模式下显示额外信息
                        if debug_mode:
                            st.markdown(f"**Debug Info:**")
                            st.markdown(f"- UniProt ID: {uniprot_id}")
                            st.markdown(f"- Mutation List: {result['mutations']}")
                            st.markdown(f"- 3D View Object: None")
                    else:
                        # 如果有3D结构，正常显示
                        st.write(translations["main"]["interactive_3d_structure"])
                        showmol(view, height=600, width=800)
                        
                        # debug模式下显示额外信息
                        if debug_mode:
                            st.markdown(f"**Debug Info:**")
                            st.markdown(f"- UniProt ID: {uniprot_id}")
                            st.markdown(f"- Mutation List: {result['mutations']}")
                            st.markdown(f"- 3D View Object Type: {type(view)}")
            except Exception as e:
                if debug_mode:
                    st.error(translations["main"]["structure_error_debug"])
                    st.exception(e)
                else:
                    st.info(translations["main"]["structure_not_available"])
                    st.info(translations["main"]["enable_debug_suggestion"])
        
        # 4. 序列信息标签页
        with tabs[3]:
            # 显示序列长度
            st.write(translations["main"]["sequence_length"].format(length=len(result['sequence'])))
            
            # 序列显示选项控制
            col1, col2 = st.columns([2, 3])
            
            with col1:
                # 视图模式选项
                view_mode = st.radio(
                    translations["main"]["view_mode"],
                    [translations["main"]["wt_sequence"], translations["main"]["mut_sequence"], translations["main"]["both_sequences"]],
                    index=0
                )
                
                # 行长度选项
                line_length = st.slider(
                    translations["main"]["line_length"],
                    min_value=40,
                    max_value=120,
                    value=60,
                    step=5
                )
                
                # 分组显示选项
                group_by_10 = st.checkbox(
                    translations["main"]["group_by_10"],
                    value=True
                )
                
                # 突变窗口选项
                show_window = st.checkbox(
                    translations["main"]["show_window"],
                    value=False
                )
                
                if show_window:
                    window_size = st.slider(
                        translations["main"]["window_size"],
                        min_value=10,
                        max_value=100,
                        value=30,
                        step=5
                    )
                else:
                    window_size = 30
                
                # 计算突变窗口
                mutation_positions = [m.position for m in result["mutations"]]
                windows = [(pos - window_size, pos + window_size) for pos in mutation_positions]
                
                if windows:
                    merged_windows = merge_windows(windows, gap=window_size//2)
                    # 确保窗口不超出序列范围
                    merged_windows = [(max(1, w[0]), min(len(result["sequence"]), w[1])) for w in merged_windows]
                else:
                    merged_windows = None
            
            # 显示序列
            with st.container(border=True):
                st.write(translations["main"]["protein_sequence_with_mutations"])
                
                if view_mode == translations["main"]["wt_sequence"] or view_mode == translations["main"]["both_sequences"]:
                    if view_mode == translations["main"]["both_sequences"]:
                        st.subheader(translations["main"]["wt_sequence"])
                    
                    # 渲染野生型序列
                    for window in merged_windows if show_window and merged_windows else [None]:
                        html = render_sequence_html(
                            result["sequence"],
                            result["mutations"],
                            line_length=line_length,
                            group=10 if group_by_10 else 0,
                            show_ruler=True,
                            window=window,
                            mode="wt"
                        )
                        st.markdown(html, unsafe_allow_html=True)
                
                if view_mode == translations["main"]["mut_sequence"] or view_mode == translations["main"]["both_sequences"]:
                    if view_mode == translations["main"]["both_sequences"]:
                        st.subheader(translations["main"]["mut_sequence"])
                    
                    # 渲染突变后序列
                    for window in merged_windows if show_window and merged_windows else [None]:
                        html = render_sequence_html(
                            result["sequence"],
                            result["mutations"],
                            line_length=line_length,
                            group=10 if group_by_10 else 0,
                            show_ruler=True,
                            window=window,
                            mode="mut"
                        )
                        st.markdown(html, unsafe_allow_html=True)
            
            # FASTA下载按钮
            col1, col2 = st.columns(2)
            
            with col1:
                # 生成野生型FASTA
                wt_fasta = generate_fasta(result["sequence"], result["uniprot_id"], result["mutations"], mode="wt")
                st.download_button(
                    label=translations["main"]["download_wt_fasta"],
                    data=wt_fasta,
                    file_name=f"{result['uniprot_id']}_wt.fasta",
                    mime="text/fasta"
                )
            
            with col2:
                # 生成突变后FASTA
                mut_fasta = generate_fasta(result["sequence"], result["uniprot_id"], result["mutations"], mode="mut")
                st.download_button(
                    label=translations["main"]["download_mut_fasta"],
                    data=mut_fasta,
                    file_name=f"{result['uniprot_id']}_mut.fasta",
                    mime="text/fasta"
                )
        
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
