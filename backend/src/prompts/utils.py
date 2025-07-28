"""
提示词工具函数模块

提供提示词模板的应用和处理功能
"""

from typing import Dict, Any, Union
import json
from string import Template


def apply_prompt_template(template: str, state: Dict[str, Any]) -> str:
    """应用提示词模板
    
    Args:
        template: 提示词模板字符串
        state: 状态字典，用于填充模板
        
    Returns:
        str: 填充后的提示词
    """
    try:
        # 使用 string.Template 进行安全的模板替换
        template_obj = Template(template)
        
        # 准备模板变量
        template_vars = {
            "state": format_state_for_prompt(state)
        }
        
        # 添加状态中的所有键值对作为模板变量
        for key, value in state.items():
            if isinstance(value, (str, int, float, bool)):
                template_vars[key] = str(value)
            elif isinstance(value, (list, dict)):
                template_vars[key] = json.dumps(value, ensure_ascii=False, default=str)
            else:
                template_vars[key] = str(value)
        
        # 应用模板
        return template_obj.safe_substitute(template_vars)
        
    except Exception as e:
        # 如果模板应用失败，返回原始模板
        return template


def format_state_for_prompt(state: Dict[str, Any]) -> str:
    """格式化状态信息用于提示词
    
    Args:
        state: 状态字典
        
    Returns:
        str: 格式化后的状态字符串
    """
    try:
        # 过滤掉不需要在提示词中显示的字段
        filtered_state = {}
        exclude_keys = {
            "dataframe", "messages", "graph", "checkpointer", 
            "_reasoning_llm", "_basic_llm", "llm_config"
        }
        
        for key, value in state.items():
            if key not in exclude_keys:
                if value is not None:
                    filtered_state[key] = value
        
        # 格式化为易读的字符串
        return json.dumps(filtered_state, ensure_ascii=False, indent=2, default=str)
        
    except Exception:
        return str(state)


def create_system_prompt(role: str, tasks: list, context: str = "") -> str:
    """创建系统提示词
    
    Args:
        role: 角色描述
        tasks: 任务列表
        context: 额外上下文
        
    Returns:
        str: 系统提示词
    """
    tasks_text = "\n".join([f"{i+1}. {task}" for i, task in enumerate(tasks)])
    
    prompt = f"""你是一个{role}。

你的任务是：
{tasks_text}"""
    
    if context:
        prompt += f"\n\n{context}"
    
    return prompt


def create_user_prompt(instruction: str, data: Dict[str, Any] = None) -> str:
    """创建用户提示词
    
    Args:
        instruction: 指令描述
        data: 相关数据
        
    Returns:
        str: 用户提示词
    """
    prompt = instruction
    
    if data:
        data_text = json.dumps(data, ensure_ascii=False, indent=2, default=str)
        prompt += f"\n\n相关数据：\n{data_text}"
    
    return prompt


def merge_prompts(*prompts: str, separator: str = "\n\n") -> str:
    """合并多个提示词
    
    Args:
        *prompts: 要合并的提示词
        separator: 分隔符
        
    Returns:
        str: 合并后的提示词
    """
    return separator.join(filter(None, prompts))


def truncate_prompt(prompt: str, max_length: int = 4000) -> str:
    """截断过长的提示词
    
    Args:
        prompt: 原始提示词
        max_length: 最大长度
        
    Returns:
        str: 截断后的提示词
    """
    if len(prompt) <= max_length:
        return prompt
    
    # 保留开头和结尾，中间用省略号替代
    start_length = max_length // 2 - 50
    end_length = max_length // 2 - 50
    
    return (
        prompt[:start_length] + 
        "\n\n... [内容过长，已省略] ...\n\n" + 
        prompt[-end_length:]
    ) 