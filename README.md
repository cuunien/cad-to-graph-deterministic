# CAD-to-Graph Conversion with Dataset-Scale Reliability Verification

[![Paper](https://img.shields.io/badge/Paper-PDF-red)](link-to-paper)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Deterministic CAD-to-graph conversion framework with explicit dataset-scale reliability verification. This repository contains the implementation for the paper:

> **Deterministic CAD-to-Graph Conversion with Explicit Dataset-Scale Reliability Verification**  
> Van-Hai Nguyen  
> Phenikaa University, 2026

## Overview

This project provides a **deterministic CAD-to-graph conversion pipeline** with built-in reliability auditing at dataset scale. Unlike typical CAD preprocessing pipelines that assume correctness, this framework explicitly verifies:

- **Structural integrity**: connectivity, label coverage, graph statistics
- **Determinism**: reproducibility via canonical graph hashing (SHA256)
- **Representation robustness**: controlled comparison across adjacency types and feature sets

### Key Features

- **Stable face indexing** using OpenCascade's `TopTools_IndexedMapOfShape`
- **Flexible adjacency definitions**: edge-based or vertex-based
- **Configurable feature sets**: full geometric attributes or reduced variants
- **Dataset-scale health metrics**: connectivity, label coverage, structural distributions
- **Canonical graph hashing** for reproducibility verification
- **Paper-grade artifacts**: automated figure/table generation for publications

## Dataset

This framework is demonstrated on the **MFCAD dataset** (15,488 STEP models with face-level semantic labels):

📦 **Download dataset**: [https://github.com/hducg/MFCAD](https://github.com/hducg/MFCAD)

After downloading, place the STEP files in `dataset/step/` directory.

## Installation

### Requirements

- Python 3.9+
- `pythonocc-core` (install via conda-forge recommended)

### Setup

```bash
# Create conda environment (recommended)
conda create -n cad2graph python=3.9
conda activate cad2graph

# Install pythonocc-core
conda install -c conda-forge pythonocc-core

# Install other dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Convert CAD to Graphs

```bash
python -m cad2graph.cli \
  --input_dir dataset/step \
  --output_dir outputs/my_run \
  --adjacency edge \
  --feature_set full \
  --workers 4
```

**Options**:
- `--adjacency`: `edge` (faces share edge) or `vertex` (faces share vertex)
- `--feature_set`: `full` (all geometric attributes) or `light` (reduced features)
- `--workers`: number of parallel processes (0 = sequential)
- `--overwrite`: 0 (skip existing) or 1 (overwrite)

### 2. Generate Health Report

```bash
python scripts/make_report.py --run_dir outputs/my_run
```

Outputs in `outputs/my_run/report/`:
- `health_report.csv`: dataset-scale statistics
- `cc_distribution.csv`, `class_distribution.csv`
- Figures: `fig_nodes_edges_hist.png`, `fig_degree_hist.png`, etc.

### 3. Verify Determinism

```bash
# Hash all graphs
python scripts/hash_graphs.py --run_dir outputs/my_run

# Run conversion again with same config
python -m cad2graph.cli \
  --input_dir dataset/step \
  --output_dir outputs/my_run_repeat \
  --adjacency edge \
  --feature_set full

# Hash second run
python scripts/hash_graphs.py --run_dir outputs/my_run_repeat

# Compare
python scripts/compare_hashes.py \
  --run_dir1 outputs/my_run \
  --run_dir2 outputs/my_run_repeat
```

Expected: `match_rate = 1.0` (100% reproducible)

### 4. Compare Representation Variants

```bash
# Generate comparison table
python scripts/make_report.py \
  --run_dir outputs/run_edge_full \
  --compare_run_dir outputs/run_edge_light \
  --compare_run_dir outputs/run_vertex_full
```

Outputs `run_comparison.csv` with aggregate statistics across variants.

## Repository Structure

```
.
├── cad2graph/              # Main package
│   ├── cli.py             # Command-line interface
│   ├── pipeline.py        # Conversion pipeline
│   ├── occ_utils.py       # OpenCascade wrappers
│   ├── io_utils.py        # I/O utilities
│   ├── determinism.py     # Canonical hashing
│   ├── reporting.py       # Health reports & figures
│   └── ...
├── scripts/               # Utility scripts
│   ├── run_convert.py     # Conversion wrapper
│   ├── make_report.py     # Report generation
│   ├── hash_graphs.py     # Graph hashing
│   ├── compare_hashes.py  # Hash comparison
│   └── package_paper1.py  # Paper artifact packaging
├── occ/                   # Legacy tools
│   └── dataset_visualizer.py  # CAD viewer (optional)
├── outputs/               # Generated outputs (gitignored)
│   └── paper1_package/    # Paper figures & tables (kept)
├── dataset/               # MFCAD dataset (gitignored, download separately)
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Outputs

Each conversion run produces:

```
outputs/<run_name>/
├── graphs/                # Graph JSONs (one per part)
├── audits/                # Audit metadata
├── profiles/              # Timing profiles
├── summary.csv            # Run-level summary
├── logs/                  # Execution logs
└── report/                # Health reports & figures
    ├── health_report.csv
    ├── hashes.csv         # Canonical hashes
    ├── determinism_report.csv
    ├── run_comparison.csv
    └── *.png              # Figures
```

## Reproducibility

All experiments in the paper can be reproduced:

1. **Dataset health** (Table 1, Figures 3-6): Run conversion + `make_report.py`
2. **Determinism** (Table 2): Run twice with same config + `compare_hashes.py`
3. **Representation robustness** (Table 3): Run with different `--adjacency` and `--feature_set` + `make_report.py --compare_run_dir`

Paper artifacts are pre-packaged in `outputs/paper1_package/`.

## Citation

If you use this code or methodology in your research, please cite:

```bibtex
@article{nguyen2026deterministic,
  title={Deterministic CAD-to-Graph Conversion with Explicit Dataset-Scale Reliability Verification},
  author={Nguyen, Van-Hai},
  journal={[Journal Name]},
  year={2026},
  publisher={Phenikaa University}
}
```

## Acknowledgments

This research is funded by Phenikaa University under grant PU2024-1-A-04.

Dataset: [MFCAD](https://github.com/hducg/MFCAD) by hducg.

## License

MIT License. See [LICENSE](LICENSE) for details.
