"""数据质量分析工具"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import re
from collections import Counter
from loguru import logger

from ..schemas.data_quality import (
    QualityLevel, ColumnType, TimeQualityIssue, TimeColumnQuality,
    ParameterQualityIssue, ParameterColumnQuality, CategoryQualityIssue,
    CategoryColumnQuality, DataQualityReport
)
from ..core.fast_data_processor import create_fast_processor, FastDataProcessor


class DataQualityAnalyzer:
    """数据质量分析器（已优化）"""
    
    def __init__(self):
        """初始化数据质量分析器"""
        self.data: Optional[pd.DataFrame] = None  # 保留兼容性
        self.processor: Optional[FastDataProcessor] = None
        self.column_types: Dict[str, ColumnType] = {}
        
    def load_data(self, file_path: Path, engine_type: Optional[str] = None) -> pd.DataFrame:
        """加载数据（使用 FastDataProcessor）
        
        Args:
            file_path: 文件路径
            engine_type: 引擎类型（可选，自动选择）
            
        Returns:
            pd.DataFrame: 加载的数据
        """
        try:
            # 创建快速处理器
            self.processor = create_fast_processor(file_path, engine_type)
            
            # 加载数据（使用采样）
            self.data = self.processor.load_sample()
            
            logger.info(f"成功加载数据，引擎: {self.processor.engine_type}")
            return self.data
            
        except Exception as e:
            logger.error(f"数据加载失败: {e}")
            raise
    
    def close(self):
        """关闭处理器，释放资源"""
        if self.processor:
            self.processor.close()
            self.processor = None
        self.data = None
        logger.info("DataQualityAnalyzer 已关闭")
    
    def set_column_types(self, column_types: Dict[str, ColumnType]):
        """设置列类型"""
        self.column_types = column_types
    
    def auto_detect_column_types(self) -> Dict[str, ColumnType]:
        """自动检测列类型"""
        if self.data is None:
            raise ValueError("请先加载数据")
        
        detected_types = {}
        
        for col in self.data.columns:
            col_data = self.data[col].dropna()
            
            if len(col_data) == 0:
                continue
                
            # 检测时间列
            if self._is_time_column(col_data):
                detected_types[col] = ColumnType.TIME
            # 检测数值参数列
            elif pd.api.types.is_numeric_dtype(col_data):
                detected_types[col] = ColumnType.PARAMETER
            # 其他作为类目列
            else:
                detected_types[col] = ColumnType.CATEGORY
        
        self.column_types = detected_types
        return detected_types
    
    def _is_time_column(self, series: pd.Series) -> bool:
        """判断是否为时间列"""
        # 尝试解析前几个值
        sample_size = min(10, len(series))
        sample = series.head(sample_size)
        
        time_count = 0
        for value in sample:
            if self._try_parse_datetime(str(value)):
                time_count += 1
        
        return time_count / sample_size > 0.7
    
    def _try_parse_datetime(self, value: str) -> bool:
        """尝试解析日期时间"""
        common_formats = [
            '%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y',
            '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S',
            '%d-%m-%Y', '%d.%m.%Y', '%Y.%m.%d'
        ]
        
        for fmt in common_formats:
            try:
                datetime.strptime(value, fmt)
                return True
            except ValueError:
                continue
        
        # 尝试pandas的自动解析
        try:
            pd.to_datetime(value)
            return True
        except:
            return False
    
    def analyze_time_column(self, column_name: str) -> TimeColumnQuality:
        """分析时间列质量"""
        if self.data is None:
            raise ValueError("请先加载数据")
        
        if column_name not in self.data.columns:
            raise ValueError(f"列 {column_name} 不存在")
        
        col_data = self.data[column_name].dropna()
        
        # 格式一致性分析
        format_analysis = self._analyze_time_format_consistency(col_data)
        
        # 范围合理性分析
        range_analysis = self._analyze_time_range_validity(col_data)
        
        # 连续性分析
        continuity_analysis = self._analyze_time_continuity(col_data)
        
        # 精度分析
        precision_analysis = self._analyze_time_precision(col_data)
        
        # 异常值检测
        anomalies = self._detect_time_anomalies(col_data, column_name)
        
        # 计算各项得分
        format_score = format_analysis['consistency_score']
        range_score = range_analysis['validity_score']
        continuity_score = continuity_analysis['continuity_score']
        precision_score = precision_analysis['consistency_score']
        anomaly_score = max(0, 100 - len(anomalies) * 5)  # 每个异常扣5分
        
        # 综合得分
        overall_score = (format_score + range_score + continuity_score + 
                        precision_score + anomaly_score) / 5
        
        # 质量等级
        quality_level = self._get_quality_level(overall_score)
        
        # 生成建议
        recommendations = self._generate_time_recommendations(
            format_analysis, range_analysis, continuity_analysis, 
            precision_analysis, anomalies
        )
        
        return TimeColumnQuality(
            column_name=column_name,
            format_consistency=format_analysis,
            detected_formats=format_analysis['detected_formats'],
            format_consistency_score=format_score,
            time_range=range_analysis,
            range_validity_score=range_score,
            continuity_analysis=continuity_analysis,
            continuity_score=continuity_score,
            precision_info=precision_analysis,
            precision_consistency_score=precision_score,
            anomalies=anomalies,
            anomaly_score=anomaly_score,
            overall_score=overall_score,
            quality_level=quality_level,
            recommendations=recommendations
        )
    
    def _analyze_time_format_consistency(self, series: pd.Series) -> Dict[str, Any]:
        """分析时间格式一致性"""
        formats = []
        parsed_count = 0
        
        for value in series.head(100):  # 采样分析
            str_value = str(value)
            detected_format = self._detect_time_format(str_value)
            if detected_format:
                formats.append(detected_format)
                parsed_count += 1
        
        format_counter = Counter(formats)
        unique_formats = list(format_counter.keys())
        
        # 一致性得分：主要格式占比
        if len(unique_formats) == 0:
            consistency_score = 0
        elif len(unique_formats) == 1:
            consistency_score = 100
        else:
            main_format_ratio = format_counter.most_common(1)[0][1] / len(formats)
            consistency_score = main_format_ratio * 100
        
        return {
            'detected_formats': unique_formats,
            'format_distribution': dict(format_counter),
            'consistency_score': consistency_score,
            'parsed_ratio': parsed_count / len(series) * 100
        }
    
    def _detect_time_format(self, value: str) -> Optional[str]:
        """检测时间格式"""
        patterns = {
            r'^\d{4}-\d{2}-\d{2}$': 'YYYY-MM-DD',
            r'^\d{4}/\d{2}/\d{2}$': 'YYYY/MM/DD',
            r'^\d{2}/\d{2}/\d{4}$': 'DD/MM/YYYY',
            r'^\d{2}-\d{2}-\d{4}$': 'DD-MM-YYYY',
            r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$': 'YYYY-MM-DD HH:MM:SS',
            r'^\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}$': 'YYYY/MM/DD HH:MM:SS',
        }
        
        for pattern, format_name in patterns.items():
            if re.match(pattern, value):
                return format_name
        
        return None
    
    def _analyze_time_range_validity(self, series: pd.Series) -> Dict[str, Any]:
        """分析时间范围合理性"""
        try:
            # 尝试转换为datetime
            datetime_series = pd.to_datetime(series, errors='coerce')
            valid_dates = datetime_series.dropna()
            
            if len(valid_dates) == 0:
                return {
                    'min_date': None,
                    'max_date': None,
                    'date_range_days': 0,
                    'validity_score': 0,
                    'issues': ['无法解析任何有效日期']
                }
            
            min_date = valid_dates.min()
            max_date = valid_dates.max()
            date_range = (max_date - min_date).days
            
            # 合理性检查
            issues = []
            validity_score = 100
            
            # 检查未来日期
            future_dates = valid_dates[valid_dates > datetime.now()]
            if len(future_dates) > 0:
                issues.append(f"发现 {len(future_dates)} 个未来日期")
                validity_score -= 20
            
            # 检查过于久远的日期
            very_old_dates = valid_dates[valid_dates < datetime(1900, 1, 1)]
            if len(very_old_dates) > 0:
                issues.append(f"发现 {len(very_old_dates)} 个过于久远的日期")
                validity_score -= 20
            
            # 检查无效日期比例
            invalid_ratio = (len(series) - len(valid_dates)) / len(series)
            if invalid_ratio > 0.1:
                issues.append(f"无效日期比例过高: {invalid_ratio:.1%}")
                validity_score -= invalid_ratio * 100
            
            return {
                'min_date': min_date.isoformat() if pd.notna(min_date) else None,
                'max_date': max_date.isoformat() if pd.notna(max_date) else None,
                'date_range_days': date_range,
                'valid_count': len(valid_dates),
                'invalid_count': len(series) - len(valid_dates),
                'validity_score': max(0, validity_score),
                'issues': issues
            }
            
        except Exception as e:
            return {
                'min_date': None,
                'max_date': None,
                'date_range_days': 0,
                'validity_score': 0,
                'issues': [f'日期解析错误: {str(e)}']
            }
    
    def _analyze_time_continuity(self, series: pd.Series) -> Dict[str, Any]:
        """分析时间连续性"""
        try:
            datetime_series = pd.to_datetime(series, errors='coerce').dropna().sort_values()
            
            if len(datetime_series) < 2:
                return {
                    'continuity_score': 0,
                    'gaps': [],
                    'average_interval': None,
                    'interval_consistency': 0
                }
            
            # 计算时间间隔
            intervals = datetime_series.diff().dropna()
            
            # 检测间隔模式
            interval_seconds = intervals.dt.total_seconds()
            interval_mode = interval_seconds.mode().iloc[0] if len(interval_seconds.mode()) > 0 else None
            
            # 检测大的时间间隙
            if interval_mode:
                large_gaps = intervals[intervals.dt.total_seconds() > interval_mode * 3]
                gap_info = [
                    {
                        'start': datetime_series[datetime_series.diff() == gap].iloc[0].isoformat(),
                        'duration_days': gap.days,
                        'duration_seconds': gap.total_seconds()
                    }
                    for gap in large_gaps
                ]
            else:
                gap_info = []
            
            # 连续性得分
            if len(gap_info) == 0:
                continuity_score = 100
            else:
                # 根据间隙数量和大小计算得分
                gap_penalty = min(50, len(gap_info) * 10)
                continuity_score = max(0, 100 - gap_penalty)
            
            return {
                'continuity_score': continuity_score,
                'gaps': gap_info,
                'average_interval': interval_mode,
                'interval_consistency': self._calculate_interval_consistency(interval_seconds),
                'total_gaps': len(gap_info)
            }
            
        except Exception as e:
            return {
                'continuity_score': 0,
                'gaps': [],
                'average_interval': None,
                'interval_consistency': 0,
                'error': str(e)
            }
    
    def _calculate_interval_consistency(self, intervals: pd.Series) -> float:
        """计算间隔一致性"""
        if len(intervals) == 0:
            return 0
        
        # 计算变异系数
        mean_interval = intervals.mean()
        std_interval = intervals.std()
        
        if mean_interval == 0:
            return 0
        
        cv = std_interval / mean_interval
        # 变异系数越小，一致性越高
        consistency = max(0, 100 - cv * 100)
        return min(100, consistency)
    
    def _analyze_time_precision(self, series: pd.Series) -> Dict[str, Any]:
        """分析时间精度"""
        precision_levels = {
            'year': 0,
            'month': 0,
            'day': 0,
            'hour': 0,
            'minute': 0,
            'second': 0
        }
        
        sample_size = min(50, len(series))
        for value in series.head(sample_size):
            str_value = str(value)
            
            # 检测精度级别
            if re.search(r'\d{2}:\d{2}:\d{2}', str_value):
                precision_levels['second'] += 1
            elif re.search(r'\d{2}:\d{2}', str_value):
                precision_levels['minute'] += 1
            elif re.search(r'\d{2}:\d{2}', str_value):
                precision_levels['hour'] += 1
            elif re.search(r'\d{4}-\d{2}-\d{2}', str_value):
                precision_levels['day'] += 1
            elif re.search(r'\d{4}-\d{2}', str_value):
                precision_levels['month'] += 1
            elif re.search(r'\d{4}', str_value):
                precision_levels['year'] += 1
        
        # 找出主要精度级别
        main_precision = max(precision_levels, key=precision_levels.get)
        main_precision_count = precision_levels[main_precision]
        
        # 一致性得分
        consistency_score = (main_precision_count / sample_size) * 100
        
        return {
            'precision_distribution': precision_levels,
            'main_precision': main_precision,
            'consistency_score': consistency_score
        }
    
    def _detect_time_anomalies(self, series: pd.Series, column_name: str) -> List[TimeQualityIssue]:
        """检测时间异常值"""
        anomalies = []
        
        try:
            datetime_series = pd.to_datetime(series, errors='coerce')
            
            # 检测无法解析的日期
            invalid_mask = datetime_series.isna() & series.notna()
            if invalid_mask.any():
                invalid_indices = series[invalid_mask].index.tolist()
                anomalies.append(TimeQualityIssue(
                    issue_type="invalid_format",
                    description="无法解析的日期格式",
                    affected_rows=invalid_indices,
                    severity="high"
                ))
            
            # 检测未来日期
            valid_dates = datetime_series.dropna()
            if len(valid_dates) > 0:
                future_mask = valid_dates > datetime.now()
                if future_mask.any():
                    future_indices = valid_dates[future_mask].index.tolist()
                    anomalies.append(TimeQualityIssue(
                        issue_type="future_date",
                        description="未来日期",
                        affected_rows=future_indices,
                        severity="medium"
                    ))
                
                # 检测过于久远的日期
                old_mask = valid_dates < datetime(1900, 1, 1)
                if old_mask.any():
                    old_indices = valid_dates[old_mask].index.tolist()
                    anomalies.append(TimeQualityIssue(
                        issue_type="too_old",
                        description="过于久远的日期",
                        affected_rows=old_indices,
                        severity="medium"
                    ))
            
        except Exception as e:
            anomalies.append(TimeQualityIssue(
                issue_type="analysis_error",
                description=f"时间异常检测失败: {str(e)}",
                affected_rows=[],
                severity="high"
            ))
        
        return anomalies
    
    def _generate_time_recommendations(self, format_analysis, range_analysis, 
                                     continuity_analysis, precision_analysis, 
                                     anomalies) -> List[str]:
        """生成时间列改进建议"""
        recommendations = []
        
        # 格式建议
        if format_analysis['consistency_score'] < 80:
            recommendations.append("建议统一时间格式，提高数据一致性")
        
        # 范围建议
        if range_analysis['validity_score'] < 80:
            recommendations.append("检查并修正无效的日期值")
        
        # 连续性建议
        if continuity_analysis['continuity_score'] < 70:
            recommendations.append("注意时间序列中的间隙，考虑数据补全")
        
        # 精度建议
        if precision_analysis['consistency_score'] < 70:
            recommendations.append("统一时间精度级别")
        
        # 异常值建议
        if len(anomalies) > 0:
            recommendations.append("处理检测到的异常时间值")
        
        return recommendations
    
    def _get_quality_level(self, score: float) -> QualityLevel:
        """根据得分获取质量等级"""
        if score >= 90:
            return QualityLevel.EXCELLENT
        elif score >= 70:
            return QualityLevel.GOOD
        elif score >= 50:
            return QualityLevel.FAIR
        else:
            return QualityLevel.POOR
    
    def analyze_parameter_column(self, column_name: str) -> ParameterColumnQuality:
        """分析参数列质量"""
        if self.data is None:
            raise ValueError("请先加载数据")
        
        if column_name not in self.data.columns:
            raise ValueError(f"列 {column_name} 不存在")
        
        col_data = self.data[column_name].dropna()
        
        # 数值范围分析
        range_analysis = self._analyze_parameter_range(col_data)
        
        # 数据分布分析
        distribution_analysis = self._analyze_parameter_distribution(col_data)
        
        # 异常值检测
        outlier_analysis = self._detect_parameter_outliers(col_data)
        
        # 精度和单位分析
        precision_analysis = self._analyze_parameter_precision(col_data)
        unit_analysis = self._analyze_parameter_units(col_data)
        
        # 缺失值模式分析
        missing_analysis = self._analyze_missing_pattern(self.data[column_name])
        
        # 发现的问题
        issues = self._identify_parameter_issues(
            range_analysis, distribution_analysis, outlier_analysis,
            precision_analysis, unit_analysis, missing_analysis, column_name
        )
        
        # 计算各项得分
        range_score = range_analysis['validity_score']
        distribution_score = distribution_analysis['normality_score']
        outlier_score = max(0, 100 - outlier_analysis['outlier_ratio'] * 100)
        precision_score = precision_analysis['consistency_score']
        completeness_score = missing_analysis['completeness_score']
        
        # 综合得分
        overall_score = (range_score + distribution_score + outlier_score + 
                        precision_score + completeness_score) / 5
        
        # 质量等级
        quality_level = self._get_quality_level(overall_score)
        
        # 生成建议
        recommendations = self._generate_parameter_recommendations(
            range_analysis, distribution_analysis, outlier_analysis,
            precision_analysis, unit_analysis, missing_analysis
        )
        
        return ParameterColumnQuality(
            column_name=column_name,
            range_analysis=range_analysis,
            range_validity_score=range_score,
            distribution_analysis=distribution_analysis,
            distribution_score=distribution_score,
            outlier_analysis=outlier_analysis,
            outlier_score=outlier_score,
            precision_analysis=precision_analysis,
            unit_consistency=unit_analysis,
            precision_score=precision_score,
            missing_pattern=missing_analysis,
            completeness_score=completeness_score,
            issues=issues,
            overall_score=overall_score,
            quality_level=quality_level,
            recommendations=recommendations
        )
    
    def _analyze_parameter_range(self, series: pd.Series) -> Dict[str, Any]:
        """分析参数范围合理性"""
        if not pd.api.types.is_numeric_dtype(series):
            return {
                'min_value': None,
                'max_value': None,
                'range_span': 0,
                'validity_score': 0,
                'issues': ['非数值类型数据']
            }
        
        min_val = series.min()
        max_val = series.max()
        range_span = max_val - min_val
        
        issues = []
        validity_score = 100
        
        # 检查负值（如果不应该有负值）
        negative_count = (series < 0).sum()
        if negative_count > 0:
            negative_ratio = negative_count / len(series)
            if negative_ratio > 0.1:  # 超过10%的负值可能有问题
                issues.append(f"发现大量负值: {negative_ratio:.1%}")
                validity_score -= 20
        
        # 检查极值
        q1, q3 = series.quantile([0.25, 0.75])
        iqr = q3 - q1
        extreme_lower = q1 - 3 * iqr
        extreme_upper = q3 + 3 * iqr
        
        extreme_count = ((series < extreme_lower) | (series > extreme_upper)).sum()
        if extreme_count > 0:
            extreme_ratio = extreme_count / len(series)
            if extreme_ratio > 0.05:
                issues.append(f"发现极端值: {extreme_ratio:.1%}")
                validity_score -= extreme_ratio * 200
        
        return {
            'min_value': float(min_val),
            'max_value': float(max_val),
            'range_span': float(range_span),
            'negative_count': int(negative_count),
            'extreme_count': int(extreme_count),
            'validity_score': max(0, validity_score),
            'issues': issues
        }
    
    def _analyze_parameter_distribution(self, series: pd.Series) -> Dict[str, Any]:
        """分析参数分布"""
        if not pd.api.types.is_numeric_dtype(series):
            return {
                'mean': None,
                'std': None,
                'skewness': None,
                'kurtosis': None,
                'normality_score': 0
            }
        
        mean_val = series.mean()
        std_val = series.std()
        skewness = series.skew()
        kurtosis = series.kurtosis()
        
        # 正态性评分（基于偏度和峰度）
        normality_score = 100
        
        # 偏度检查（理想值接近0）
        if abs(skewness) > 2:
            normality_score -= 30
        elif abs(skewness) > 1:
            normality_score -= 15
        
        # 峰度检查（理想值接近0）
        if abs(kurtosis) > 3:
            normality_score -= 30
        elif abs(kurtosis) > 1:
            normality_score -= 15
        
        return {
            'mean': float(mean_val),
            'std': float(std_val),
            'median': float(series.median()),
            'skewness': float(skewness),
            'kurtosis': float(kurtosis),
            'normality_score': max(0, normality_score),
            'quartiles': {
                'q1': float(series.quantile(0.25)),
                'q2': float(series.quantile(0.5)),
                'q3': float(series.quantile(0.75))
            }
        }
    
    def _detect_parameter_outliers(self, series: pd.Series) -> Dict[str, Any]:
        """检测参数异常值"""
        if not pd.api.types.is_numeric_dtype(series):
            return {
                'outlier_count': 0,
                'outlier_ratio': 0,
                'outlier_indices': [],
                'method': 'none'
            }
        
        # 使用IQR方法检测异常值
        q1, q3 = series.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outlier_mask = (series < lower_bound) | (series > upper_bound)
        outlier_indices = series[outlier_mask].index.tolist()
        
        return {
            'outlier_count': int(outlier_mask.sum()),
            'outlier_ratio': float(outlier_mask.sum() / len(series)),
            'outlier_indices': outlier_indices,
            'lower_bound': float(lower_bound),
            'upper_bound': float(upper_bound),
            'method': 'iqr'
        }
    
    def _analyze_parameter_precision(self, series: pd.Series) -> Dict[str, Any]:
        """分析参数精度"""
        if not pd.api.types.is_numeric_dtype(series):
            return {
                'decimal_places': [],
                'consistency_score': 0
            }
        
        decimal_places = []
        
        for value in series.head(100):  # 采样分析
            if pd.isna(value):
                continue
            
            str_val = str(float(value))
            if '.' in str_val:
                decimal_part = str_val.split('.')[1].rstrip('0')
                decimal_places.append(len(decimal_part))
            else:
                decimal_places.append(0)
        
        if not decimal_places:
            return {
                'decimal_places': [],
                'consistency_score': 0
            }
        
        # 计算精度一致性
        decimal_counter = Counter(decimal_places)
        most_common_precision = decimal_counter.most_common(1)[0][0]
        consistency_ratio = decimal_counter[most_common_precision] / len(decimal_places)
        consistency_score = consistency_ratio * 100
        
        return {
            'decimal_places': decimal_places,
            'precision_distribution': dict(decimal_counter),
            'most_common_precision': most_common_precision,
            'consistency_score': consistency_score
        }
    
    def _analyze_parameter_units(self, series: pd.Series) -> Dict[str, Any]:
        """分析参数单位一致性"""
        # 简化的单位检测（实际应用中可能需要更复杂的逻辑）
        string_values = series.astype(str)
        
        # 检测是否包含单位信息（使用非捕获组避免warning）
        unit_patterns = [
            r'[0-9]+\s*(?:kg|g|mg|lb)',  # 重量单位
            r'[0-9]+\s*(?:m|cm|mm|km|ft|in)',  # 长度单位
            r'[0-9]+\s*(?:°C|°F|K)',  # 温度单位
            r'[0-9]+\s*(?:%|percent)',  # 百分比
        ]
        
        has_units = False
        unit_types = []
        
        for pattern in unit_patterns:
            # 使用regex=True但不捕获组，避免warning
            matches = string_values.str.contains(pattern, regex=True, na=False)
            if matches.any():
                has_units = True
                unit_types.append(pattern)
        
        return {
            'has_units': has_units,
            'unit_patterns': unit_types,
            'consistency_score': 100 if not has_units else 80  # 简化评分
        }
    
    def _analyze_missing_pattern(self, series: pd.Series) -> Dict[str, Any]:
        """分析缺失值模式"""
        total_count = len(series)
        missing_count = series.isna().sum()
        completeness_ratio = (total_count - missing_count) / total_count
        
        # 检测缺失值模式
        missing_indices = series[series.isna()].index.tolist()
        
        # 检查是否有连续缺失
        consecutive_missing = []
        if missing_indices:
            current_start = missing_indices[0]
            current_end = missing_indices[0]
            
            for i in range(1, len(missing_indices)):
                if missing_indices[i] == missing_indices[i-1] + 1:
                    current_end = missing_indices[i]
                else:
                    if current_end > current_start:
                        consecutive_missing.append((current_start, current_end))
                    current_start = missing_indices[i]
                    current_end = missing_indices[i]
            
            if current_end > current_start:
                consecutive_missing.append((current_start, current_end))
        
        return {
            'total_count': total_count,
            'missing_count': int(missing_count),
            'completeness_ratio': float(completeness_ratio),
            'completeness_score': float(completeness_ratio * 100),
            'missing_indices': missing_indices,
            'consecutive_missing': consecutive_missing,
            'has_pattern': len(consecutive_missing) > 0
        }
    
    def _identify_parameter_issues(self, range_analysis, distribution_analysis, 
                                 outlier_analysis, precision_analysis, 
                                 unit_analysis, missing_analysis, column_name) -> List[ParameterQualityIssue]:
        """识别参数列质量问题"""
        issues = []
        
        # 范围问题
        if range_analysis['validity_score'] < 80:
            for issue_desc in range_analysis['issues']:
                issues.append(ParameterQualityIssue(
                    issue_type="range_validity",
                    description=issue_desc,
                    affected_rows=[],
                    severity="medium",
                    suggested_action="检查数据收集过程和数据验证规则"
                ))
        
        # 异常值问题
        if outlier_analysis['outlier_ratio'] > 0.05:
            issues.append(ParameterQualityIssue(
                issue_type="outliers",
                description=f"发现 {outlier_analysis['outlier_count']} 个异常值",
                affected_rows=outlier_analysis['outlier_indices'],
                severity="medium",
                suggested_action="审查异常值，确定是否为数据错误或真实极值"
            ))
        
        # 精度不一致问题
        if precision_analysis['consistency_score'] < 70:
            issues.append(ParameterQualityIssue(
                issue_type="precision_inconsistency",
                description="数值精度不一致",
                affected_rows=[],
                severity="low",
                suggested_action="统一数值精度格式"
            ))
        
        # 缺失值问题
        if missing_analysis['completeness_score'] < 90:
            issues.append(ParameterQualityIssue(
                issue_type="missing_values",
                description=f"缺失值比例: {(1-missing_analysis['completeness_ratio']):.1%}",
                affected_rows=missing_analysis['missing_indices'],
                severity="high" if missing_analysis['completeness_score'] < 70 else "medium",
                suggested_action="分析缺失原因，考虑数据插补或删除策略"
            ))
        
        return issues
    
    def _generate_parameter_recommendations(self, range_analysis, distribution_analysis,
                                          outlier_analysis, precision_analysis,
                                          unit_analysis, missing_analysis) -> List[str]:
        """生成参数列改进建议"""
        recommendations = []
        
        if range_analysis['validity_score'] < 80:
            recommendations.append("检查并修正数值范围异常的数据")
        
        if distribution_analysis['normality_score'] < 60:
            recommendations.append("考虑数据变换以改善分布特性")
        
        if outlier_analysis['outlier_ratio'] > 0.05:
            recommendations.append("处理检测到的异常值")
        
        if precision_analysis['consistency_score'] < 70:
            recommendations.append("统一数值精度格式")
        
        if missing_analysis['completeness_score'] < 90:
            recommendations.append("处理缺失值问题")
        
        return recommendations
    
    def analyze_category_column(self, column_name: str) -> CategoryColumnQuality:
        """分析类目列质量"""
        if self.data is None:
            raise ValueError("请先加载数据")
        
        if column_name not in self.data.columns:
            raise ValueError(f"列 {column_name} 不存在")
        
        col_data = self.data[column_name].dropna()
        
        # 类别一致性分析
        consistency_analysis = self._analyze_category_consistency(col_data)
        
        # 编码规范分析
        encoding_analysis = self._analyze_category_encoding(col_data)
        
        # 类别分布分析
        distribution_analysis = self._analyze_category_distribution(col_data)
        
        # 异常类别检测
        anomaly_analysis = self._detect_category_anomalies(col_data)
        
        # 层级结构分析
        hierarchy_analysis = self._analyze_category_hierarchy(col_data)
        
        # 发现的问题
        issues = self._identify_category_issues(
            consistency_analysis, encoding_analysis, distribution_analysis,
            anomaly_analysis, hierarchy_analysis, column_name
        )
        
        # 计算各项得分
        consistency_score = consistency_analysis['consistency_score']
        encoding_score = encoding_analysis['encoding_score']
        distribution_score = distribution_analysis['balance_score']
        anomaly_score = max(0, 100 - len(anomaly_analysis['anomalies']) * 10)
        hierarchy_score = hierarchy_analysis['structure_score'] if hierarchy_analysis else 100
        
        # 综合得分
        overall_score = (consistency_score + encoding_score + distribution_score + 
                        anomaly_score + hierarchy_score) / 5
        
        # 质量等级
        quality_level = self._get_quality_level(overall_score)
        
        # 生成建议
        recommendations = self._generate_category_recommendations(
            consistency_analysis, encoding_analysis, distribution_analysis,
            anomaly_analysis, hierarchy_analysis
        )
        
        return CategoryColumnQuality(
            column_name=column_name,
            consistency_analysis=consistency_analysis,
            consistency_score=consistency_score,
            encoding_analysis=encoding_analysis,
            encoding_score=encoding_score,
            distribution_analysis=distribution_analysis,
            distribution_score=distribution_score,
            anomaly_analysis=anomaly_analysis,
            anomaly_score=anomaly_score,
            hierarchy_analysis=hierarchy_analysis,
            hierarchy_score=hierarchy_score,
            issues=issues,
            overall_score=overall_score,
            quality_level=quality_level,
            recommendations=recommendations
        )
    
    def _analyze_category_consistency(self, series: pd.Series) -> Dict[str, Any]:
        """分析类别一致性"""
        # 检查大小写不一致
        str_values = series.astype(str)
        
        # 统计不同的值
        unique_values = set(str_values)
        
        # 检查可能的重复（忽略大小写和空格）
        normalized_values = {}
        duplicates = []
        
        for value in unique_values:
            normalized = value.lower().strip()
            if normalized in normalized_values:
                duplicates.append({
                    'original': [normalized_values[normalized], value],
                    'normalized': normalized
                })
            else:
                normalized_values[normalized] = value
        
        # 一致性得分
        if len(duplicates) == 0:
            consistency_score = 100
        else:
            duplicate_ratio = len(duplicates) / len(unique_values)
            consistency_score = max(0, 100 - duplicate_ratio * 100)
        
        return {
            'unique_count': len(unique_values),
            'normalized_count': len(normalized_values),
            'duplicates': duplicates,
            'consistency_score': consistency_score
        }
    
    def _analyze_category_encoding(self, series: pd.Series) -> Dict[str, Any]:
        """分析编码规范"""
        str_values = series.astype(str)
        
        # 检查编码模式
        patterns = {
            'has_numbers': str_values.str.contains(r'\d', regex=True).any(),
            'has_special_chars': str_values.str.contains(r'[^a-zA-Z0-9\s]', regex=True).any(),
            'mixed_case': str_values.apply(lambda x: x != x.lower() and x != x.upper()).any(),
            'has_spaces': str_values.str.contains(r'\s', regex=True).any(),
            'consistent_length': str_values.str.len().nunique() == 1
        }
        
        # 编码规范得分
        encoding_score = 100
        
        # 检查是否有明显的编码问题
        if patterns['mixed_case'] and not patterns['has_spaces']:
            encoding_score -= 10  # 混合大小写但没有空格可能是编码问题
        
        if patterns['has_special_chars']:
            special_char_ratio = str_values.str.contains(r'[^a-zA-Z0-9\s]', regex=True).mean()
            if special_char_ratio > 0.1:
                encoding_score -= 20
        
        return {
            'patterns': patterns,
            'encoding_score': encoding_score,
            'length_distribution': dict(str_values.str.len().value_counts().head(10))
        }
    
    def _analyze_category_distribution(self, series: pd.Series) -> Dict[str, Any]:
        """分析类别分布"""
        value_counts = series.value_counts()
        total_count = len(series)
        
        # 计算分布均匀性
        expected_freq = total_count / len(value_counts)
        chi_square = sum((count - expected_freq) ** 2 / expected_freq for count in value_counts)
        
        # 检查是否有过于稀少的类别
        rare_threshold = max(1, total_count * 0.01)  # 少于1%的类别
        rare_categories = value_counts[value_counts < rare_threshold]
        
        # 检查是否有过于集中的类别
        dominant_threshold = total_count * 0.8  # 超过80%的类别
        dominant_categories = value_counts[value_counts > dominant_threshold]
        
        # 平衡性得分
        balance_score = 100
        
        if len(rare_categories) > 0:
            rare_ratio = len(rare_categories) / len(value_counts)
            balance_score -= rare_ratio * 50
        
        if len(dominant_categories) > 0:
            balance_score -= 30
        
        return {
            'category_count': len(value_counts),
            'value_distribution': dict(value_counts.head(20)),
            'rare_categories': dict(rare_categories),
            'dominant_categories': dict(dominant_categories),
            'balance_score': max(0, balance_score),
            'chi_square': chi_square
        }
    
    def _detect_category_anomalies(self, series: pd.Series) -> Dict[str, Any]:
        """检测异常类别"""
        str_values = series.astype(str)
        value_counts = str_values.value_counts()
        
        anomalies = []
        
        # 检测可能的拼写错误（基于编辑距离）
        from difflib import SequenceMatcher
        
        categories = list(value_counts.index)
        for i, cat1 in enumerate(categories):
            for cat2 in categories[i+1:]:
                similarity = SequenceMatcher(None, cat1.lower(), cat2.lower()).ratio()
                if 0.7 < similarity < 1.0:  # 相似但不完全相同
                    anomalies.append({
                        'type': 'similar_categories',
                        'categories': [cat1, cat2],
                        'similarity': similarity
                    })
        
        # 检测异常长度的类别
        lengths = str_values.str.len()
        mean_length = lengths.mean()
        std_length = lengths.std()
        
        if std_length > 0:
            outlier_threshold = mean_length + 2 * std_length
            long_categories = str_values[lengths > outlier_threshold].unique()
            
            if len(long_categories) > 0:
                anomalies.append({
                    'type': 'unusual_length',
                    'categories': list(long_categories),
                    'threshold': outlier_threshold
                })
        
        return {
            'anomalies': anomalies,
            'anomaly_count': len(anomalies)
        }
    
    def _analyze_category_hierarchy(self, series: pd.Series) -> Optional[Dict[str, Any]]:
        """分析类别层级结构"""
        str_values = series.astype(str)
        
        # 检测可能的层级分隔符
        separators = ['/', '-', '_', '.', '|', '>']
        hierarchy_info = None
        
        for sep in separators:
            if str_values.str.contains(f'\\{sep}', regex=True).any():
                # 分析层级结构
                split_values = str_values.str.split(sep, expand=True)
                levels = split_values.shape[1]
                
                if levels > 1:
                    hierarchy_info = {
                        'separator': sep,
                        'levels': levels,
                        'level_distribution': {}
                    }
                    
                    for level in range(levels):
                        if level < split_values.shape[1]:
                            level_values = split_values[level].dropna()
                            hierarchy_info['level_distribution'][f'level_{level}'] = dict(
                                level_values.value_counts().head(10)
                            )
                    break
        
        if hierarchy_info:
            structure_score = 90  # 有层级结构得分较高
        else:
            structure_score = 100  # 无层级结构也是正常的
        
        return {
            'has_hierarchy': hierarchy_info is not None,
            'hierarchy_info': hierarchy_info,
            'structure_score': structure_score
        } if hierarchy_info else None
    
    def _identify_category_issues(self, consistency_analysis, encoding_analysis,
                                distribution_analysis, anomaly_analysis,
                                hierarchy_analysis, column_name) -> List[CategoryQualityIssue]:
        """识别类目列质量问题"""
        issues = []
        
        # 一致性问题
        if consistency_analysis['consistency_score'] < 80:
            for duplicate in consistency_analysis['duplicates']:
                issues.append(CategoryQualityIssue(
                    issue_type="inconsistent_naming",
                    description=f"发现可能重复的类别: {duplicate['original']}",
                    affected_values=duplicate['original'],
                    severity="medium",
                    suggested_mapping={duplicate['original'][1]: duplicate['original'][0]}
                ))
        
        # 编码问题
        if encoding_analysis['encoding_score'] < 80:
            issues.append(CategoryQualityIssue(
                issue_type="encoding_inconsistency",
                description="类别编码不规范",
                affected_values=[],
                severity="low"
            ))
        
        # 分布问题
        if distribution_analysis['balance_score'] < 60:
            rare_cats = list(distribution_analysis['rare_categories'].keys())
            if rare_cats:
                issues.append(CategoryQualityIssue(
                    issue_type="rare_categories",
                    description=f"发现稀少类别: {len(rare_cats)} 个",
                    affected_values=rare_cats,
                    severity="medium"
                ))
        
        # 异常类别
        for anomaly in anomaly_analysis['anomalies']:
            if anomaly['type'] == 'similar_categories':
                issues.append(CategoryQualityIssue(
                    issue_type="similar_categories",
                    description=f"发现相似类别: {anomaly['categories']}",
                    affected_values=anomaly['categories'],
                    severity="medium",
                    suggested_mapping={anomaly['categories'][1]: anomaly['categories'][0]}
                ))
        
        return issues
    
    def _generate_category_recommendations(self, consistency_analysis, encoding_analysis,
                                         distribution_analysis, anomaly_analysis,
                                         hierarchy_analysis) -> List[str]:
        """生成类目列改进建议"""
        recommendations = []
        
        if consistency_analysis['consistency_score'] < 80:
            recommendations.append("统一类别命名，消除重复和不一致")
        
        if encoding_analysis['encoding_score'] < 80:
            recommendations.append("规范类别编码格式")
        
        if distribution_analysis['balance_score'] < 60:
            recommendations.append("处理稀少类别，考虑合并或重新分类")
        
        if len(anomaly_analysis['anomalies']) > 0:
            recommendations.append("检查并修正异常类别")
        
        if hierarchy_analysis and hierarchy_analysis['structure_score'] < 90:
            recommendations.append("优化层级结构的一致性")
        
        return recommendations
    
    def generate_quality_report(self, dataset_id: str, analysis_id: str) -> DataQualityReport:
        """生成完整的数据质量报告"""
        if self.data is None:
            raise ValueError("请先加载数据")
        
        if not self.column_types:
            self.auto_detect_column_types()
        
        # 分析各类型列
        time_columns = []
        parameter_columns = []
        category_columns = []
        
        for col_name, col_type in self.column_types.items():
            try:
                if col_type == ColumnType.TIME:
                    time_quality = self.analyze_time_column(col_name)
                    time_columns.append(time_quality)
                elif col_type == ColumnType.PARAMETER:
                    param_quality = self.analyze_parameter_column(col_name)
                    parameter_columns.append(param_quality)
                elif col_type == ColumnType.CATEGORY:
                    cat_quality = self.analyze_category_column(col_name)
                    category_columns.append(cat_quality)
            except Exception as e:
                logger.error(f"分析列 {col_name} 时出错: {e}")
                continue
        
        # 计算整体得分
        all_scores = []
        all_scores.extend([col.overall_score for col in time_columns if col.overall_score is not None])
        all_scores.extend([col.overall_score for col in parameter_columns if col.overall_score is not None])
        all_scores.extend([col.overall_score for col in category_columns if col.overall_score is not None])
        
        # 确保分数在合理范围内
        valid_scores = [score for score in all_scores if 0 <= score <= 100]
        overall_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
        overall_score = round(overall_score, 1)  # 保留一位小数
        quality_level = self._get_quality_level(overall_score)
        
        # 统计信息
        total_columns = len(self.data.columns)
        analyzed_columns = len(valid_scores)
        high_quality_columns = sum(1 for score in valid_scores if score >= 80)
        low_quality_columns = sum(1 for score in valid_scores if score < 60)
        
        # 收集关键问题
        key_issues = []
        all_recommendations = []
        
        for col in time_columns + parameter_columns + category_columns:
            if col.overall_score is not None and col.overall_score < 70:
                key_issues.append(f"{col.column_name}: 质量得分 {col.overall_score:.1f}")
            if hasattr(col, 'recommendations') and col.recommendations:
                all_recommendations.extend(col.recommendations)
        
        # 去重建议并限制数量
        unique_recommendations = list(set(all_recommendations))[:10]  # 最多10条建议
        
        # 生成摘要
        summary = {
            'total_score': overall_score,
            'column_breakdown': {
                'time_columns': len(time_columns),
                'parameter_columns': len(parameter_columns),
                'category_columns': len(category_columns)
            },
            'quality_distribution': {
                'excellent': sum(1 for score in valid_scores if score >= 90),
                'good': sum(1 for score in valid_scores if 70 <= score < 90),
                'fair': sum(1 for score in valid_scores if 50 <= score < 70),
                'poor': sum(1 for score in valid_scores if score < 50)
            }
        }
        
        return DataQualityReport(
            dataset_id=dataset_id,
            analysis_id=analysis_id,
            created_at=datetime.now(),
            time_columns=time_columns,
            parameter_columns=parameter_columns,
            category_columns=category_columns,
            overall_score=overall_score,
            quality_level=quality_level,
            summary=summary,
            key_issues=key_issues,
            recommendations=unique_recommendations,
            total_columns=total_columns,
            analyzed_columns=analyzed_columns,
            high_quality_columns=high_quality_columns,
            low_quality_columns=low_quality_columns
        ) 