import pandas as pd
import os
from .alphafold import download_pdb

class Visualizer:
    """蛋白质可视化类"""
    
    def plot_sequence_profile(self, results_df, plddt_profile=None):
        """绘制序列特征分布图
        
        Args:
            results_df: 包含突变结果的数据框
            plddt_profile: pLDDT分布数据框
            
        Returns:
            plotly.Figure: 序列特征分布图
        """
        import plotly.graph_objects as go
        fig = go.Figure()
        
        # 设置x轴范围
        x_range = [1, max(results_df["Position"])]
        if plddt_profile is not None:
            x_range = [1, max(x_range[1], max(plddt_profile["Position"]))]
        
        # 1. 绘制ESM LLR
        fig.add_trace(go.Scatter(
            x=results_df["Position"],
            y=results_df["ESM_LLR"],
            mode="markers",
            name="ESM LLR",
            marker=dict(size=10, color="blue"),
            text=results_df["Mutation"],
            textposition="top center",
            hovertemplate="Mutation: %{text}<br>Position: %{x}<br>ESM LLR: %{y:.2f}<extra></extra>"
        ))
        
        # 2. 绘制位点敏感度
        fig.add_trace(go.Scatter(
            x=results_df["Position"],
            y=results_df["Site_Sensitivity"],
            mode="markers",
            name="Site Sensitivity",
            marker=dict(size=10, color="green", symbol="triangle-up"),
            text=results_df["Mutation"],
            hovertemplate="Mutation: %{text}<br>Position: %{x}<br>Site Sensitivity: %{y:.2f}<extra></extra>"
        ))
        
        # 3. 绘制pLDDT曲线
        if plddt_profile is not None:
            fig.add_trace(go.Scatter(
                x=plddt_profile["Position"],
                y=plddt_profile["pLDDT"],
                mode="lines",
                name="AlphaFold pLDDT",
                line=dict(color="red", width=2),
                yaxis="y2"
            ))
        
        # 布局设置
        fig.update_layout(
            xaxis=dict(
                title="Amino Acid Position",
                range=x_range,
                showgrid=True
            ),
            yaxis=dict(
                title="ESM LLR / Site Sensitivity",
                showgrid=True
            ),
            yaxis2=dict(
                title="AlphaFold pLDDT",
                overlaying="y",
                side="right",
                range=[0, 100],
                showgrid=False
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode="x unified",
            height=600,
            margin=dict(t=50)
        )
        
        return fig
    
    def create_3d_structure(self, uniprot_id, mutations, structure_file=None, width=800, height=600):
        """创建3D结构视图
        
        Args:
            uniprot_id: UniProt ID
            mutations: Mutation 对象列表
            structure_file: 可选，已下载的结构文件路径，避免重复下载
            width: 视图宽度
            height: 视图高度
            
        Returns:
            py3Dmol.view: 3D结构视图
        """
        # 下载PDB文件或使用提供的结构文件
        pdb_file = structure_file or download_pdb(uniprot_id)
        
        # 检查是否成功下载到文件
        if pdb_file is None:
            # 返回None而不是抛出异常，让UI层处理这种情况
            return None
        
        # 确定文件格式
        file_extension = os.path.splitext(pdb_file)[1].lower()
        if file_extension in ['.cif', '.mmcif']:
            file_format = 'mmcif'
        else:
            file_format = 'pdb'

        # 创建3D视图
        import py3Dmol
        view = py3Dmol.view(width=width, height=height)
        view.addModel(open(pdb_file, 'r').read(), file_format)
        
        # 设置样式 - 使用B-factor作为pLDDT的来源
        view.setStyle({
            "cartoon": {
                "color": "spectrum",
                "colorscheme": {"prop": "b", "gradient": "redyellowblue", "min": 0, "max": 100}
            }
        })
        
        # 高亮突变位置
        mutation_positions = [mutation.position for mutation in mutations]
        
        for position in mutation_positions:
            # 高亮突变位置的侧链
            view.addStyle({
                "resi": str(position)
            }, {
                "stick": {
                    "color": "red",
                    "radius": 0.3
                },
                "sphere": {
                    "color": "red",
                    "opacity": 0.5,
                    "radius": 0.8
                }
            })
        
        # 添加标签
        for mutation in mutations:
            view.addLabel(
                f"{mutation}",
                {
                    "position": {
                        "resi": mutation.position,
                        "chain": "A"
                    },
                    "fontSize": 14,
                    "backgroundColor": "red",
                    "textColor": "white",
                    "opacity": 0.9
                }
            )
        
        # 设置视图
        view.zoomTo({
            "resi": mutation_positions
        })
        view.rotate(90, [1, 0, 0])
        
        return view
    
    def build_fullpage_3d_html(self, view, title: str) -> str:
        """构建完整的3D视图HTML页面
        
        Args:
            view: py3Dmol.view对象
            title: 页面标题
            
        Returns:
            str: 完整的HTML文档
        """
        # 确保py3Dmol已导入（虽然view已在create_3d_structure中创建，但为了保险添加）
        import py3Dmol
        fragment = view._make_html()
        return f"""<!doctype html>
<html lang='en'>
<head>
    <meta charset='utf-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>{title}</title>
</head>
<body>
    <h1 style='text-align: center; margin: 20px 0;'>{title}</h1>
    <div style='display: flex; justify-content: center;'>
        {fragment}
    </div>
</body>
</html>"""
    
    def plot_plddt_heatmap(self, plddt_profile):
        """绘制pLDDT热图
        
        Args:
            plddt_profile: pLDDT分布数据框
            
        Returns:
            plotly.Figure: pLDDT热图
        """
        import plotly.graph_objects as go
        fig = go.Figure(data=go.Heatmap(
            z=[plddt_profile["pLDDT"]],
            x=plddt_profile["Position"],
            y=["pLDDT"],
            colorscale="RdYlGn",
            zmin=0,
            zmax=100,
            colorbar=dict(title="pLDDT Score")
        ))
        
        fig.update_layout(
            xaxis_title="Amino Acid Position",
            yaxis_title="Feature",
            height=200,
            margin=dict(t=30)
        )
        
        return fig

# 创建全局可视化器实例
visualizer = Visualizer()
