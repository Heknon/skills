def __getattr__(name):
    import newdyn
    return getattr(newdyn, name)
