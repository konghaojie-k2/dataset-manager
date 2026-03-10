#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dataset Manager CLI

Command-line interface for dataset management
"""

import click
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from src.core.enhanced_metadata_service import enhanced_metadata_service
from src.core.data_understanding_service import data_understanding_service
from src.core.data_cleaning_service import data_cleaning_service
from src.core.data_validation_service import data_validation_service
from src.core.data_generation_service import data_generation_service
from src.core.data_visualization_service import data_visualization_service
from src.core.data_transformation_service import data_transformation_service

import pandas as pd
import asyncio


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Dataset Manager CLI - AI-Native data management tool"""
    pass


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--sample-size", default=1000, help="Sample size for analysis")
def analyze(file_path, sample_size):
    """Analyze dataset and show metadata"""
    click.echo(f"📊 Analyzing: {file_path}")
    
    # Load data
    df = pd.read_csv(file_path)
    click.echo(f"📈 Loaded {len(df)} rows, {len(df.columns)} columns")
    
    # Analyze
    result = asyncio.run(
        enhanced_metadata_service.analyze_dataset(
            dataset_id=Path(file_path).stem,
            dataframe=df,
            sample_size=sample_size
        )
    )
    
    # Display results
    click.echo(f"\n🏷️  Semantic Types:")
    for col in result["column_semantics"][:5]:
        click.echo(f"  - {col['name']}: {col['semantic_type']}")
    
    click.echo(f"\n📉 Quality Score: {result['quality_score']['overall_score']}/100")
    
    click.echo(f"\n💡 Summary: {result['data_understanding']['summary']}")


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
def understand(file_path):
    """Generate data understanding report"""
    click.echo(f"🧠 Understanding: {file_path}")
    
    df = pd.read_csv(file_path)
    result = asyncio.run(data_understanding_service.understand(df))
    
    click.echo(f"\n📝 {result['summary']}")
    
    if result.get("insights"):
        click.echo("\n💡 Key Insights:")
        for insight in result["insights"][:3]:
            click.echo(f"  • {insight}")


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def clean(file_path, output):
    """Clean dataset issues"""
    click.echo(f"🧹 Cleaning: {file_path}")
    
    df = pd.read_csv(file_path)
    result = asyncio.run(data_cleaning_service.clean(df))
    
    click.echo(f"\n✅ {result['summary']}")
    click.echo(f"   Original: {result['original_rows']} rows")
    click.echo(f"   Cleaned: {result['cleaned_rows']} rows")
    
    if result.get("fixes_applied"):
        click.echo("\n🔧 Fixes applied:")
        for fix in result["fixes_applied"][:5]:
            click.echo(f"  - {fix}")
    
    if output:
        result["cleaned_data"].to_csv(output, index=False)
        click.echo(f"\n💾 Saved to: {output}")


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--schema", type=click.Path(exists=True), help="JSON schema file")
def validate(file_path, schema):
    """Validate dataset against schema"""
    click.echo(f"✅ Validating: {file_path}")
    
    df = pd.read_csv(file_path)
    schema_dict = {}
    if schema:
        import json
        with open(schema) as f:
            schema_dict = json.load(f)
    
    result = asyncio.run(data_validation_service.validate(df, schema_dict))
    
    if result["is_valid"]:
        click.echo(f"\n✅ Validation passed! Score: {result['score']}/100")
    else:
        click.echo(f"\n❌ Validation failed! Score: {result['score']}/100")
        
        if result.get("errors"):
            click.echo("\n🚨 Errors:")
            for error in result["errors"][:5]:
                click.echo(f"  - {error}")


@cli.command()
@click.argument("data_type", type=click.Choice(["user", "sales", "log", "iot", "financial"]))
@click.option("--rows", default=100, help="Number of rows to generate")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def generate(data_type, rows, output):
    """Generate sample data"""
    click.echo(f"🎲 Generating {rows} rows of {data_type} data...")
    
    result = asyncio.run(data_generation_service.generate(data_type, rows))
    
    if output:
        result.to_csv(output, index=False)
        click.echo(f"💾 Saved to: {output}")
    else:
        click.echo(f"\n{result.head()}")


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
def visualize(file_path):
    """Suggest visualizations for dataset"""
    click.echo(f"📊 Analyzing for visualizations: {file_path}")
    
    df = pd.read_csv(file_path)
    result = asyncio.run(data_visualization_service.analyze(df))
    
    click.echo("\n📈 Suggested Charts:")
    for viz in result.get("numeric_visualizations", [])[:3]:
        click.echo(f"  - {viz['column']}: {viz['suggested_chart']}")
    
    for viz in result.get("categorical_visualizations", [])[:3]:
        click.echo(f"  - {viz['column']}: {viz['suggested_chart']}")
    
    if result.get("recommendations"):
        click.echo("\n💡 Recommendations:")
        for rec in result["recommendations"]:
            click.echo(f"  • {rec}")


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.argument("transformation", type=click.Choice([
    "pivot", "aggregate", "filter", "sort", "normalize", "encode"
]))
@click.option("--args", "-a", multiple=True, help="Transformation arguments (key=value)")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def transform(file_path, transformation, args, output):
    """Transform dataset"""
    click.echo(f"🔄 Transforming: {file_path} ({transformation})")
    
    df = pd.read_csv(file_path)
    
    # Parse arguments
    params = {}
    for arg in args:
        if "=" in arg:
            k, v = arg.split("=", 1)
            params[k] = v
    
    service = data_transformation_service
    result = asyncio.run(service.transform(df, transformation, **params))
    
    click.echo(f"\n📊 Shape: {result['original_shape']} → {result['result_shape']}")
    
    if output:
        result["result"].to_csv(output, index=False)
        click.echo(f"💾 Saved to: {output}")


if __name__ == "__main__":
    cli()
