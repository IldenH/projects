with import <nixpkgs> {};
  mkShell {
    packages = [
      cargo
      rustc
      rustfmt
      rustPackages.clippy
      rust-analyzer
      bacon

      sqlite
      pkg-config

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

      nodejs_20
      nodePackages.npm
      nodePackages.typescript-language-server
      nodePackages.typescript
      emmet-ls
      vscode-langservers-extracted
      prettierd
      tailwindcss-language-server
      svelte-language-server

      live-server
    ];
  }
