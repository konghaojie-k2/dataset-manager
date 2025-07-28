"""MCP 外部工具注册表"""

from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod
from loguru import logger


class ExternalTool(ABC):
    """外部工具抽象类"""
    
    def __init__(self, name: str, description: str):
        """初始化外部工具
        
        Args:
            name: 工具名称
            description: 工具描述
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """执行工具"""
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """获取工具参数模式"""
        pass


class DatabaseQueryTool(ExternalTool):
    """数据库查询工具"""
    
    def __init__(self, connector_name: str):
        """初始化数据库查询工具
        
        Args:
            connector_name: 数据库连接器名称
        """
        super().__init__(
            name="database_query",
            description="执行数据库查询"
        )
        self.connector_name = connector_name
    
    async def execute(self, query: str, **kwargs) -> Any:
        """执行数据库查询
        
        Args:
            query: SQL查询语句
            **kwargs: 其他参数
            
        Returns:
            Any: 查询结果
        """
        try:
            logger.info(f"执行数据库查询: {query}")
            
            # 这里应该通过MCP服务器管理器获取连接器并执行查询
            # 暂时返回模拟结果
            return {
                "connector": self.connector_name,
                "query": query,
                "results": [],
                "row_count": 0
            }
            
        except Exception as e:
            logger.error(f"数据库查询执行失败: {e}")
            raise
    
    def get_schema(self) -> Dict[str, Any]:
        """获取工具参数模式"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL查询语句"
                }
            },
            "required": ["query"]
        }


class APICallTool(ExternalTool):
    """API调用工具"""
    
    def __init__(self, connector_name: str):
        """初始化API调用工具
        
        Args:
            connector_name: API连接器名称
        """
        super().__init__(
            name="api_call",
            description="调用外部API"
        )
        self.connector_name = connector_name
    
    async def execute(self, endpoint: str, method: str = "GET", **kwargs) -> Any:
        """执行API调用
        
        Args:
            endpoint: API端点
            method: HTTP方法
            **kwargs: 其他参数
            
        Returns:
            Any: API响应
        """
        try:
            logger.info(f"执行API调用: {method} {endpoint}")
            
            # 这里应该通过MCP服务器管理器获取连接器并执行API调用
            # 暂时返回模拟结果
            return {
                "connector": self.connector_name,
                "endpoint": endpoint,
                "method": method,
                "status_code": 200,
                "data": {}
            }
            
        except Exception as e:
            logger.error(f"API调用执行失败: {e}")
            raise
    
    def get_schema(self) -> Dict[str, Any]:
        """获取工具参数模式"""
        return {
            "type": "object",
            "properties": {
                "endpoint": {
                    "type": "string",
                    "description": "API端点路径"
                },
                "method": {
                    "type": "string",
                    "description": "HTTP方法",
                    "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]
                }
            },
            "required": ["endpoint"]
        }


class DataVisualizationTool(ExternalTool):
    """数据可视化工具"""
    
    def __init__(self):
        """初始化数据可视化工具"""
        super().__init__(
            name="data_visualization",
            description="生成数据可视化图表"
        )
    
    async def execute(self, data: List[Dict], chart_type: str, **kwargs) -> Any:
        """生成可视化图表
        
        Args:
            data: 数据列表
            chart_type: 图表类型
            **kwargs: 其他参数
            
        Returns:
            Any: 图表结果
        """
        try:
            logger.info(f"生成可视化图表: {chart_type}")
            
            # 这里实现具体的可视化逻辑
            # 可以集成matplotlib、plotly等库
            
            return {
                "chart_type": chart_type,
                "data_points": len(data),
                "chart_url": f"/charts/{chart_type}_chart.png",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"数据可视化失败: {e}")
            raise
    
    def get_schema(self) -> Dict[str, Any]:
        """获取工具参数模式"""
        return {
            "type": "object",
            "properties": {
                "data": {
                    "type": "array",
                    "description": "要可视化的数据"
                },
                "chart_type": {
                    "type": "string",
                    "description": "图表类型",
                    "enum": ["bar", "line", "scatter", "pie", "histogram"]
                }
            },
            "required": ["data", "chart_type"]
        }


class ExternalToolsRegistry:
    """外部工具注册表"""
    
    def __init__(self):
        """初始化工具注册表"""
        self.tools: Dict[str, ExternalTool] = {}
        
        # 注册默认工具
        self._register_default_tools()
        
        logger.info("外部工具注册表初始化完成")
    
    def _register_default_tools(self):
        """注册默认工具"""
        # 这里可以注册一些默认的工具
        self.register_tool(DataVisualizationTool())
    
    def register_tool(self, tool: ExternalTool):
        """注册工具
        
        Args:
            tool: 外部工具实例
        """
        self.tools[tool.name] = tool
        logger.info(f"工具已注册: {tool.name}")
    
    def unregister_tool(self, tool_name: str) -> bool:
        """注销工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            bool: 是否注销成功
        """
        if tool_name in self.tools:
            del self.tools[tool_name]
            logger.info(f"工具已注销: {tool_name}")
            return True
        return False
    
    def get_tool(self, tool_name: str) -> Optional[ExternalTool]:
        """获取工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Optional[ExternalTool]: 工具实例
        """
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具
        
        Returns:
            List[Dict[str, Any]]: 工具列表
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "schema": tool.get_schema()
            }
            for tool in self.tools.values()
        ]
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """执行工具
        
        Args:
            tool_name: 工具名称
            **kwargs: 工具参数
            
        Returns:
            Any: 执行结果
        """
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"工具不存在: {tool_name}")
        
        return await tool.execute(**kwargs) 