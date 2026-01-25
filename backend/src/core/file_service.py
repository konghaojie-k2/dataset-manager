"""文件管理服务"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, Any
from fastapi import UploadFile
from loguru import logger

from ..tools.file_processor import FileProcessor


class FileService:
    """文件管理服务"""
    
    def __init__(self, upload_dir: Path):
        """初始化文件服务
        
        Args:
            upload_dir: 上传目录
        """
        self.upload_dir = Path(upload_dir)
        # 延迟初始化：只在目录不存在时创建，使用线程池避免阻塞
        if not self.upload_dir.exists():
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            _executor = ThreadPoolExecutor(max_workers=1)
            try:
                loop = asyncio.get_running_loop()
                loop.run_in_executor(_executor, lambda: self.upload_dir.mkdir(parents=True, exist_ok=True))
            except RuntimeError:
                self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        self.file_processor = FileProcessor(upload_dir=self.upload_dir)
        
        logger.info("文件管理服务初始化完成")
    
    async def upload_file(self, file: UploadFile) -> Tuple[str, Path, Dict[str, Any]]:
        """上传文件
        
        Args:
            file: 上传的文件
            
        Returns:
            Tuple[str, Path, Dict[str, Any]]: (文件ID, 文件路径, 文件信息)
        """
        try:
            # 保存文件
            file_id, file_path = await self.file_processor.save_uploaded_file(file)
            
            # 获取文件信息
            file_info = self.file_processor.get_file_info(file_path)
            
            logger.info(f"文件上传成功: {file.filename} -> {file_id}")
            
            return file_id, file_path, file_info
            
        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            raise
    
    def delete_file(self, file_path: Path) -> bool:
        """删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否删除成功
        """
        try:
            if file_path.exists():
                file_path.unlink()
            
            # 清理提取的临时文件
            self.file_processor.cleanup_extracted_files(file_path)
            
            logger.info(f"文件删除成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"文件删除失败: {e}")
            return False
    
    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 文件信息
        """
        return self.file_processor.get_file_info(file_path)
    
    def extract_csv_files(self, file_path: Path):
        """提取CSV文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[Path]: CSV文件列表
        """
        return self.file_processor.extract_csv_files(file_path)
    
    def load_csv_data(self, csv_path: Path, sample_rows: int = None):
        """加载CSV数据
        
        Args:
            csv_path: CSV文件路径
            sample_rows: 采样行数
            
        Returns:
            pd.DataFrame: 数据框
        """
        return self.file_processor.load_csv_data(csv_path, sample_rows) 