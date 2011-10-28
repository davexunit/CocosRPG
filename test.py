if __name__ == "__main__":
    #import gc
    #gc.enable()
    #gc.set_debug(gc.DEBUG_UNCOLLECTABLE)

    import game.main
    game.main.main()

    #gc.collect()
    #for x in gc.garbage:
    #    s = str(x)
    #    if len(s) > 80: s = s[:80]
    #    print type(x), " - ", s
