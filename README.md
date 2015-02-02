PKMidiCron
============

An app to fire commands when a midi message is received. Possible uses:

- Remote PC control via MIDI
- Central MIDI Router for complex setups
- Programmable generative sequencer
- Anything you can dream up!


Bindings
===============================
You add bindings to define how the app should respond to particular midi messages coming into it. Each Binding 


Send Message Action
------------------------
This action will send a midi message, or forward the original midi message that triggered the action. This allows you to create a midi patch bay that routes messages of all kinds between ports and applications. Selecting all ports will loop through and perform the action once for each port in the list.

Run Program Action
------------------------
This action will execute a shell script, exe, or app bundle.

Open File Action
------------------------
This will open a document using the appropriate program associated with the file's extension. For example, you could open a jpeg or a txt file.

Execute Script
------------------------
This action will execute a custom python script which you can create using the built-in editor. More information on python scripts to follow.


Simulator
===============================
The simulator will allow you to test your bindings by sending the precise message that you need. It also serves as a useful replacement for the other midi simualtor apps out there.

Clicking "Route Internally" bypasses the midi hardware and just passes it to the bindings for evaluation. This is helpful when developing your bindings in a sensistive hardware setup.

Activity Log
===============================
This is a simple midi monitor, which displaus all messages from all ports enabled in the preferences. In the preferences window, you can also enable all ports by default which will ignore the individual enabled/disabled settings of each port and just accept all possible incoming midi, INCLUDING midi from new ports that are connected while the app is running.


Scripting Guide
================================

PKMidiCron has the ability to edit and execute python scripts when a midi message is recieved. This allows this app to be as flexible as your programming abilities will allow. Ideal uses:

- Midi Hub, passing data from one port to another.
- Syncing lights and other hardware using MIDI, and possible Python extensions.

The scripting engine implemented in this application is relatively open and free from unnecessary restrictions imposed by other applications. This allows you to create new graphical interfaces using the PyQt toolkit or load your won third-party modules, and even hack into the application code itself should you so desire. It's all up to you.

The Basics
------------------------

To create a script, add a new binding with an action to execute a script. Then click the '...' button to open the script editor. The easiest way to get start is to copy and paste the following script into the editor, and hit compile:

'''
print('This is executed when the compile button is pressed.')
'''

Next hit the "Console" button to show the debugging console. Then the "Compile" button and notice that your first message has been printed to the console. This shows that your code will be re-executed every time you hit the compile button. 

You can also add other python-legal statements and keep hitting the compile button to test for typos and run the code, like so:

'''
12 + 3
x = 1
n = 32
z = n * (X - n)
print(x, n, z)
'''

Upon successful compilation and execution, The left gutter of the editor (where the line numebrs are) will show green. It will show yellow when you have un-saved changes in the code. If there is an error, the gutter turns red and the details of the error will be displayed in the console.


Responding to Midi
------------------------

Being able to compile and run code is great, but that doesn't help us unless we are just trying to learning the basics of writing python. In order to be really useful we'll need to start responding to midi messages, and for this we'll need to write a *callback*.

''''
def onMidiMessage(midi):
    print('This is executed when a matching midi message is recieved')
    print('...and here is the message:', midi)
'''

A callback is a function that is "called back in" by some other piece of code when something meaningful happens. It's telling a little kid, "so when you hear your Daddy come through the door, yell SURPRISE! OK?". Daddying coming through the door is the something meaningful, and yelling SURPRISE! is the callback containing the instructions to carry out when that something happens.

In the above example, we define a callback function called onMidiMessage. The name of the function is important because the engine is going to look for this function when a midi message is recieved. So now if you copy the above code into your script, compile it, and click the "Test" button, you will see your messages printed out in the script's console below the editor.


Dealing with midi data
--------------------------------
The "midi" argument passed to the "onMidiMessage" callback is a special object with lots of convenient functions for getting the messages' type, values, timestamp, etc. A full list of the functions is provided [here http://vedanamedia.com/products/pkmidicron#MidiMessage]

You can use the built-in ""outputs" function to send a message to a particular midi port. For example, to send a note-on message to the "IAC Bus 3" output port, you would do this:

'''
m = MidiMessage.noteOn(1, 64, 100)
outputs().sendMessage('IAC Bus 3', m)
'''

The first call creates a new note-on message for channel 1, note number 64, and velocity of 100. The second call sends the message to the output port named "IAC Bus 3"?. There object returned byt the "outputs()" call has several other methods for accessing the output ports, described [here http://vedanamedia.com/products/pkmidicron#ports].

Another way to send midi messages is using the built-int rtmidi module. This module provides direct access to the midi input and output hardware, allowing you to query and open midi ports. Full API docuemntation for rtmidi is provided [here http://vedanamedia.com/products/pkmidicron/rtmidi#rtmidi]

For more information on pyrtmidi, including source code, go here: https://github.com/patrickkidd/pyrtmidi.

Communicating between scripts (importing modules)
------------------------------
It doesn't take long before your scripts will become a little complicated and will need to start breakign them into peices. In a typical python program, you will define several .py files (called modules) within the same directory, and then use Python's "import" statement to import the functions from one module into another. In PKMidiCron you will define modules by adding script actions, and import them using the names specified in the name field.

For example, in generic Python you would import a module like this:

my_mod.py
----------------------------------
def GreatFunc(x):
    y = x + 2
    print('GreatFunc: I can do math, see?', y)

your_mod.py
----------------------------------
import my_mod
print('your_mod')
my_mod.GreatFunc(1)
my_mod.GreatFunc(5)

Then you could run the code like this
'''
$ python3 my_mod.py 
my_mod: Here I am!
$ python3 your_mod.py 
my_mod: Here I am!
your_mod: Here we are!
GreatFunc: I can do math, see? 3
GreatFunc: I can do math, see? 7
$ 
'''

Notice how your_mod is importing my_mod and calling it's function. So, to do the same in PKMidiCron, we would just create a couple of actions, one named my_mod and one named your_mod, and leave the rest of the code the same.


Creating Graphical Interfaces with PyQt
------------------------------
It is possible to create complex graphical interfaces that respond in real-time to midi events as well as user input. You can do this using the Qt toolkit. Bindings are provided by the PyQt toolkit. Full documentation can be found on the Qt (http://qt-project.org) and PyQt (http://riverbankcomputing.co.uk) project websites.

The following is a simple example of how to pop a window that shows the last message recieved, along with a button to close it:

'''
from PyQt5.QtWidgets import *

class Widget(QWidget):
    def __init__(self):
        super().__init__()
        self.button = QPushButton('close', self)
        self.button.clicked.connect(self.close)
        self.label = QLabel(self)
        Layout = QVBoxLayout(self)
        Layout.addWidget(self.button)
        Layout.addWidget(self.label)
        self.setLayout(Layout)

w = Widget()
def onMidiMessage(m):
    w.show()
    w.raise_()
    w.label.setText(str(m))
    outputs().sendMessage('IAC Bus 3', m)
'''

Here is the same code, but with comments explaining every detail:

'''
from PyQt5.QtWidgets import *

# these are the blueprints of the widget we want to create
class Widget(QWidget):
    
    # this function will get called 
    def __init__(self):
        super().__init__()

        # create our button
        self.button = QPushButton('close', self)

        # call the close() function on this QWidget when the button is clicked
        self.button.clicked.connect(self.close)

        # create our label
        self.label = QLabel(self)

        # lay everything out vertically.
        Layout = QVBoxLayout(self)
        Layout.addWidget(self.button)
        Layout.addWidget(self.label)
        self.setLayout(Layout)

# create an instance of the widget using the blueprints above
w = Widget()

def onMidiMessage(m):

    # show the widget if it's hidden
    w.show()

    # make sure it's on top of all other windows (could be annoying)
    w.raise_()

    # update the label with the new message
    w.label.setText(str(m))

    # forward the message on to "IAC Bus 3". Beware infinite loops!!!
    outputs().sendMessage('IAC Bus 3', m)
'''

- For more infomation on defining classes in Python: http://python.org/
- For more information on programming with Qt: http://qt-project.org/


Loading External Modules
-----------------------------------------
The real power of Python is the third-party modules available. For example, someone may have written one to communicate with your light controller, or DAW, or other device. Maybe you want ot keep your website updated with your tracklist? Who knows.

You can add folders to the search paths in the app's preferences. First create a folder on your hard drive where you want to store all of your modules like '/Users/patrick/pmc'. Then just drag the folder onto the python paths list in preferences. You can edit a path once you've added it by double-clicking the entry in the list.


Advanced Scripting Gotchyas
-------------------------------
The scripting engine is intended to provide a clean and stable environment to write complex interactions with midi data.

- All scripts are executed in the application's main thread.
- While the application's object-space is generally protected from user scripts, I'm sure it wouldn't be hard to figure out a way to break the app from a script. It's hard enough to do this that you will probably know what you are doing if you do.
