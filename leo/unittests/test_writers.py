#@+leo-ver=5-thin
#@+node:ekr.20220812224747.1: * @file ../unittests/test_writers.py
"""Tests of leo/plugins/writers"""
import textwrap
from leo.core import leoGlobals as g
from leo.core.leoTest2 import LeoUnitTest
from leo.plugins.writers.dart import DartWriter
from leo.plugins.writers.markdown import MarkdownWriter
from leo.plugins.writers.leo_rst import RstWriter
from leo.plugins.writers.treepad import TreePad_Writer
#@+others
#@+node:ekr.20220812144517.1: ** class BaseTestWriter(LeoUnitTest)
class BaseTestWriter(LeoUnitTest):
    """The base class for all tests of Leo's writer plugins."""
#@+node:ekr.20220812141705.1: ** class TestBaseWriter(BaseTestWriter)
class TestBaseWriter(BaseTestWriter):
    """Test cases for the BaseWriter class."""
    #@+others
    #@+node:ekr.20220812141805.1: *3* TestBaseWriter.test_put_node_sentinel
    def test_put_node_sentinel(self):

        from leo.plugins.writers.basewriter import BaseWriter
        c, root = self.c, self.c.p
        at = c.atFileCommands
        x = BaseWriter(c)
        table = (
            ('#', None),
            ('<--', '-->'),
        )
        child = root.insertAsLastChild()
        child.h = 'child'
        grandchild = child.insertAsLastChild()
        grandchild.h = 'grandchild'
        greatgrandchild = grandchild.insertAsLastChild()
        greatgrandchild.h = 'greatgrandchild'
        for p in (root, child, grandchild, greatgrandchild):
            for delim1, delim2 in table:
                at.outputList = []
                x.put_node_sentinel(p, delim1, delim2)
    #@-others
#@+node:ekr.20220812175240.1: ** class TestDartWriter(BaseTestWriter)
class TestDartWriter(BaseTestWriter):
    """Test Cases for the dart writer plugin."""
    #@+others
    #@+node:ekr.20220812175936.1: *3* TestDartWriter.test_dart_writer
    def test_dart_writer(self):

        c, root = self.c, self.c.p
        child = root.insertAsLastChild()
        child.h = 'h'
        child.b = 'dart line 1\ndart_line2\n'
        x = DartWriter(c)
        x.write(root)
    #@-others
#@+node:ekr.20231219151314.1: ** class TestMDWriter(BaseTestWriter)
class TestMarkdownWriter(BaseTestWriter):
    """Test Cases for the markdown writer plugin."""
    #@+others
    #@+node:ekr.20231219151402.1: *3* TestMDWriter.test_markdown_writer
    def test_markdown_writer(self):
        
        ### Should be a round-trip test.
        
        g.trace('=====')

        contents = textwrap.dedent("""
            # 1st level title X

            some text in body X

            ## 2nd level title Z

            some text in body Z

            # 1st level title A

            ## 2nd level title B 

            some body content of the 2nd node 
        """).strip() + '\n'

        c, root = self.c, self.c.p
        child = root.insertAsLastChild()
        child.h = 'h'
        child.b = contents
        x = MarkdownWriter(c)
        x.write(child)
        results_list = c.atFileCommands.outputList
        results_s = ''.join(results_list)
        if 0:
            g.printObj(contents, tag='contents')
            g.printObj(results_s, tag='results_s')
        # results = ''.join(results_list)
        self.assertEqual(results_s, contents)
        ### self.assertEqual(results_list,  g.splitLines(contents))
    #@-others
#@+node:ekr.20220812175633.1: ** class TestRstWriter(BaseTestWriter)
class TestRstWriter(BaseTestWriter):
    """Test Cases for the leo_rst writer plugin."""
    #@+others
    #@+node:ekr.20220812175959.1: *3* TestRstWriter.test_rst_writer
    def test_rst_writer(self):

        c, root = self.c, self.c.p
        child = root.insertAsLastChild()
        child.h = 'h'
        # For full coverage, we don't want a leading newline.
        child.b = textwrap.dedent("""\
            .. toc

            ====
            top
            ====

            The top section

            section 1
            ---------

            section 1, line 1
            --
            section 1, line 2

            section 2
            ---------

            section 2, line 1

            section 2.1
            ~~~~~~~~~~~

            section 2.1, line 1

            section 2.1.1
            .............

            section 2.2.1 line 1

            section 3
            ---------

            section 3, line 1

            section 3.1.1
            .............

            section 3.1.1, line 1
        """)  # No newline, on purpose.
        x = RstWriter(c)
        x.write(root)
    #@-others
#@+node:ekr.20220812175716.1: ** class TestTreepadWriter(BaseTestWriter)
class TestTreepadWriter(BaseTestWriter):
    """Test Cases for the treepad writer plugin."""
    #@+others
    #@+node:ekr.20220812180015.1: *3* TestTreepadWriter.test_treepad_writer
    def test_treepad_writer(self):

        c, root = self.c, self.c.p
        child = root.insertAsLastChild()
        child.h = 'h'
        child.b = 'line 1\nline2\n'
        x = TreePad_Writer(c)
        x.write(root)
    #@-others
#@-others
#@@language python
#@-leo
