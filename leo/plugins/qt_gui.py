#@+leo-ver=5-thin
#@+node:ekr.20140907085654.18699: * @file ../plugins/qt_gui.py
'''This file contains the gui wrapper for Qt: g.app.gui.'''
#@+<< imports >>
#@+node:ekr.20140918102920.17891: ** << imports >> (qt_gui.py)
import leo.core.leoColor as leoColor
import leo.core.leoGlobals as g
import leo.core.leoGui as leoGui
from leo.core.leoQt import isQt5, Qsci, QString, QtCore, QtGui, QtWidgets
    # This import causes pylint to fail on this file and on leoBridge.py.
    # The failure is in astroid: raw_building.py.
import leo.plugins.qt_events as qt_events
import leo.plugins.qt_frame as qt_frame
import leo.plugins.qt_idle_time as qt_idle_time
import leo.plugins.qt_text as qt_text
import datetime
# import os
import re
import sys
if 1:
    # This defines the commands defined by @g.command.
    # pylint: disable=unused-import
    import leo.plugins.qt_commands as qt_commands
    assert qt_commands
#@-<< imports >>
# < < new_gui: commands for tabs > >
#@+others
#@+node:ekr.20110605121601.18134: ** init (qt_gui.py)
def init():

    if g.app.unitTesting: # Not Ok for unit testing!
        return False
    if not QtCore:
        return False
    if g.app.gui:
        return g.app.gui.guiName() == 'qt'
    g.app.gui = LeoQtGui()
    g.app.gui.finishCreate()
    g.plugin_signon(__name__)
    return True
#@+node:ekr.20140907085654.18700: ** class LeoQtGui(leoGui.LeoGui)
class LeoQtGui(leoGui.LeoGui):
    '''A class implementing Leo's Qt gui.'''
    #@+others
    #@+node:ekr.20110605121601.18477: *3*  qt_gui.__init__ (sets qtApp) (changed)
    def __init__(self):
        '''Ctor for LeoQtGui class.'''
        super().__init__('qt')
             # Initialize the base class.
        self.active = True
        self.consoleOnly = False # Console is separate from the log.
        self.iconimages = {}
        self.idleTimeClass = qt_idle_time.IdleTime
        self.insert_char_flag = False # A flag for eventFilter.
        self.mGuiName = 'qt'
        self.main_window = None
            # The *singleton* QMainWindow.
        self.plainTextWidget = qt_text.PlainTextWrapper
        self.styleSheetManagerClass = StyleSheetManager
            # For c.idle_focus_helper and activate/deactivate events.
        # Create objects...
        self.qtApp = QtWidgets.QApplication(sys.argv)
        self.reloadSettings()
        self.appIcon = self.getIconImage('leoapp32.png')
        #
        # Define various classes key stokes.
        #@+<< define FKeys >>
        #@+node:ekr.20180419110303.1: *4* << define FKeys >>
        self.FKeys = ['F1','F2','F3','F4','F5','F6','F7','F8','F9','F10','F11','F12']
            # These do not generate keystrokes on MacOs.
        #@-<< define FKeys >>
        #@+<< define ignoreChars >>
        #@+node:ekr.20180419105250.1: *4* << define ignoreChars >>
        # Always ignore these characters
        self.ignoreChars = [
            # These are in ks.special characters.
            # They should *not* be ignored.
                # 'Left', 'Right', 'Up', 'Down',
                # 'Next', 'Prior',
                # 'Home', 'End',
                # 'Delete', 'Escape',
                # 'BackSpace', 'Linefeed', 'Return', 'Tab',
            # F-Keys are also ok.
                # 'F1','F2','F3','F4','F5','F6','F7','F8','F9','F10','F11','F12',
            'KP_0','KP_1','KP_2','KP_3','KP_4','KP_5','KP_6','KP_7','KP_8','KP_9',
            'KP_Multiply, KP_Separator,KP_Space, KP_Subtract, KP_Tab',
            'KP_F1','KP_F2','KP_F3','KP_F4',
            'KP_Add', 'KP_Decimal', 'KP_Divide', 'KP_Enter', 'KP_Equal',
                # Keypad chars should be have been converted to other keys.
                # Users should just bind to the corresponding normal keys.
            'CapsLock', 'Caps_Lock',
            'NumLock', 'Num_Lock',
            'ScrollLock',
            'Alt_L', 'Alt_R',
            'Control_L', 'Control_R',
            'Meta_L', 'Meta_R',
            'Shift_L', 'Shift_R',
            'Win_L', 'Win_R',
                # Clearly, these should never be generated.
            'Break', 'Pause', 'Sys_Req',
                # These are real keys, but they don't mean anything.
            'Begin', 'Clear',
                # Don't know what these are.
        ]
        #@-<< define ignoreChars >>
        #@+<< define specialChars >>
        #@+node:ekr.20180419081404.1: *4* << define specialChars >>
        # Keys whose names must never be inserted into text.
        self.specialChars = [
            # These are *not* special keys.
                # 'BackSpace', 'Linefeed', 'Return', 'Tab',
            'Left', 'Right', 'Up', 'Down',
                # Arrow keys
            'Next', 'Prior',
                # Page up/down keys.
            'Home', 'End',
                # Home end keys.
            'Delete', 'Escape',
                # Others.
            'Enter', 'Insert', 'Ins',
                # These should only work if bound.
            'Menu',
                # #901.
            'PgUp', 'PgDn',
                # #868.
        ]
        #@-<< define specialChars >>
        # Put up the splash screen()
        if (g.app.use_splash_screen and
            not g.app.batchMode and
            not g.app.silentMode and
            not g.unitTesting
        ):
            self.splashScreen = self.createSplashScreen()
        if g.new_gui:
            self.leoFrames = {}
                # Keys are DynamicWindows, values are frames.
            self.alwaysShowTabs = True
                # # Set to true to workaround a problem
                # # setting the window title when tabs are shown.
            self.main_window = self.make_main_window()
            self.make_outlines_dock()
            # All the other work is done later!
            # self.create_status_bar()
        else:
            # #1171:
            self.frameFactory = qt_frame.TabbedFrameFactory()
                # This creates commands *only*.
            ### Sets these ivars:
                # self.alwaysShowTabs = True
                    # # Set to true to workaround a problem
                    # # setting the window title when tabs are shown.
                # self.leoFrames = {}
                    # # Keys are DynamicWindows, values are frames.
                # self.masterFrame = None
        
    def reloadSettings(self):
        pass
    #@+node:ekr.20110605121601.18484: *3*  qt_gui.destroySelf (calls qtApp.quit)
    def destroySelf(self):

        QtCore.pyqtRemoveInputHook()
        if 'shutdown' in g.app.debug:
            g.pr('LeoQtGui.destroySelf: calling qtApp.Quit')
        self.qtApp.quit()
    #@+node:ekr.20110605121601.18485: *3* qt_gui.Clipboard


    #@+node:ekr.20160917125946.1: *4* qt_gui.replaceClipboardWith
    def replaceClipboardWith(self, s):
        '''Replace the clipboard with the string s.'''
        cb = self.qtApp.clipboard()
        if cb:
            # cb.clear()  # unnecessary, breaks on some Qt versions
            s = g.toUnicode(s)
            QtWidgets.QApplication.processEvents()
            # Fix #241: QMimeData object error
            cb.setText(QString(s))
            QtWidgets.QApplication.processEvents()
        else:
            g.trace('no clipboard!')
    #@+node:ekr.20160917125948.1: *4* qt_gui.getTextFromClipboard
    def getTextFromClipboard(self):
        '''Get a unicode string from the clipboard.'''
        cb = self.qtApp.clipboard()
        if cb:
            QtWidgets.QApplication.processEvents()
            return cb.text()
        g.trace('no clipboard!')
        return ''
    #@+node:ekr.20160917130023.1: *4* qt_gui.setClipboardSelection
    def setClipboardSelection(self, s):
        '''
        Set the clipboard selection to s.
        There are problems with PyQt5.
        '''
        if isQt5:
            # Alas, returning s reopens #218.
            return
        if s:
            # This code generates a harmless, but annoying warning on PyQt5.
            cb = self.qtApp.clipboard()
            cb.setText(QString(s), mode=cb.Selection)
    #@+node:ekr.20110605121601.18487: *3* qt_gui.Dialogs & panels
    #@+node:ekr.20110605121601.18488: *4* qt_gui.alert
    def alert(self, c, message):
        if g.unitTesting: return
        b = QtWidgets.QMessageBox
        d = b(None)
        d.setWindowTitle('Alert')
        d.setText(message)
        d.setIcon(b.Warning)
        d.addButton('Ok', b.YesRole)
        c.in_qt_dialog = True
        d.exec_()
        c.in_qt_dialog = False
    #@+node:ekr.20110605121601.18489: *4* qt_gui.makeFilter
    def makeFilter(self, filetypes):
        '''Return the Qt-style dialog filter from filetypes list.'''
        filters = ['%s (%s)' % (z) for z in filetypes]
        return ';;'.join(filters)
    #@+node:ekr.20150615211522.1: *4* qt_gui.openFindDialog & helpers
    def openFindDialog(self, c):
        if g.unitTesting:
            return
        d = self.globalFindDialog
        if not d:
            d = self.createFindDialog(c)
            self.globalFindDialog = d
            # Fix #516: Do the following only once...
            d.setStyleSheet(c.active_stylesheet)
            # Set the commander's FindTabManager.
            assert g.app.globalFindTabManager
            c.ftm = g.app.globalFindTabManager
            fn = c.shortFileName() or 'Untitled'
            d.setWindowTitle('Find in %s' % fn)
            c.frame.top.find_status_edit.setText('')
        c.inCommand = False
        if d.isVisible():
            # The order is important, and tricky.
            d.focusWidget()
            d.show()
            d.raise_()
            d.activateWindow()
        else:
            d.show()
            d.exec_()
    #@+node:ekr.20150619053138.1: *5* qt_gui.createFindDialog
    def createFindDialog(self, c):
        '''Create and init a non-modal Find dialog.'''
        g.app.globalFindTabManager = c.findCommands.ftm
        top = c.frame.top
            # top is the DynamicWindow class.
        w = top.findTab
        top.find_status_label.setText('Find Status:')

        d = QtWidgets.QDialog()
        # Fix #516: Hide the dialog. Never delete it.

        def closeEvent(event, d=d):
            event.ignore()
            d.hide()

        d.closeEvent = closeEvent
        layout = QtWidgets.QVBoxLayout(d)
        layout.addWidget(w)
        self.attachLeoIcon(d)
        d.setLayout(layout)
        c.styleSheetManager.set_style_sheets(w=d)
        g.app.gui.setFilter(c, d, d, 'find-dialog')
            # This makes most standard bindings available.
        d.setModal(False)
        return d
    #@+node:ekr.20150619053840.1: *5* qt_gui.findDialogSelectCommander
    def findDialogSelectCommander(self, c):
        '''Update the Find Dialog when c changes.'''
        if self.globalFindDialog:
            c.ftm = g.app.globalFindTabManager
            d = self.globalFindDialog
            fn = c.shortFileName() or 'Untitled'
            d.setWindowTitle('Find in %s' % fn)
            c.inCommand = False
    #@+node:ekr.20150619131141.1: *5* qt_gui.hideFindDialog
    def hideFindDialog(self):
        d = self.globalFindDialog
        if d:
            d.hide()
    #@+node:ekr.20110605121601.18492: *4* qt_gui.panels
    def createComparePanel(self, c):
        """Create a qt color picker panel."""
        return None # This window is optional.

    def createFindTab(self, c, parentFrame):
        """Create a qt find tab in the indicated frame."""
        pass # Now done in dw.createFindTab.

    def createLeoFrame(self, c, title):
        """Create a new Leo frame."""
        gui = self
        return qt_frame.LeoQtFrame(c, title, gui)

    def createSpellTab(self, c, spellHandler, tabName):
        return qt_frame.LeoQtSpellTab(c, spellHandler, tabName)

    #@+node:ekr.20110605121601.18493: *4* qt_gui.runAboutLeoDialog
    def runAboutLeoDialog(self, c, version, theCopyright, url, email):
        """Create and run a qt About Leo dialog."""
        if g.unitTesting:
            return
        b = QtWidgets.QMessageBox
        d = b(c.frame.top)
        d.setText('%s\n%s\n%s\n%s' % (
            version, theCopyright, url, email))
        d.setIcon(b.Information)
        yes = d.addButton('Ok', b.YesRole)
        d.setDefaultButton(yes)
        c.in_qt_dialog = True
        d.exec_()
        c.in_qt_dialog = False
    #@+node:ekr.20110605121601.18496: *4* qt_gui.runAskDateTimeDialog
    def runAskDateTimeDialog(self, c, title,
        message='Select Date/Time',
        init=None,
        step_min=None
    ):
        """Create and run a qt date/time selection dialog.

        init - a datetime, default now
        step_min - a dict, keys are QtWidgets.QDateTimeEdit Sections, like
          QtWidgets.QDateTimeEdit.MinuteSection, and values are integers,
          the minimum amount that section of the date/time changes
          when you roll the mouse wheel.

        E.g. (5 minute increments in minute field):

            print g.app.gui.runAskDateTimeDialog(c, 'When?',
              message="When is it?",
              step_min={QtWidgets.QDateTimeEdit.MinuteSection: 5})

        """

        class DateTimeEditStepped(QtWidgets.QDateTimeEdit):
            """QDateTimeEdit which allows you to set minimum steps on fields, e.g.
              DateTimeEditStepped(parent, {QtWidgets.QDateTimeEdit.MinuteSection: 5})
            for a minimum 5 minute increment on the minute field.
            """

            def __init__(self, parent=None, init=None, step_min=None):
                if step_min is None: step_min = {}
                self.step_min = step_min
                if init:
                    super().__init__(init, parent)
                else:
                    super().__init__(parent)

            def stepBy(self, step):
                cs = self.currentSection()
                if cs in self.step_min and abs(step) < self.step_min[cs]:
                    step = self.step_min[cs] if step > 0 else - self.step_min[cs]
                QtWidgets.QDateTimeEdit.stepBy(self, step)

        class Calendar(QtWidgets.QDialog):

            def __init__(self,
                parent=None,
                message='Select Date/Time',
                init=None,
                step_min=None
            ):
                if step_min is None: step_min = {}
                super().__init__(parent)
                layout = QtWidgets.QVBoxLayout()
                self.setLayout(layout)
                layout.addWidget(QtWidgets.QLabel(message))
                self.dt = DateTimeEditStepped(init=init, step_min=step_min)
                self.dt.setCalendarPopup(True)
                layout.addWidget(self.dt)
                buttonBox = QtWidgets.QDialogButtonBox(
                    QtWidgets.QDialogButtonBox.Ok |
                    QtWidgets.QDialogButtonBox.Cancel)
                layout.addWidget(buttonBox)
                buttonBox.accepted.connect(self.accept)
                buttonBox.rejected.connect(self.reject)

        if g.unitTesting: return None
        if step_min is None: step_min = {}
        b = Calendar
        if not init:
            init = datetime.datetime.now()
        d = b(c.frame.top, message=message, init=init, step_min=step_min)
        d.setStyleSheet(c.active_stylesheet)
        d.setWindowTitle(title)
        c.in_qt_dialog = True
        val = d.exec_()
        c.in_qt_dialog = False
        if val != d.Accepted:
            return None
        return d.dt.dateTime().toPyDateTime()
    #@+node:ekr.20110605121601.18494: *4* qt_gui.runAskLeoIDDialog
    def runAskLeoIDDialog(self):
        """Create and run a dialog to get g.app.LeoID."""
        if g.unitTesting: return None
        message = (
            "leoID.txt not found\n\n" +
            "Please enter an id that identifies you uniquely.\n" +
            "Your cvs/bzr login name is a good choice.\n\n" +
            "Leo uses this id to uniquely identify nodes.\n\n" +
            "Your id must contain only letters and numbers\n" +
            "and must be at least 3 characters in length.")
        parent = None
        title = 'Enter Leo id'
        s, ok = QtWidgets.QInputDialog.getText(parent, title, message)
        return s
    #@+node:ekr.20110605121601.18491: *4* qt_gui.runAskOkCancelNumberDialog
    def runAskOkCancelNumberDialog(self, c, title, message, cancelButtonText=None, okButtonText=None):
        """Create and run askOkCancelNumber dialog ."""
        if g.unitTesting: return None
        # n,ok = QtWidgets.QInputDialog.getDouble(None,title,message)
        d = QtWidgets.QInputDialog()
        d.setStyleSheet(c.active_stylesheet)
        d.setWindowTitle(title)
        d.setLabelText(message)
        if cancelButtonText:
            d.setCancelButtonText(cancelButtonText)
        if okButtonText:
            d.setOkButtonText(okButtonText)
        self.attachLeoIcon(d)
        ok = d.exec_()
        n = d.textValue()
        try:
            n = float(n)
        except ValueError:
            n = None
        return n if ok else None
    #@+node:ekr.20110605121601.18490: *4* qt_gui.runAskOkCancelStringDialog
    def runAskOkCancelStringDialog(self, c, title, message, cancelButtonText=None,
                                   okButtonText=None, default="", wide=False):
        """Create and run askOkCancelString dialog.

        wide - edit a long string
        """
        if g.unitTesting: return None
        d = QtWidgets.QInputDialog()
        d.setStyleSheet(c.active_stylesheet)
        d.setWindowTitle(title)
        d.setLabelText(message)
        d.setTextValue(default)
        if wide:
            d.resize(int(g.windows()[0].get_window_info()[0] * .9), 100)
        if cancelButtonText:
            d.setCancelButtonText(cancelButtonText)
        if okButtonText:
            d.setOkButtonText(okButtonText)
        self.attachLeoIcon(d)
        ok = d.exec_()
        return str(d.textValue()) if ok else None
    #@+node:ekr.20110605121601.18495: *4* qt_gui.runAskOkDialog
    def runAskOkDialog(self, c, title, message=None, text="Ok"):
        """Create and run a qt askOK dialog ."""
        if g.unitTesting:
            return
        b = QtWidgets.QMessageBox
        d = b(c.frame.top)
        stylesheet = getattr(c, 'active_stylesheet', None)
        if stylesheet:
            d.setStyleSheet(stylesheet)
        d.setWindowTitle(title)
        if message: d.setText(message)
        d.setIcon(b.Information)
        d.addButton(text, b.YesRole)
        c.in_qt_dialog = True
        d.exec_()
        c.in_qt_dialog = False
    #@+node:ekr.20110605121601.18497: *4* qt_gui.runAskYesNoCancelDialog
    def runAskYesNoCancelDialog(self, c, title,
        message=None,
        yesMessage="&Yes",
        noMessage="&No",
        yesToAllMessage=None,
        defaultButton="Yes",
        cancelMessage=None,
    ):
        """Create and run an askYesNo dialog."""
        if g.unitTesting:
            return None
        b = QtWidgets.QMessageBox
        d = b(c.frame.top)
        stylesheet = getattr(c, 'active_stylesheet', None)
        if stylesheet:
            d.setStyleSheet(stylesheet)
        if message: d.setText(message)
        d.setIcon(b.Warning)
        d.setWindowTitle(title)
        yes = d.addButton(yesMessage, b.YesRole)
        no = d.addButton(noMessage, b.NoRole)
        yesToAll = d.addButton(yesToAllMessage, b.YesRole) if yesToAllMessage else None
        if cancelMessage:
            cancel = d.addButton(cancelMessage, b.RejectRole)
        else:
            cancel = d.addButton(b.Cancel)
        if defaultButton == "Yes": d.setDefaultButton(yes)
        elif defaultButton == "No": d.setDefaultButton(no)
        else: d.setDefaultButton(cancel)
        c.in_qt_dialog = True
        val = d.exec_()
        c.in_qt_dialog = False
        if val == 0: val = 'yes'
        elif val == 1: val = 'no'
        elif yesToAll and val == 2: val = 'yes-to-all'
        else: val = 'cancel'
        return val
    #@+node:ekr.20110605121601.18498: *4* qt_gui.runAskYesNoDialog
    def runAskYesNoDialog(self, c, title, message=None, yes_all=False, no_all=False):
        """
        Create and run an askYesNo dialog.
        Return one of ('yes','yes-all','no','no-all')

        :Parameters:
        - `c`: commander
        - `title`: dialog title
        - `message`: dialog message
        - `yes_all`: bool - show YesToAll button
        - `no_all`: bool - show NoToAll button
        """
        if g.unitTesting: return None
        b = QtWidgets.QMessageBox
        buttons = b.Yes | b.No
        if yes_all:
            buttons |= b.YesToAll
        if no_all:
            buttons |= b.NoToAll
        d = b(c.frame.top)
        d.setStyleSheet(c.active_stylesheet)
        d.setStandardButtons(buttons)
        d.setWindowTitle(title)
        if message: d.setText(message)
        d.setIcon(b.Information)
        d.setDefaultButton(b.Yes)
        c.in_qt_dialog = True
        val = d.exec_()
        c.in_qt_dialog = False
        return {
            b.Yes: 'yes',
            b.No: 'no',
            b.YesToAll: 'yes-all',
            b.NoToAll: 'no-all'
        }.get(val, 'no')
    #@+node:ekr.20110605121601.18499: *4* qt_gui.runOpenDirectoryDialog
    def runOpenDirectoryDialog(self, title, startdir):
        """Create and run an Qt open directory dialog ."""
        parent = None
        d = QtWidgets.QFileDialog()
        self.attachLeoIcon(d)
        s = d.getExistingDirectory(parent, title, startdir)
        return s
    #@+node:ekr.20110605121601.18500: *4* qt_gui.runOpenFileDialog & helper
    def runOpenFileDialog(self, c, title, filetypes,
        defaultextension='',
        multiple=False,
        startpath=None,
        callback=None,
            # New in Leo 6.0.  If a callback is given, use the pyzo file browser.
    ):
        """
        Create and run an Qt open file dialog.
        """
        # pylint: disable=arguments-differ
        if g.unitTesting:
            return ''
        #
        # 2018/03/14: Bug fixes:
        # - Use init_dialog_folder only if a path is not given
        # - *Never* Use os.curdir by default!
        if not startpath:
            startpath = g.init_dialog_folder(c, c.p, use_at_path=True)
                # Returns c.last_dir or os.curdir
        if callback:
            dialog = self.PyzoFileDialog()
            dialog.init()
            dialog.open_dialog(c, callback, defaultextension, startpath)
            return None
        #
        # No callback: use the legacy file browser.
        filter_ = self.makeFilter(filetypes)
        dialog = QtWidgets.QFileDialog()
        dialog.setStyleSheet(c.active_stylesheet)
        self.attachLeoIcon(dialog)
        func = dialog.getOpenFileNames if multiple else dialog.getOpenFileName
        c.in_qt_dialog = True
        try:
            val = func(
                parent=None,
                caption=title,
                directory=startpath,
                filter=filter_,
            )
        finally:
            c.in_qt_dialog = False
        if isQt5: # this is a *Py*Qt change rather than a Qt change
            val, junk_selected_filter = val
        if multiple:
            files = [g.os_path_normslashes(s) for s in val]
            if files:
                c.last_dir = g.os_path_dirname(files[-1])
            return files
        s = g.os_path_normslashes(val)
        if s:
            c.last_dir = g.os_path_dirname(s)
        return s
    #@+node:ekr.20190518102229.1: *5* class PyzoFileDialog
    class PyzoFileDialog:
        '''A class supporting the pyzo file dialog.'''

        file_browser = None
            # A module.

        #@+others
        #@+node:ekr.20190518102720.1: *6* pfd.init & helpers
        def init(self):
            '''
            Initialize the browser code, using the actual pyzo if possible, or the
            code in leo/external/pyzo otherwise.    
            '''
            if g.app.pluginsController.isLoaded('pyzo_support.py'):
                self.init_real_pyzo()
            else:
                self.init_internal_pyzo()
        #@+node:ekr.20190518102823.1: *7* pfd.init_internal_pyzo
        def init_internal_pyzo(self):
            '''
            Init the internal version of pyzo in leo/external/pyzo.
            '''
            # Adjust sys.path.
            g.trace()
            path = g.os_path_finalize_join(g.app.loadDir,'..','external')
            assert g.os_path_exists(path), repr(path)
            if not path in sys.path:
                sys.path.append(path)
            #
            # Imports.
            import pyzo
            import pyzo.core.menu as menu
            pyzo.core.menu = menu
                # Looks weird, but needed to import pyzoFileBrowser.
            import pyzo.tools.pyzoFileBrowser as fb
            self.file_browser = fb
                # For open_dialog.
            #
            # Instantiate the browser.
            from pyzo.core.main import loadIcons
            loadIcons()
                # Required to instantiate PyzoFileBrowser.
        #@+node:ekr.20190518110307.1: *7* pfd.init_real_pyzo
        def init_real_pyzo(self):
            '''Init the real pyzo, which has already been inited by pyzo_support.py'''
            g.trace()
            if 0: # Probably already done.
                import pyzo
                import pyzo.core.menu as menu
                pyzo.core.menu = menu
                    # Looks weird, but needed to import pyzoFileBrowser.
            import pyzo.tools.pyzoFileBrowser as fb
            self.file_browser = fb
                # For open_dialog.
        #@+node:ekr.20190518103005.1: *6* pfd.open_dialog
        def open_dialog(self, c, callback, defaultextension, startpath, parent=None):
            '''Open pyzo's file browser.'''
            w = self.file_browser.PyzoFileBrowser(parent=parent)
                # Instantiate a file browser.
            g.app.permanentScriptDict ['file_browser'] = w
                # Save reference to the window so it won't disappear.
            g.trace('startpath:', startpath)
            g.app.gui.attachLeoIcon(w)
            w.setPath(startpath)
                # Tell it what to look at.
            w.setStyleSheet("background: #657b83;")
                # Use dark background.
            #
            # Monkey patch double-clicks.
            tree = w._browsers[0]._tree
            
            def double_click_callback(event, self=tree):
                # From Tree.mouseDoubleClickEvent
                item = self.itemAt(event.x(), event.y())
                    # item is a tree.DirItem or tree.FileItem
                    # item._proxy is a DirProxy or FileProxy.
                path = item._proxy.path()
                if g.os_path_isfile(path):
                    callback(c, False, path)
                        # This is the open_completer function.
            
            tree.mouseDoubleClickEvent = double_click_callback
            #
            # Show it!
            w.show()

        #@-others
    #@+node:ekr.20110605121601.18501: *4* qt_gui.runPropertiesDialog
    def runPropertiesDialog(self,
        title='Properties',
        data=None,
        callback=None,
        buttons=None
    ):
        """Dispay a modal TkPropertiesDialog"""
        if data is None: data = {}
        g.warning('Properties menu not supported for Qt gui')
        result = 'Cancel'
        return result, data
    #@+node:ekr.20110605121601.18502: *4* qt_gui.runSaveFileDialog
    def runSaveFileDialog(self, c, initialfile='', title='Save', filetypes=None, defaultextension=''):
        """Create and run an Qt save file dialog ."""
        if filetypes is None:
            filetypes = []
        if g.unitTesting:
            return ''
        parent = None
        filter_ = self.makeFilter(filetypes)
        d = QtWidgets.QFileDialog()
        d.setStyleSheet(c.active_stylesheet)
        self.attachLeoIcon(d)
        c.in_qt_dialog = True
        obj = d.getSaveFileName(
            parent,
            title,
            # os.curdir,
            g.init_dialog_folder(c, c.p, use_at_path=True),
            filter_)
        c.in_qt_dialog = False
        # Very bizarre: PyQt5 version can return a tuple!
        s = obj[0] if isinstance(obj, (list, tuple)) else obj
        s = s or ''
        if s:
            c.last_dir = g.os_path_dirname(s)
        return s
    #@+node:ekr.20110605121601.18503: *4* qt_gui.runScrolledMessageDialog
    def runScrolledMessageDialog(self,
        short_title='',
        title='Message',
        label='',
        msg='',
        c=None, **keys
    ):
        # pylint: disable=dangerous-default-value
        # How are we supposed to avoid **keys?
        if g.unitTesting: return None

        def send(title=title, label=label, msg=msg, c=c, keys=keys):
            return g.doHook('scrolledMessage',
                short_title=short_title, title=title,
                label=label, msg=msg, c=c, **keys)

        if not c or not c.exists:
            #@+<< no c error>>
            #@+node:ekr.20110605121601.18504: *5* << no c error>>
            g.es_print_error('%s\n%s\n\t%s' % (
                "The qt plugin requires calls to g.app.gui.scrolledMessageDialog to include 'c'",
                "as a keyword argument",
                g.callers()
            ))
            #@-<< no c error>>
        else:
            retval = send()
            if retval: return retval
            #@+<< load viewrendered plugin >>
            #@+node:ekr.20110605121601.18505: *5* << load viewrendered plugin >>
            pc = g.app.pluginsController
            # 2011/10/20: load viewrendered (and call vr.onCreate)
            # *only* if not already loaded.
            if not pc.isLoaded('viewrendered.py') and not pc.isLoaded('viewrendered2.py'):
                vr = pc.loadOnePlugin('viewrendered.py')
                if vr:
                    g.blue('viewrendered plugin loaded.')
                    vr.onCreate('tag', {'c': c})
            #@-<< load viewrendered plugin >>
            retval = send()
            if retval: return retval
            #@+<< no dialog error >>
            #@+node:ekr.20110605121601.18506: *5* << no dialog error >>
            g.es_print_error(
                'No handler for the "scrolledMessage" hook.\n\t%s' % (
                    g.callers()))
            #@-<< no dialog error >>
        #@+<< emergency fallback >>
        #@+node:ekr.20110605121601.18507: *5* << emergency fallback >>
        b = QtWidgets.QMessageBox
        d = b(None) # c.frame.top)
        d.setWindowFlags(QtCore.Qt.Dialog)
            # That is, not a fixed size dialog.
        d.setWindowTitle(title)
        if msg: d.setText(msg)
        d.setIcon(b.Information)
        d.addButton('Ok', b.YesRole)
        c.in_qt_dialog = True
        d.exec_()
        c.in_qt_dialog = False
        #@-<< emergency fallback >>
    #@+node:ekr.20110607182447.16456: *3* qt_gui.Event handlers
    #@+node:ekr.20110605121601.18481: *4* qt_gui.onDeactiveEvent
    # deactivated_name = ''
    deactivated_widget = None

    def onDeactivateEvent(self, event, c, obj, tag):
        '''
        Gracefully deactivate the Leo window.
        Called several times for each window activation.
        '''
        w = self.get_focus()
        w_name = w and w.objectName()
        if 'focus' in g.app.debug:
            g.trace(repr(w_name))
        self.active = False
            # Used only by c.idle_focus_helper.
        #
        # Careful: never save headline widgets.
        if w_name == 'headline':
            self.deactivated_widget = c.frame.tree.treeWidget
        else:
            self.deactivated_widget = w if w_name else None
        #
        # Causes problems elsewhere...
            # if c.exists and not self.deactivated_name:
                # self.deactivated_name = self.widget_name(self.get_focus())
                # self.active = False
                # c.k.keyboardQuit(setFocus=False)
        g.doHook('deactivate', c=c, p=c.p, v=c.p, event=event)
    #@+node:ekr.20110605121601.18480: *4* LeoQtGui.onActivateEvent
    # Called from eventFilter

    def onActivateEvent(self, event, c, obj, tag):
        '''
        Restore the focus when the Leo window is activated.
        Called several times for each window activation.
        '''
        trace = 'focus' in g.app.debug
        w = self.get_focus() or self.deactivated_widget
        self.deactivated_widget = None
        w_name = w and w.objectName()
        # Fix #270: Vim keys don't always work after double Alt+Tab.
        # Fix #359: Leo hangs in LeoQtEventFilter.eventFilter
        # #1273: add teest on c.vim_mode.
        if c.exists and c.vim_mode and c.vimCommands and not self.active and not g.app.killed:
            c.vimCommands.on_activate()
        self.active = True
            # Used only by c.idle_focus_helper.
        if g.isMac:
            pass # Fix #757: MacOS: replace-then-find does not work in headlines.
        else:
            # Leo 5.6: Recover from missing focus.
            # c.idle_focus_handler can't do this.
            if w and w_name in ('log-widget', 'richTextEdit', 'treeWidget'):
                # Restore focus **only** to body or tree
                if trace: g.trace('==>', w_name)
                c.widgetWantsFocusNow(w)
            else:
                if trace: g.trace(repr(w_name), '==> BODY')
                c.bodyWantsFocusNow()
        # Cause problems elsewhere.
            # if c.exists and self.deactivated_name:
                # self.active = True
                # w_name = self.deactivated_name
                # self.deactivated_name = None
                # if c.p.v:
                    # c.p.v.restoreCursorAndScroll()
                # if w_name.startswith('tree') or w_name.startswith('head'):
                    # c.treeWantsFocusNow()
                # else:
                    # c.bodyWantsFocusNow()
        g.doHook('activate', c=c, p=c.p, v=c.p, event=event)
    #@+node:ekr.20130921043420.21175: *4* qt_gui.setFilter (changed)
    # w's type is in (DynamicWindow,QMinibufferWrapper,LeoQtLog,LeoQtTree,
    # QTextEditWrapper,LeoQTextBrowser,LeoQuickSearchWidget,cleoQtUI)

    def setFilter(self, c, obj, w, tag):
        '''
        Create an event filter in obj.
        w is a wrapper object, not necessarily a QWidget.
        '''
        # gui = self
        assert isinstance(obj, QtWidgets.QWidget), obj
        theFilter = qt_events.LeoQtEventFilter(c, w=w, tag=tag)
        obj.installEventFilter(theFilter)
        w.ev_filter = theFilter
            # Set the official ivar in w.
    #@+node:ekr.20110605121601.18508: *3* qt_gui.Focus
    #@+node:ekr.20190601055031.1: *4* qt_gui.ensure_commander_visible
    def ensure_commander_visible(self, c1):
        """
        Check to see if c.frame is in a tabbed ui, and if so, make sure
        the tab is visible
        """
        # pylint: disable=arguments-differ
        #
        # START: copy from Code-->Startup & external files-->
        # @file runLeo.py -->run & helpers-->doPostPluginsInit & helpers (runLeo.py)
        # For the qt gui, select the first-loaded tab.
        if 'focus' in g.app.debug:
            g.trace(c1)
        if hasattr(g.app.gui, 'frameFactory'):
            factory = g.app.gui.frameFactory
            if factory and hasattr(factory, 'setTabForCommander'):
                c = c1
                factory.setTabForCommander(c)
                c.bodyWantsFocusNow()
        # END: copy
    #@+node:ekr.20190601054958.1: *4* qt_gui.get_focus
    def get_focus(self, c=None, raw=False, at_idle=False):
        """Returns the widget that has focus."""
        # pylint: disable=arguments-differ
        trace = 'focus' in g.app.debug
        trace_idle = False
        trace = trace and (trace_idle or not at_idle)
        app = QtWidgets.QApplication
        w = app.focusWidget()
        if w and not raw and isinstance(w, qt_text.LeoQTextBrowser):
            has_w = hasattr(w, 'leo_wrapper') and w.leo_wrapper
            if has_w:
                if trace: g.trace(w)
            elif c:
                # Kludge: DynamicWindow creates the body pane
                # with wrapper = None, so return the LeoQtBody.
                w = c.frame.body
        if trace:
            name = w.objectName() if hasattr(w, 'objectName') else w.__class__.__name__
            g.trace('(LeoQtGui)', name)
        return w


    #@+node:ekr.20190601054955.1: *4* qt_gui.raise_dock
    def raise_dock(self, widget):
        '''Raise the nearest parent QDockWidget, if any.'''
        while widget:
            if isinstance(widget, QtWidgets.QDockWidget):
                widget.raise_()
                return
            if not hasattr(widget, 'parent'):
                return
            widget = widget.parent()
    #@+node:ekr.20190601054959.1: *4* qt_gui.set_focus
    def set_focus(self, c, w):
        """Put the focus on the widget."""
        # pylint: disable=arguments-differ
        if not w:
            return
        if getattr(w, 'widget', None):
            if not isinstance(w, QtWidgets.QWidget):
                # w should be a wrapper.
                w = w.widget
        if 'focus' in g.app.debug:
            name = w.objectName() if hasattr(w, 'objectName') else w.__class__.__name__
            g.trace('(LeoQtGui)', name)
        # #1159: raise a parent QDockWidget.
        self.raise_dock(w)
        w.setFocus()
    #@+node:ekr.20110605121601.18510: *3* qt_gui.getFontFromParams
    size_warnings = []

    def getFontFromParams(self, family, size, slant, weight, defaultSize=12):
        '''Required to handle syntax coloring.'''
        if isinstance(size, str):
            if size.endswith('pt'):
                size = size[: -2].strip()
            elif size.endswith('px'):
                if size not in self.size_warnings:
                    self.size_warnings.append(size)
                    g.es('px ignored in font setting: %s' % size)
                size = size[: -2].strip()
        try:
            size = int(size)
        except Exception:
            size = 0
        if size < 1: size = defaultSize
        d = {
            'black': QtGui.QFont.Black,
            'bold': QtGui.QFont.Bold,
            'demibold': QtGui.QFont.DemiBold,
            'light': QtGui.QFont.Light,
            'normal': QtGui.QFont.Normal,
        }
        weight_val = d.get(weight.lower(), QtGui.QFont.Normal)
        italic = slant == 'italic'
        if not family:
            family = g.app.config.defaultFontFamily
        if not family:
            family = 'DejaVu Sans Mono'
        try:
            font = QtGui.QFont(family, size, weight_val, italic)
            if sys.platform.startswith('linux'):
                font.setHintingPreference(font.PreferFullHinting)
            # g.es(font,font.hintingPreference())
            return font
        except Exception:
            g.es("exception setting font", g.callers(4))
            g.es("", "family,size,slant,weight:", "", family, "", size, "", slant, "", weight)
            # g.es_exception() # This just confuses people.
            return g.app.config.defaultFont
    #@+node:ekr.20110605121601.18511: *3* qt_gui.getFullVersion
    def getFullVersion(self, c=None):
        '''Return the PyQt version (for signon)'''
        try:
            qtLevel = 'version %s' % QtCore.QT_VERSION_STR
        except Exception:
            # g.es_exception()
            qtLevel = '<qtLevel>'
        return 'PyQt %s' % (qtLevel)
    #@+node:ekr.20110605121601.18514: *3* qt_gui.Icons
    #@+node:ekr.20110605121601.18515: *4* qt_gui.attachLeoIcon
    def attachLeoIcon(self, window):
        """Attach a Leo icon to the window."""
        #icon = self.getIconImage('leoApp.ico')
        if self.appIcon:
            window.setWindowIcon(self.appIcon)
    #@+node:ekr.20110605121601.18516: *4* qt_gui.getIconImage
    def getIconImage(self, name):
        '''Load the icon and return it.'''
        # Return the image from the cache if possible.
        if name in self.iconimages:
            image = self.iconimages.get(name)
            return image
        try:
            iconsDir = g.os_path_join(g.app.loadDir, "..", "Icons")
            homeIconsDir = g.os_path_join(g.app.homeLeoDir, "Icons")
            for theDir in (homeIconsDir, iconsDir):
                fullname = g.os_path_finalize_join(theDir, name)
                if g.os_path_exists(fullname):
                    if 0: # Not needed: use QTreeWidget.setIconsize.
                        pixmap = QtGui.QPixmap()
                        pixmap.load(fullname)
                        image = QtGui.QIcon(pixmap)
                    else:
                        image = QtGui.QIcon(fullname)
                    self.iconimages[name] = image
                    return image
            # No image found.
            return None
        except Exception:
            g.es_print("exception loading:", fullname)
            g.es_exception()
            return None
    #@+node:ekr.20110605121601.18517: *4* qt_gui.getImageImage
    def getImageImage(self, name):
        '''Load the image in file named `name` and return it.'''
        fullname = self.getImageFinder(name)
        try:
            pixmap = QtGui.QPixmap()
            pixmap.load(fullname)
            return pixmap
        except Exception:
            g.es("exception loading:", name)
            g.es_exception()
            return None
    #@+node:tbrown.20130316075512.28478: *4* qt_gui.getImageFinder
    dump_given = False

    def getImageFinder(self, name):
        '''Theme aware image (icon) path searching.'''
        trace = 'themes' in g.app.debug
        exists = g.os_path_exists
        getString = g.app.config.getString
        
        def dump(var, val):
            print('%20s: %s' % (var, val))
            
        join = g.os_path_join
        #
        # "Just works" for --theme and theme .leo files *provided* that
        # theme .leo files actually contain these settings!
        #
        theme_name1 = getString('color-theme')
        theme_name2 = getString('theme-name')
        roots = [
            g.os_path_join(g.computeHomeDir(), '.leo'),
            g.computeLeoDir(),
        ]
        theme_subs = [
            "themes/{theme}/Icons",
            "themes/{theme}",
            "Icons/{theme}",
        ]
        bare_subs = ["Icons", "."]
            # "." for icons referred to as Icons/blah/blah.png
        paths = []
        for theme_name in (theme_name1, theme_name2):
            for root in roots:
                for sub in theme_subs:
                    paths.append(join(root, sub.format(theme=theme_name)))
        for root in roots:
            for sub in bare_subs:
                paths.append(join(root, sub))
        table = [z for z in paths if exists(z)]
        if trace and not self.dump_given:
            self.dump_given = True
            getString = g.app.config.getString
            g.trace('\n...')
            # dump('g.app.theme_color', g.app.theme_color)
            dump('@string color_theme', getString('color-theme'))
            # dump('g.app.theme_name', g.app.theme_name)
            dump('@string theme_name', getString('theme-name'))
            print('directory table...')
            g.printObj(table)
            print('')
        for base_dir in table:
            path = join(base_dir, name)
            if exists(path):
                if trace: g.trace('%s is  in %s\n' % (name, base_dir))
                return path
            if trace:
                g.trace(name, 'not in', base_dir)
        g.trace('not found:', name)
        return None
    #@+node:ekr.20110605121601.18518: *4* qt_gui.getTreeImage
    def getTreeImage(self, c, path):
        image = QtGui.QPixmap(path)
        if image.height() > 0 and image.width() > 0:
            return image, image.height()
        return None, None
    #@+node:ekr.20131007055150.17608: *3* qt_gui.insertKeyEvent
    def insertKeyEvent(self, event, i):
        '''Insert the key given by event in location i of widget event.w.'''
        import leo.core.leoGui as leoGui
        assert isinstance(event, leoGui.LeoKeyEvent)
        qevent = event.event
        assert isinstance(qevent, QtGui.QKeyEvent)
        qw = getattr(event.w, 'widget', None)
        if qw and isinstance(qw, QtWidgets.QTextEdit):
            if 1:
                # Assume that qevent.text() *is* the desired text.
                # This means we don't have to hack eventFilter.
                qw.insertPlainText(qevent.text())
            else:
                # Make no such assumption.
                # We would like to use qevent to insert the character,
                # but this would invoke eventFilter again!
                # So set this flag for eventFilter, which will
                # return False, indicating that the widget must handle
                # qevent, which *presumably* is the best that can be done.
                g.app.gui.insert_char_flag = True
    #@+node:ekr.20190819135820.1: *3* qt_gui.main window & docks
    #@+node:ekr.20190819135946.14: *4* qt_gui.create_mini_buffer_helper
    def create_mini_buffer_helper(self, parent):
        '''Create the widgets for Leo's minibuffer area.'''
        ### dw = self # For VisLineEdit
        # Create widgets.
        frame = self.createFrame(parent, 'minibufferFrame',
            hPolicy=QtWidgets.QSizePolicy.MinimumExpanding,
            vPolicy=QtWidgets.QSizePolicy.Fixed)
        frame.setMinimumSize(QtCore.QSize(100, 0))
        label = self.createLabel(frame, 'minibufferLabel', 'Minibuffer:')

        class VisLineEdit(QtWidgets.QLineEdit):
            """In case user has hidden minibuffer with gui-minibuffer-hide"""

            def focusInEvent(self, event):
                self.parent().show()
                if g.app.dock:
                    # Ensure the Tabs dock is visible, for completions.
                    dock = getattr(g.app.gui, 'tabs_dock', None)
                    if dock:
                        dock.raise_()
                        parent.raise_()
                super().focusInEvent(event)
                    # Call the base class method.

            def focusOutEvent(self, event):
                self.store_selection()
                super().focusOutEvent(event)

            def restore_selection(self):
                w = self
                i, j, ins = self._sel_and_insert
                if i == j:
                    w.setCursorPosition(i)
                else:
                    length = j - i
                    # Set selection is a QLineEditMethod
                    if ins < j:
                        w.setSelection(j, -length)
                    else:
                        w.setSelection(i, length)

            def store_selection(self):
                w = self
                ins = w.cursorPosition()
                if w.hasSelectedText():
                    i = w.selectionStart()
                    s = w.selectedText()
                    j = i + len(s)
                else:
                    i = j = ins
                w._sel_and_insert = (i, j, ins)

        lineEdit = VisLineEdit(frame)
        lineEdit._sel_and_insert = (0, 0, 0)
        lineEdit.setObjectName('lineEdit') # name important.
        # Pack.
        hLayout = self.createHLayout(frame, 'minibufferHLayout', spacing=4)
        hLayout.setContentsMargins(3, 2, 2, 0)
        hLayout.addWidget(label)
        hLayout.addWidget(lineEdit)
        if g.app.dock:
            # Parent is a QDockWidget.
            pass
        else:
            self.verticalLayout.addWidget(frame)
        label.setBuddy(lineEdit)
            # Transfers focus request from label to lineEdit.
        #
        # Official ivars.
        self.lineEdit = lineEdit
        # self.leo_minibuffer_frame = frame
        # self.leo_minibuffer_layout = layout
        return frame
    #@+node:ekr.20190822103219.1: *4* qt_gui.create_outline_frame (new)
    def create_outline_frame(self, c):
        """Create a new frame in the Outlines Dock"""
        ### From frameFactory.createFrame(leoFrame)
        assert c and c.frame
        g.trace(c.shortFileName())
        tabw = self.outline_tab
        dw = qt_frame.DynamicWindow(c, tabw)
        self.leoFrames[dw] = c.frame
        # Shorten the title.
        title = g.os_path_basename(c.mFileName) if c.mFileName else c.frame.title
        tip = c.frame.title
        dw.setWindowTitle(tip)
        idx = tabw.addTab(dw, title)
        if tip: tabw.setTabToolTip(idx, tip)
        dw.construct(master=tabw)
        tabw.setCurrentIndex(idx)
        g.app.gui.setFilter(c, dw, dw, tag='tabbed-frame')
        # Work around the problem with missing dirty indicator by always showing the tab.
        tabw.tabBar().setVisible(self.alwaysShowTabs or tabw.count() > 1)
        tabw.setTabsClosable(c.config.getBool('outline-tabs-show-close', True))
        dw.show()
        tabw.show()
        return dw
    #@+node:ekr.20190819135417.1: *4* qt_gui.create_outlines_tab (new)
    def create_outlines_tab(self, parent):
        '''Create the widgets and ivars for Leo's outline.'''
        w = QtWidgets.QTabWidget(parent)
        w.setObjectName('tree-tabs')
        self.outline_tab = w
        return w
        # # Create widgets.
        # treeFrame = self.createFrame(parent, 'outlineFrame',
            # vPolicy=QtWidgets.QSizePolicy.Expanding)
        # innerFrame = self.createFrame(treeFrame, 'outlineInnerFrame',
            # hPolicy=QtWidgets.QSizePolicy.Preferred)
        # treeWidget = self.createTreeWidget(innerFrame, 'treeWidget')
        # grid = self.createGrid(treeFrame, 'outlineGrid')
        # grid.addWidget(innerFrame, 0, 0, 1, 1)
        # innerGrid = self.createGrid(innerFrame, 'outlineInnerGrid')
        # innerGrid.addWidget(treeWidget, 0, 0, 1, 1)
        # # Official ivars...
        # self.treeWidget = treeWidget
        # return treeFrame
    #@+node:ekr.20190819090632.1: *4* qt_gui.createBodyPane
    def createBodyPane(self, parent):
        '''
        Create the *pane* for the body, but does not create the actual QTextBrowser.
        parent is None when --dock is in effect.
        '''
        if 1:
            return QtWidgets.QFrame(parent=parent)
        #
        # Create widgets.
        #
        # bodyFrame has a VGridLayout.
        bodyFrame = self.createFrame(parent, 'bodyFrame')
        grid = self.createGrid(bodyFrame, 'bodyGrid')
        #
        # innerFrame has a VBoxLayout.
        innerFrame = self.createFrame(bodyFrame, 'innerBodyFrame')
        box = self.createVLayout(innerFrame, 'bodyVLayout', spacing=0)
        #
        # Pack the body alone or *within* a LeoLineTextWidget.
        body = self.createText(None, 'richTextEdit') # A LeoQTextBrowser
        if self.use_gutter:
            c = g.TracingNullObject(tag='c')
            lineWidget = qt_text.LeoLineTextWidget(c, body)
            box.addWidget(lineWidget)
        else:
            box.addWidget(body)
        grid.addWidget(innerFrame, 0, 0, 1, 1)
        #
        # Official ivars
        # self.richTextEdit = body
        # self.leo_body_frame = bodyFrame
        # self.leo_body_inner_frame = innerFrame
        return bodyFrame
    #@+node:ekr.20190819085949.2: *4* qt_gui.createFindDockOrTab
    def createFindDockOrTab(self, parent):
        '''Create a Find dock or tab in the Log pane.'''
        assert g.app.dock
        assert not parent, repr(parent)
        #
        # Create widgets.
        findTab = QtWidgets.QWidget()
        findTab.setObjectName('findTab')
        findScrollArea = QtWidgets.QScrollArea()
        findScrollArea.setObjectName('findScrollArea')
        #
        # For LeoFind.finishCreate.
        self.findScrollArea = findScrollArea
        self.findTab = findTab
        #
        # Create a tab in the log Dock, if necessary.
        ### if not c.config.getBool('dockable-log-tabs', default=False):
        if True: ### Temp.
            self.tabWidget.addTab(findScrollArea, 'Find')
        return findScrollArea
    #@+node:ekr.20190819092902.1: *4* qt_gui.createRawSpellTab
    def createRawSpellTab(self, parent):
        # dw = self
        vLayout = self.createVLayout(parent, 'spellVLayout', margin=2)
        spellFrame = self.createFrame(parent, 'spellFrame')
        vLayout2 = self.createVLayout(spellFrame, 'spellVLayout')
        grid = self.createGrid(None, 'spellGrid', spacing=2)
        table = (
            ('Add', 'Add', 2, 1),
            ('Find', 'Find', 2, 0),
            ('Change', 'Change', 3, 0),
            ('FindChange', 'Change,Find', 3, 1),
            ('Ignore', 'Ignore', 4, 0),
            ('Hide', 'Hide', 4, 1),
        )
        for(ivar, label, row, col) in table:
            name = 'spell_%s_button' % label
            button = self.createButton(spellFrame, name, label)
            grid.addWidget(button, row, col)
            ### Not ready yet.
                # func = getattr(self, 'do_leo_spell_btn_%s' % ivar)
                # button.clicked.connect(func)
            # This name is significant.
            setattr(self, 'leo_spell_btn_%s' % (ivar), button)
        self.leo_spell_btn_Hide.setCheckable(False)
        spacerItem = QtWidgets.QSpacerItem(20, 40,
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        grid.addItem(spacerItem, 5, 0, 1, 1)
        listBox = QtWidgets.QListWidget(spellFrame)
        self.setSizePolicy(listBox,
            kind1=QtWidgets.QSizePolicy.MinimumExpanding,
            kind2=QtWidgets.QSizePolicy.Expanding)
        listBox.setMinimumSize(QtCore.QSize(0, 0))
        listBox.setMaximumSize(QtCore.QSize(150, 150))
        listBox.setObjectName("leo_spell_listBox")
        grid.addWidget(listBox, 1, 0, 1, 2)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20,
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        grid.addItem(spacerItem1, 2, 2, 1, 1)
        lab = self.createLabel(spellFrame, 'spellLabel', 'spellLabel')
        grid.addWidget(lab, 0, 0, 1, 2)
        vLayout2.addLayout(grid)
        vLayout.addWidget(spellFrame)
        ### listBox.itemDoubleClicked.connect(self.do_leo_spell_btn_FindChange)
        ### Not yet.
            # # Official ivars.
            # self.spellFrame = spellFrame
            # self.spellGrid = grid
            # self.leo_spell_widget = parent # 2013/09/20: To allow bindings to be set.
            # self.leo_spell_listBox = listBox # Must exist
            # self.leo_spell_label = lab # Must exist (!!)
    #@+node:ekr.20190819085949.4: *4* qt_gui.createSpellDockOrTab
    def createSpellDockOrTab(self, parent):
        '''Create a Spell dock  or tab in the Log pane.'''
        assert g.app.dock
        assert not parent, repr(parent)
        #
        # Create an outer widget.
        spellTab = QtWidgets.QWidget()
        spellTab.setObjectName('docked.spellTab')
        #
        # Create the contents.
        self.createRawSpellTab(spellTab)
            ### Renamed from createSpellTab.
        #
        # Create the Spell tab in the Log dock, if necessary.
        ### if not c.config.getBool('dockable-log-tabs', default=False):
        if True: ### Temp?
            tabWidget = self.tabWidget
            tabWidget.addTab(spellTab, 'Spell')
            tabWidget.setCurrentIndex(1)
        return spellTab
    #@+node:ekr.20190819085949.6: *4* qt_gui.createTabsDock
    def createTabsDock(self, parent):
        '''Create the Tabs dock.'''
        assert g.app.dock
        assert not parent, repr(parent)
        #
        # Create the log contents
        logFrame = self.createFrame(None, 'logFrame',
            vPolicy=QtWidgets.QSizePolicy.Minimum)
        innerFrame = self.createFrame(logFrame, 'logInnerFrame',
            hPolicy=QtWidgets.QSizePolicy.Preferred,
            vPolicy=QtWidgets.QSizePolicy.Expanding)
        tabWidget = self.createTabWidget(innerFrame, 'logTabWidget')
        #
        # Pack. This *is* required.
        innerGrid = self.createGrid(innerFrame, 'logInnerGrid')
        innerGrid.addWidget(tabWidget, 0, 0, 1, 1)
        outerGrid = self.createGrid(logFrame, 'logGrid')
        outerGrid.addWidget(innerFrame, 0, 0, 1, 1)
        #
        # Official ivars
        self.tabWidget = tabWidget # Used by LeoQtLog.
        return logFrame
    #@+node:ekr.20190819091420.1: *4* qt_gui.createTreeWidget
    def createTreeWidget(self, parent, name):
        
        from leo.plugins.qt_frame import LeoQTreeWidget
        ### c = self.leo_c
        c = g.TracingNullObject(tag='qt_gui.leo_c')
        w = LeoQTreeWidget(c, parent)
        self.setSizePolicy(w)
        # 12/01/07: add new config setting.
        ### multiple_selection = c.config.getBool('qt-tree-multiple-selection', default=True)
        if True: ###multiple_selection:
            w.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
            w.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        else:
            w.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
            w.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        w.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        w.setHeaderHidden(False)
        w.setObjectName(name)
        return w
    #@+node:ekr.20190819072045.1: *4* qt_gui.make_main_window (new)
    def make_main_window(self):
        '''Make a QMainWindow.'''
        window = QtWidgets.QMainWindow()
        window.setGeometry(50, 50, 500, 300)
        window.show()
        return window
    #@+node:ekr.20190822113212.1: *4* qt_gui.make_outlines_dock (new)
    def make_outlines_dock(self):
        """Create the Outlines dock."""
        ### Like make_all_docks
        main_window = self.main_window
        ### For now, make it the central widget.
        is_central = True
        height, name = 100, 'Outlines'
        w = self.create_outlines_tab(parent=None)
        dock = self.createDockWidget(
            closeable=not is_central,
            moveable=not is_central,
            height=height,
            name=name)
        dock.setWidget(w)
        if is_central:
            main_window.setCentralWidget(dock)
        else:
            area = QtCore.Qt.BottomDockWidgetArea
            main_window.addDockWidget(area, dock)
        # Remember the dock.
        setattr(self, '%s_dock' % (name), dock)
    #@+node:ekr.20110605121601.18528: *3* qt_gui.makeScriptButton
    def makeScriptButton(self, c,
        args=None,
        p=None, # A node containing the script.
        script=None, # The script itself.
        buttonText=None,
        balloonText='Script Button',
        shortcut=None, bg='LightSteelBlue1',
        define_g=True, define_name='__main__', silent=False, # Passed on to c.executeScript.
    ):
        '''Create a script button for the script in node p.
        The button's text defaults to p.headString'''
        k = c.k
        if p and not buttonText: buttonText = p.h.strip()
        if not buttonText: buttonText = 'Unnamed Script Button'
        #@+<< create the button b >>
        #@+node:ekr.20110605121601.18529: *4* << create the button b >>
        iconBar = c.frame.getIconBarObject()
        b = iconBar.add(text=buttonText)
        #@-<< create the button b >>
        #@+<< define the callbacks for b >>
        #@+node:ekr.20110605121601.18530: *4* << define the callbacks for b >>
        def deleteButtonCallback(event=None, b=b, c=c):
            if b: b.pack_forget()
            c.bodyWantsFocus()

        def executeScriptCallback(event=None,
            b=b,
            c=c,
            buttonText=buttonText,
            p=p and p.copy(),
            script=script
        ):
            if c.disableCommandsMessage:
                g.blue('', c.disableCommandsMessage)
            else:
                g.app.scriptDict = {'script_gnx': p.gnx}
                c.executeScript(args=args, p=p, script=script,
                define_g=define_g, define_name=define_name, silent=silent)
                # Remove the button if the script asks to be removed.
                if g.app.scriptDict.get('removeMe'):
                    g.es("removing", "'%s'" % (buttonText), "button at its request")
                    b.pack_forget()
            # Do not assume the script will want to remain in this commander.
        #@-<< define the callbacks for b >>
        b.configure(command=executeScriptCallback)
        if shortcut:
            #@+<< bind the shortcut to executeScriptCallback >>
            #@+node:ekr.20110605121601.18531: *4* << bind the shortcut to executeScriptCallback >>
            # In qt_gui.makeScriptButton.
            func = executeScriptCallback
            if shortcut:
                shortcut = g.KeyStroke(shortcut)
            ok = k.bindKey('button', shortcut, func, buttonText)
            if ok:
                g.blue('bound @button', buttonText, 'to', shortcut)
            #@-<< bind the shortcut to executeScriptCallback >>
        #@+<< create press-buttonText-button command >>
        #@+node:ekr.20110605121601.18532: *4* << create press-buttonText-button command >> qt_gui.makeScriptButton
        # #1121. Like sc.cleanButtonText
        buttonCommandName = 'press-%s-button' % buttonText.replace(' ','-').strip('-')
        #
        # This will use any shortcut defined in an @shortcuts node.
        k.registerCommand(buttonCommandName, executeScriptCallback, pane='button')
        #@-<< create press-buttonText-button command >>
    #@+node:ekr.20170612065255.1: *3* qt_gui.put_help
    def put_help(self, c, s, short_title=''):
        '''Put the help command.'''
        s = g.adjustTripleString(s.rstrip(), c.tab_width)
        if s.startswith('<') and not s.startswith('<<'):
            pass # how to do selective replace??
        pc = g.app.pluginsController
        table = (
            'viewrendered3.py',
            'viewrendered2.py',
            'viewrendered.py',
        )
        for name in table:
            if pc.isLoaded(name):
                vr = pc.loadOnePlugin(name)
                break
        else:
            vr = pc.loadOnePlugin('viewrendered.py')
        if vr:
            kw = {
                'c': c,
                'flags': 'rst',
                'kind': 'rst',
                'label': '',
                'msg': s,
                'name': 'Apropos',
                'short_title': short_title,
                'title': ''}
            vr.show_scrolled_message(tag='Apropos', kw=kw)
            c.bodyWantsFocus()
            if g.unitTesting:
                vr.close_rendering_pane(event={'c': c})
        elif g.unitTesting:
            pass
        else:
            g.es(s)
        return vr # For unit tests
    #@+node:ekr.20110605121601.18521: *3* qt_gui.runAtIdle
    def runAtIdle(self, aFunc):
        '''This can not be called in some contexts.'''
        QtCore.QTimer.singleShot(0, aFunc)
    #@+node:ekr.20110605121601.18483: *3* qt_gui.runMainLoop & runWithIpythonKernel
    #@+node:ekr.20130930062914.16000: *4* qt_gui.runMainLoop
    def runMainLoop(self):
        '''Start the Qt main loop.'''
        g.app.gui.dismiss_splash_screen()
        g.app.gui.show_tips()
        if self.script:
            log = g.app.log
            if log:
                g.pr('Start of batch script...\n')
                log.c.executeScript(script=self.script)
                g.pr('End of batch script')
            else:
                g.pr('no log, no commander for executeScript in LeoQtGui.runMainLoop')
        elif g.app.useIpython and g.app.ipython_inited:
            self.runWithIpythonKernel()
        else:
            # This can be alarming when using Python's -i option.
            sys.exit(self.qtApp.exec_())
    #@+node:ekr.20130930062914.16001: *4* qt_gui.runWithIpythonKernel (commands)
    def runWithIpythonKernel(self):
        '''Init Leo to run in an IPython shell.'''
        try:
            import leo.core.leoIPython as leoIPython
            g.app.ipk = ipk = leoIPython.InternalIPKernel()
            ipk.new_qt_console(event=None)
        except Exception:
            g.es_exception()
            print('can not init leo.core.leoIPython.py')
            sys.exit(1)

        @g.command("ipython-new")
        def qtshell_f(event):
            """ Launch new ipython shell window, associated with the same ipython kernel """
            g.app.ipk.new_qt_console(event=event)

        @g.command("ipython-exec")
        def ipython_exec_f(event):
            """ Execute script in current node in ipython namespace """
            c = event and event.get('c')
            if c:
                script = g.getScript(c, c.p, useSentinels=False)
                if script.strip():
                    g.app.ipk.run_script(file_name=c.p.h,script=script)

        ipk.kernelApp.start()
    #@+node:ekr.20190822105332.1: *3* qt_gui.setChanged (new, to do)
    def setChanged(self, c, changed):
        # Find the tab corresponding to c.
        g.trace(changed, c.shortFileName())
        if 0: ### Not ready yet
            dw = c.frame.top # A DynamicWindow
            i = self.indexOf(dw)
            if i < 0: return
            s = self.tabText(i)
            if len(s) > 2:
                if changed:
                    if not s.startswith('* '):
                        title = "* " + s
                        self.setTabText(i, title)
                else:
                    if s.startswith('* '):
                        title = s[2:]
                        self.setTabText(i, title)
    #@+node:ekr.20180117053546.1: *3* qt_gui.show_tips & helpers
    @g.command('show-next-tip')
    def show_next_tip(self, event=None):
        g.app.gui.show_tips(force=True)
        
    class DialogWithCheckBox(QtWidgets.QMessageBox):

        def __init__(self, controller, tip):
            super().__init__()
            c = g.app.log.c
            self.leo_checked = True
            self.setObjectName('TipMessageBox')
            self.setIcon(self.Information)
            # self.setMinimumSize(5000, 4000)
                # Doesn't work.
                # Prevent the dialog from jumping around when
                # selecting multiple tips.
            self.setWindowTitle('Leo Tips')
            self.setText(repr(tip))
            self.next_tip_button = self.addButton('Show Next Tip', self.ActionRole)
            self.setStandardButtons(self.Ok) # | self.Close)
            self.setDefaultButton(self.Ok)
            c.styleSheetManager.set_style_sheets(w=self)
            if isQt5:
                # Workaround #693: show-next-tip display overlapped in
                # Python 2.7.12, PyQt version 4.8.7
                layout = self.layout()
                cb = QtWidgets.QCheckBox()
                cb.setObjectName('TipCheckbox')
                cb.setText('Show Tip On Startup')
                cb.setCheckState(2)
                cb.stateChanged.connect(controller.onClick)
                layout.addWidget(cb, 4, 0, -1, -1)
                if 0: # Does not work well.
                    sizePolicy = QtWidgets.QSizePolicy
                    vSpacer =QtWidgets.QSpacerItem(200, 200, sizePolicy.Minimum, sizePolicy.Expanding)
                    layout.addItem(vSpacer)
            
    def show_tips(self, force=False):
        import leo.core.leoTips as leoTips
        if g.app.unitTesting:
            return
        c = g.app.log and g.app.log.c
        if not c:
            g.pr('qt_gui:show_tips: NO g.app.log')
            return # pyzo guard.
        self.show_tips_flag = c.config.getBool('show-tips', default=False)
        if not force and not self.show_tips_flag:
            return
        tm = leoTips.TipManager()
        if 1: # QMessageBox is always a modal dialog.
            while True:
                tip = tm.get_next_tip()
                m = self.DialogWithCheckBox(controller=self,tip=tip)
                c.in_qt_dialog = True
                m.exec_()
                c.in_qt_dialog = False
                b = m.clickedButton()
                self.update_tips_setting()
                if b != m.next_tip_button:
                    break
        else:
            m.buttonClicked.connect(self.onButton)
            m.setModal(False)
            m.show()
    #@+node:ekr.20180117080131.1: *4* onButton (not used)
    def onButton(self, m):
        m.hide()
    #@+node:ekr.20180117073603.1: *4* onClick
    def onClick(self, state):
        self.show_tips_flag = bool(state)
    #@+node:ekr.20180117083930.1: *5* update_tips_setting
    def update_tips_setting(self):
        c = g.app.log.c
        if c and self.show_tips_flag != c.config.getBool('show-tips', default=False):
            c.config.setUserSetting('@bool show-tips', self.show_tips_flag)
    #@+node:ekr.20180127103142.1: *4* onNext
    def onNext(self, *args, **keys):
        g.trace(args, keys)
        return True
    #@+node:ekr.20111215193352.10220: *3* qt_gui.Splash Screen
    #@+node:ekr.20110605121601.18479: *4* qt_gui.createSplashScreen
    def createSplashScreen(self):
        '''Put up a splash screen with the Leo logo.'''
        from leo.core.leoQt import QtCore
        qt = QtCore.Qt
        splash = None
        if sys.platform.startswith('win'):
            table = ('SplashScreen.jpg', 'SplashScreen.png', 'SplashScreen.ico')
        else:
            table = ('SplashScreen.xpm',)
        for name in table:
            fn = g.os_path_finalize_join(g.app.loadDir, '..', 'Icons', name)
            if g.os_path_exists(fn):
                pm = QtGui.QPixmap(fn)
                if not pm.isNull():
                    splash = QtWidgets.QSplashScreen(pm,
                        qt.WindowStaysOnTopHint)
                    splash.show()
                    # This sleep is required to do the repaint.
                    QtCore.QThread.msleep(10)
                    splash.repaint()
                    break
        return splash
    #@+node:ekr.20110613103140.16424: *4* qt_gui.dismiss_splash_screen
    def dismiss_splash_screen(self):

        gui = self
        # Warning: closing the splash screen must be done in the main thread!
        if g.unitTesting:
            return
        if gui.splashScreen:
            gui.splashScreen.hide()
            # gui.splashScreen.deleteLater()
            gui.splashScreen = None
    #@+node:ekr.20140825042850.18411: *3* qt_gui.Utils...
    #@+node:ekr.20110605121601.18522: *4* qt_gui.isTextWidget/Wrapper
    def isTextWidget(self, w):
        '''Return True if w is some kind of Qt text widget.'''
        if Qsci:
            return isinstance(w, (Qsci.QsciScintilla, QtWidgets.QTextEdit)), w
        return isinstance(w, QtWidgets.QTextEdit), w

    def isTextWrapper(self, w):
        '''Return True if w is a Text widget suitable for text-oriented commands.'''
        return w and hasattr(w, 'supportsHighLevelInterface') and w.supportsHighLevelInterface
    #@+node:ekr.20110605121601.18527: *4* qt_gui.widget_name
    def widget_name(self, w):
        # First try the widget's getName method.
        if not 'w':
            name = '<no widget>'
        elif hasattr(w, 'getName'):
            name = w.getName()
        elif hasattr(w, 'objectName'):
            name = str(w.objectName())
        elif hasattr(w, '_name'):
            name = w._name
        else:
            name = repr(w)
        return name
    #@+node:ekr.20111027083744.16532: *4* qt_gui.enableSignalDebugging
    if isQt5:
        ### To do: https://doc.qt.io/qt-5/qsignalspy.html
        from PyQt5.QtTest import QSignalSpy
        assert QSignalSpy
    else:
        # enableSignalDebugging(emitCall=foo) and spy your signals until you're sick to your stomach.
        _oldConnect = QtCore.QObject.connect
        _oldDisconnect = QtCore.QObject.disconnect
        _oldEmit = QtCore.QObject.emit

        def _wrapConnect(self, callableObject):
            """Returns a wrapped call to the old version of QtCore.QObject.connect"""

            @staticmethod
            def call(*args):
                callableObject(*args)
                self._oldConnect(*args)

            return call

        def _wrapDisconnect(self, callableObject):
            """Returns a wrapped call to the old version of QtCore.QObject.disconnect"""

            @staticmethod
            def call(*args):
                callableObject(*args)
                self._oldDisconnect(*args)

            return call

        def enableSignalDebugging(self, **kwargs):
            """Call this to enable Qt Signal debugging. This will trap all
            connect, and disconnect calls."""
            f = lambda * args: None
            connectCall = kwargs.get('connectCall', f)
            disconnectCall = kwargs.get('disconnectCall', f)
            emitCall = kwargs.get('emitCall', f)

            def printIt(msg):

                def call(*args):
                    print(msg, args)

                return call
            # Monkey-patch.

            QtCore.QObject.connect = self._wrapConnect(connectCall)
            QtCore.QObject.disconnect = self._wrapDisconnect(disconnectCall)

            def new_emit(self, *args):
                emitCall(self, *args)
                self._oldEmit(self, *args)

            QtCore.QObject.emit = new_emit
    #@+node:ekr.20190819091957.1: *3* qt_gui.Widgets...
    #@+node:ekr.20190819094016.1: *4* qt_gui.createButton
    def createButton(self, parent, name, label):
        w = QtWidgets.QPushButton(parent)
        w.setObjectName(name)
        w.setText(label)
        return w
    #@+node:ekr.20190819091950.1: *4* qt_gui.createDockWidget
    def createDockWidget(self, closeable, moveable, height, name):
        '''Make a new dock widget in the main window'''
        dock = QtWidgets.QDockWidget(parent=self.main_window)
            # The parent must be a QMainWindow.
        features = dock.NoDockWidgetFeatures
        if moveable:
            features |= dock.DockWidgetMovable
            features |= dock.DockWidgetFloatable
        if closeable:
            features |= dock.DockWidgetClosable
        dock.setFeatures(features)
        dock.setMinimumHeight(height)
        dock.setObjectName('dock.%s' % name)
        dock.setWindowTitle(name.capitalize())
        dock.show() # Essential!
        return dock
    #@+node:ekr.20190819091122.1: *4* qt_gui.createFrame
    def createFrame(self, parent, name,
        hPolicy=None, vPolicy=None,
        lineWidth=1,
        shadow=QtWidgets.QFrame.Plain,
        shape=QtWidgets.QFrame.NoFrame,
    ):
        '''Create a Qt Frame.'''
        w = QtWidgets.QFrame(parent)
        self.setSizePolicy(w, kind1=hPolicy, kind2=vPolicy)
        w.setFrameShape(shape)
        w.setFrameShadow(shadow)
        w.setLineWidth(lineWidth)
        w.setObjectName(name)
        return w
    #@+node:ekr.20190819091851.1: *4* qt_gui.createGrid
    def createGrid(self, parent, name, margin=0, spacing=0):
        w = QtWidgets.QGridLayout(parent)
        w.setContentsMargins(QtCore.QMargins(margin, margin, margin, margin))
        w.setSpacing(spacing)
        w.setObjectName(name)
        return w
    #@+node:ekr.20190819093830.1: *4* qt_gui.createHLayout & createVLayout
    def createHLayout(self, parent, name, margin=0, spacing=0):
        hLayout = QtWidgets.QHBoxLayout(parent)
        hLayout.setObjectName(name)
        hLayout.setSpacing(spacing)
        hLayout.setContentsMargins(QtCore.QMargins(0, 0, 0, 0))
        return hLayout

    def createVLayout(self, parent, name, margin=0, spacing=0):
        vLayout = QtWidgets.QVBoxLayout(parent)
        vLayout.setObjectName(name)
        vLayout.setSpacing(spacing)
        vLayout.setContentsMargins(QtCore.QMargins(0, 0, 0, 0))
        return vLayout
    #@+node:ekr.20190819094302.1: *4* qt_gui.createLabel
    def createLabel(self, parent, name, label):
        w = QtWidgets.QLabel(parent)
        w.setObjectName(name)
        w.setText(label)
        return w
    #@+node:ekr.20190819092523.1: *4* qt_gui.createTabWidget
    def createTabWidget(self, parent, name, hPolicy=None, vPolicy=None):
        w = QtWidgets.QTabWidget(parent)
        self.setSizePolicy(w, kind1=hPolicy, kind2=vPolicy)
        w.setObjectName(name)
        return w
    #@+node:ekr.20190819091214.1: *4* qt_gui.setSizePolicy
    def setSizePolicy(self, widget, kind1=None, kind2=None):
        if kind1 is None: kind1 = QtWidgets.QSizePolicy.Ignored
        if kind2 is None: kind2 = QtWidgets.QSizePolicy.Ignored
        sizePolicy = QtWidgets.QSizePolicy(kind1, kind2)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            widget.sizePolicy().hasHeightForWidth())
        widget.setSizePolicy(sizePolicy)
    #@-others
#@+node:tbrown.20150724090431.1: ** class StyleClassManager
class StyleClassManager:
    style_sclass_property = 'style_class' # name of QObject property for styling
    #@+others
    #@+node:tbrown.20150724090431.2: *3* update_view
    def update_view(self, w):
        """update_view - Make Qt apply w's style

        :param QWidgit w: widgit to style
        """

        w.setStyleSheet("/* */")  # forces visual update
    #@+node:tbrown.20150724090431.3: *3* add_sclass
    def add_sclass(self, w, prop):
        """Add style class or list of classes prop to QWidget w"""
        if not prop:
            return
        props = self.sclasses(w)
        if isinstance(prop, str):
            props.append(prop)
        else:
            props.extend(prop)

        self.set_sclasses(w, props)
    #@+node:tbrown.20150724090431.4: *3* clear_sclasses
    def clear_sclasses(self, w):
        """Remove all style classes from QWidget w"""
        w.setProperty(self.style_sclass_property, '')
    #@+node:tbrown.20150724090431.5: *3* has_sclass
    def has_sclass(self, w, prop):
        """Check for style class or list of classes prop on QWidget w"""
        if not prop:
            return None
        props = self.sclasses(w)
        if isinstance(prop, str):
            ans = [prop in props]
        else:
            ans = [i in props for i in prop]
        return all(ans)
    #@+node:tbrown.20150724090431.6: *3* remove_sclass
    def remove_sclass(self, w, prop):
        """Remove style class or list of classes prop from QWidget w"""
        if not prop:
            return
        props = self.sclasses(w)
        if isinstance(prop, str):
            props = [i for i in props if i != prop]
        else:
            props = [i for i in props if i not in prop]

        self.set_sclasses(w, props)
    #@+node:tbrown.20150724090431.7: *3* sclass_tests
    def sclass_tests(self):
        """Test style class property manipulation functions"""

        # pylint: disable=len-as-condition

        class Test_W:
            """simple standin for QWidget for testing"""
            def __init__(self):
                self.x = ''
            def property(self, name, default=None):
                return self.x or default
            def setProperty(self, name, value):
                self.x = value

        w = Test_W()

        assert not self.has_sclass(w, 'nonesuch')
        assert not self.has_sclass(w, ['nonesuch'])
        assert not self.has_sclass(w, ['nonesuch', 'either'])
        assert len(self.sclasses(w)) == 0

        self.add_sclass(w, 'test')

        assert not self.has_sclass(w, 'nonesuch')
        assert self.has_sclass(w, 'test')
        assert self.has_sclass(w, ['test'])
        assert not self.has_sclass(w, ['test', 'either'])
        assert len(self.sclasses(w)) == 1

        self.add_sclass(w, 'test')
        assert len(self.sclasses(w)) == 1
        self.add_sclass(w, ['test', 'test', 'other'])
        assert len(self.sclasses(w)) == 2
        assert self.has_sclass(w, 'test')
        assert self.has_sclass(w, 'other')
        assert self.has_sclass(w, ['test', 'other', 'test'])
        assert not self.has_sclass(w, ['test', 'other', 'nonesuch'])

        self.remove_sclass(w, ['other', 'nothere'])
        assert self.has_sclass(w, 'test')
        assert not self.has_sclass(w, 'other')
        assert len(self.sclasses(w)) == 1

        self.toggle_sclass(w, 'third')
        assert len(self.sclasses(w)) == 2
        assert self.has_sclass(w, ['test', 'third'])
        self.toggle_sclass(w, 'third')
        assert len(self.sclasses(w)) == 1
        assert not self.has_sclass(w, ['test', 'third'])

        self.clear_sclasses(w)
        assert len(self.sclasses(w)) == 0
        assert not self.has_sclass(w, 'test')
    #@+node:tbrown.20150724090431.8: *3* sclasses
    def sclasses(self, w):
        """return list of style classes for QWidget w"""
        return str(w.property(self.style_sclass_property) or '').split()
    #@+node:tbrown.20150724090431.9: *3* set_sclasses
    def set_sclasses(self, w, classes):
        """Set style classes for QWidget w to list in classes"""
        w.setProperty(self.style_sclass_property, ' %s ' % ' '.join(set(classes)))
    #@+node:tbrown.20150724090431.10: *3* toggle_sclass
    def toggle_sclass(self, w, prop):
        """Toggle style class or list of classes prop on QWidget w"""
        if not prop:
            return
        props = set(self.sclasses(w))

        if isinstance(prop, str):
            prop = set([prop])
        else:
            prop = set(prop)

        current = props.intersection(prop)
        props.update(prop)
        props = props.difference(current)

        self.set_sclasses(w, props)
    #@-others
#@+node:ekr.20140913054442.17860: ** class StyleSheetManager
class StyleSheetManager:
    '''A class to manage (reload) Qt style sheets.'''
    #@+others
    #@+node:ekr.20180316091829.1: *3*  ssm.Birth
    #@+node:ekr.20140912110338.19371: *4* ssm.__init__
    def __init__(self, c, safe=False):
        '''Ctor the ReloadStyle class.'''
        self.c = c
        self.color_db = leoColor.leo_color_database
        self.safe = safe
        self.settings_p = g.findNodeAnywhere(c, '@settings')
        self.mng = StyleClassManager()
        # This warning is inappropriate in some contexts.
            # if not self.settings_p:
                # g.es("No '@settings' node found in outline.  See:")
                # g.es("http://leoeditor.com/tutorial-basics.html#configuring-leo")
    #@+node:ekr.20170222051716.1: *4* ssm.reload_settings
    def reload_settings(self, sheet=None):
        '''
        Recompute and apply the stylesheet.
        Called automatically by the reload-settings commands.
        '''
        if not sheet:
            sheet = self.get_style_sheet_from_settings()
        if sheet:
            w = self.get_master_widget()
            w.setStyleSheet(sheet)
        # self.c.redraw()

    reloadSettings = reload_settings
    #@+node:ekr.20180316091500.1: *3* ssm.Paths...
    #@+node:ekr.20180316065346.1: *4* ssm.compute_icon_directories
    def compute_icon_directories(self):
        '''
        Return a list of *existing* directories that could contain theme-related icons.
        '''
        exists = g.os_path_exists
        home = g.app.homeDir
        join = g.os_path_finalize_join
        leo = join(g.app.loadDir, '..')
        table = [
            join(home, '.leo', 'Icons'),
            # join(home, '.leo'),
            join(leo, 'themes', 'Icons'),
            join(leo, 'themes'),
            join(leo, 'Icons'),
        ]
        table = [z for z in table if exists(z)]
        for directory in self.compute_theme_directories():
            if directory not in table:
                table.append(directory)
            directory2 = join(directory, 'Icons')
            if directory2 not in table:
                table.append(directory2)
        return [g.os_path_normslashes(z) for z in table if g.os_path_exists(z)]
    #@+node:ekr.20180315101238.1: *4* ssm.compute_theme_directories
    def compute_theme_directories(self):
        '''
        Return a list of *existing* directories that could contain theme .leo files.
        '''
        lm = g.app.loadManager
        table = lm.computeThemeDirectories()[:]
        directory = g.os_path_normslashes(g.app.theme_directory)
        if directory and directory not in table:
            table.insert(0, directory)
        return table
            # All entries are known to exist and have normalized slashes.
    #@+node:ekr.20170307083738.1: *4* ssm.find_icon_path
    def find_icon_path(self, setting):
        '''Return the path to the open/close indicator icon.'''
        c = self.c
        s = c.config.getString(setting)
        if not s:
            return None # Not an error.
        for directory in self.compute_icon_directories():
            path = g.os_path_finalize_join(directory, s)
            if g.os_path_exists(path):
                return path
        g.es_print('no icon found for:', setting)
        return None
    #@+node:ekr.20180316091920.1: *3* ssm.Settings
    #@+node:ekr.20110605121601.18176: *4* ssm.default_style_sheet
    def default_style_sheet(self):
        '''Return a reasonable default style sheet.'''
        # Valid color names: http://www.w3.org/TR/SVG/types.html#ColorKeywords
        g.trace('===== using default style sheet =====')
        return '''\

    /* A QWidget: supports only background attributes.*/
    QSplitter::handle {
        background-color: #CAE1FF; /* Leo's traditional lightSteelBlue1 */
    }
    QSplitter {
        border-color: white;
        background-color: white;
        border-width: 3px;
        border-style: solid;
    }
    QTreeWidget {
        background-color: #ffffec; /* Leo's traditional tree color */
    }
    QsciScintilla {
        background-color: pink;
    }
    '''
    #@+node:ekr.20140916170549.19551: *4* ssm.get_data
    def get_data(self, setting):
        '''Return the value of the @data node for the setting.'''
        c = self.c
        return c.config.getData(setting, strip_comments=False, strip_data=False) or []
    #@+node:ekr.20140916170549.19552: *4* ssm.get_style_sheet_from_settings
    def get_style_sheet_from_settings(self):
        '''
        Scan for themes or @data qt-gui-plugin-style-sheet nodes.
        Return the text of the relevant node.
        '''
        aList1 = self.get_data('qt-gui-plugin-style-sheet')
        aList2 = self.get_data('qt-gui-user-style-sheet')
        if aList2: aList1.extend(aList2)
        sheet = ''.join(aList1)
        sheet = self.expand_css_constants(sheet)
        return sheet
    #@+node:ekr.20140915194122.19476: *4* ssm.print_style_sheet
    def print_style_sheet(self):
        '''Show the top-level style sheet.'''
        w = self.get_master_widget()
        sheet = w.styleSheet()
        print('style sheet for: %s...\n\n%s' % (w, sheet))
    #@+node:ekr.20110605121601.18175: *4* ssm.set_style_sheets
    def set_style_sheets(self, all=True, top=None, w=None):
        '''Set the master style sheet for all widgets using config settings.'''
        if g.app.loadedThemes:
            return
        c = self.c
        if top is None: top = c.frame.top
        selectors = ['qt-gui-plugin-style-sheet']
        if all:
            selectors.append('qt-gui-user-style-sheet')
        sheets = []
        for name in selectors:
            sheet = c.config.getData(name, strip_comments=False)
                # don't strip `#selector_name { ...` type syntax
            if sheet:
                if '\n' in sheet[0]:
                    sheet = ''.join(sheet)
                else:
                    sheet = '\n'.join(sheet)
            if sheet and sheet.strip():
                line0 = '\n/* ===== From %s ===== */\n\n' % (name)
                sheet = line0 + sheet
                sheets.append(sheet)
        if sheets:
            sheet = "\n".join(sheets)
            # store *before* expanding, so later expansions get new zoom
            c.active_stylesheet = sheet
            sheet = self.expand_css_constants(sheet)
            if not sheet: sheet = self.default_style_sheet()
            if w is None:
                w = self.get_master_widget(top)
            w.setStyleSheet(sheet)
    #@+node:ekr.20180316091943.1: *3* ssm.Stylesheet
    # Computations on stylesheets themeselves.
    #@+node:ekr.20140915062551.19510: *4* ssm.expand_css_constants & helpers
    css_warning_given = False

    def expand_css_constants(self, sheet, font_size_delta=None, settingsDict=None):
        '''Expand @ settings into their corresponding constants.'''
        trace_dict = False
        c = self.c
        # Warn once if the stylesheet uses old style style-sheet comment
        if settingsDict is None:
            settingsDict = c.config.settingsDict
        if trace_dict:
            g.trace('===== settingsDict.keys()...')
            g.printObj(sorted(settingsDict.keys()))
        constants, deltas = self.adjust_sizes(font_size_delta, settingsDict)
        sheet = self.replace_indicator_constants(sheet)
        for pass_n in range(10):
            to_do = self.find_constants_referenced(sheet)
            if not to_do:
                break
            old_sheet = sheet
            sheet = self.do_pass(constants, deltas, settingsDict, sheet, to_do)
            if sheet == old_sheet:
                break
        else:
           g.trace('Too many iterations')
        if to_do:
            g.trace('Unresolved @constants')
            g.printObj(to_do)
        sheet = self.resolve_urls(sheet)
        sheet = sheet.replace('\\\n', '') # join lines ending in \
        return sheet
    #@+node:ekr.20150617085045.1: *5* ssm.adjust_sizes
    def adjust_sizes(self, font_size_delta, settingsDict):
        '''Adjust constants to reflect c._style_deltas.'''
        c = self.c
        constants = {} # old: self.find_constants_defined(sheet)
        deltas = c._style_deltas
        # legacy
        if font_size_delta:
            deltas['font-size-body'] = font_size_delta
        for delta in c._style_deltas:
            # adjust @font-size-body by font_size_delta
            # easily extendable to @font-size-*
            val = c.config.getString(delta)
            passes = 10
            while passes and val and val.startswith('@'):
                key = g.app.config.canonicalizeSettingName(val[1:])
                val = settingsDict.get(key)
                if val:
                    val = val.val
                passes -= 1
            if deltas[delta] and (val is not None):
                size = ''.join(i for i in val if i in '01234567890.')
                units = ''.join(i for i in val if i not in '01234567890.')
                size = max(1, int(size) + deltas[delta])
                constants["@" + delta] = "%s%s" % (size, units)
        return constants, deltas
    #@+node:ekr.20180316093159.1: *5* ssm.do_pass
    def do_pass(self, constants, deltas, settingsDict, sheet, to_do):
        
        to_do.sort(key=len, reverse=True)
        for const in to_do:
            value = None
            if const in constants:
                # This constant is about to be removed.
                value = constants[const]
                if const[1:] not in deltas and not self.css_warning_given:
                    self.css_warning_given = True
                    g.es_print("'%s' from style-sheet comment definition, " % const)
                    g.es_print("please use regular @string / @color type @settings.")
            else:
                key = g.app.config.canonicalizeSettingName(const[1:])
                    # lowercase, without '@','-','_', etc.
                value = settingsDict.get(key)
                if value is not None:
                    # New in Leo 5.5: Do NOT add comments here.
                    # They RUIN style sheets if they appear in a nested comment!
                        # value = '%s /* %s */' % (value.val, key)
                    value = value.val
                elif key in self.color_db:
                    # New in Leo 5.5: Do NOT add comments here.
                    # They RUIN style sheets if they appear in a nested comment!
                    value = self.color_db.get(key)
                        # value = '%s /* %s */' % (value, key)
            if value:
                # Partial fix for #780.
                try:
                    sheet = re.sub(
                        const + "(?![-A-Za-z0-9_])",
                            # don't replace shorter constants occuring in larger
                        value,
                        sheet,
                    )
                except Exception:
                    g.es_print('Exception handling style sheet')
                    g.es_print(sheet)
                    g.es_exception()
            else:
                pass
                # tricky, might be an undefined identifier, but it might
                # also be a @foo in a /* comment */, where it's harmless.
                # So rely on whoever calls .setStyleSheet() to do the right thing.
        return sheet
    #@+node:tbrown.20131120093739.27085: *5* ssm.find_constants_referenced
    def find_constants_referenced(self, text):
        """find_constants - Return a list of constants referenced in the supplied text,
        constants match::

            @[A-Za-z_][-A-Za-z0-9_]*
            i.e. @foo_1-5

        :Parameters:
        - `text`: text to search
        """
        aList = sorted(set(re.findall(r"@[A-Za-z_][-A-Za-z0-9_]*", text)))
        # Exempt references to Leo constructs.
        for s in ('@button', '@constants', '@data', '@language'):
            if s in aList:
                aList.remove(s)
        return aList
    #@+node:tbrown.20130411121812.28335: *5* ssm.find_constants_defined (no longer used)
    def find_constants_defined(self, text):
        r"""find_constants - Return a dict of constants defined in the supplied text.

        NOTE: this supports a legacy way of specifying @<identifiers>, regular
        @string and @color settings should be used instead, so calling this
        wouldn't be needed.  expand_css_constants() issues a warning when
        @<identifiers> are found in the output of this method.

        Constants match::

            ^\s*(@[A-Za-z_][-A-Za-z0-9_]*)\s*=\s*(.*)$
            i.e.
            @foo_1-5=a
                @foo_1-5 = a more here

        :Parameters:
        - `text`: text to search
        """
        pattern = re.compile(r"^\s*(@[A-Za-z_][-A-Za-z0-9_]*)\s*=\s*(.*)$")
        ans = {}
        text = text.replace('\\\n', '') # merge lines ending in \
        for line in text.split('\n'):
            test = pattern.match(line)
            if test:
                ans.update([test.groups()])
        # constants may refer to other constants, de-reference here
        change = True
        level = 0
        while change and level < 10:
            level += 1
            change = False
            for k in ans:
                # pylint: disable=unnecessary-lambda
                # process longest first so @solarized-base0 is not replaced
                # when it's part of @solarized-base03
                for o in sorted(ans, key=lambda x: len(x), reverse=True):
                    if o in ans[k]:
                        change = True
                        ans[k] = ans[k].replace(o, ans[o])
        if level == 10:
            print("Ten levels of recursion processing styles, abandoned.")
            g.es("Ten levels of recursion processing styles, abandoned.")
        return ans
    #@+node:ekr.20150617090104.1: *5* ssm.replace_indicator_constants
    def replace_indicator_constants(self, sheet):
        '''
        In the stylesheet, replace (if they exist)::

            image: @tree-image-closed
            image: @tree-image-open

        by::

            url(path/closed.png)
            url(path/open.png)

        path can be relative to ~ or to leo/Icons.

        Assuming that ~/myIcons/closed.png exists, either of these will work::

            @string tree-image-closed = nodes-dark/triangles/closed.png
            @string tree-image-closed = myIcons/closed.png

        Return the updated stylesheet.
        '''
        close_path = self.find_icon_path('tree-image-closed')
        open_path = self.find_icon_path('tree-image-open')
        # Make all substitutions in the stylesheet.
        table = (
            (open_path,  re.compile(r'\bimage:\s*@tree-image-open', re.IGNORECASE)),
            (close_path, re.compile(r'\bimage:\s*@tree-image-closed', re.IGNORECASE)),
            # (open_path,  re.compile(r'\bimage:\s*at-tree-image-open', re.IGNORECASE)),
            # (close_path, re.compile(r'\bimage:\s*at-tree-image-closed', re.IGNORECASE)),
        )
        for path, pattern in table:
            for mo in pattern.finditer(sheet):
                old = mo.group(0)
                new = 'image: url(%s)' % path
                sheet = sheet.replace(old, new)
        return sheet
    #@+node:ekr.20180320054305.1: *5* ssm.resolve_urls
    def resolve_urls(self, sheet):
        '''Resolve all relative url's so they use absolute paths.'''
        trace = 'themes' in g.app.debug
        pattern = re.compile(r'url\((.*)\)')
        join = g.os_path_finalize_join
        directories = self.compute_icon_directories()
        paths_traced = False
        if trace:
            paths_traced = True
            g.trace('Search paths...')
            g.printObj(directories)
        # Pass 1: Find all replacements without changing the sheet.
        replacements = []
        for mo in pattern.finditer(sheet):
            url = mo.group(1)
            if url.startswith(':/'):
                url = url[2:]
            elif g.os_path_isabs(url):
                if trace: g.trace('ABS:', url)
                continue
            for directory in directories:
                path = join(directory, url)
                if g.os_path_exists(path):
                    if trace: g.trace('%35s ==> %s' % (url, path))
                    old = mo.group(0)
                    new = 'url(%s)' % path
                    replacements.append((old, new),)
                    break
            else:
                g.trace('%35s ==> %s' % (url, 'NOT FOUND'))
                if not paths_traced:
                    paths_traced = True
                    g.trace('Search paths...')
                    g.printObj(directories)
        # Pass 2: Now we can safely make the replacements.
        for old, new in reversed(replacements):
            sheet = sheet.replace(old, new)
        return sheet
    #@+node:ekr.20140912110338.19372: *4* ssm.munge
    def munge(self, stylesheet):
        '''
        Return the stylesheet without extra whitespace.

        To avoid false mismatches, this should approximate what Qt does.
        To avoid false matches, this should not munge too much.
        '''
        s = ''.join([s.lstrip().replace('  ', ' ').replace(' \n', '\n')
            for s in g.splitLines(stylesheet)])
        return s.rstrip()
            # Don't care about ending newline.
    #@+node:ekr.20180317062556.1: *3* sss.Theme files
    #@+node:ekr.20180316092116.1: *3* ssm.Widgets
    #@+node:ekr.20140913054442.19390: *4* ssm.get_master_widget
    def get_master_widget(self, top=None):
        '''
        Carefully return the master widget.
        c.frame.top is a DynamicWindow.
        '''
        if top is None:
            top = self.c.frame.top
        master = top.leo_master or top
        return master
    #@+node:ekr.20140913054442.19391: *4* ssm.set selected_style_sheet
    def set_selected_style_sheet(self):
        '''For manual testing: update the stylesheet using c.p.b.'''
        if not g.unitTesting:
            c = self.c
            sheet = c.p.b
            sheet = self.expand_css_constants(sheet)
            w = self.get_master_widget(c.frame.top)
            w.setStyleSheet(sheet)
    #@-others
#@-others
#@@language python
#@@tabwidth -4
#@@pagewidth 70
#@-leo
