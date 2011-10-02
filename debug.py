import sys
import types
import cocos
import pyglet

def get_refcounts():
    d = {}
    sys.modules
    # collect all classes
    for m in sys.modules.values():
        for sym in dir(m):
            o = getattr (m, sym)
            if type(o) is types.ClassType:
                d[o] = sys.getrefcount (o)
    # sort by refcount
    pairs = map (lambda x: (x[1],x[0]), d.items())
    pairs.sort()
    pairs.reverse()
    return pairs

def print_top(count):
    for n, c in get_refcounts()[:count]:
        print '%10d %s' % (n, c.__name__)

def print_referrers(obj):
    import gc
    referrers = gc.get_referrers(obj)
    print "num referrers", len(referrers)
    for r in referrers:
        print "REFERRER"
        print r

