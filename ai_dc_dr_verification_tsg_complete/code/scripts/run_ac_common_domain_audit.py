"""Repair/reproduce Exp18 without method-specific or native-outcome censoring.

Example: PYTHONPATH=code/src:vendor python code/scripts/run_ac_common_domain_audit.py --reuse-legacy --workers 2
The optional reuse flag accepts only the archived, hash-bound original success
ledger. Both methods on IEEE30 outages 29 and 31 are freshly diagnosed.
"""
from __future__ import annotations
import os
for variable in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[variable] = '1'
import argparse
import logging
from pathlib import Path
from aicdr.ac_common_domain import run_common_domain_panel
from aicdr.utils import load_config

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=2, choices=range(1, 9))
    parser.add_argument('--reuse-legacy', action='store_true')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    cfg = load_config(root / 'configs/default.yaml')
    cfg['experiments']['ac_n1_workers'] = args.workers
    logging.basicConfig(level=logging.INFO)
    run_common_domain_panel(root, cfg, logging.getLogger('ac_common_domain'),
                            resume=args.resume, reuse_legacy=args.reuse_legacy)

if __name__ == '__main__':
    main()
