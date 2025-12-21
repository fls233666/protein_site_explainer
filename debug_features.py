from src.uniprot import get_uniprot_entry

# 获取P00760的UniProt条目
entry = get_uniprot_entry('P00760')

print('UniProt ID:', entry.uniprot_id)
print('Sequence length:', len(entry.sequence))
print('Features at position 1:')
features_at_1 = [f for f in entry.features if f.start <= 1 <= f.end]
for f in features_at_1:
    print(f'  {f.type} ({f.start}-{f.end}): {f.description}')

print('\nAll features:')
for i, f in enumerate(entry.features[:10]):
    print(f'  {i+1}. {f.type} ({f.start}-{f.end}): {f.description}')
