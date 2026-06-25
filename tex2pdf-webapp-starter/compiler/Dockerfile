FROM texlive/texlive:latest

WORKDIR /work

# latexmk is included in common TeX Live images. This explicit check makes build failures clear.
RUN latexmk --version
