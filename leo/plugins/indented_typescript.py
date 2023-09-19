#@+leo-ver=5-thin
#@+node:ekr.20230917013414.1: * @file ../plugins/indented_typescript.py
"""
A plugin to edit typescript files using indentation instead of curly brackets.

- The ``open2`` event handler deletes curly brackets,
  after checking that nothing (except comments?) follows curly brackets.
- The ``read1`` event handler inserts curly brackets based on indentation.

Both event handlers will do a check similar to Python's tabnanny module.
"""
import re
from typing import Any
from leo.core import leoGlobals as g
from leo.core.leoCommands import Commands as Cmdr
from leo.core.leoNodes import Position, VNode
from leo.plugins.importers.typescript import TS_Importer

#@+others
#@+node:ekr.20230917084259.1: ** top-level (indented_typescript.py)
#@+node:ekr.20230917015308.1: *3* init (indented_typescript.py)
def init() -> bool:
    """Return True if the plugin has loaded successfully."""
    g.registerHandler('before-create-leo-frame', onCreate)
    g.registerHandler('after-reading-external-file', onAfterRead)
    g.registerHandler('before-writing-external-file', onBeforeWrite)
    return True
#@+node:ekr.20230917084347.1: *3* event handlers (indented_typescript.py)
def onCreate(tag: str, keys: Any) -> None:
    """Instantiate an IndentedTypeScript instance for c."""
    c=keys.get('c')
    if c:
        gControllers[c.hash()] = IndentedTypeScript(c)
    else:
        g.trace(f"Can not happen. c: {c!r}")

def onAfterRead(tag: str, kwargs: Any) -> None:
    """after-reading-external-file event handler for indented_typescript.py"""
    c, p = kwargs.get('c'), kwargs.get('p')
    if c and p:
        controller = gControllers.get(c.hash())
        controller.after_read(c, p)
    else:
        g.trace(f"Can not happen. c: {c!r} p: {p!r}")

def onBeforeWrite(tag: str, kwargs: Any) -> None:
    """before-writing-external-file event handler for indented_typescript.py"""
    c, p = kwargs.get('c'), kwargs.get('p')
    if c and p:
        controller = gControllers.get(c.hash())
        controller.before_write(c, p)
    else:
        g.trace(f"Can not happen. c: {c!r} p: {p!r}")
#@+node:ekr.20230917083456.1: ** class IndentedTypeScript
class IndentedTypeScript:
    """A class to support indented typescript files."""

    def __init__(self, c: Cmdr) -> None:
        self.c = c
        self.importer = TS_Importer(c)

    #@+others
    #@+node:ekr.20230917091730.1: *3* IndentedTS.after_read
    def after_read(self, c: Cmdr, p: Position) -> None:
        """Remove curly brackets from the file given by p.h."""

        # Backup all bodies in case there is an error.
        backup_d: dict[VNode, str] = {}  # Keys are vnodes, values are p.b.
        for p2 in p.self_and_subtree():
            if p2.gnx not in backup_d:
                backup_d [p2.v] = p.b
        
        # Handle each node separately.
        try:
            seen: dict[str, bool] = {}  # Keys are gnxs, values are True.
            for p2 in p.self_and_subtree():
                if p2.gnx not in seen:
                    seen [p2.gnx] = True
                    self.remove_brackets(p2)
        except Exception as e:
            # Restore all body text.
            for v in backup_d:
                v.b = backup_d [v]
            g.es_print(f"Error in indented_typescript plugin: {e}.")
            g.es_print(f"No changes made to {p.h} and its subtree.")
                    
    #@+node:ekr.20230917091801.1: *3* IndentedTS.before_write
    def before_write(self, c, p):
        assert c == self.c
        assert p.isAnyAtFileNode(), p.h
        if not p.h.strip().endswith('.ts'):
            g.trace(f"Not a .ts file: {p.h}")
            return
        g.trace(p.h)
    #@+node:ekr.20230917185546.1: *3* IndentedTS.check_guide_lines
    # No need to worry about comments in guide lines.
    bracket_pat = re.compile(r'^\s*}.*?{\s*$')
    matched_bracket_pat = re.compile(r'{.*?}\s*')

    def check_guide_lines(self, guide_lines: list[str]) -> None:
        """
        Check that all lines contain at most one unmatched '{' or '}'.
        If '}' precedes '{' then only whitespace may appear before '}' and after '{'.
        Raise TypeError if there is a problem.
        """
        trace = False
        for i, line0 in enumerate(guide_lines):
            line = re.sub(self.matched_bracket_pat, '', line0)
            if trace and line != line0:
                g.trace(f"Sub0: Line {i:4}: {line0.strip()}")
                g.trace(f"Sub1: Line {i:4}: {line.strip()}")
            n1 = line.count('{')
            n2 = line.count('}')
            if n1 > 1 or n2 > 1:
                raise TypeError(f"Too many curly brackets in line {i:4}: {line.strip()}")
            if n1 == 1 and n2 == 1 and line.find('{') > line.find('}'):
                m = self.bracket_pat.match(line)
                if not m:
                    raise TypeError(f"Too invalid curly brackets in line {i:4}: {line.strip()}")
                if trace:
                    g.trace(f"Good: Line {i:4}: {line.strip()}")
    #@+node:ekr.20230917184851.1: *3* IndentedTS.find_matching_brackets
    def find_matching_brackets(self, guide_lines: list[str]) -> tuple[int, int]:
        pass
    #@+node:ekr.20230917184608.1: *3* IndentedTS.remove_brackets
    def remove_brackets(self, p: Position) -> None:
        """
        The top-level driver for each node.
        
        Using guide lines, remove most curly brackets from p.b.
        """
        contents = p.b
        if not contents.strip():
            return
        lines = g.splitLines(contents)
        guide_lines = self.importer.make_guide_lines(lines)
        assert lines and len(lines) == len(guide_lines)
        # g.trace(f"{p.h} {len(contents)} chars, {len(lines)} lines")
        
        # May raise TypeError
        self.check_guide_lines(guide_lines)

        ###  To do: compute result_lines.
        # p.b = ''.join(result_lines)
    #@-others
#@-others

gControllers: dict[str, IndentedTypeScript] = {}  # keys are c.hash()
#@-leo
