from typing import List, Tuple, Optional, Literal
from src.parsing import Mutation


def apply_mutations(sequence: str, mutations: List[Mutation]) -> str:
    """
    将突变应用到蛋白质序列
    
    Args:
        sequence: 原始蛋白质序列
        mutations: Mutation对象列表
        
    Returns:
        str: 应用突变后的序列
    """
    seq_list = list(sequence)
    
    # 按照位置排序，处理同一位置的多个突变（取最后一个）
    for mutation in sorted(mutations, key=lambda x: x.position):
        if 1 <= mutation.position <= len(sequence):
            # 转换为0-based索引
            seq_list[mutation.position - 1] = mutation.mut_aa
    
    return "".join(seq_list)


def merge_windows(windows: List[Tuple[int, int]], gap: int = 0) -> List[Tuple[int, int]]:
    """
    合并重叠或相邻的窗口
    
    Args:
        windows: 窗口列表，每个窗口是(start, end)元组
        gap: 允许的间隙大小
        
    Returns:
        List[Tuple[int, int]]: 合并后的窗口列表
    """
    if not windows:
        return []
    
    # 按起始位置排序
    sorted_windows = sorted(windows, key=lambda x: x[0])
    merged = [sorted_windows[0]]
    
    for current in sorted_windows[1:]:
        last = merged[-1]
        
        # 如果当前窗口与最后一个窗口重叠或相邻（考虑gap），则合并
        if current[0] <= last[1] + gap + 1:
            new_start = min(last[0], current[0])
            new_end = max(last[1], current[1])
            merged[-1] = (new_start, new_end)
        else:
            merged.append(current)
    
    return merged


def render_sequence_html(
    sequence: str, 
    mutations: List[Mutation], 
    *, 
    line_length: int = 60, 
    group: int = 10, 
    show_ruler: bool = True, 
    start_index: int = 1, 
    window: Optional[Tuple[int, int]] = None, 
    mode: Literal["wt", "mut"] = "wt"
) -> str:
    """
    生成蛋白质序列的HTML表示，高亮突变位点
    
    Args:
        sequence: 原始蛋白质序列
        mutations: Mutation对象列表
        line_length: 每行显示的氨基酸数量
        group: 每多少个氨基酸添加一个空格
        show_ruler: 是否显示行首的位置标记
        start_index: 序列的起始索引（1-based）
        window: 只显示该窗口范围内的序列
        mode: 显示模式，"wt"表示野生型，"mut"表示突变型
        
    Returns:
        str: HTML格式的序列显示
    """
    # 创建突变位置字典，用于快速查找
    mutation_dict = {m.position: m for m in mutations}
    
    # 应用突变（如果需要）
    display_sequence = apply_mutations(sequence, mutations) if mode == "mut" else sequence
    
    # 确定要显示的序列范围
    total_length = len(sequence)
    if window:
        display_start = max(1, window[0])
        display_end = min(total_length, window[1])
    else:
        display_start = 1
        display_end = total_length
    
    # 转换为0-based索引
    display_start_0 = display_start - 1
    display_end_0 = display_end
    
    html_parts = []
    html_parts.append('<div class="seq-view"><pre>')
    
    # 生成序列行
    for line_start in range(display_start_0, display_end_0, line_length):
        line_end = min(line_start + line_length, display_end_0)
        line_seq = display_sequence[line_start:line_end]
        
        # 计算该行的实际起始和结束位置（1-based）
        actual_start = line_start + 1
        actual_end = line_end
        
        # 添加行首标记
        if show_ruler:
            html_parts.append(f'<strong>{actual_start}-{actual_end}:</strong> ')
        
        # 生成行内容
        for i, aa in enumerate(line_seq):
            # 计算当前氨基酸的实际位置（1-based）
            pos = actual_start + i
            
            # 检查是否是突变位点
            if pos in mutation_dict:
                mutation = mutation_dict[pos]
                # 添加高亮标记
                html_parts.append(f'<span class="mut" title="{str(mutation)}">{aa}</span>')
            else:
                html_parts.append(aa)
            
            # 添加分组空格
            if group > 0 and (i + 1) % group == 0 and i < len(line_seq) - 1:
                html_parts.append(' ')
        
        html_parts.append('\n')
    
    html_parts.append('</pre></div>')
    
    return "".join(html_parts)


def generate_fasta(sequence: str, uniprot_id: str, mutations: Optional[List[Mutation]] = None, mode: Literal["wt", "mut"] = "wt") -> str:
    """
    生成FASTA格式的序列
    
    Args:
        sequence: 原始蛋白质序列
        uniprot_id: UniProt ID
        mutations: Mutation对象列表（可选）
        mode: 序列模式，"wt"表示野生型，"mut"表示突变型
        
    Returns:
        str: FASTA格式的序列
    """
    # 应用突变（如果需要）
    display_sequence = apply_mutations(sequence, mutations) if mode == "mut" else sequence
    
    # 生成FASTA头部
    if mode == "wt":
        header = f">{uniprot_id} wildtype"
    else:
        mutation_str = ",".join(str(m) for m in mutations) if mutations else ""
        header = f">{uniprot_id} mutated [{mutation_str}]"
    
    # 生成FASTA序列（每行60个字符）
    fasta_seq = ""
    for i in range(0, len(display_sequence), 60):
        fasta_seq += display_sequence[i:i+60] + "\n"
    
    return header + "\n" + fasta_seq
