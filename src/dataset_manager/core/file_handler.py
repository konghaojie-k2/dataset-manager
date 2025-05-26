"""文件处理核心模块"""

import zipfile
import uuid
from pathlib import Path
from typing import List, Optional, Tuple
import pandas as pd
import aiofiles
from loguru import logger
from fastapi import UploadFile, HTTPException

from ..models.dataset import DatasetMetadata


class FileHandler:
    """文件处理器"""
    
    def __init__(self, upload_dir: Path):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"文件处理器初始化，上传目录: {self.upload_dir}")
    
    async def save_uploaded_file(self, file: UploadFile) -> Tuple[str, Path]:
        """保存上传的文件
        
        Args:
            file: 上传的文件
            
        Returns:
            Tuple[str, Path]: (文件ID, 文件路径)
        """
        # 生成唯一文件ID
        file_id = str(uuid.uuid4())
        
        # 验证文件格式
        if not self._is_valid_file(file.filename):
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件格式: {file.filename}。仅支持CSV文件或ZIP压缩包"
            )
        
        # 确定文件保存路径
        file_extension = Path(file.filename).suffix.lower()
        save_path = self.upload_dir / f"{file_id}{file_extension}"
        
        # 保存文件
        try:
            async with aiofiles.open(save_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            logger.info(f"文件保存成功: {save_path}")
            return file_id, save_path
            
        except Exception as e:
            logger.error(f"文件保存失败: {e}")
            raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    def _is_valid_file(self, filename: str) -> bool:
        """验证文件格式"""
        if not filename:
            return False
        
        valid_extensions = {'.csv', '.zip'}
        file_extension = Path(filename).suffix.lower()
        return file_extension in valid_extensions
    
    def extract_csv_files(self, file_path: Path) -> List[Path]:
        """从ZIP文件中提取CSV文件
        
        Args:
            file_path: ZIP文件路径
            
        Returns:
            List[Path]: 提取的CSV文件路径列表
        """
        csv_files = []
        
        if file_path.suffix.lower() == '.csv':
            # 如果是CSV文件，直接返回
            return [file_path]
        
        elif file_path.suffix.lower() == '.zip':
            # 如果是ZIP文件，提取其中的CSV文件
            extract_dir = file_path.parent / f"{file_path.stem}_extracted"
            extract_dir.mkdir(exist_ok=True)
            
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # 获取ZIP文件中的所有文件
                    file_list = zip_ref.namelist()
                    
                    for file_name in file_list:
                        if file_name.lower().endswith('.csv'):
                            # 提取CSV文件
                            zip_ref.extract(file_name, extract_dir)
                            extracted_path = extract_dir / file_name
                            csv_files.append(extracted_path)
                            logger.info(f"提取CSV文件: {extracted_path}")
                
                if not csv_files:
                    raise ValueError("ZIP文件中未找到CSV文件")
                    
            except Exception as e:
                logger.error(f"ZIP文件提取失败: {e}")
                raise HTTPException(status_code=400, detail=f"ZIP文件提取失败: {str(e)}")
        
        return csv_files
    
    def load_csv_data(self, csv_path: Path, sample_rows: int = 1000) -> pd.DataFrame:
        """加载CSV数据
        
        Args:
            csv_path: CSV文件路径
            sample_rows: 采样行数，用于预览
            
        Returns:
            pd.DataFrame: 数据框
        """
        try:
            # 尝试不同的编码格式
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_path, encoding=encoding, nrows=sample_rows)
                    logger.info(f"成功加载CSV文件: {csv_path}, 编码: {encoding}, 形状: {df.shape}")
                    return df
                except UnicodeDecodeError:
                    continue
            
            # 如果所有编码都失败，抛出异常
            raise ValueError("无法识别文件编码格式")
            
        except Exception as e:
            logger.error(f"CSV文件加载失败: {e}")
            raise HTTPException(status_code=400, detail=f"CSV文件加载失败: {str(e)}")
    
    def get_file_info(self, file_path: Path) -> dict:
        """获取文件基本信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            dict: 文件信息
        """
        try:
            stat = file_path.stat()
            return {
                'file_name': file_path.name,
                'file_size': stat.st_size,
                'file_path': str(file_path),
                'created_time': stat.st_ctime,
                'modified_time': stat.st_mtime
            }
        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取文件信息失败: {str(e)}")
    
    def cleanup_extracted_files(self, file_path: Path):
        """清理提取的临时文件
        
        Args:
            file_path: 原始文件路径
        """
        if file_path.suffix.lower() == '.zip':
            extract_dir = file_path.parent / f"{file_path.stem}_extracted"
            if extract_dir.exists():
                try:
                    import shutil
                    shutil.rmtree(extract_dir)
                    logger.info(f"清理临时目录: {extract_dir}")
                except Exception as e:
                    logger.warning(f"清理临时目录失败: {e}") 