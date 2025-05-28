"""可视化工具"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from loguru import logger

# 设置matplotlib中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class VisualizationTools:
    """可视化工具类"""
    
    def __init__(self, style: str = "whitegrid", palette: str = "husl"):
        """初始化可视化工具
        
        Args:
            style: seaborn样式
            palette: 调色板
        """
        sns.set_style(style)
        sns.set_palette(palette)
        self.figure_size = (12, 8)
    
    def plot_distribution(
        self, 
        data: pd.Series, 
        title: str = None,
        save_path: Path = None
    ) -> plt.Figure:
        """绘制数据分布图
        
        Args:
            data: 数据序列
            title: 图表标题
            save_path: 保存路径
            
        Returns:
            plt.Figure: 图表对象
        """
        fig, axes = plt.subplots(1, 2, figsize=self.figure_size)
        
        # 直方图
        axes[0].hist(data.dropna(), bins=30, alpha=0.7, edgecolor='black')
        axes[0].set_title(f'{title or data.name} - 直方图')
        axes[0].set_xlabel('值')
        axes[0].set_ylabel('频次')
        
        # 箱线图
        axes[1].boxplot(data.dropna())
        axes[1].set_title(f'{title or data.name} - 箱线图')
        axes[1].set_ylabel('值')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"图表已保存到: {save_path}")
        
        return fig
    
    def plot_correlation_matrix(
        self, 
        data: pd.DataFrame, 
        title: str = "相关性矩阵",
        save_path: Path = None
    ) -> plt.Figure:
        """绘制相关性矩阵热力图
        
        Args:
            data: 数据框
            title: 图表标题
            save_path: 保存路径
            
        Returns:
            plt.Figure: 图表对象
        """
        # 只选择数值型列
        numeric_data = data.select_dtypes(include=[np.number])
        
        if numeric_data.empty:
            logger.warning("没有数值型列可以计算相关性")
            return None
        
        corr_matrix = numeric_data.corr()
        
        fig, ax = plt.subplots(figsize=self.figure_size)
        
        # 创建热力图
        sns.heatmap(
            corr_matrix, 
            annot=True, 
            cmap='coolwarm', 
            center=0,
            square=True,
            fmt='.2f',
            ax=ax
        )
        
        ax.set_title(title)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"相关性矩阵已保存到: {save_path}")
        
        return fig
    
    def plot_missing_data(
        self, 
        data: pd.DataFrame, 
        title: str = "缺失数据分析",
        save_path: Path = None
    ) -> plt.Figure:
        """绘制缺失数据可视化
        
        Args:
            data: 数据框
            title: 图表标题
            save_path: 保存路径
            
        Returns:
            plt.Figure: 图表对象
        """
        missing_data = data.isnull().sum()
        missing_percent = (missing_data / len(data)) * 100
        
        # 只显示有缺失值的列
        missing_data = missing_data[missing_data > 0]
        missing_percent = missing_percent[missing_percent > 0]
        
        if missing_data.empty:
            logger.info("数据中没有缺失值")
            return None
        
        fig, axes = plt.subplots(1, 2, figsize=self.figure_size)
        
        # 缺失值数量
        missing_data.plot(kind='bar', ax=axes[0])
        axes[0].set_title('缺失值数量')
        axes[0].set_xlabel('列名')
        axes[0].set_ylabel('缺失值数量')
        axes[0].tick_params(axis='x', rotation=45)
        
        # 缺失值百分比
        missing_percent.plot(kind='bar', ax=axes[1], color='orange')
        axes[1].set_title('缺失值百分比')
        axes[1].set_xlabel('列名')
        axes[1].set_ylabel('缺失值百分比 (%)')
        axes[1].tick_params(axis='x', rotation=45)
        
        plt.suptitle(title)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"缺失数据图表已保存到: {save_path}")
        
        return fig
    
    def plot_categorical_distribution(
        self, 
        data: pd.Series, 
        top_n: int = 10,
        title: str = None,
        save_path: Path = None
    ) -> plt.Figure:
        """绘制分类变量分布图
        
        Args:
            data: 分类数据序列
            top_n: 显示前N个类别
            title: 图表标题
            save_path: 保存路径
            
        Returns:
            plt.Figure: 图表对象
        """
        value_counts = data.value_counts().head(top_n)
        
        fig, axes = plt.subplots(1, 2, figsize=self.figure_size)
        
        # 条形图
        value_counts.plot(kind='bar', ax=axes[0])
        axes[0].set_title(f'{title or data.name} - 分布条形图')
        axes[0].set_xlabel('类别')
        axes[0].set_ylabel('数量')
        axes[0].tick_params(axis='x', rotation=45)
        
        # 饼图
        value_counts.plot(kind='pie', ax=axes[1], autopct='%1.1f%%')
        axes[1].set_title(f'{title or data.name} - 分布饼图')
        axes[1].set_ylabel('')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"分类分布图表已保存到: {save_path}")
        
        return fig
    
    def create_data_overview_dashboard(
        self, 
        data: pd.DataFrame, 
        save_dir: Path = None
    ) -> Dict[str, plt.Figure]:
        """创建数据概览仪表板
        
        Args:
            data: 数据框
            save_dir: 保存目录
            
        Returns:
            Dict[str, plt.Figure]: 图表字典
        """
        figures = {}
        
        if save_dir:
            save_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. 缺失数据分析
        missing_fig = self.plot_missing_data(
            data, 
            save_path=save_dir / "missing_data.png" if save_dir else None
        )
        if missing_fig:
            figures["missing_data"] = missing_fig
        
        # 2. 相关性矩阵
        corr_fig = self.plot_correlation_matrix(
            data,
            save_path=save_dir / "correlation_matrix.png" if save_dir else None
        )
        if corr_fig:
            figures["correlation_matrix"] = corr_fig
        
        # 3. 数值型变量分布
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for i, col in enumerate(numeric_cols[:5]):  # 最多显示5个数值型列
            fig = self.plot_distribution(
                data[col], 
                title=col,
                save_path=save_dir / f"distribution_{col}.png" if save_dir else None
            )
            figures[f"distribution_{col}"] = fig
        
        # 4. 分类型变量分布
        categorical_cols = data.select_dtypes(include=['object', 'category']).columns
        for i, col in enumerate(categorical_cols[:3]):  # 最多显示3个分类型列
            fig = self.plot_categorical_distribution(
                data[col],
                title=col,
                save_path=save_dir / f"categorical_{col}.png" if save_dir else None
            )
            figures[f"categorical_{col}"] = fig
        
        logger.info(f"生成了 {len(figures)} 个图表")
        return figures
    
    def close_all_figures(self):
        """关闭所有图表"""
        plt.close('all')
        logger.info("已关闭所有图表") 