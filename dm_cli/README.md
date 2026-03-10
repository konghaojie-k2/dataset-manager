# Dataset Manager CLI

AI-Native 命令行工具 for 数据管理

## 安装

```bash
cd dataset-manager
pip install -e .
```

## 使用

### 分析数据
```bash
dm analyze data.csv
dm analyze data.csv --sample-size 500
```

### 理解数据
```bash
dm understand data.csv
```

### 数据清洗
```bash
dm clean data.csv -o cleaned.csv
```

### 数据验证
```bash
dm validate data.csv
dm validate data.csv --schema schema.json
```

### 生成示例数据
```bash
dm generate user --rows 1000 -o users.csv
dm generate sales --rows 500 -o sales.csv
dm generate log --rows 10000 -o logs.csv
```

### 可视化建议
```bash
dm visualize data.csv
```

### 数据转换
```bash
dm transform data.csv normalize -a columns=price,salary -o normalized.csv
dm transform data.csv encode -a columns=category -o encoded.csv
```

## 命令列表

| 命令 | 功能 |
|------|------|
| `analyze` | 分析数据集元数据 |
| `understand` | 生成数据理解报告 |
| `clean` | 清洗数据问题 |
| `validate` | 验证数据 |
| `generate` | 生成示例数据 |
| `visualize` | 可视化建议 |
| `transform` | 数据转换 |

## 选项

- `--help` - 显示帮助
- `--version` - 显示版本
