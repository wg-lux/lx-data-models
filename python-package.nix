{
  lib,
  python312Packages,
  ffmpeg-headless,
  tesseract,
  glib,
  zlib,
  libglvnd,
}:

let
  py = python312Packages;
  pname = "lx-dtypes";
  version = "0.1.1";

  src = lib.cleanSourceWith {
    src = ./.;
    filter =
      path: type:
      let
        rel = lib.removePrefix "${toString ./.}/" (toString path);
        base = builtins.baseNameOf (toString path);
        ignored_base_names = [
          ".devenv"
          ".direnv"
          ".env"
          ".git"
          ".mypy_cache"
          ".pytest_cache"
          ".ruff_cache"
          ".venv"
          "__pycache__"
          "result"
        ];
        ignored_prefixes = [
          "docs/_build/"
          "htmlcov/"
        ];
      in
      !(builtins.elem base ignored_base_names || lib.any (prefix: lib.hasPrefix prefix rel) ignored_prefixes);
  };

  python_deps = with py; [
    bibtexparser
    django
    django-ninja
    django-stubs
    django-stubs-ext
    icecream
    numpy
    opencv-python-headless
    openpyxl
    pandas
    pandas-stubs
    pandera
    pillow
    pydantic
    python-ffmpeg
    pyyaml
    requests
    scikit-learn
    scipy
    types-pyyaml
  ];

  runtime_tools = [
    ffmpeg-headless
    tesseract
  ];
in
py.buildPythonPackage {
  inherit pname version src;
  pyproject = true;

  nativeBuildInputs = [
    py.hatchling
  ];

  propagatedBuildInputs = python_deps;

  buildInputs = [
    glib
    zlib
    libglvnd
  ] ++ runtime_tools;

  pythonImportsCheck = [
    "lx_dtypes"
    "lx_dtypes.models.interface"
  ];

  postInstall = ''
    featureRoot="$out/share/lx-data-models/features"
    mkdir -p "$featureRoot"
    cp ${./features/PackagedKnowledgeBaseResources.yml} \
      "$featureRoot/packaged_knowledge_base_resources.yml"
    cp ${./features/FrameCleanerIntegration.yml} \
      "$featureRoot/frame_cleaner_integration.yml"
    cp ${./features/ReportReaderIntegration.yml} \
      "$featureRoot/report_reader_integration.yml"
  '';

  makeWrapperArgs = [
    "--prefix PATH : ${lib.makeBinPath runtime_tools}"
    "--prefix LD_LIBRARY_PATH : ${lib.makeLibraryPath [
      glib
      zlib
      libglvnd
    ]}"
  ];

  meta = with lib; {
    description = "Python package for lx-dtypes data models and knowledge-base tooling";
    homepage = "https://github.com/wg-lux/lx-data-models";
    license = licenses.mit;
    platforms = platforms.linux;
  };
}
