"""
提示词加载器模块

从 .md 文件加载提示词模板，参考 DeerFlow 的设计模式
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import re
import yaml
from loguru import logger


class PromptLoader:
    """提示词加载器，从 .md 文件加载提示词"""
    
    def __init__(self, prompts_dir: Path = None):
        """初始化加载器
        
        Args:
            prompts_dir: 提示词文件目录，默认为当前目录下的 templates
        """
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent / "templates"
        
        self.prompts_dir = Path(prompts_dir)
        self.prompts_cache: Dict[str, Dict[str, Any]] = {}
        
        # 确保目录存在
        self.prompts_dir.mkdir(exist_ok=True)
        logger.info(f"提示词加载器初始化，目录: {self.prompts_dir}")
    
    def load_prompt(self, filename: str) -> Dict[str, Any]:
        """加载单个提示词文件
        
        Args:
            filename: 文件名（不含扩展名）
            
        Returns:
            Dict: 包含提示词信息的字典
        """
        if filename in self.prompts_cache:
            return self.prompts_cache[filename]
        
        file_path = self.prompts_dir / f"{filename}.md"
        
        if not file_path.exists():
            logger.warning(f"提示词文件不存在: {file_path}")
            return {}
        
        try:
            content = file_path.read_text(encoding='utf-8')
            prompt_data = self._parse_markdown_prompt(content)
            prompt_data['filename'] = filename
            prompt_data['file_path'] = str(file_path)
            
            self.prompts_cache[filename] = prompt_data
            logger.debug(f"加载提示词文件: {filename}")
            
            return prompt_data
            
        except Exception as e:
            logger.error(f"加载提示词文件失败 {filename}: {e}")
            return {}
    
    def load_all_prompts(self) -> Dict[str, Dict[str, Any]]:
        """加载所有提示词文件
        
        Returns:
            Dict: 所有提示词的字典
        """
        all_prompts = {}
        
        for md_file in self.prompts_dir.glob("*.md"):
            filename = md_file.stem
            prompt_data = self.load_prompt(filename)
            if prompt_data:
                all_prompts[filename] = prompt_data
        
        logger.info(f"加载了 {len(all_prompts)} 个提示词文件")
        return all_prompts
    
    def reload_prompt(self, filename: str) -> Dict[str, Any]:
        """重新加载指定的提示词文件
        
        Args:
            filename: 文件名
            
        Returns:
            Dict: 提示词数据
        """
        if filename in self.prompts_cache:
            del self.prompts_cache[filename]
        
        return self.load_prompt(filename)
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self.prompts_cache.clear()
        logger.info("提示词缓存已清空")
    
    def _parse_markdown_prompt(self, content: str) -> Dict[str, Any]:
        """解析 Markdown 格式的提示词文件
        
        Args:
            content: 文件内容
            
        Returns:
            Dict: 解析后的提示词数据
        """
        # 分离 YAML 前置元数据和内容
        parts = content.split('---', 2)
        
        metadata = {}
        prompt_content = content
        
        if len(parts) >= 3:
            # 有 YAML 前置元数据
            try:
                metadata = yaml.safe_load(parts[1]) or {}
                prompt_content = parts[2].strip()
            except yaml.YAMLError as e:
                logger.warning(f"解析 YAML 元数据失败: {e}")
                prompt_content = content
        
        # 解析提示词部分
        sections = self._parse_sections(prompt_content)
        
        return {
            'metadata': metadata,
            'sections': sections,
            'raw_content': content
        }
    
    def _parse_sections(self, content: str) -> Dict[str, str]:
        """解析提示词的各个部分
        
        Args:
            content: 提示词内容
            
        Returns:
            Dict: 各部分内容
        """
        sections = {}
        
        # 使用正则表达式匹配标题和内容
        pattern = r'^##\s+(.+?)$'
        matches = list(re.finditer(pattern, content, re.MULTILINE))
        
        if not matches:
            # 没有分节，整个内容作为主要部分
            sections['main'] = content.strip()
            return sections
        
        for i, match in enumerate(matches):
            section_name = match.group(1).strip().lower().replace(' ', '_')
            start_pos = match.end()
            
            # 确定这一节的结束位置
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(content)
            
            section_content = content[start_pos:end_pos].strip()
            sections[section_name] = section_content
        
        # 如果有内容在第一个标题之前，作为介绍部分
        if matches:
            intro_content = content[:matches[0].start()].strip()
            if intro_content:
                sections['intro'] = intro_content
        
        return sections
    
    def get_prompt_template(self, filename: str, section: str = 'main') -> str:
        """获取提示词模板
        
        Args:
            filename: 文件名
            section: 部分名称，默认为 'main'
            
        Returns:
            str: 提示词模板
        """
        prompt_data = self.load_prompt(filename)
        
        if not prompt_data:
            return ""
        
        # 对于数据质量相关的模板，返回完整内容
        if filename.startswith('data_quality'):
            return prompt_data.get('raw_content', '')
        
        sections = prompt_data.get('sections', {})
        
        # 尝试获取指定部分
        if section in sections:
            return sections[section]
        
        # 如果没有指定部分，尝试获取 main 部分
        if 'main' in sections:
            return sections['main']
        
        # 如果都没有，返回完整内容
        return prompt_data.get('raw_content', '')
    
    def get_prompt_metadata(self, filename: str) -> Dict[str, Any]:
        """获取提示词元数据
        
        Args:
            filename: 文件名
            
        Returns:
            Dict: 元数据
        """
        prompt_data = self.load_prompt(filename)
        return prompt_data.get('metadata', {})
    
    def list_available_prompts(self) -> List[str]:
        """列出所有可用的提示词文件
        
        Returns:
            List: 文件名列表
        """
        return [f.stem for f in self.prompts_dir.glob("*.md")]
    
    def create_prompt_template(self, 
                             filename: str, 
                             content: str, 
                             metadata: Dict[str, Any] = None) -> bool:
        """创建新的提示词模板文件
        
        Args:
            filename: 文件名
            content: 提示词内容
            metadata: 元数据
            
        Returns:
            bool: 是否创建成功
        """
        try:
            file_path = self.prompts_dir / f"{filename}.md"
            
            # 构建文件内容
            file_content = ""
            
            if metadata:
                file_content += "---\n"
                file_content += yaml.dump(metadata, default_flow_style=False, allow_unicode=True)
                file_content += "---\n\n"
            
            file_content += content
            
            file_path.write_text(file_content, encoding='utf-8')
            logger.info(f"创建提示词文件: {filename}")
            
            # 清除缓存以便重新加载
            if filename in self.prompts_cache:
                del self.prompts_cache[filename]
            
            return True
            
        except Exception as e:
            logger.error(f"创建提示词文件失败 {filename}: {e}")
            return False


# 全局加载器实例
prompt_loader = PromptLoader() 