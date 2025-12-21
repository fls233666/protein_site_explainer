import streamlit as st
import pandas as pd
import numpy as np
import requests.exceptions
from src.explain import explain_mutations, explainer
from src.viz import visualizer
from src.cache import clear_cache

# 设置页面配置
st.set_page_config(
    page_title="Protein Site Explainer",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 页面标题
st.title("🧬 Protein Site Explainer")

# 侧边栏
with st.sidebar:
    st.header("Input Parameters")
    
    # UniProt ID输入
    uniprot_id = st.text_input(
        "UniProt ID",
        value="P0DTC2",  # SARS-CoV-2 Spike protein example
        help="Enter a valid UniProt ID (e.g., P0DTC2 for SARS-CoV-2 Spike)")
    
    # 突变列表输入
    mutation_list_str = st.text_area(
        "Mutation List",
        value="D614G, A222V, T478K",  # Spike protein examples
        help="Enter mutations in A123T format, separated by commas or spaces")
    
    # 高级选项
    st.subheader("Advanced Options")
    
    # 计算敏感度的选项
    calculate_sensitivity = st.checkbox(
        "Calculate Site Sensitivity",
        value=True,
        help="Calculate mean sensitivity for all non-wildtype amino acids")
    
    # 清除缓存按钮
    if st.button("Clear Cache"):
        clear_cache()
        st.success("Cache cleared successfully!")

# 主内容区域
st.header("Results")

# 提交按钮
if st.button("Explain Mutations"):
    if not uniprot_id.strip():
        st.error("Please enter a valid UniProt ID")
    elif not mutation_list_str.strip():
        st.error("Please enter at least one mutation")
    else:
        try:
            # 使用加载状态
            with st.spinner("Processing mutations..."):
                # 调用解释函数
                result = explain_mutations(uniprot_id, mutation_list_str)
                
            # 显示结果表格
            st.subheader("Mutation Analysis Results")
            results_df = result["results_df"]
            st.dataframe(results_df, use_container_width=True)
            
            # 下载CSV功能
            csv = results_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"{uniprot_id}_mutations.csv",
                mime="text/csv"
            )
            
            # 可视化区域
            st.subheader("Sequence Visualization")
            
            # 1. 序列特征图
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # 获取pLDDT分布
                plddt_profile = explainer.get_plddt_profile(result["alphafold_data"])
                
                # 绘制序列特征图
                fig = visualizer.plot_sequence_profile(results_df, plddt_profile)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # 绘制pLDDT热图
                plddt_fig = visualizer.plot_plddt_heatmap(plddt_profile)
                st.plotly_chart(plddt_fig, use_container_width=True)
            
            # 2. 3D结构视图
            st.subheader("3D Structure View")
            
            # 创建3D视图
            view = visualizer.create_3d_structure(uniprot_id, result["mutations"])
            
            # 在Streamlit中显示3D视图
            st.py3Dmol(view)
            
            # 3. 序列信息
            st.subheader("Sequence Information")
            
            # 显示序列长度
            st.write(f"**Sequence Length:** {len(result['sequence'])} amino acids")
            
            # 显示带有突变标记的序列
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
            
            st.text(sequence_display)
            
        except ValueError as e:
            st.error(f"Input error: {e}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                st.error(f"UniProt ID not found: {uniprot_id}")
            else:
                st.error(f"API error: {e}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            st.exception(e)

# 页脚信息
st.sidebar.markdown("---")
st.sidebar.subheader("About")
st.sidebar.info(
    "Protein Site Explainer analyzes mutations using:\n" \
    "- ESM-2 language model for LLR calculation\n" \
    "- AlphaFold for structural confidence (pLDDT)\n" \
    "- UniProt features mapping\n" \
    "- 3D structure visualization with py3Dmol"
)

# 示例部分
st.sidebar.markdown("---")
st.sidebar.subheader("Examples")
st.sidebar.markdown(
    "**Example 1:** SARS-CoV-2 Spike protein\n" \
    "- UniProt ID: P0DTC2\n" \
    "- Mutations: D614G, A222V, T478K\n" \
    "\n" \
    "**Example 2:** Human p53\n" \
    "- UniProt ID: P04637\n" \
    "- Mutations: R175H, R248Q, R273H"
)
