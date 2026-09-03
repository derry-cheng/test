# TSG manuscript boundary

`main.tex` is the canonical IEEE Transactions on Smart Grid source and
`main.pdf` is the checked-in ten-page release. Editable draw.io/SVG figures,
derivation notes, the revision matrix, and the bibliography are kept beside
the source. Generated experiment tables and solver outputs remain under their
own `experiments/exp*/results/final/` directories.

Build from the repository root with:

```text
cd paper
latexmk -pdf -interaction=nonstopmode main.tex
```

The audit stage checks the expected source inventory, citation coverage,
figure dimensions, page count, and numerical certificates before release.
