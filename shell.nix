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

      plantuml

      nixd
      alejandra
    ];
  }
