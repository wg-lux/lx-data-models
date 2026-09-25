{
  lib,
  stdenvNoCC,
}:

let
  kbSource = ./lx_dtypes/data/star_upper_gi;
  kbModuleName = builtins.baseNameOf (toString kbSource);
  pname = "lx-dtypes-kb-${lib.replaceStrings [ "_" ] [ "-" ] kbModuleName}";
  version = "0.1.1";

  kbModuleVersion = "0.1.1";
in
stdenvNoCC.mkDerivation {
  inherit pname version;

  src = lib.cleanSource kbSource;

  dontUnpack = true;

  installPhase = ''
    runHook preInstall

    kbRoot="$out/share/lx-dtypes/knowledge-bases"
    registryRoot="$out/share/lx-dtypes/registries"
    registryPath="$registryRoot/${kbModuleName}.json"

    mkdir -p "$kbRoot/${kbModuleName}" "$registryRoot"
    cp -r ${kbSource}/. "$kbRoot/${kbModuleName}/"

    cat > "$registryPath" <<EOF
    {
      "modules": {
        "${kbModuleName}": {
          "${kbModuleVersion}": {
            "input_dirs": [
              "$kbRoot"
            ]
          }
        }
      }
    }
    EOF

    runHook postInstall
  '';

  meta = with lib; {
    description = "Knowledge-base bundle for ${kbModuleName} packaged for lx-dtypes registry consumption";
    license = licenses.mit;
    platforms = platforms.linux;
  };
}
