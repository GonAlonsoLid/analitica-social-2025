#!/usr/bin/env python3
"""
Ejecuta el análisis de insights, sentimiento y temático (para marketing).
Requiere datos crudos en data/raw/
"""
from src.analysis.insights import run_insights_analysis
from src.analysis.sentiment import run_sentiment_analysis
from src.analysis.thematic import run_thematic_analysis
from src.analysis.sentiment_sources_report import run_full_report

if __name__ == "__main__":
    print("1. Insights básicos (requiere data/clean/)...")
    run_insights_analysis()
    print()
    print("2. Análisis de sentimiento...")
    run_sentiment_analysis()
    print()
    print("3. Análisis temático para marketing...")
    run_thematic_analysis()
    print()
    print("4. Análisis de sentimiento por fuente + gráficas para marketing...")
    run_full_report()
