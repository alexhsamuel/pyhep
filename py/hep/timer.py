#-----------------------------------------------------------------------
#
# module hep.timer
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Execution timers.

This module provides the 'Timer' class, for timing program execution and
other activities.  

The most-recently-started timer is considered the "active" timer.
Less-recently-started timers (which have not subsequently been stopped)
are "inactive".  Each timer accumulates two elapsed times:

  "inclusive" time -- The sum of elapsed times between starts and stops,
  whether the timer was active or inactive.

  "exclusive" time -- The sum of time intervals in which this timer was
  running and active.

Note that a timer cannot be started if it is already running, and only
the active timer may be stopped, i.e. running timers must be correctly
nested.

On Linux, the timer precision is 10 msec.

In addition, this module maintains a dictionary of named timers.  Use
the 'get' function to access it.  If a timer doesn't exist for the given
name, a new timer is created under that name.  The 'start' and 'stop'
functions allow you to start and stop a timer by name; the 'stop'
function without arguments will stop the active timer.

The 'stopAll' function stops all running timers, and 'printAll' prints
the inclusive and exclusive time elapsed for each timer in the
dictionary.  These two functions are called automatically when Python
exits."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import atexit
from   hep.ext import Timer
from   hep.ext import timer_get as get
from   hep.ext import timer_start as start
from   hep.ext import timer_stop as stop
from   hep.ext import timer_stopAll as stopAll
from   hep.ext import timer_printAll as printAll

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class TimerRun:

    def __init__(self, timer):
        self.__timer = timer
        timer.start()


    def __del__(self):
        self.__timer.stop()



#-----------------------------------------------------------------------
# initialization
#-----------------------------------------------------------------------

# 'atexit' calls registered functions in reverse order of registration.
atexit.register(printAll)
atexit.register(stopAll)

