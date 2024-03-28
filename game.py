from api import Api
import numpy as np
from random import randrange
import json
import time
from minimax import minimax
from board import Board


class Game:
    def __init__(self, our_agent, opponent, size=3, target=3, first_move=True, gameId=None) -> None:
        self.our_agent = our_agent #our agent GME teamId: 1265
        self.opponent = opponent #either an instance of Api class (mellon) or an int(teamId) for opponent team
        self.first_move = first_move #do dwe need this? the first move always goes to the starting team

        # game doesnot already exist
        if not gameId:

            #check if the opponent is an instance of the Api class -we're debugging
            if isinstance(opponent, Api):
                #creating a new game with interactive play
                print("\n[interactive/debug mode - playing with ourselves]\n")
                self.debug = True
                self.gameId = our_agent.create_game(opponent.tid, size, target)
            else:
                #creating a new game with an outside team (opponent is an int)
                self.debug = False
                self.gameId = our_agent.create_game(opponent, size, target)

            #set up the game params
            self.size, self.target = size, target

        # game already exists 
        else:

            #check if the opponent is an instance of the Api class -we're debugging
            if isinstance(opponent, Api):
                #continuing a debugging game
                print("\n[interactive/debug mode - playing with ourselves]\n")
                self.debug = True

            else:
                #playing an outside opponent 
                self.debug = False

            #set up the game params
            self.size, self.target = self.get_game_params(gameId)
            self.gameId = gameId
        
        #init the numpy board
        self.board = Board(self.size, self.target)
        
        
        
    def play_game(self, who_starts="us"):
        """
        main game loop, alternates turns between user and agent
        or listens for moves in API and plays our agent against opponents there
        don't forget: the team that created the game always has the first move
        """

        #init turn based upon who is creating the game
        if who_starts == "us":
            turn = 0
        else:
            turn = 1

        #init game state (game is continuing on -1, else is won or tied)
        game_state = -1

        while game_state == -1:
            #show the board
            print("\n")
            print("---BOARD MAP---")
            self.display_board(self.our_agent, self.gameId)
            matrix = np.array(self.string_to_matrix(json.loads(self.opponent.get_board_string(self.gameId))["output"]))
            self.board.board = matrix
            print("\n")
            print("---NUMPY BOARD---")
            print(self.board)
            print(00000000000000000000000)
            res = json.loads(self.opponent.get_moves(self.gameId, 1))
            print(res)
            print(11111111111111111111111)
            try:
                myturn = (res["message"] == "No moves")
            except:
                myturn = (res["moves"][-1]["teamId"] != self.opponent.tid)
            print(2222222222222222222222222222222)
            print(myturn)
            if myturn:
                #agents turn
                print(333333333333333333333333333)
                # move = self.get_move_dummy_agent() #debug/testing agent makes random moves
                move = self.get_move_agent()
                print(444444444444444444444444)
                #update the numpy representation of the board
                self.board.add_symbol(move, 1)
                print(55555555555555555555)
                #check on the status of the game
                game_state = self.board.check_win_con(self.target, move)[1]
                print(6666666666666666666666)
                print("\n-------game_state: ", game_state)
                
            else:
                print("==================")
                print(res)
                print("==================")
                continue

        print("\n\n\nGAME OVER! game_state: ", game_state)
        print("->  0 on minimax agent win\n->  1 on opponent(or user) win\n->  2 on tie")
        print("\n")
        print("---FINAL BOARD MAP---")
        self.display_board(self.our_agent, self.gameId)
        print("---FINAL NUMPY BOARD---")
        print(self.board)
    
        

    def get_game_params(self, gameId):
        """
        collects the board string of a gameId from the API 
        returns the target and the board size
        """
        b = json.loads(self.our_agent.get_board_string(gameId))

        one_row = b['output'].split("\n")
        t = int(b['target'])
        return len(one_row[0]), t



    def display_board(self, agent, gameId):
        """
        display the board as an ASCII representation
        ex: 
        ------
        |X|O|X|
        ------
        |-|O|X|
        ------
        |O|X|O|
        """

        for line in json.loads(agent.get_board_string(gameId))["output"].split("\n"):
            if line != '':
                line_map = "|"

                for char in line:
                    line_map = line_map+f"{char}|"
                print('--'*len(line))
                print(line_map)
            else:
                continue

    def get_move_user(self):    
        """
        collects input from a human and posts to board using the API
        returns the user's move
        """
        status = 0
        while status == 0:
            #ask for move
            move = input("\nmove? format: int,int\nmove: ")

            #perform some validation of the input
            move = move.split(',')
            if len(move) == 1:
                print("please use format: int,int")
                continue
            elif len(move) > 2:
                print("please use format: int,int")
                continue
            else:
                try:
                    move = int(move[0]), int(move[1])
                except ValueError:
                    print("please use format: int,int")
                    continue

            #move posted to api
            d = dict(json.loads(self.opponent.make_move(self.gameId, move)))

            #check that move was sccesfully passed to the API, otherwise try again
            if d["code"] == "OK":
                status = 1
                return move
            else:
                continue

    def get_move_agent(self):
        """
        uses the current numpy representation of the board (created in init)
        passes board to minimax agent
        uses while loop to monitor API for move submission
        returns the move coords
        """
        #pass board to minimax agent and receive move back
        move = minimax(self.board, 1, True)[1]

        status = 0
        while status == 0:

            #supply move coords to the API
            d = dict(json.loads(self.our_agent.make_move(self.gameId, move)))

            #check that move was sccesfully passed to the API, otherwise try again
            if d["code"] == "OK":
                status = 1
                return move
            else:
                print(d)
                continue

        return move


    def get_move_dummy_agent(self):
        """
        randomly playing agent
        finds list of the currently unocupied spaces, chooses one at random 
        returns dummy move
        """
        #collect board state from API
        d = dict(json.loads(self.our_agent.get_board_map(self.gameId)))

        if not d['output']:
            #first move is not made so make it in middle of 3x3
            self.our_agent.make_move(self.gameId, (1,1))
            return (1,1)

        else:
            while True:
                #find a move that is available
                move = (randrange(self.size), randrange(self.size))
                if f"{move[0]},{move[1]}" in d['output']:
                    continue
                else:
                    #open space identified, post it to API
                    print("(dummy) agent's move: ", move)
                    self.our_agent.make_move(self.gameId, move)
                    return move
    


    def check_for_opponent_moves(self, who_starts):
        """
        check on API and find if our opponent has made any moves
        returns true if a move by our agent needs to be made
        returns false if we're still waiting for the opponent
        """

        #collect list of moves from API
        d = dict(json.loads(self.our_agent.get_moves(self.gameId, 1)))

        #check for API reporting a failure when there are no moves yet made
        if d["code"] == "FAIL":
            if d["message"] == "No moves" and who_starts=="us":
                #we need to make the first move
                return True
            elif d["message"] == "No moves" and who_starts=="them":
                #we need to wait for them to move
                return False
            else:
                #this happens if the game is no longer open
                print("something else happened...")
                print(d)
                exit()

        #check if our team was the last one to move
        elif d["moves"][0]["teamId"] == self.our_agent.tid:
            return False

        #the opponent just moved
        else:
            move=(int(d["moves"][0]["move"].split(',')[0]), int(d["moves"][0]["move"].split(',')[1]))
            
            #update the numpy board
            self.board.add_symbol(move, -1)

            return True


    def string_to_matrix(self, matrix_string):
        rows = matrix_string.strip().split('\n')
        matrix = []
        for row in rows:
            matrix.append([0 if c == '-' else 1 if c == 'O' else -1 for c in row])
        return matrix




            
        

