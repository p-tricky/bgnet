from classes.controller import Controller

croller = Controller(gnubg)
croller.setup_game()
#croller.train(num_games=100000, save_interval=10000)
croller.train(num_games=20, save_interval=5)

