from src.uniprot import get_uniprot_entry, get_features_at_position

# 完全复制测试用例的逻辑
entry = get_uniprot_entry("P00760")
features = get_features_at_position(entry.features, 1)

print(f"Type of features: {type(features)}")
print(f"Number of features at position 1: {len(features)}")
print(f"All features at position 1:")
for i, f in enumerate(features):
    print(f"  {i+1}. Type: '{f.type}', Start: {f.start}, End: {f.end}, Description: '{f.description}'")

# 复制测试用例中的筛选逻辑
signal_peptide_features = [f for f in features if f.type == "signal"]
print(f"\nNumber of signal peptide features: {len(signal_peptide_features)}")
print(f"Filter condition: f.type == \"signal\"")

# 检查所有特征的类型
print(f"\nAll feature types in entry.features:")
all_types = sorted(list(set(f.type for f in entry.features)))
for feature_type in all_types:
    print(f"  '{feature_type}'")
