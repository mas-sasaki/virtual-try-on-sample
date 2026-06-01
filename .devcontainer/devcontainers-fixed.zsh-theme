# Oh My Zsh! theme - fixed version

# Oh My Zsh の git_prompt_info を使用（組み込み機能）
ZSH_THEME_GIT_PROMPT_PREFIX="%{$fg[cyan]%}(%{$fg[red]%}"
ZSH_THEME_GIT_PROMPT_SUFFIX="%{$reset_color%} "
ZSH_THEME_GIT_PROMPT_DIRTY="%{$fg[cyan]%})"
ZSH_THEME_GIT_PROMPT_CLEAN="%{$fg[cyan]%})"

PROMPT='%{$fg[green]%}%n %(?:%{$reset_color%}> :%{$fg_bold[red]%}> )%{$fg_bold[blue]%}%~%{$reset_color%} $(git_prompt_info)%{$fg[white]%}$%{$reset_color%} '
