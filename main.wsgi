import sys
import os
sys.path.insert(0, '/usr/local/share/sesti')
os.chdir("/usr/local/share/sesti")
print "Hello as hello!"
from main import app as application
