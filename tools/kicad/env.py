"""Paths shared by every kit script: the episode's board folder and the KiCad / Freerouting installs.

Every script takes the episode folder as its first argument, for example
  episodes/002-plant-whisperer     (or that episode's 5-electronics folder)
and reads the episode's own design from 5-electronics/src/design.py and src/layout.py.

Machine paths come from environment variables when set, otherwise from the usual install spots:
  KICAD_SHARE      KiCad's SharedSupport folder (symbols/, footprints/, 3dmodels/)
  JAVA             java binary for Freerouting
  FREEROUTING_JAR  freerouting-<version>.jar
"""

import glob
import os
import shutil
import sys

KIT = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")


def hw_dir(arg):
    """The episode's 5-electronics folder, from either the episode folder or 5-electronics itself."""
    p = os.path.abspath(arg)
    if os.path.basename(p) != "5-electronics":
        p = os.path.join(p, "5-electronics")
    if not os.path.isdir(p):
        raise SystemExit("no 5-electronics folder at " + p)
    return p


def use_episode(argv):
    """Put the kit and the episode's src/ on the import path; return the 5-electronics folder."""
    if len(argv) < 2:
        raise SystemExit("usage: %s <episode folder> ..." % os.path.basename(argv[0]))
    hw = hw_dir(argv[1])
    src = os.path.join(hw, "src")
    if not os.path.isfile(os.path.join(src, "design.py")):
        raise SystemExit("no %s/design.py: start one with tools/kicad/new_board.sh" % src)
    for p in (src, KIT):
        if p not in sys.path:
            sys.path.insert(0, p)
    return hw


def first(*cands):
    for c in cands:
        if c and os.path.exists(c):
            return c
    return None


def kicad_share():
    p = first(os.environ.get("KICAD_SHARE"),
              "/Applications/KiCad/KiCad.app/Contents/SharedSupport",
              "/usr/share/kicad", "/usr/local/share/kicad")
    if not p:
        raise SystemExit("KiCad libraries not found: set KICAD_SHARE to the folder holding symbols/ and footprints/")
    return p


def java():
    found = sorted(glob.glob(HOME + "/.local/opt/jdk*/Contents/Home/bin/java")) + \
        sorted(glob.glob(HOME + "/.local/opt/jdk*/bin/java"))
    return first(os.environ.get("JAVA"), *reversed(found)) or shutil.which("java") or "java"


def freerouting_jar():
    jars = sorted(glob.glob(HOME + "/.local/opt/freerouting/freerouting-*.jar"))
    p = first(os.environ.get("FREEROUTING_JAR"), *reversed(jars))
    if not p:
        raise SystemExit("Freerouting not found: set FREEROUTING_JAR (download from "
                         "https://github.com/freerouting/freerouting/releases)")
    return p
