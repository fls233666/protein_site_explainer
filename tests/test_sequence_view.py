import pytest
from src.sequence_view import apply_mutations, render_sequence_html, merge_windows, generate_fasta
from src.parsing import Mutation


def test_apply_mutations():
    """测试apply_mutations函数的正确性"""
    # 测试基本突变应用
    sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    mutations = [Mutation("A", 1, "X"), Mutation("Z", 26, "Y")]
    result = apply_mutations(sequence, mutations)
    assert result == "XBCDEFGHIJKLMNOPQRSTUVWXYY"
    
    # 测试同一位置的多个突变（应保留最后一个）
    mutations = [Mutation("A", 1, "X"), Mutation("X", 1, "Y"), Mutation("Y", 1, "Z")]
    result = apply_mutations(sequence, mutations)
    assert result == "ZBCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    # 测试边界情况（位置为1和序列长度）
    mutations = [Mutation("A", 1, "X"), Mutation("Z", 26, "Y")]
    result = apply_mutations(sequence, mutations)
    assert result[0] == "X"
    assert result[-1] == "Y"
    
    # 测试超出范围的突变（应被忽略）
    mutations = [Mutation("A", 0, "X"), Mutation("Z", 27, "Y")]
    result = apply_mutations(sequence, mutations)
    assert result == sequence


def test_render_sequence_html_wt_mode():
    """测试render_sequence_html在wt模式下的功能"""
    sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    mutations = [Mutation("A", 1, "X"), Mutation("Z", 26, "Y")]
    
    html = render_sequence_html(sequence, mutations, line_length=10, group=5, mode="wt")
    
    # 检查行首标记是否正确
    assert "1-10:" in html
    assert "11-20:" in html
    assert "21-26:" in html
    
    # 检查突变位点是否被正确高亮
    assert '<span class="mut" title="A1X">A</span>' in html
    assert '<span class="mut" title="Z26Y">Z</span>' in html
    
    # 检查是否有分组空格
    assert "BCDE FGHIJ" in html  # 每5个氨基酸一个空格
    
    # 检查序列长度是否正确（26个氨基酸）
    # 移除HTML标签和空格后应该有26个字符
    import re
    clean_html = re.sub(r'<[^>]*>', '', html)  # 移除HTML标签
    clean_html = re.sub(r'\s+', '', clean_html)  # 移除所有空格
    # 移除行首标记（如"1-10:"）
    clean_html = re.sub(r'\d+-\d+:', '', clean_html)
    assert len(clean_html) == 26


def test_render_sequence_html_mut_mode():
    """测试render_sequence_html在mut模式下的功能"""
    sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    mutations = [Mutation("A", 1, "X"), Mutation("Z", 26, "Y")]
    
    html = render_sequence_html(sequence, mutations, line_length=10, group=5, mode="mut")
    
    # 检查突变是否被应用
    assert '<span class="mut" title="A1X">X</span>' in html
    assert '<span class="mut" title="Z26Y">Y</span>' in html
    
    # 检查序列长度是否正确（26个氨基酸）
    import re
    clean_html = re.sub(r'<[^>]*>', '', html)
    clean_html = re.sub(r'\s+', '', clean_html)
    clean_html = re.sub(r'\d+-\d+:', '', clean_html)
    assert len(clean_html) == 26


def test_render_sequence_html_window():
    """测试render_sequence_html的window参数"""
    sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    mutations = [Mutation("A", 1, "X"), Mutation("Z", 26, "Y"), Mutation("M", 13, "N")]
    
    # 只显示中间窗口（10-16）
    html = render_sequence_html(sequence, mutations, line_length=10, window=(10, 16), mode="wt")
    
    # 检查是否只显示窗口内的序列
    assert "10-16:" in html
    assert "JKL" in html  # 检查窗口内的前几个字符
    assert "NOP" in html  # 检查窗口内的后几个字符
    assert "A" not in html  # 超出窗口的字符不应显示
    assert "Z" not in html  # 超出窗口的字符不应显示
    
    # 检查窗口内的突变是否被高亮
    assert '<span class="mut" title="M13N">M</span>' in html


def test_merge_windows():
    """测试merge_windows函数"""
    # 测试不重叠窗口
    windows = [(1, 10), (20, 30), (40, 50)]
    merged = merge_windows(windows)
    assert merged == windows
    
    # 测试重叠窗口
    windows = [(1, 10), (5, 15), (12, 20)]
    merged = merge_windows(windows)
    assert merged == [(1, 20)]
    
    # 测试相邻窗口
    windows = [(1, 10), (11, 20), (21, 30)]
    merged = merge_windows(windows)
    assert merged == [(1, 30)]
    
    # 测试带gap的窗口
    windows = [(1, 10), (15, 20)]
    merged = merge_windows(windows, gap=5)
    assert merged == [(1, 20)]  # 间隙为5，应该合并
    
    merged = merge_windows(windows, gap=3)
    assert merged == windows  # 间隙为3，不应该合并


def test_generate_fasta():
    """测试generate_fasta函数"""
    sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    mutations = [Mutation("A", 1, "X"), Mutation("Z", 26, "Y")]
    uniprot_id = "TEST123"
    
    # 测试野生型FASTA
    wt_fasta = generate_fasta(sequence, uniprot_id, mutations, mode="wt")
    assert f">{uniprot_id} wildtype" in wt_fasta
    assert "ABCDEFGHIJKLMNOPQRSTUVWXYZ" in wt_fasta.replace("\n", "")
    
    # 测试突变型FASTA
    mut_fasta = generate_fasta(sequence, uniprot_id, mutations, mode="mut")
    assert f">{uniprot_id} mutated [A1X,Z26Y]" in mut_fasta
    assert "XBCDEFGHIJKLMNOPQRSTUVWXY" in mut_fasta.replace("\n", "")
    
    # 测试FASTA行长度（每行60个字符）
    long_sequence = "A" * 100
    fasta = generate_fasta(long_sequence, uniprot_id, [], mode="wt")
    lines = fasta.strip().split("\n")
    # 跳过第一行（标题行）
    for line in lines[1:]:
        assert len(line) <= 60
    
    # 测试没有突变的情况
    fasta = generate_fasta(sequence, uniprot_id, [], mode="mut")
    assert f">{uniprot_id} mutated []" in fasta
    assert sequence in fasta.replace("\n", "")
