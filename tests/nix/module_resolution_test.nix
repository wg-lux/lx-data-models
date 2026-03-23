{
  ntlib,
  pkgs,
  app_package,
  kb_package,
  ...
}:
{
  suites."data-module-resolution" = {
    pos = __curPos;
    tests = [
      {
        name = "registry-resolves-installed-module-root";
        type = "script";
        script = ''
          ${ntlib.helpers.path [
            pkgs.coreutils
            pkgs.gnugrep
            pkgs.jq
          ]}
          ${ntlib.helpers.scriptHelpers}

          registry_path="${kb_package}/share/lx-dtypes/registries/star_upper_gi.json"
          kb_root="${kb_package}/share/lx-dtypes/knowledge-bases"
          module_root="$kb_root/star_upper_gi"

          assert "-f $registry_path" "registry JSON should be installed"
          assert "-d $module_root" "module root should be installed"
          assert "-f $module_root/config.yaml" "module config should be installed"

          resolved_input_dir="$(jq -r '.modules.star_upper_gi["0.1.0"].input_dirs[0]' "$registry_path")"

          assert "\"$resolved_input_dir\" = \"$kb_root\"" \
            "registry should resolve to the packaged knowledge-base root"
          assert "-f $resolved_input_dir/star_upper_gi/main.yaml" \
            "resolved module root should contain the module payload"
        '';
      }
      {
        name = "app-bundle-ships-kb-registry";
        type = "script";
        script = ''
          ${ntlib.helpers.path [
            pkgs.coreutils
            pkgs.gnugrep
          ]}
          ${ntlib.helpers.scriptHelpers}

          app_registry_path="${app_package}/share/lx-dtypes/registries/star_upper_gi.json"
          wrapped_cli="${app_package}/bin/lx-dtypes-kb-registry"

          assert "-f $app_registry_path" "app bundle should ship the packaged KB registry"
          assert "-f $wrapped_cli" "app bundle should ship the registry CLI"

          output="$($wrapped_cli show "$app_registry_path" 2>/dev/null)"
          assert_contains "$output" "star_upper_gi" "wrapped registry CLI should see bundled KB registry"
          assert_file_contains "$wrapped_cli" "LX_DTYPES_KB_REGISTRY" \
            "wrapped app should export the bundled registry variable"
          assert_file_contains "$wrapped_cli" "$app_registry_path" \
            "wrapped app should point LX_DTYPES_KB_REGISTRY at the bundled registry"
        '';
      }
    ];
  };
}
