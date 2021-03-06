import os
import sys

from rasa.__main__ import main

# insert path of this script in syspath so actions.py will be found
sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))

#
# This is exactly like issuing the command:
#  $ rasa run actions
#
sys.argv.append('run')
sys.argv.append('--enable-api')
# sys.argv.append('--debug')

main()
