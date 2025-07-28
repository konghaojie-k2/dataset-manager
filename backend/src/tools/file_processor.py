"""文件处理工具"""

import zipfile
import pandas as pd
import uuid
import aiofiles
import shutil
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from loguru import logger
from fastapi import UploadFile, HTTPException

from ..utils.helpers import format_size, validate_file_extension


class FileProcessor:
    """文件处理工具类"""
    
    def __init__(self, allowed_extensions: List[str] = None, upload_dir: Path = None):
        """初始化文件处理器
        
        Args:
            allowed_extensions: 允许的文件扩展名列表
            upload_dir: 上传目录（可选）
        """
        self.allowed_extensions = allowed_extensions or [".csv", ".xlsx", ".xls", ".zip"]
        self.upload_dir = Path(upload_dir) if upload_dir else None
        if self.upload_dir:
            self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_uploaded_file(self, file: UploadFile, upload_dir: Path = None) -> Tuple[str, Path]:
        """保存上传的文件
        
        Args:
            file: 上传的文件
            upload_dir: 上传目录（可选，如果不提供则使用初始化时的目录）
            
        Returns:
            Tuple[str, Path]: (文件ID, 文件路径)
        """
        # 使用提供的目录或默认目录
        target_dir = Path(upload_dir) if upload_dir else self.upload_dir
        if not target_dir:
            raise ValueError("未指定上传目录")
        
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一文件ID
        file_id = str(uuid.uuid4())
        
        # 验证文件格式
        if not self._is_valid_filename(file.filename):
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件格式: {file.filename}。仅支持CSV文件或ZIP压缩包"
            )
        
        # 确定文件保存路径
        file_extension = Path(file.filename).suffix.lower()
        save_path = target_dir / f"{file_id}{file_extension}"
        
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
    
    def _is_valid_filename(self, filename: str) -> bool:
        """验证文件名格式"""
        if not filename:
            return False
        
        valid_extensions = {'.csv', '.zip'}
        file_extension = Path(filename).suffix.lower()
        return file_extension in valid_extensions
    
    def extract_csv_files(self, file_path: Path) -> List[Path]:
        """从ZIP文件中提取CSV文件或返回CSV文件路径
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[Path]: CSV文件路径列表
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
    
    def load_csv_data(self, csv_path: Path, sample_rows: int = None) -> pd.DataFrame:
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
            
            kwargs = {}
            if sample_rows:
                kwargs['nrows'] = sample_rows
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_path, encoding=encoding, **kwargs)
                    logger.info(f"成功加载CSV文件: {csv_path}, 编码: {encoding}, 形状: {df.shape}")
                    return df
                except UnicodeDecodeError:
                    continue
            
            # 如果所有编码都失败，抛出异常
            raise ValueError("无法识别文件编码格式")
            
        except Exception as e:
            logger.error(f"CSV文件加载失败: {e}")
            raise HTTPException(status_code=400, detail=f"CSV文件加载失败: {str(e)}")
    
    def cleanup_extracted_files(self, file_path: Path):
        """清理提取的临时文件
        
        Args:
            file_path: 原始文件路径
        """
        if file_path.suffix.lower() == '.zip':
            extract_dir = file_path.parent / f"{file_path.stem}_extracted"
            if extract_dir.exists():
                try:
                    shutil.rmtree(extract_dir)
                    logger.info(f"清理临时目录: {extract_dir}")
                except Exception as e:
                    logger.warning(f"清理临时目录失败: {e}")

    def validate_file(self, file_path: Path) -> bool:
        """验证文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否为有效文件
        """
        if not file_path.exists():
            logger.error(f"文件不存在: {file_path}")
            return False
        
        if not validate_file_extension(file_path, self.allowed_extensions):
            logger.error(f"不支持的文件格式: {file_path.suffix}")
            return False
        
        return True
    
    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 文件信息
        """
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        stat = file_path.stat()
        
        return {
            "name": file_path.name,
            "path": str(file_path),
            "size": stat.st_size,
            "size_formatted": format_size(stat.st_size),
            "extension": file_path.suffix,
            "created_time": stat.st_ctime,
            "modified_time": stat.st_mtime,
            # 兼容旧接口
            "file_name": file_path.name,
            "file_size": stat.st_size,
            "file_path": str(file_path),
            "modified_time": stat.st_mtime
        }
    
    def extract_zip(self, zip_path: Path, extract_to: Path) -> List[Path]:
        """解压ZIP文件
        
        Args:
            zip_path: ZIP文件路径
            extract_to: 解压目标目录
            
        Returns:
            List[Path]: 解压出的文件列表
        """
        extracted_files = []
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
                
                for file_name in zip_ref.namelist():
                    file_path = extract_to / file_name
                    if file_path.is_file():
                        extracted_files.append(file_path)
                
            logger.info(f"成功解压 {len(extracted_files)} 个文件")
            return extracted_files
            
        except Exception as e:
            logger.error(f"解压文件失败: {e}")
            raise
    
    def read_data_file(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """读取数据文件
        
        Args:
            file_path: 文件路径
            **kwargs: 读取参数
            
        Returns:
            pd.DataFrame: 数据框
        """
        if not self.validate_file(file_path):
            raise ValueError(f"无效的文件: {file_path}")
        
        try:
            if file_path.suffix.lower() == '.csv':
                return pd.read_csv(file_path, **kwargs)
            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                return pd.read_excel(file_path, **kwargs)
            else:
                raise ValueError(f"不支持的文件格式: {file_path.suffix}")
                
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            raise
    
    def get_data_preview(self, file_path: Path, rows: int = 10) -> Dict[str, Any]:
        """获取数据预览
        
        Args:
            file_path: 文件路径
            rows: 预览行数
            
        Returns:
            Dict[str, Any]: 预览信息
        """
        try:
            df = self.read_data_file(file_path, nrows=rows)
            
            return {
                "shape": df.shape,
                "columns": list(df.columns),
                "dtypes": df.dtypes.to_dict(),
                "preview_data": df.to_dict('records'),
                "sample_size": len(df)
            }
            
        except Exception as e:
            logger.error(f"获取数据预览失败: {e}")
            raise
    
    def process_uploaded_file(self, file_path: Path, output_dir: Path) -> Dict[str, Any]:
        """处理上传的文件
        
        Args:
            file_path: 上传的文件路径
            output_dir: 输出目录
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        result = {
            "original_file": self.get_file_info(file_path),
            "processed_files": [],
            "errors": []
        }
        
        try:
            if file_path.suffix.lower() == '.zip':
                # 解压ZIP文件
                extracted_files = self.extract_zip(file_path, output_dir)
                
                for extracted_file in extracted_files:
                    if validate_file_extension(extracted_file, ['.csv', '.xlsx', '.xls']):
                        try:
                            file_info = self.get_file_info(extracted_file)
                            preview = self.get_data_preview(extracted_file)
                            
                            result["processed_files"].append({
                                "file_info": file_info,
                                "preview": preview
                            })
                            
                        except Exception as e:
                            result["errors"].append(f"处理文件 {extracted_file} 失败: {e}")
            
            else:
                # 直接处理数据文件
                preview = self.get_data_preview(file_path)
                result["processed_files"].append({
                    "file_info": result["original_file"],
                    "preview": preview
                })
            
            logger.info(f"文件处理完成，共处理 {len(result['processed_files'])} 个文件")
            return result
            
        except Exception as e:
            logger.error(f"文件处理失败: {e}")
            result["errors"].append(str(e))
            return result 