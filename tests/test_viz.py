import pytest
import os
import tempfile
from unittest import mock
from src.viz import visualizer
from src.alphafold import download_pdb
import py3Dmol

# 模拟一个简单的PDB文件内容
sample_pdb_content = """ATOM      1  N   ALA A   1      10.000   0.000   0.000  1.00 90.00           N  
ATOM      2  CA  ALA A   1      10.500   0.000   0.000  1.00 90.00           C  
ATOM      3  C   ALA A   1      11.000   0.000   0.000  1.00 90.00           C  
ATOM      4  O   ALA A   1      11.500   0.000   0.000  1.00 90.00           O  
ATOM      5  CB  ALA A   1      10.500   1.000   0.000  1.00 90.00           C  
ATOM      6  N   ALA A   2      12.000   0.000   0.000  1.00 90.00           N  
ATOM      7  CA  ALA A   2      12.500   0.000   0.000  1.00 90.00           C  
ATOM      8  C   ALA A   2      13.000   0.000   0.000  1.00 90.00           C  
ATOM      9  O   ALA A   2      13.500   0.000   0.000  1.00 90.00           O  
ATOM     10  CB  ALA A   2      12.500   1.000   0.000  1.00 90.00           C  
END
"""

# 模拟一个简单的CIF文件内容
sample_cif_content = """data_P0DTC2
#
_entry.id   P0DTC2
#
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_entity_id
_atom_site.label_seq_id
_atom_site.pdbx_PDB_ins_code
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.occupancy
_atom_site.B_iso_or_equiv
_atom_site.pdbx_formal_charge
_atom_site.auth_seq_id
_atom_site.auth_comp_id
_atom_site.auth_asym_id
_atom_site.auth_atom_id
_atom_site.pdbx_PDB_model_num
ATOM      1  N   N   . ALA A 1   1       ? 10.000 0.000 0.000 1.0 90.0 ? 1   ALA A N   1  
ATOM      2  C   CA  . ALA A 1   1       ? 10.500 0.000 0.000 1.0 90.0 ? 1   ALA A CA  1  
ATOM      3  C   C   . ALA A 1   1       ? 11.000 0.000 0.000 1.0 90.0 ? 1   ALA A C   1  
ATOM      4  O   O   . ALA A 1   1       ? 11.500 0.000 0.000 1.0 90.0 ? 1   ALA A O   1  
ATOM      5  C   CB  . ALA A 1   1       ? 10.500 1.000 0.000 1.0 90.0 ? 1   ALA A CB  1  
#
loop_
_pdbx_poly_seq_scheme.asym_id
_pdbx_poly_seq_scheme.entity_id
_pdbx_poly_seq_scheme.mon_id
_pdbx_poly_seq_scheme.ndb_seq_num
_pdbx_poly_seq_scheme.pdb_seq_num
_pdbx_poly_seq_scheme.auth_seq_num
_pdbx_poly_seq_scheme.pdb_mon_id
_pdbx_poly_seq_scheme.auth_mon_id
_pdbx_poly_seq_scheme.pdb_strand_id
_pdbx_poly_seq_scheme.pdb_ins_code
A 1 ALA 1   1   1   ALA ALA A .
#
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_entity_id
_atom_site.label_seq_id
_atom_site.pdbx_PDB_ins_code
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.occupancy
_atom_site.B_iso_or_equiv
_atom_site.pdbx_formal_charge
_atom_site.auth_seq_id
_atom_site.auth_comp_id
_atom_site.auth_asym_id
_atom_site.auth_atom_id
_atom_site.pdbx_PDB_model_num
ATOM      6  N   N   . ALA A 1   2       ? 12.000 0.000 0.000 1.0 90.0 ? 2   ALA A N   1  
ATOM      7  C   CA  . ALA A 1   2       ? 12.500 0.000 0.000 1.0 90.0 ? 2   ALA A CA  1  
ATOM      8  C   C   . ALA A 1   2       ? 13.000 0.000 0.000 1.0 90.0 ? 2   ALA A C   1  
ATOM      9  O   O   . ALA A 1   2       ? 13.500 0.000 0.000 1.0 90.0 ? 2   ALA A O   1  
ATOM     10  C   CB  . ALA A 1   2       ? 12.500 1.000 0.000 1.0 90.0 ? 2   ALA A CB  1  
#
loop_
_pdbx_poly_seq_scheme.asym_id
_pdbx_poly_seq_scheme.entity_id
_pdbx_poly_seq_scheme.mon_id
_pdbx_poly_seq_scheme.ndb_seq_num
_pdbx_poly_seq_scheme.pdb_seq_num
_pdbx_poly_seq_scheme.auth_seq_num
_pdbx_poly_seq_scheme.pdb_mon_id
_pdbx_poly_seq_scheme.auth_mon_id
_pdbx_poly_seq_scheme.pdb_strand_id
_pdbx_poly_seq_scheme.pdb_ins_code
A 1 ALA 2   2   2   ALA ALA A .
"""

# 模拟Mutation类
class MockMutation:
    def __init__(self, position):
        self.position = position
    def __str__(self):
        return f"A{self.position}V"


def test_create_3d_structure_pdb():
    """测试create_3d_structure函数处理PDB格式文件"""
    # 创建临时PDB文件
    with tempfile.NamedTemporaryFile(suffix=".pdb", delete=False, mode='w') as tmp_pdb:
        tmp_pdb.write(sample_pdb_content)
        tmp_pdb_path = tmp_pdb.name
    
    try:
        # 模拟download_pdb返回临时PDB文件路径
        with mock.patch('src.viz.download_pdb', return_value=tmp_pdb_path):
            # 创建模拟突变列表
            mutations = [MockMutation(1), MockMutation(2)]
            
            # 调用create_3d_structure函数
            view = visualizer.create_3d_structure("P0DTC2", mutations)
            
            # 验证返回值类型
            assert isinstance(view, py3Dmol.view)
            
            # 验证HTML生成
            html = view._make_html()
            assert html is not None
            assert isinstance(html, str)
            assert len(html) > 0
            
    finally:
        # 清理临时文件
        if os.path.exists(tmp_pdb_path):
            os.unlink(tmp_pdb_path)


def test_create_3d_structure_cif():
    """测试create_3d_structure函数处理CIF格式文件"""
    # 创建临时CIF文件
    with tempfile.NamedTemporaryFile(suffix=".cif", delete=False, mode='w') as tmp_cif:
        tmp_cif.write(sample_cif_content)
        tmp_cif_path = tmp_cif.name
    
    try:
        # 模拟download_pdb返回临时CIF文件路径
        with mock.patch('src.viz.download_pdb', return_value=tmp_cif_path):
            # 创建模拟突变列表
            mutations = [MockMutation(1), MockMutation(2)]
            
            # 调用create_3d_structure函数
            view = visualizer.create_3d_structure("P0DTC2", mutations)
            
            # 验证返回值类型
            assert isinstance(view, py3Dmol.view)
            
            # 验证HTML生成
            html = view._make_html()
            assert html is not None
            assert isinstance(html, str)
            assert len(html) > 0
            
    finally:
        # 清理临时文件
        if os.path.exists(tmp_cif_path):
            os.unlink(tmp_cif_path)


def test_create_3d_structure_mmcif():
    """测试create_3d_structure函数处理MMCIF格式文件"""
    # 创建临时MMCIF文件
    with tempfile.NamedTemporaryFile(suffix=".mmcif", delete=False, mode='w') as tmp_mmcif:
        tmp_mmcif.write(sample_cif_content)
        tmp_mmcif_path = tmp_mmcif.name
    
    try:
        # 模拟download_pdb返回临时MMCIF文件路径
        with mock.patch('src.viz.download_pdb', return_value=tmp_mmcif_path):
            # 创建模拟突变列表
            mutations = [MockMutation(1), MockMutation(2)]
            
            # 调用create_3d_structure函数
            view = visualizer.create_3d_structure("P0DTC2", mutations)
            
            # 验证返回值类型
            assert isinstance(view, py3Dmol.view)
            
            # 验证HTML生成
            html = view._make_html()
            assert html is not None
            assert isinstance(html, str)
            assert len(html) > 0
            
    finally:
        # 清理临时文件
        if os.path.exists(tmp_mmcif_path):
            os.unlink(tmp_mmcif_path)


def test_create_3d_structure_empty_mutations():
    """测试create_3d_structure函数处理空突变列表的情况"""
    # 创建临时PDB文件
    with tempfile.NamedTemporaryFile(suffix=".pdb", delete=False, mode='w') as tmp_pdb:
        tmp_pdb.write(sample_pdb_content)
        tmp_pdb_path = tmp_pdb.name
    
    try:
        # 模拟download_pdb返回临时PDB文件路径
        with mock.patch('src.viz.download_pdb', return_value=tmp_pdb_path):
            # 调用create_3d_structure函数，传入空突变列表
            view = visualizer.create_3d_structure("P0DTC2", [])
            
            # 验证返回值类型
            assert isinstance(view, py3Dmol.view)
            
            # 验证HTML生成
            html = view._make_html()
            assert html is not None
            assert isinstance(html, str)
            assert len(html) > 0
            
    finally:
        # 清理临时文件
        if os.path.exists(tmp_pdb_path):
            os.unlink(tmp_pdb_path)


def test_create_3d_structure_with_structure_file():
    """测试create_3d_structure函数使用提供的structure_file参数"""
    # 创建临时PDB文件
    with tempfile.NamedTemporaryFile(suffix=".pdb", delete=False, mode='w') as tmp_pdb:
        tmp_pdb.write(sample_pdb_content)
        tmp_pdb_path = tmp_pdb.name
    
    try:
        # 创建模拟突变列表
        mutations = [MockMutation(1), MockMutation(2)]
        
        # 使用mock来验证download_pdb不会被调用
        with mock.patch('src.viz.download_pdb') as mock_download_pdb:
            # 调用create_3d_structure函数，传入structure_file参数
            view = visualizer.create_3d_structure("P0DTC2", mutations, structure_file=tmp_pdb_path)
            
            # 验证download_pdb没有被调用
            mock_download_pdb.assert_not_called()
            
            # 验证返回值类型
            assert isinstance(view, py3Dmol.view)
            
            # 验证HTML生成
            html = view._make_html()
            assert html is not None
            assert isinstance(html, str)
            assert len(html) > 0
            
    finally:
        # 清理临时文件
        if os.path.exists(tmp_pdb_path):
            os.unlink(tmp_pdb_path)


def test_build_fullpage_3d_html():
    """测试build_fullpage_3d_html函数"""
    # 创建临时PDB文件
    with tempfile.NamedTemporaryFile(suffix=".pdb", delete=False, mode='w') as tmp_pdb:
        tmp_pdb.write(sample_pdb_content)
        tmp_pdb_path = tmp_pdb.name
    
    try:
        # 模拟download_pdb返回临时PDB文件路径
        with mock.patch('src.viz.download_pdb', return_value=tmp_pdb_path):
            # 创建模拟突变列表
            mutations = [MockMutation(1)]
            
            # 调用create_3d_structure函数
            view = visualizer.create_3d_structure("P0DTC2", mutations)
            
            # 调用build_fullpage_3d_html函数
            title = "Test 3D Structure"
            full_html = visualizer.build_fullpage_3d_html(view, title)
            
            # 验证返回值类型
            assert isinstance(full_html, str)
            assert len(full_html) > 0
            
            # 验证HTML结构完整性
            assert "<!doctype html>" in full_html
            assert "<html" in full_html  # 检查HTML标签的开始部分，不关心是否包含属性
            assert "<head>" in full_html
            assert "<meta charset='utf-8'>" in full_html
            assert f"<title>{title}</title>" in full_html
            assert "<body>" in full_html
            assert f"<h1 style='text-align: center; margin: 20px 0;'>{title}</h1>" in full_html
            
            # 验证3D视图内容包含在HTML中
            # 不直接比较整个fragment，因为每次调用都会生成随机ID
            # 而是检查一些关键部分
            assert "3dmolviewer_" in full_html  # 检查包含3Dmol viewer的div
            assert "$3Dmol.createViewer" in full_html  # 检查JavaScript创建viewer的代码
            assert "addModel" in full_html  # 检查添加模型的代码
            assert "setStyle" in full_html  # 检查设置样式的代码
            
    finally:
        # 清理临时文件
        if os.path.exists(tmp_pdb_path):
            os.unlink(tmp_pdb_path)
