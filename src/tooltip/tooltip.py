# file: tooltip.py

## Copyright (C) 2009 Tucker Beck; 2011-12 Ulrich Goertz (ug@geometry.de)

## Permission is hereby granted, free of charge, to any person obtaining a copy of
## this software and associated documentation files (the "Software"), to deal in
## the Software without restriction, including without limitation the rights to
## use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
## of the Software, and to permit persons to whom the Software is furnished to do
## so, subject to the following conditions:
##
## The above copyright notice and this permission notice shall be included in all
## copies or substantial portions of the Software.
##
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
## SOFTWARE.


# The code in this file was contributed by Tucker Beck as recipe 576688 to the
# ActiveState community, see
# http://code.activestate.com/recipes/576688-tooltip-for-tkinter/
# and slightly adapted for Kombilo.

from Tkinter import *
from time import time


class ToolTip(Toplevel):
    """
    Provides a ToolTip widget for Tkinter.
    To apply a ToolTip to any Tkinter widget, simply pass the widget to the
    ToolTip constructor
    """
    def __init__(self, wdgt, msg=None, msgFunc=None, delay=.5, follow=True):
        """
        Initialize the ToolTip

        Arguments:
          wdgt: The widget this ToolTip is assigned to
          msg:  A static string message assigned to the ToolTip
          msgFunc: A function that retrieves a string to use as the ToolTip text
          delay:   The delay in seconds before the ToolTip appears(may be float)
          follow:  If True, the ToolTip follows motion, otherwise hides
        """
        self.wdgt = wdgt
        self.parent = self.wdgt.master                                          # The parent of the ToolTip is the parent of the ToolTips widget
        Toplevel.__init__(self, self.parent, bg='black', padx=1, pady=1)        # Initalise the Toplevel
        self.withdraw()                                                         # Hide initially
        self.overrideredirect(True)                                             # The ToolTip Toplevel should have no frame or title bar

        self.msgVar = StringVar()                                               # The msgVar will contain the text displayed by the ToolTip
        if msg == None:
            self.msgVar.set(_('No message provided'))
        else:
            self.msgVar.set(msg)
        self.msgFunc = msgFunc
        self.delay = delay
        self.follow = follow
        self.visible = 0
        self.lastMotion = 0
        Message(self, textvariable=self.msgVar, bg='#FFFFDD', aspect=1000).grid()  # The text of the ToolTip is displayed in a Message widget
        self.wdgt.bind('<Enter>', self.spawn, '+')                            # Add bindings to the widget.  This will NOT override bindings that the widget already has
        self.wdgt.bind('<Leave>', self.hide, '+')
        self.wdgt.bind('<Motion>', self.move, '+')

    def spawn(self, event=None):
        """
        Spawn the ToolTip.  This simply makes the ToolTip eligible for display.
        Usually this is caused by entering the widget

        Arguments:
          event: The event that called this funciton
        """
        self.visible = 1
        self.after(int(self.delay * 1000), self.show)                       # The after function takes a time argument in miliseconds

    def show(self):
        """
        Displays the ToolTip if the time delay has been long enough
        """
        if self.visible == 1 and time() - self.lastMotion > self.delay:
            self.visible = 2
        if self.visible == 2:
            self.deiconify()

    def move(self, event):
        """
        Processes motion within the widget.

        Arguments:
          event: The event that called this function
        """
        self.lastMotion = time()
        if self.follow == False:                                          # If the follow flag is not set, motion within the widget will make the ToolTip dissapear
            self.withdraw()
            self.visible = 1
        self.geometry('+%i+%i' % (event.x_root + 10, event.y_root + 10))  # Offset the ToolTip 10x10 pixes southwest of the pointer
        try:
            self.msgVar.set(self.msgFunc())                               # Try to call the message function.  Will not change the message if the message function is None or the message function fails
        except:
            pass
        self.after(int(self.delay * 1000), self.show)

    def hide(self, event=None):
        """
        Hides the ToolTip.  Usually this is caused by leaving the widget

        Arguments:
          event: The event that called this function
        """
        self.visible = 0
        self.withdraw()


def range2d(n, m):
    """
    Returns a list of values in a 2d range

    Arguments:
      n: The number of rows in the 2d range
      m: The number of columns in the 2d range
    Returns:
      A list of values in a 2d range
    """
    return [(i, j) for i in range(n) for j in range(m)]


def print_msg():
    return 'Dynamic description.'


def main():
    root = Tk()
    btnList = []
    for (i, j) in range2d(6, 4):
        text = 'delay=%i\n' % i
        delay = i
        if j >= 2:
            follow = True
            text += '+follow\n'
        else:
            follow = False
            text += '-follow\n'
        if j % 2 == 0:
            msg = None
            msgFunc = print_msg
            text += 'Message Function'
        else:
            msg = 'Button at %s' % str((i, j))
            msgFunc = None
            text += 'Static Message'
        btnList.append(Button(root, text=text))
        ToolTip(btnList[-1], msg=msg, msgFunc=msgFunc, follow=follow, delay=delay)
        btnList[-1].grid(row=i, column=j, sticky=N + S + E + W)
    root.mainloop()

if __name__ == '__main__':
    main()
