import plotly.graph_objects as go
import py3Dmol
import pandas as pd
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
        fig = go.Figure()
        
        # 设置x轴范围
        x_range = [1, max(results_df["Position"])]
        if plddt_profile is not None:
            x_range = [1, max(x_range[1], max(plddt_profile["Position"]))]
        
        # 1. 绘制ESM LLR
        fig.add_trace(go.Scatter(
            x=results_df["Position"],
            y=results_df["ESM_LLR"],
            mode="markers+text",
            name="ESM LLR",
            marker=dict(size=10, color="blue"),
            text=results_df["Mutation"],
            textposition="top center"
        ))
        
        # 2. 绘制位点敏感度
        fig.add_trace(go.Scatter(
            x=results_df["Position"],
            y=results_df["Site_Sensitivity"],
            mode="markers",
            name="Site Sensitivity",
            marker=dict(size=10, color="green", symbol="triangle-up")
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
            title="Protein Sequence Features",
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
            height=600
        )
        
        return fig
    
    def create_3d_structure(self, uniprot_id, mutations, width=800, height=600):
        """创建3D结构视图
        
        Args:
            uniprot_id: UniProt ID
            mutations: Mutation 对象列表
            width: 视图宽度
            height: 视图高度
            
        Returns:
            py3Dmol.view: 3D结构视图
        """
        # 下载PDB文件
        pdb_file = download_pdb(uniprot_id)
        
        # 创建3D视图
        view = py3Dmol.view(width=width, height=height)
        view.addModel(open(pdb_file, 'r').read(), 'pdb')
        
        # 设置样式
        view.setStyle({
            "cartoon": {
                "color": "spectrum",
                "colorscheme": "pLDDT"
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
    
    def plot_plddt_heatmap(self, plddt_profile):
        """绘制pLDDT热图
        
        Args:
            plddt_profile: pLDDT分布数据框
            
        Returns:
            plotly.Figure: pLDDT热图
        """
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
            title="AlphaFold pLDDT Score Distribution",
            xaxis_title="Amino Acid Position",
            yaxis_title="Feature",
            height=200
        )
        
        return fig

# 创建全局可视化器实例
visualizer = Visualizer()
