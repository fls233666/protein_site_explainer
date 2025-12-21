import pytest
import requests.exceptions
import pandas as pd
from src.explain import explain_mutations
from src.uniprot import UniProtEntry, Feature
from src.alphafold import AlphaFoldData


@pytest.mark.smoke
def test_full_explain_flow(monkeypatch):
    """测试完整的解释流程（smoke test）"""
    # 模拟UniProtEntry
    mock_uniprot_entry = UniProtEntry(
        uniprot_id="P0DTC2",
        sequence="MVSKGEELFTGVVPILVELDGDVNGHKFSVSGEGEGDATYGKLTLKFICTTGKLPVPWPTLVTTFGYGLQCFARYPDHMKQHDFFKSAMPEGYVQERTIFFKDDGNYKTRAEVKFEGDTLVNRIELKGIDFKEDGNILGHKLEYNYNSHNVYIMADKQKNGIKVNFKIRHNIEDGSVQLADHYQQNTPIGDGPVLLPDNHYLSTQSALSKDPNEKRDHMVLLEFVTAAGITHGMDELYK",
        features=[Feature("signal peptide", "Signal peptide", 1, 10)]
    )
    
    # 模拟AlphaFoldData
    mock_alphafold_data = AlphaFoldData(
        uniprot_id="P0DTC2",
        plddt_scores=[(i, 90.0) for i in range(1, 240)]  # 模拟239个位置的pLDDT分数
    )
    
    # 模拟ESM评分结果
    mock_esm_results = [{"llr": -1.5, "sensitivity": -0.8}]
    
    # 模拟各个函数
    def mock_get_uniprot_entry(uniprot_id):
        return mock_uniprot_entry
    
    def mock_get_alphafold_data(uniprot_id):
        return mock_alphafold_data
    
    def mock_score_mutations(sequence, mutations, calculate_sensitivity=True):
            return mock_esm_results
    
    # 使用monkeypatch
    monkeypatch.setattr("src.explain.get_uniprot_entry", mock_get_uniprot_entry)
    monkeypatch.setattr("src.explain.get_alphafold_data", mock_get_alphafold_data)
    monkeypatch.setattr("src.explain.score_mutations", mock_score_mutations)
    
    result = explain_mutations(
        uniprot_id="P0DTC2",
        mutation_list_str="G32A"
    )
    
    # 验证结果结构
    assert "uniprot_id" in result
    assert "sequence" in result
    assert "mutations" in result
    assert "results_df" in result
    assert "uniprot_entry" in result
    assert "alphafold_data" in result
    
    # 验证数据框内容
    df = result["results_df"]
    assert len(df) == 1
    assert df.iloc[0]["Mutation"] == "G32A"
    assert df.iloc[0]["Position"] == 32
    assert "ESM_LLR" in df.columns
    assert "Site_Sensitivity" in df.columns
    assert "AlphaFold_pLDDT" in df.columns
    assert "UniProt_Features" in df.columns
    
    # 验证值的范围
    assert isinstance(df.iloc[0]["ESM_LLR"], float)
    assert isinstance(df.iloc[0]["Site_Sensitivity"], float)
    assert isinstance(df.iloc[0]["AlphaFold_pLDDT"], float)
    assert 0 <= df.iloc[0]["AlphaFold_pLDDT"] <= 100


@pytest.mark.smoke
def test_multiple_mutations(monkeypatch):
    """测试多个突变的解释（smoke test）"""
    # 模拟UniProtEntry
    mock_uniprot_entry = UniProtEntry(
        uniprot_id="P0DTC2",
        sequence="MVSKGEELFTGVVPILVELDGDVNGHKFSVSGEGEGDATYGKLTLKFICTTGKLPVPWPTLVTTFGYGLQCFARYPDHMKQHDFFKSAMPEGYVQERTIFFKDDGNYKTRAEVKFEGDTLVNRIELKGIDFKEDGNILGHKLEYNYNSHNVYIMADKQKNGIKVNFKIRHNIEDGSVQLADHYQQNTPIGDGPVLLPDNHYLSTQSALSKDPNEKRDHMVLLEFVTAAGITHGMDELYK",
        features=[Feature("signal peptide", "Signal peptide", 1, 10)]
    )
    
    # 模拟AlphaFoldData
    mock_alphafold_data = AlphaFoldData(
        uniprot_id="P0DTC2",
        plddt_scores=[(i, 90.0) for i in range(1, 240)]  # 模拟239个位置的pLDDT分数
    )
    
    # 模拟ESM评分结果
    mock_esm_results = [{"llr": -1.5, "sensitivity": -0.8}, {"llr": -2.0, "sensitivity": -1.2}]
    
    # 模拟各个函数
    def mock_get_uniprot_entry(uniprot_id):
        return mock_uniprot_entry
    
    def mock_get_alphafold_data(uniprot_id):
        return mock_alphafold_data
    
    def mock_score_mutations(sequence, mutations, calculate_sensitivity=True):
            return mock_esm_results
    
    # 使用monkeypatch
    monkeypatch.setattr("src.explain.get_uniprot_entry", mock_get_uniprot_entry)
    monkeypatch.setattr("src.explain.get_alphafold_data", mock_get_alphafold_data)
    monkeypatch.setattr("src.explain.score_mutations", mock_score_mutations)
    
    result = explain_mutations(
        uniprot_id="P0DTC2",
        mutation_list_str="G32A, P193A"
    )
    
    assert len(result["results_df"]) == 2
    assert set(result["results_df"]["Mutation"]) == {"G32A", "P193A"}
