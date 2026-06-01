{
  description = "Project Description Here";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };

      in {

        devShells.default = pkgs.mkShell {
          name = "dev-env";

          buildInputs = with pkgs; [
            # Python
            python312
            uv

            # IaC & Cloud
            terraform
            google-cloud-sdk

            # 開発ツール
            go-task
            gh
            pre-commit
            jq

            # コーディングエージェント
            claude-code
            gemini-cli

            # ここにプロジェクト固有のパッケージを追加
          ];

          shellHook = ''
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.zlib}/lib:$LD_LIBRARY_PATH"

            export PYTHONDONTWRITEBYTECODE=1
            export PYTHONUNBUFFERED=1
            export UV_NO_CACHE=1
            export UV_LINK_MODE=copy
            export TZ="Asia/Tokyo"
            export LANG="en_US.UTF-8"

            if [ -f ".venv/bin/activate" ]; then
              source .venv/bin/activate
            fi

            clear
            echo -e "\033[1;36m🚀 Nix devShell activated\033[0m"
          '';
        };
      }
    );
}
