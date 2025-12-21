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

# 页面标题
st.title(translations["page_title_display"])

# 侧边栏
with st.sidebar:
    # 语言选择器
    st.markdown("### Language / 语言")
    language_options = {"English": "en", "简体中文": "zh"}
    selected_language_display = [key for key, value in language_options.items() if value == st.session_state["language"]][0]
    selected_language_display = st.selectbox(
        "",
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
    if st.button(translations["main"]["explain_mutations"], type="primary", use_container_width=True):
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
                            use_container_width=True
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
                        st.py3Dmol(view)
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
                    
                    st.text_area("", sequence_display, height=200, label_visibility="collapsed")
                
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
    f"{translations['sidebar']['example_2_mutations']}\n"
)
