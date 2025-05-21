with import <nixpkgs> {};
  mkShell {
    packages = [
      cargo
      rustc
      rustfmt
      rustPackages.clippy
      rust-analyzer
      bacon

      ghc
      ghcid
      haskell-language-server
      ormolu

      plantuml

      pyright

      (python3.withPackages (packages:
        with packages; [
          black # needs to be here for jupyterlab to work

          matplotlib
          numpy
          sympy
          scipy
          pandas

          # python3 -m jupyterlab
          jupyterlab
          ipykernel
          ipywidgets
          ipython
        ]))

      nixd
      alejandra

      go

      typst
      tinymist
      typstyle

      ghostscript
      imagemagick
    ];
  }
