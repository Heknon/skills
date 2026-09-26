# Session settings so no git command waits for an editor, a pager or a
# password. Run once per terminal session: . <skill>\recipes\session.ps1
# Nothing here is written to git's configuration files.
# Written from session.sh, which ran on Linux; not run on Windows.
$env:GIT_EDITOR = ':'            # git handles ':' itself: no program runs
$env:GIT_SEQUENCE_EDITOR = ':'   # rebase todo lists are taken as they are
$env:GIT_PAGER = 'cat'           # git handles 'cat' itself: no pager
$env:GIT_TERMINAL_PROMPT = '0'   # fail instead of asking for a username
$env:GIT_MERGE_AUTOEDIT = 'no'   # merge never asks for a message
$env:GIT_SSH_COMMAND = 'ssh -o BatchMode=yes'   # ssh fails instead of asking
git --version
