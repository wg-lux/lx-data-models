{
  description = "Pure Nix packaging for lx-data-models knowledge bases";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    nixtest.url = "gitlab:TECHNOFAB/nixtest?dir=lib";
  };

  outputs =
    inputs@{
      nixpkgs,
      flake-utils,
      nixtest,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };

        ntlib = nixtest.lib { inherit pkgs; };
        kb_package = pkgs.callPackage ./package.nix { };
        python_package = pkgs.callPackage ./python-package.nix { };
        app_package = pkgs.callPackage ./app-package.nix {
          inherit kb_package python_package;
        };
        nixtests = ntlib.mkNixtest {
          modules = ntlib.autodiscover {
            dir = builtins.path {
              path = ./tests/nix;
              name = "lx-data-models-nixtests";
            };
          };
          args = {
            inherit pkgs ntlib app_package kb_package;
          };
        };
      in
      {
        packages = {
          default = app_package;
          lx-dtypes = python_package;
          lx-dtypes-app = app_package;
          star-endoscopy-kb = kb_package;
          nixtests = nixtests;
        };

        apps = {
          default = {
            type = "app";
            program = "${app_package}/bin/lx-dtypes-kb-registry";
          };
          nixtests = {
            type = "app";
            program = "${nixtests}/bin/nixtests:run";
          };
        };

        checks = {
          lx-dtypes = python_package;
          lx-dtypes-app = app_package;
          star-endoscopy-kb = kb_package;
          nixtests = nixtests;
        };
      }
    );
}
