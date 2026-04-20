{
  lib,
  symlinkJoin,
  makeWrapper,
  python_package,
  kb_package,
}:

symlinkJoin {
  name = "lx-dtypes-app";
  paths = [
    python_package
    kb_package
  ];

  nativeBuildInputs = [ makeWrapper ];

  postBuild = ''
    registry_path="$out/share/lx-dtypes/registries/star_upper_gi.json"

    if [ -d "$out/bin" ]; then
      for program in "$out/bin/"*; do
        if [ -f "$program" ]; then
          wrapProgram "$program" \
            --set-default LX_DTYPES_KB_REGISTRY "$registry_path"
        fi
      done
    fi
  '';

  meta = python_package.meta // {
    description = "lx-dtypes Python package bundled with the packaged STAR upper GI knowledge base";
    mainProgram = "lx-dtypes-kb-registry";
  };
}
