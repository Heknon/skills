# Session settings so no git command waits for an editor, a pager or a
# password. Source it once per shell: . <skill>/recipes/session.sh
# Nothing here is written to git's configuration files. Ran on Linux
# with git 2.43.0 and 2.55.0.
export GIT_EDITOR=:              # git handles ':' itself: no program runs
export GIT_SEQUENCE_EDITOR=:     # rebase todo lists are taken as they are
export GIT_PAGER=cat             # git handles 'cat' itself: no pager
export GIT_TERMINAL_PROMPT=0     # fail instead of asking for a username
export GIT_MERGE_AUTOEDIT=no     # merge never asks for a message
export GIT_SSH_COMMAND='ssh -o BatchMode=yes'   # ssh fails instead of asking
git --version
