import traceback
import sys
import ipdb
import datetime
from classes.controller import Controller

try:
    croller = Controller(gnubg)
    croller.setup_game()
    start = datetime.datetime.now()
    #croller.load_nn("1000games")
    croller.train(num_games=10001, save_interval=500)
    #croller.play_human_opponent()
    croller.test(100)
    end = datetime.datetime.now()
    diff = end - start
    print("minutes: " + str(int(diff.total_seconds()) / 60))
    gnubg.command("exit")

except:
    typ, value, tb = sys.exc_info()
    traceback.print_exc()
    ipdb.post_mortem(tb)

