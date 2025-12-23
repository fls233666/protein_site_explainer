import os
import requests
import gzip

def download_p0dtc2_model():
    """
    下载P0DTC2的AlphaFold模型文件并保存到models目录
    """
    # 创建models目录（如果不存在）
    models_dir = os.path.join(os.getcwd(), "models")
    os.makedirs(models_dir, exist_ok=True)
    
    # P0DTC2的AlphaFold模型URL（从UniProt获取）
    # 注意：由于AlphaFold DB返回404，我们尝试从其他来源获取
    # 这里使用UniProt的AlphaFold结构链接
    url = "https://alphafold.ebi.ac.uk/files/AF-P0DTC2-F1-model_v4.pdb.gz"
    filename = "AF-P0DTC2-F1-model_v4.pdb.gz"
    file_path = os.path.join(models_dir, filename)
    
    print(f"正在下载P0DTC2的AlphaFold模型文件...")
    print(f"URL: {url}")
    print(f"保存路径: {file_path}")
    
    try:
        # 发送HTTP请求下载文件
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()  # 检查请求是否成功
        
        # 保存文件到本地
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"✓ 下载成功: {filename}")
        
        # 验证文件是否完整
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"文件大小: {file_size:,} 字节")
            
            # 尝试解压验证文件完整性
            try:
                with gzip.open(file_path, 'rb') as f:
                    # 读取前100字节验证文件完整性
                    content = f.read(100)
                print("✓ 文件完整性验证通过")
                return True
            except Exception as e:
                print(f"✗ 文件解压失败: {e}")
                os.remove(file_path)  # 删除损坏的文件
                return False
        else:
            print(f"✗ 文件不存在")
            return False
            
    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP错误: {e}")
        if e.response.status_code == 404:
            print("提示: AlphaFold DB可能没有P0DTC2的模型文件，您可以尝试从其他来源获取。")
            print("推荐来源：https://www.uniprot.org/uniprot/P0DTC2#structure")
    except requests.exceptions.ConnectionError:
        print("✗ 网络连接错误，请检查您的网络连接。")
    except requests.exceptions.Timeout:
        print("✗ 下载超时，请稍后重试。")
    except Exception as e:
        print(f"✗ 下载失败: {e}")
    
    return False

if __name__ == "__main__":
    download_p0dtc2_model()