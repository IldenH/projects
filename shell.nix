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

      black
      pyright

      (python312.withPackages (packages:
        with packages; [
          matplotlib
          numpy
          sympy
        ]))

      nixd
      alejandra

      go
    ];
  }
