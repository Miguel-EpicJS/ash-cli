def get_bash_completion() -> str:
    return """
_ash_cli_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="--model --temp --max-tokens --url --debug -v --reset --session --sessions --list-models --export --import --rename --version --help"

    if [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
}
complete -F _ash_cli_completion ash-cli
"""


def get_zsh_completion() -> str:
    return """
#compdef ash-cli
_ash_cli() {
    _arguments \\
        '--model[Model ID to use]' \\
        '--temp[Sampling temperature]' \\
        '--max-tokens[Maximum tokens to generate]' \\
        '--url[Model API base URL]' \\
        '(--debug -v)'{-v,--debug}'[Enable debug mode]' \\
        '--reset[Reset configuration to defaults]' \\
        '--session[Session ID to load]' \\
        '--sessions[List all sessions]' \\
        '--list-models[List available models]' \\
        '--export[Export session to file]' \\
        '--import[Import session from file]' \\
        '--rename[Rename session]' \\
        '--version[Show version]' \\
        '--help[Show help]'
}
_ash_cli "$@"
"""
