echo off
cls

::cd c:\Repos\leo-editor
call %~dp0\set-repo-dir

echo test-one-leo: test_leoFind.TestFind
call py -m unittest leo.unittests.core.test_leoGlobals.TestGlobals.test_g_handleScriptException
