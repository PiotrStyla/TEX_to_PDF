# Free Demo: GitHub Pages + GitHub Actions

Ta wersja dodaje darmowe publiczne demo bez VPS i bez Rendera.

## Co zawiera

```text
docs/
├── index.html
└── style.css

examples/sample-paper/
├── main.tex
├── formatka/slayer.sty
└── tresc/
    ├── 00-strona-tytulowa.tex
    └── 10-tresc.tex

.github/workflows/
└── build-sample-pdf.yml
```

## GitHub Pages

Włącz:

```text
Settings → Pages
Source: Deploy from a branch
Branch: main
Folder: /docs
Save
```

Po chwili strona powinna być dostępna pod:

```text
https://piotrstyla.github.io/TEX_to_PDF/
```

## GitHub Actions PDF build

Uruchom:

```text
Actions → Build Sample PDF → Run workflow
```

Po zakończeniu wejdź w run i pobierz artifact:

```text
sample-tex-to-pdf
```

W środku będzie `main.pdf`.

## Ograniczenie

To nie jest backend online. GitHub Pages hostuje statyczną stronę, a GitHub Actions buduje PDF jako artifact.
Prawdziwe online upload → PDF wymaga backendu na VPS albo innym hostingu z LaTeX/Docker.
