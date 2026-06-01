# syntax=docker/dockerfile:1
FROM --platform=amd64 mcr.microsoft.com/devcontainers/base:ubuntu

# direnv のインストール
RUN apt-get update && apt-get install -y --no-install-recommends direnv \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# タイムゾーンを JST に設定
RUN ln -sf /usr/share/zoneinfo/Asia/Tokyo /etc/localtime \
    && echo "Asia/Tokyo" > /etc/timezone

USER vscode

# zsh テーマのコピー（ファイルが存在する場合のみコピーして適用する安全な記述）
COPY --chown=vscode:vscode devcontainers-fixed.zsh-theme* /tmp/
RUN if [ -f "/tmp/devcontainers-fixed.zsh-theme" ]; then \
        mv /tmp/devcontainers-fixed.zsh-theme /home/vscode/.oh-my-zsh/custom/themes/ && \
        sed -i 's/ZSH_THEME=".*"/ZSH_THEME="devcontainers-fixed"/' ~/.zshrc; \
    fi

# ディレクトリ作成（~/.nix-profile は Nix がシンボリックリンクとして作成するので除外）
RUN mkdir -p ~/.local/bin ~/.config/nix ~/.config/direnv ~/.claude

# direnv の設定（warn_timeout 延長、ログ無効化）
RUN echo '[global]' > ~/.config/direnv/direnv.toml \
    && echo 'warn_timeout = "300s"' >> ~/.config/direnv/direnv.toml \
    && echo 'hide_env_diff = true' >> ~/.config/direnv/direnv.toml \
    && echo 'log_format = ""' >> ~/.config/direnv/direnv.toml

# シェル設定に direnv hook と Nix 環境を追加
RUN echo '[ -f ~/.nix-profile/etc/profile.d/nix.sh ] && . ~/.nix-profile/etc/profile.d/nix.sh' >> ~/.bashrc \
    && echo 'eval "$(direnv hook bash)"' >> ~/.bashrc \
    && echo '[ -f ~/.nix-profile/etc/profile.d/nix.sh ] && . ~/.nix-profile/etc/profile.d/nix.sh' >> ~/.zshrc \
    && echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc

ENV CLAUDE_CONFIG_DIR="/home/vscode/.claude"
ENV LANG="en_US.UTF-8"
ENV PATH="/home/vscode/.nix-profile/bin:$PATH"
