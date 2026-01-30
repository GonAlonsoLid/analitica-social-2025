#!/usr/bin/env python3
"""
Ejecuta el pipeline de limpieza de datos.
Lee de data/raw/ y guarda en data/clean/
"""
from src.cleaning.pipeline import run_cleaning_pipeline

if __name__ == "__main__":
    run_cleaning_pipeline()
