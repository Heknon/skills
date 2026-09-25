def test_header_shows_timezone(pytester):
    pytester.makepyfile("def test_a(): pass")
    result = pytester.runpytest()
    result.stdout.fnmatch_lines(["timezone: *"])


def test_header_can_be_hidden(pytester):
    pytester.makepyfile("def test_a(): pass")
    result = pytester.runpytest("--no-tz-header")
    result.stdout.no_fnmatch_line("timezone: *")


def test_quiet_run_has_no_header(pytester):
    pytester.makepyfile("def test_a(): pass")
    result = pytester.runpytest("-q")
    result.stdout.no_fnmatch_line("timezone: *")
