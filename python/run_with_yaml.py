#!/usr/bin/env python3
"""
Run MIDT pipeline from YAML configuration file.
Usage: python run_with_yaml.py my_analysis.yaml
"""

import sys
from pathlib import Path

# Add pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from midt_pipeline import run_pipeline_from_config_file

def main():
    if len(sys.argv) != 2:
        print("Usage: python run_with_yaml.py <config.yaml>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    if not Path(config_file).exists():
        print(f"Config file not found: {config_file}")
        sys.exit(1)
    
    print(f"🚀 Running MIDT pipeline with config: {config_file}")
    
    # Run pipeline
    summary = run_pipeline_from_config_file(
        config_file, 
        n_jobs=1  # or more for parallel processing
    )
    
    print(f"🎉 Pipeline completed!")
    print(f"Success rate: {summary['successful_subjects']}/{summary['total_subjects']}")

if __name__ == "__main__":
    main()