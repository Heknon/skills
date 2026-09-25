import nox


@nox.session
def tests(session):
    session.install("-e", ".[test]")
    session.run("pytest", "-m", "not slow")


@nox.session
def slow(session):
    session.install("-e", ".[test]")
    session.run("pytest", "-m", "slow")
