#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能数据生成服务

根据描述自动生成示例数据集
"""

from typing import Dict, Any, List, Optional
from loguru import logger
import pandas as pd
import random
from datetime import datetime, timedelta


class DataGenerationService:
    """智能数据生成服务"""
    
    def __init__(self):
        self.generators = {
            "user": self._generate_user_data,
            "sales": self._generate_sales_data,
            "log": self._generate_log_data,
            "iot": self._generate_iot_data,
            "financial": self._generate_financial_data,
        }
        logger.info("智能数据生成服务初始化完成")
    
    async def generate(
        self,
        data_type: str,
        row_count: int = 100,
        **options
    ) -> pd.DataFrame:
        """生成示例数据
        
        Args:
            data_type: 数据类型 (user, sales, log, iot, financial)
            row_count: 行数
            **options: 其他选项
            
        Returns:
            生成的数据框
        """
        logger.info(f"生成数据: {data_type}, {row_count} 行")
        
        generator = self.generators.get(data_type)
        if not generator:
            raise ValueError(f"不支持的数据类型: {data_type}")
        
        return await generator(row_count, **options)
    
    async def _generate_user_data(self, row_count: int, **options) -> pd.DataFrame:
        """生成用户数据"""
        names = ["张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十"]
        cities = ["北京", "上海", "深圳", "广州", "杭州", "成都"]
        industries = ["IT", "金融", "制造", "医疗", "教育", "零售"]
        
        data = {
            "user_id": range(1, row_count + 1),
            "user_name": [random.choice(names) for _ in range(row_count)],
            "age": [random.randint(18, 65) for _ in range(row_count)],
            "city": [random.choice(cities) for _ in range(row_count)],
            "industry": [random.choice(industries) for _ in range(row_count)],
            "salary": [random.randint(5000, 50000) for _ in range(row_count)],
            "register_date": [
                (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d")
                for _ in range(row_count)
            ],
            "is_active": [random.choice([True, False]) for _ in range(row_count)],
        }
        
        return pd.DataFrame(data)
    
    async def _generate_sales_data(self, row_count: int, **options) -> pd.DataFrame:
        """生成销售数据"""
        products = ["产品A", "产品B", "产品C", "产品D", "产品E"]
        channels = ["线上", "线下", "代理", "直销"]
        regions = ["华东", "华南", "华北", "西南", "西北"]
        
        base_date = datetime.now() - timedelta(days=180)
        
        data = {
            "order_id": range(1, row_count + 1),
            "order_date": [
                (base_date + timedelta(days=random.randint(0, 180))).strftime("%Y-%m-%d")
                for _ in range(row_count)
            ],
            "product": [random.choice(products) for _ in range(row_count)],
            "quantity": [random.randint(1, 100) for _ in range(row_count)],
            "unit_price": [round(random.uniform(10, 1000), 2) for _ in range(row_count)],
            "channel": [random.choice(channels) for _ in range(row_count)],
            "region": [random.choice(regions) for _ in range(row_count)],
            "customer_id": [random.randint(1, 1000) for _ in range(row_count)],
        }
        
        df = pd.DataFrame(data)
        df["total_amount"] = df["quantity"] * df["unit_price"]
        
        return df
    
    async def _generate_log_data(self, row_count: int, **options) -> pd.DataFrame:
        """生成日志数据"""
        log_levels = ["INFO", "WARNING", "ERROR", "DEBUG"]
        services = ["api", "auth", "payment", "notification", "search"]
        methods = ["GET", "POST", "PUT", "DELETE"]
        status_codes = [200, 201, 400, 401, 403, 404, 500, 502]
        
        base_time = datetime.now() - timedelta(hours=24)
        
        data = {
            "timestamp": [
                (base_time + timedelta(seconds=random.randint(0, 86400))).strftime("%Y-%m-%d %H:%M:%S")
                for _ in range(row_count)
            ],
            "level": [random.choice(log_levels) for _ in range(row_count)],
            "service": [random.choice(services) for _ in range(row_count)],
            "method": [random.choice(methods) for _ in range(row_count)],
            "path": [f"/api/{random.choice(['user', 'order', 'product', 'data'])}" for _ in range(row_count)],
            "status_code": [random.choice(status_codes) for _ in range(row_count)],
            "response_time_ms": [random.randint(10, 5000) for _ in range(row_count)],
            "ip": [f"192.168.{random.randint(1,255)}.{random.randint(1,255)}" for _ in range(row_count)],
        }
        
        return pd.DataFrame(data)
    
    async def _generate_iot_data(self, row_count: int, **options) -> pd.DataFrame:
        """生成 IoT 数据"""
        device_ids = [f"device_{i:03d}" for i in range(1, 21)]
        sensors = ["temperature", "humidity", "pressure", "vibration"]
        
        base_time = datetime.now() - timedelta(hours=24)
        
        data = {
            "timestamp": [
                (base_time + timedelta(minutes=random.randint(0, 1440))).strftime("%Y-%m-%d %H:%M:%S")
                for _ in range(row_count)
            ],
            "device_id": [random.choice(device_ids) for _ in range(row_count)],
            "sensor_type": [random.choice(sensors) for _ in range(row_count)],
            "value": [round(random.uniform(0, 100), 2) for _ in range(row_count)],
            "unit": ["°C", "%", "Pa", "mm/s"],
            "battery": [random.randint(0, 100) for _ in range(row_count)],
            "signal_strength": [random.randint(-100, -30) for _ in range(row_count)],
        }
        
        df = pd.DataFrame(data)
        # 为每行分配正确的单位
        df["unit"] = df["sensor_type"].map({
            "temperature": "°C",
            "humidity": "%",
            "pressure": "Pa",
            "vibration": "mm/s"
        })
        
        return df
    
    async def _generate_financial_data(self, row_count: int, **options) -> pd.DataFrame:
        """生成金融数据"""
        account_types = ["储蓄", "信用卡", "理财", "基金"]
        transaction_types = ["收入", "支出", "转账", "投资", "还款"]
        
        base_date = datetime.now() - timedelta(days=365)
        
        data = {
            "transaction_id": range(1, row_count + 1),
            "transaction_date": [
                (base_date + timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
                for _ in range(row_count)
            ],
            "account_id": [f"ACC{random.randint(1000, 9999)}" for _ in range(row_count)],
            "account_type": [random.choice(account_types) for _ in range(row_count)],
            "transaction_type": [random.choice(transaction_types) for _ in range(row_count)],
            "amount": [round(random.uniform(100, 50000), 2) for _ in range(row_count)],
            "balance": [round(random.uniform(0, 100000), 2) for _ in range(row_count)],
            "category": [random.choice(["餐饮", "交通", "购物", "娱乐", "医疗", "教育", "投资"]) for _ in range(row_count)],
        }
        
        return pd.DataFrame(data)
    
    def get_available_types(self) -> List[str]:
        """获取可用的数据类型"""
        return list(self.generators.keys())


# 导出
data_generation_service = DataGenerationService()

__all__ = ['DataGenerationService', 'data_generation_service']
