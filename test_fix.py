from src.alphafold import download_pdb

print("Testing download_pdb with UniProt ID P0DTC2...")
result = download_pdb("P0DTC2")
print(f"download_pdb('P0DTC2') returned: {result}")
print("Test completed successfully!")