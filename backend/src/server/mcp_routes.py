"""MCP 相关的API路由"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from loguru import logger

from ..mcp import MCPServerManager, ExternalToolsRegistry
from ..schemas.mcp import MCPServerConfig, MCPToolCall
from .dependencies import get_dataset_service


# 创建MCP路由器
mcp_router = APIRouter(prefix="/api/v1/mcp", tags=["mcp"])

# 全局MCP管理器实例
mcp_manager: MCPServerManager = None
tools_registry: ExternalToolsRegistry = None


@mcp_router.post("/servers")
async def start_mcp_server(config: MCPServerConfig):
    """启动MCP服务器
    
    Args:
        config: 服务器配置
        
    Returns:
        dict: 启动结果
    """
    try:
        global mcp_manager
        if not mcp_manager:
            mcp_manager = MCPServerManager()
        
        success = await mcp_manager.start_server(config.name, config.model_dump())
        
        if success:
            return {
                "success": True,
                "message": f"MCP服务器启动成功: {config.name}",
                "server_name": config.name
            }
        else:
            raise HTTPException(status_code=500, detail="MCP服务器启动失败")
            
    except Exception as e:
        logger.error(f"启动MCP服务器失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@mcp_router.delete("/servers/{server_name}")
async def stop_mcp_server(server_name: str):
    """停止MCP服务器
    
    Args:
        server_name: 服务器名称
        
    Returns:
        dict: 停止结果
    """
    try:
        global mcp_manager
        if not mcp_manager:
            raise HTTPException(status_code=404, detail="MCP管理器未初始化")
        
        success = await mcp_manager.stop_server(server_name)
        
        if success:
            return {
                "success": True,
                "message": f"MCP服务器已停止: {server_name}"
            }
        else:
            raise HTTPException(status_code=404, detail="MCP服务器不存在")
            
    except Exception as e:
        logger.error(f"停止MCP服务器失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@mcp_router.get("/servers")
async def list_mcp_servers():
    """列出所有MCP服务器
    
    Returns:
        List[Dict[str, Any]]: 服务器列表
    """
    try:
        global mcp_manager
        if not mcp_manager:
            return []
        
        servers = mcp_manager.list_servers()
        return servers
        
    except Exception as e:
        logger.error(f"获取MCP服务器列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@mcp_router.get("/servers/{server_name}")
async def get_mcp_server_status(server_name: str):
    """获取MCP服务器状态
    
    Args:
        server_name: 服务器名称
        
    Returns:
        Dict[str, Any]: 服务器状态
    """
    try:
        global mcp_manager
        if not mcp_manager:
            raise HTTPException(status_code=404, detail="MCP管理器未初始化")
        
        status = mcp_manager.get_server_status(server_name)
        
        if status:
            return status
        else:
            raise HTTPException(status_code=404, detail="MCP服务器不存在")
            
    except Exception as e:
        logger.error(f"获取MCP服务器状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@mcp_router.post("/tools/call")
async def call_mcp_tool(tool_call: MCPToolCall):
    """调用MCP工具
    
    Args:
        tool_call: 工具调用请求
        
    Returns:
        Any: 工具执行结果
    """
    try:
        global mcp_manager
        if not mcp_manager:
            raise HTTPException(status_code=404, detail="MCP管理器未初始化")
        
        result = await mcp_manager.call_server_tool(
            tool_call.server_name,
            tool_call.tool_name,
            **tool_call.parameters
        )
        
        if result is not None:
            return {
                "success": True,
                "result": result
            }
        else:
            raise HTTPException(status_code=404, detail="工具调用失败")
            
    except Exception as e:
        logger.error(f"调用MCP工具失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@mcp_router.get("/tools")
async def list_external_tools():
    """列出所有外部工具
    
    Returns:
        List[Dict[str, Any]]: 工具列表
    """
    try:
        global tools_registry
        if not tools_registry:
            tools_registry = ExternalToolsRegistry()
        
        tools = tools_registry.list_tools()
        return tools
        
    except Exception as e:
        logger.error(f"获取外部工具列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@mcp_router.post("/tools/{tool_name}/execute")
async def execute_external_tool(tool_name: str, parameters: Dict[str, Any]):
    """执行外部工具
    
    Args:
        tool_name: 工具名称
        parameters: 工具参数
        
    Returns:
        Any: 执行结果
    """
    try:
        global tools_registry
        if not tools_registry:
            tools_registry = ExternalToolsRegistry()
        
        result = await tools_registry.execute_tool(tool_name, **parameters)
        
        return {
            "success": True,
            "tool_name": tool_name,
            "result": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"执行外部工具失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 