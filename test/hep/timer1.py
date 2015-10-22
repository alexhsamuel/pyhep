from   hep import timer
from   hep.test import compare
import time

timer.start("timer 1")
time.sleep(0.1)
timer.start("timer 2")
time.sleep(0.2)
timer.stop("timer 2")
time.sleep(0.3)
timer.start("timer 3")
time.sleep(0.4)
timer.stop()
time.sleep(0.5)

timer.stopAll()
timer1 = timer.get("timer 1")
timer2 = timer.get("timer 2")
timer3 = timer.get("timer 3")
compare(timer1.inclusive_time, 1.5, precision=0.01)
compare(timer1.exclusive_time, 0.9, precision=0.01)
compare(timer2.inclusive_time, 0.2, precision=0.01)
compare(timer2.exclusive_time, 0.2, precision=0.01)
compare(timer3.inclusive_time, 0.4, precision=0.01)
compare(timer3.exclusive_time, 0.4, precision=0.01)
