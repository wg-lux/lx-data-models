{
  pkgs,
  lib,
  config,
  inputs,
  baseBuildInputs,
  ...
}:
let
  # Pin to specific Python 3.12 version to match pyproject.toml
  python = pkgs.python312; # known devenv issue with python3Packages since python3Full was deprecated
  uvPackage = pkgs.uv;

  buildInputs = with pkgs; [
    python312
    stdenv.cc.cc
    openssh
    pkg-config
    protobuf
    libglvnd
  ];
  runtimeLibraries = with pkgs; [
    stdenv.cc.cc.lib
    libglvnd
    glib
    zlib
  ];
  runtimePackages = with pkgs; [
    stdenv.cc.cc
    ffmpeg-headless.bin
    tesseract
    uvPackage
    libglvnd
    glib
    zlib
    ollama.out
  ];

  _module.args.buildInputs = baseBuildInputs;

  SYNC_CMD = "uv sync --extra dev --extra docs --frozen";
  DJANGO_APP_NAME = "lx_dtypes.django";
  DJANGO_APP_LABEL = "lx_dtypes_django";
  DJANGO_APP_DIR = "./lx_dtypes/contrib/${DJANGO_APP_NAME}";

in
{

  # A dotenv file was found, while dotenv integration is currently not enabled.
  dotenv.enable = true;
  dotenv.disableHint = true;

  packages = lib.unique (runtimePackages ++ buildInputs ++ runtimeLibraries);
  outputs =
    lib.optionalAttrs (inputs ? pyproject-nix) (
      let
        python_package = pkgs.callPackage ./python-package.nix { };
        kb_package = pkgs.callPackage ./package.nix { };
        app_package = pkgs.callPackage ./app-package.nix {
          inherit kb_package python_package;
        };
      in
      {
        python = python_package;
        kb = kb_package;
        app = app_package;
      }
    );
  env = {
    # include runtimePackages as well so runtime native libs (e.g. zlib) are on LD_LIBRARY_PATH
    LD_LIBRARY_PATH =
      lib.makeLibraryPath (buildInputs ++ runtimePackages)
      + ":/run/opengl-driver/lib:/run/opengl-driver-32/lib";
    LX_DTYPES_EDITOR_KB_REGISTRY = "../lx-terminology-editor/.published/kb_registry.json";
    UV_PROJECT_ENVIRONMENT = "${config.devenv.state}/venv";
  };

  languages.python = {
    enable = true;
    package = python;
    # Shell reloads must not recreate an environment used by active processes.
    venv.enable = false;
    uv = {
      enable = true;
      package = uvPackage;
      sync.enable = false;
    };
  };

  scripts = {
    export-nix-vars.exec = ''
      cat > .devenv-vars.json << EOF
      {
      }
      EOF
      echo "Exported Nix variables to .devenv-vars.json"
    '';

    env-setup.exec = ''
      # Ensure runtimePackages are included in the library path here too
      export LD_LIBRARY_PATH="${
        with pkgs; lib.makeLibraryPath (buildInputs ++ runtimePackages)
      }:/run/opengl-driver/lib:/run/opengl-driver-32/lib"
    '';

    hello.package = pkgs.zsh;
    hello.exec = "uv run python hello.py";
    pyshell.exec = "uv run python manage.py shell";
    mkmigrations.exec = "uv run python manage.py makemigrations ${DJANGO_APP_LABEL}";
    migrate.exec = "uv run python manage.py migrate";
    runserver.exec = "uv run python manage.py runserver";
    resetdb.exec = "rm -f db.sqlite3";
    resetmigrations.exec = ''
      rm -rf ${DJANGO_APP_DIR}/migrations/
      uv run python manage.py makemigrations ${DJANGO_APP_LABEL}
    '';

    mp.exec = "uv run python -m mypy lx_dtypes";
    pc.exec = "pre-commit run --all-files";

    mkdocs.exec = ''
      uv run make -C docs clean
      uv run make -C docs html
      uv run make -C docs linkcheck
      tar -czf docs_build.tar.gz -C docs _build/html
    '';
    uvsnc.exec = ''
      ${SYNC_CMD}
    '';
  };

  tasks = {

    "agent:sync" = {
      description = "Explicitly sync development and documentation dependencies";
      exec = SYNC_CMD;
    };

    "env:clean" = {
      description = "Remove the uv virtual environment and lock file for a clean sync";
      exec = ''
        echo "Removing uv virtual environment: .devenv/state/venv"
        rm -rf .devenv/state/venv
        echo "Removing uv lock file: uv.lock"
        rm -f uv.lock
        echo "Environment cleaned. Run 'devenv tasks run agent:sync' after restoring or updating the lock file."
      '';
    };

  };

  processes = {
  };

  enterShell = ''
    export VIRTUAL_ENV="$UV_PROJECT_ENVIRONMENT"
    export PATH="$VIRTUAL_ENV/bin:$PATH"

    env-setup

    use_editor_kb() {
      export LX_DTYPES_KB_REGISTRY="$LX_DTYPES_EDITOR_KB_REGISTRY"
      echo "Using editor-published KB registry: $LX_DTYPES_KB_REGISTRY"
    }

    use_packaged_kb() {
      unset LX_DTYPES_KB_REGISTRY
      echo "Using packaged/default KB resolution."
    }

    show_kb_mode() {
      if [ -n "$LX_DTYPES_KB_REGISTRY" ]; then
        echo "KB mode: registry"
        echo "LX_DTYPES_KB_REGISTRY=$LX_DTYPES_KB_REGISTRY"
      else
        echo "KB mode: packaged/default"
      fi
      echo "LX_DTYPES_EDITOR_KB_REGISTRY=$LX_DTYPES_EDITOR_KB_REGISTRY"
    }
  '';

  enterTest = ''
    nvcc -V
    pytest --maxfail=1 --disable-warnings -q
  '';
}
