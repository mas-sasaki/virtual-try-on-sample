#!/bin/bash
set -e

# ボリュームの所有権を修正
sudo chown -R vscode: \
    /home/vscode/.config/gcloud \
    /home/vscode/.gemini \
    /home/vscode/.claude \
    /home/vscode/.nix

# Nix のインストール（未インストールの場合のみ）
if ! command -v nix &> /dev/null; then
    echo "Installing Nix (single-user mode)..."

    mkdir -p ~/.config/nix
    cat > ~/.config/nix/nix.conf << 'EOF'
experimental-features = nix-command flakes
filter-syscalls = false
sandbox = false
substituters = https://cache.nixos.org
trusted-public-keys = cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY=
EOF

    curl -sSL https://nixos.org/nix/install | sh -s -- --no-daemon
fi

# Nix 環境を読み込み
if [ -f ~/.nix-profile/etc/profile.d/nix.sh ]; then
    . ~/.nix-profile/etc/profile.d/nix.sh
fi

# nix-direnv のインストール（未インストールの場合のみ）
if ! nix-env -q nix-direnv 2>/dev/null | grep -q nix-direnv; then
    echo "Installing nix-direnv..."
    nix-env -iA nixpkgs.nix-direnv
fi

# direnv の設定
mkdir -p ~/.config/direnv

if ! grep -q "DIRENV_WARN_TIMEOUT" ~/.zshrc 2>/dev/null; then
    cat >> ~/.zshrc << 'EOF'

# direnv settings
export DIRENV_WARN_TIMEOUT=1h
export DIRENV_LOG_FORMAT=
EOF
fi

cat > ~/.config/direnv/direnv.toml << 'EOF'
[global]
hide_env_diff = true
EOF

cat > ~/.config/direnv/direnvrc << 'EOF'
if [ -f ~/.nix-profile/etc/profile.d/nix.sh ]; then
    . ~/.nix-profile/etc/profile.d/nix.sh
fi

if [ -f ~/.nix-profile/share/nix-direnv/direnvrc ]; then
    source ~/.nix-profile/share/nix-direnv/direnvrc
fi
EOF

# Nix 環境フック（カレントディレクトリを動的に取得）
HOOK_SOURCE="source ${PWD}/.devcontainer/nix-env-hook.zsh"
if ! grep -qF "nix-env-hook.zsh" ~/.zshrc 2>/dev/null; then
    cat >> ~/.zshrc << EOF

# Nix devShell 環境フック
[[ -f ${PWD}/.devcontainer/nix-env-hook.zsh ]] && $HOOK_SOURCE
EOF
fi

# direnv を許可
direnv allow

echo -e "\033[1;32mDevContainer setup complete!\033[0m"
