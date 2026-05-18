"""Shell completion scripts for cubby.

`render(shell, commands)` returns a completion script that completes cubby's
command names. The command list is baked in at generation time, so a script
regenerated after an update always reflects the current command set — there is
no runtime callback into cubby.
"""

SHELLS = ("bash", "zsh", "fish")


def render(shell: str, commands: list) -> str:
    """Return the completion script for `shell`. Raises ValueError for an
    unknown shell."""
    if shell not in SHELLS:
        raise ValueError(
            f"unknown shell '{shell}' — choose from {', '.join(SHELLS)}")
    words = " ".join(commands)
    return {"bash": _BASH, "zsh": _ZSH, "fish": _FISH}[shell].format(words=words)


_BASH = """\
# cubby bash completion — add to ~/.bashrc:  eval "$(cubby completion bash)"
_cubby_complete() {{
    if [ "$COMP_CWORD" -eq 1 ]; then
        COMPREPLY=( $(compgen -W "{words}" -- "${{COMP_WORDS[COMP_CWORD]}}") )
    fi
}}
complete -F _cubby_complete cubby
"""

_ZSH = """\
# cubby zsh completion — add to ~/.zshrc:  eval "$(cubby completion zsh)"
_cubby() {{
    if (( CURRENT == 2 )); then
        compadd -- {words}
    fi
}}
compdef _cubby cubby
"""

_FISH = """\
# cubby fish completion — run:  cubby completion fish > ~/.config/fish/completions/cubby.fish
complete -c cubby -f -n '__fish_use_subcommand' -a '{words}'
"""
