{
  lib,
  stdenvNoCC,
}:

let
  pname = "star-endoscopy-kb";
  version = "0.1.0";

  kbModuleName = "star_upper_gi";
  kbModuleVersion = "0.1.0";
  kbSource = ./demo-data/star_upper_gi;
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
    description = "STAR upper GI endoscopy knowledge-base bundle packaged for lx-dtypes registry consumption";
    license = licenses.mit;
    platforms = platforms.linux;
  };
}
