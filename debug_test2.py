import os
from src.alphafold import fetch_afdb_predictions, get_alphafold_data, download_pdb
import traceback

# 测试UniProt ID
TEST_UNIPROT_ID = "P68871"  # Human hemoglobin subunit beta

print("=" * 60)
print("3. Testing Python library functions...")

# 先清除缓存，确保测试的是最新数据
from src.cache import clear_cache
print("   Clearing cache...")
clear_cache()

# 测试fetch_afdb_predictions
print("   Testing fetch_afdb_predictions...")
try:
    predictions = fetch_afdb_predictions(TEST_UNIPROT_ID)
    print(f"      Result Type: {type(predictions)}")
    print(f"      Result Length: {len(predictions)}")
    if predictions:
        print(f"      First prediction entryId: {predictions[0].get('entryId')}")
except Exception as e:
    print(f"      Error: {type(e).__name__}: {e}")
    traceback.print_exc()

# 测试get_alphafold_data
print("   Testing get_alphafold_data...")
try:
    alphafold_data = get_alphafold_data(TEST_UNIPROT_ID)
    print(f"      Result Type: {type(alphafold_data)}")
    if alphafold_data:
        print(f"      Number of pLDDT scores: {len(alphafold_data.plddt_scores)}")
        if alphafold_data.plddt_scores:
            print(f"      First pLDDT score: {alphafold_data.plddt_scores[0]}")
            print(f"      Last pLDDT score: {alphafold_data.plddt_scores[-1]}")
except Exception as e:
    print(f"      Error: {type(e).__name__}: {e}")
    traceback.print_exc()

# 测试download_pdb
print("   Testing download_pdb...")
try:
    pdb_file = download_pdb(TEST_UNIPROT_ID)
    print(f"      PDB File Path: {pdb_file}")
    print(f"      File Size: {os.path.getsize(pdb_file)} bytes")
    print(f"      File Extension: {os.path.splitext(pdb_file)[1]}")
except Exception as e:
    print(f"      Error: {type(e).__name__}: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("Debug test 2 completed!")
