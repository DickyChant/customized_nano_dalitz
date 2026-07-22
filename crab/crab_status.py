#!/usr/bin/env python
"""Status / resubmit / kill helper for the customized-NanoAOD CRAB tasks (run on lxplus).

    python crab_status.py status    [<requestName-substr>]
    python crab_status.py resubmit  [<requestName-substr>]
    python crab_status.py kill       <requestName-substr>
    python crab_status.py report    [<requestName-substr>]   # completed-lumi/eff report
"""
import os, sys, glob
os.environ.setdefault("X509_USER_PROXY", "/eos/user/s/sqian/.proxy")
from CRABAPI.RawCommand import crabCommand

def projects(sub):
    ds = sorted(glob.glob("crab_projects/crab_*"))
    return [d for d in ds if (not sub or sub in d)]

def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]; sub = sys.argv[2] if len(sys.argv) > 2 else ""
    ds = projects(sub)
    if not ds:
        sys.exit("no crab projects under crab_projects/ matching %r" % sub)
    for d in ds:
        print("=" * 8, d)
        try:
            crabCommand(cmd, dir=d)
        except Exception as e:
            print("  !", e)

if __name__ == "__main__":
    main()
