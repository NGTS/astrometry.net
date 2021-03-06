from astrometry.util.file import *

'''

Stages: a utility for saving and resuming computation, savings
intermediate results as pickle files.


'''



class CallGlobal(object):
    def __init__(self, pattern, globals, *args, **kwargs):
        self.pat = pattern
        self.args = args
        self.kwargs = kwargs
        self.globals = globals
    def getfunc(self, stage):
        func = self.pat % stage
        func = eval(func, self.globals)
        return func
    def getkwargs(self, stage, **kwargs):
        kwa = self.kwargs.copy()
        kwa.update(kwargs)
        return kwa
    def __call__(self, stage, **kwargs):
        func = self.getfunc(stage)
        kwa = self.getkwargs(stage, **kwargs)
        return func(*self.args, **kwa)

class CallGlobalTime(CallGlobal):
    def __call__(self, stage, **kwargs):
        from astrometry.util.ttime import Time
        from datetime import datetime
        t0 = Time()
        print 'Running stage', stage, 'at', datetime.now().isoformat()
        rtn = super(CallGlobalTime, self).__call__(stage, **kwargs)
        t1 = Time()
        print 'Stage', stage, ':', t1-t0
        print 'Stage', stage, 'finished:', datetime.now().isoformat()
        return rtn

def runstage(stage, picklepat, stagefunc, force=[], forceall=False, prereqs={},
             update=True, write=True, initial_args={}, **kwargs):
    # NOTE, if you add or change args here, be sure to update the recursive
    # "runstage" call below!!
    print 'Runstage', stage

    try:
        pfn = picklepat % stage
    except:
        pfn = picklepat % dict(stage=stage)
    
    if os.path.exists(pfn):
        if forceall or stage in force:
            print 'Ignoring pickle', pfn, 'and forcing stage', stage
        else:
            print 'Reading pickle', pfn
            R = unpickle_from_file(pfn)
            return R

    if stage <= 0:
        P = initial_args
    else:
        try:
            prereq = prereqs[stage]
        except KeyError:
            prereq = stage - 1

        if prereq is None:
            P = initial_args

        else:
            P = runstage(prereq, picklepat, stagefunc,
                         force=force, forceall=forceall, prereqs=prereqs, update=update,
                         write=write, initial_args=initial_args, **kwargs)

    #P.update(kwargs)
    Px = P.copy()
    Px.update(kwargs)

    print 'Running stage', stage
    print 'Prereq keys:', P.keys()
    print 'Addings kwargs keys:', Px.keys()

    R = stagefunc(stage, **Px)
    print 'Stage', stage, 'finished'
    if R is not None:
        print 'Result keys:', R.keys()

    if update:
        if R is not None:
            P.update(R)
        R = P
        
    if write:
        print 'Saving pickle', pfn
        print 'Pickling keys:', R.keys()

        pickle_to_file(R, pfn)
        print 'Saved', pfn
    return R
