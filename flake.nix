{
  description = "Pure Nix packaging for lx-data-models knowledge bases";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    inputs@{
      nixpkgs,
      flake-utils,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };

        base = pkgs.callPackage ./package.nix { };
      in
      {
        packages = {
          default = base;
          star-endoscopy-kb = base;
        };
      }
    );
}
