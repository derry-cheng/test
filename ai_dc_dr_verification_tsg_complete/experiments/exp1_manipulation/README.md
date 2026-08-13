# Experiment 1 — Strategic Manipulation

Run with `python run.py` or `./run_all.sh --stage exp1`. The experiment solves every
pre-declared DR-price × event-probability combination over ten reference days. The
expected-settlement coefficient is analytically fixed by the ten-day mean baseline;
each cell is solved to LP optimality and checkpointed. The boundary is certified
independently from ten honest-program right-hand-side dual marginals. Economic
profit subtracts the sum of all ten physical reference-day cost increments; equality
points are reported as indifference rather than strict profit. The baseline model
and solver citations are `wang2022baseline`, `caiso2017baseline`, and
`huangfu2018highs` in `manuscript/references.bib`.
