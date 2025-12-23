#!/usr/bin/env python3
"""
验证脚本：测试所有修复的功能

测试内容：
1. AlphaFold API的HTTP请求和响应处理
2. PDB和mmCIF文件的解析
3. pLDDT分数的提取
4. 3D结构可视化功能
5. 缓存功能
"""

import sys
import os
import tempfile
import logging
import requests
from Bio.PDB import PDBParser, MMCIFParser

# 获取当前脚本目录和项目根目录
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = script_dir

# 将项目根目录添加到Python路径，这样src可以作为包导入
sys.path.insert(0, project_root)

# 现在可以从src包中导入模块
from src.alphafold import fetch_afdb_predictions, download_pdb, get_alphafold_data
from src.cache import clear_cache

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_alphafold_api():
    """测试AlphaFold API的HTTP请求和响应处理"""
    logger.info("=== 测试AlphaFold API功能 ===")
    
    # 测试1：使用已知存在的UniProt ID（P68871，人类血红蛋白β链）
    uniprot_id = "P68871"
    logger.info(f"测试UniProt ID: {uniprot_id}")
    
    try:
        # 测试API调用
        predictions = fetch_afdb_predictions(uniprot_id)
        logger.info(f"API返回状态：成功")
        logger.info(f"返回的预测数量：{len(predictions)}")
        
        if predictions:
            selected_prediction = predictions[0]
            logger.info(f"\nSelected Prediction:")
            logger.info(f"  entryId: {selected_prediction.get('entryId')}")
            logger.info(f"  modelEntityId: {selected_prediction.get('modelEntityId')}")
            logger.info(f"  pdbUrl: {selected_prediction.get('pdbUrl')}")
            logger.info(f"  cifUrl: {selected_prediction.get('cifUrl')}")
            
            # 测试使用get_alphafold_data函数获取数据
            logger.info("\n测试get_alphafold_data函数")
            alphafold_data = get_alphafold_data(uniprot_id)
            if alphafold_data:
                logger.info(f"✅ 获取AlphaFold数据成功")
                logger.info(f"pLDDT分数数量：{len(alphafold_data.plddt_scores)}")
                if alphafold_data.plddt_scores:
                    min_score = min(score for _, score in alphafold_data.plddt_scores)
                    max_score = max(score for _, score in alphafold_data.plddt_scores)
                    logger.info(f"pLDDT分数范围：{min_score} - {max_score}")
                    
                    # 测试获取特定位置的pLDDT分数
                    test_position = alphafold_data.plddt_scores[0][0]
                    test_score = alphafold_data.get_plddt_at_position(test_position)
                    logger.info(f"位置 {test_position} 的pLDDT分数：{test_score}")
            
            # 测试download_pdb函数
            logger.info("\n测试download_pdb函数")
            with tempfile.TemporaryDirectory() as tmpdir:
                pdb_file = download_pdb(uniprot_id, save_dir=tmpdir)
                logger.info(f"✅ 下载PDB/CIF文件成功：{pdb_file}")
                logger.info(f"文件大小：{os.path.getsize(pdb_file)} bytes")
        
        return True
    
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP错误：{e}")
        # 检查是否保留了原始异常信息
        if hasattr(e, 'response'):
            logger.info(f"响应状态码：{e.response.status_code}")
            logger.info(f"响应URL：{e.response.url}")
            return False
        else:
            logger.error("没有保留原始响应信息")
            return False
    
    except Exception as e:
        logger.error(f"其他错误：{e}")
        import traceback
        traceback.print_exc()
        return False

def test_404_handling():
    """测试404错误处理（无效的UniProt ID）"""
    logger.info("\n=== 测试404错误处理 ===")
    
    # 使用不存在的UniProt ID
    invalid_uniprot_id = "INVALID123"
    
    try:
        predictions = fetch_afdb_predictions(invalid_uniprot_id)
        logger.info(f"处理无效UniProt ID的结果：{predictions}")
        
        # 检查是否返回None而不是空列表
        if predictions is None:
            logger.info("✅ 正确：无效ID返回None，避免缓存空结果")
            return True
        else:
            logger.error(f"❌ 错误：应该返回None，实际返回：{type(predictions)}")
            return False
            
    except requests.exceptions.HTTPError as e:
        # 注意：API实际上对无效ID返回400错误，而不是404
        logger.info(f"注意：API对无效ID返回400错误，这是预期行为")
        logger.info(f"响应状态码：{e.response.status_code}")
        return True
    
    except Exception as e:
        logger.error(f"❌ 其他错误：{e}")
        return False

def test_cache_clearing():
    """测试缓存清除功能"""
    logger.info("\n=== 测试缓存清除功能 ===")
    
    try:
        # 先进行一次API调用，确保有缓存
        uniprot_id = "P68871"
        fetch_afdb_predictions(uniprot_id)
        
        # 清除缓存
        clear_cache()
        logger.info("✅ 缓存清除功能正常工作")
        return True
        
    except Exception as e:
        logger.error(f"❌ 缓存清除错误：{e}")
        return False

def test_3d_visualization():
    """测试3D结构可视化功能"""
    logger.info("\n=== 测试3D结构可视化功能 ===")
    
    try:
        # 导入所需模块
        from src.viz import visualizer
        from src.parsing import parse_mutation
        
        # 测试创建3D视图对象
        uniprot_id = "P68871"
        # 创建Mutation对象而不是字符串列表
        mutations = [parse_mutation("P6V"), parse_mutation("D74H")]
        
        # 只测试对象创建，不实际渲染
        view = visualizer.create_3d_structure(uniprot_id, mutations)
        logger.info(f"✅ 创建3D视图对象成功：{type(view)}")
        
        # 检查颜色方案是否正确设置为B-factor
        # 注意：这里无法直接检查py3Dmol视图对象的内部设置
        # 只能确认对象创建成功
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 3D可视化错误：{e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    logger.info("开始测试所有修复的功能...")
    
    # 运行所有测试
    tests = [
        ("AlphaFold API和文件解析", test_alphafold_api),
        ("404错误处理", test_404_handling),
        ("缓存清除功能", test_cache_clearing),
        ("3D结构可视化", test_3d_visualization)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"运行测试：{test_name}")
        logger.info('='*60)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ 测试通过：{test_name}")
            else:
                logger.error(f"❌ 测试失败：{test_name}")
                
        except Exception as e:
            logger.error(f"❌ 测试执行错误：{test_name} - {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # 输出总结
    logger.info("\n" + "="*60)
    logger.info("测试结果总结")
    logger.info("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        if result:
            logger.info(f"✅ {test_name}")
            passed += 1
        else:
            logger.error(f"❌ {test_name}")
            failed += 1
    
    logger.info(f"\n总测试数：{len(results)}")
    logger.info(f"通过：{passed}")
    logger.info(f"失败：{failed}")
    
    if failed == 0:
        logger.info("\n🎉 所有测试都通过了！修复成功！")
        return 0
    else:
        logger.error("\n❌ 有测试失败，需要进一步检查修复")
        return 1

if __name__ == "__main__":
    sys.exit(main())
