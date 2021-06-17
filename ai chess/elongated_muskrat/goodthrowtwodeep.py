from copy import deepcopy
from math import sqrt, inf
from random import choice

def dist(pos1, pos2):
    """
    returns distance between two co-ordinates (a,b) and (c,d)
    """
    a, b = pos1
    c, d = pos2
    
    return sqrt((a-c)**2 + (b-d)**2)

def eval_pos(board, colour):
    """
    evaluates a "goodness score" for colour, given a board
    """
    
    beats_dict = {"r": "s", "p": "r", "s": "p"}

    # reorganises board data into a dictionary of tokens and their positions
    own_tokens = {'r': [], 'p': [], 's': []}
    opp_tokens = {'r': [], 'p': [], 's': []}
    
    for pos, token in board.items():
        if token:
            token = token[0]
            if colour == "upper":
                if token.isupper():
                    own_tokens[token.lower()].append(pos)
                else: # token is lower
                    opp_tokens[token].append(pos)
            else: # colour = "lower"
                if token.isupper():
                    opp_tokens[token.lower()].append(pos)
                else: # token is lower
                    own_tokens[token].append(pos)

    score = 0

    # assign values to own tokens as [# beatable]/[# identical * closest enemy dist]
    for hand, positions in own_tokens.items():
        if len(positions) > 0: # check that there are instances of the hand first
            beats = beats_dict[hand]
            targets = opp_tokens[beats]
            init_value = len(targets)/len(positions)
            
            for position in positions:
                min_target_dist = inf
                for target in targets:
                    target_dist = dist(position, target)
                    if target_dist < min_target_dist:
                        min_target_dist = target_dist
                        
                score += (1+init_value)/min_target_dist

    # subtract number of opponent tokens on the board
    for hand, positions in opp_tokens.items():
        for position in positions:
            score -= 2

    return score

    
class Player:
    def __init__(self, player):
        """
        Called once at the beginning of a game to initialise this player.
        Set up an internal representation of the game state.

        The parameter player is the string "upper" (if the instance will
        play as Upper), or the string "lower" (if the instance will play
        as Lower).
        """
        
        self.colour = player
        self.board = Board()

    def action(self):
        """
        Called at the beginning of each turn. Based on the current state
        of the game, select an action to play this turn.
        """

        opp = {"upper":"lower", "lower":"upper"}

        def minimax(curr_board, depth, alpha, beta, player, best_move = None):
            if depth == 0:
                return eval_pos(curr_board.board, self.colour), best_move

            all_acts = list(curr_board.available_actions(player))

            # prune bad throws - only considers best throw action
            acts = []
            best_throw = []
            best_throw_score = -inf
            for act in all_acts:
                if act[0] == "THROW":
                    anal_board = deepcopy(curr_board)
                    anal_board.half_update(act, player)
                    score = eval_pos(anal_board.board, player)
                    if score > best_throw_score:
                        best_throw_score = score
                        best_throw = [act]
                    if score == best_throw_score: # if there is an equivalent move, consider making it (good for testing)
                        best_throw = [choice([best_throw[0], act])]
                else:
                    acts.append(act)

            
            for throw in best_throw:
                acts.append(throw)

            if player == self.colour: # trying to maximise score
                max_score = -inf
                
                for act in acts:
                    child = deepcopy(curr_board)
                    child.half_update(act, player)
                    score = minimax(child, depth - 1, alpha, beta, opp[player])[0]
                    if score > max_score:
                        max_score = score
                        best_move = act
                    alpha = max(alpha, score)
                    if beta <= alpha:
                        break
                    
                return max_score, best_move
            
            else: # trying to minimise score
                min_score = inf
                
                for act in acts:
                    child = deepcopy(curr_board)
                    child.half_update(act, player)
                    score = minimax(child, depth - 1, alpha, beta, opp[player])[0]
                    min_score = min(min_score, score)
                    beta = min(beta, score)
                    if beta <= alpha:
                        break
                    
                return min_score, best_move
                
        score, best_move = minimax(self.board, 2, -inf, inf, self.colour)
        return best_move

    def update(self, opponent_action, player_action):
        """
        Called at the end of each turn to inform this player of both
        players' chosen actions. Update your internal representation
        of the game state.
        The parameter opponent_action is the opponent's chosen action,
        and player_action is this instance's latest chosen action.
        """

        if self.colour == 'upper':
            self.board.update(player_action, opponent_action)
        else: # self.colour == 'lower':
            self.board.update(opponent_action, player_action)

# modified from referee.game.py
class Board:
    def __init__(self):
        self.throws = {"upper": 0, "lower": 0}
        self.nturns = 0
        # all hexes
        _HEX_RANGE = range(-4, +4 + 1)
        _ORD_HEXES = [
            (r, q) for r in _HEX_RANGE for q in _HEX_RANGE if -r - q in _HEX_RANGE
        ]
        self._SET_HEXES = frozenset(_ORD_HEXES)

        # nearby hexes
        self._HEX_STEPS = [(1, -1), (1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1)]
        self._BEATS_WHAT = {"r": "s", "p": "r", "s": "p"}
        self._WHAT_BEATS = {"r": "p", "p": "s", "s": "r"}
        self.board = {x: [] for x in _ORD_HEXES}

    def _ADJACENT(self, x):
        rx, qx = x
        return self._SET_HEXES & {(rx + ry, qx + qy) for ry, qy in self._HEX_STEPS}

    def _BATTLE(self, symbols):
        types = {s.lower() for s in symbols}
        upper_cnt = sum([s.isupper() for s in symbols]) 
        lower_cnt = sum([s.islower() for s in symbols]) 

        if len(types) == 1:
            # no fights
            return symbols, 0, 0
        if len(types) == 3:
            # everyone dies
            return [], 0-upper_cnt, 0-lower_cnt
        # else there are two, only some die:
        for t in types:
            # those who are not defeated stay
            symbols = [s for s in symbols if s.lower() != self._BEATS_WHAT[t]]

        return symbols, sum([s.isupper() for s in symbols])-upper_cnt, sum([s.islower() for s in symbols])-lower_cnt

    def available_actions(self, colour):
        """
        A generator of currently-available actions for a particular player
        (assists validation).
        """
        throws = self.throws[colour]
        isplayer = str.islower if colour == "lower" else str.isupper
        if throws < 9:
            sign = -1 if colour == "lower" else 1
            throw_zone = (
                (r, q) for r, q in self._SET_HEXES if sign * r >= 4 - throws
            )
            for x in throw_zone:
                for s in "rps":
                    yield "THROW", s, x
        occupied = {x for x, s in self.board.items() if any(map(isplayer, s))}
        for x in occupied:
            adjacent_x = self._ADJACENT(x)
            for y in adjacent_x:
                yield "SLIDE", x, y
                if y in occupied:
                    opposite_y = self._ADJACENT(y) - adjacent_x - {x}
                    for z in opposite_y:
                        yield "SWING", x, z    

    def update(self, upper_action, lower_action):
        """
        Submit an action to the game for validation and application.
        If the action is not allowed, raise an InvalidActionException with
        a message describing allowed actions.
        Otherwise, apply the action to the game state.
        """
        # validate the actions:
        for action, c in [(upper_action, "upper"), (lower_action, "lower")]:
            actions = list(self.available_actions(c))
            if action not in actions:
                self.logger.info(f"error: {c}: illegal action {action!r}")
                available_actions_list_str = "\n* ".join(
                    [f"{a!r} - {_FORMAT_ACTION(a)}" for a in actions]
                )
                # NOTE: The game instance _could_ potentially be recovered
                # but pursue a simpler implementation that just exits now
                raise Exception(
                    f"{c} player's action, {action!r}, is not well-"
                    "formed or not available. See specification and "
                    "game rules for details, or consider currently "
                    "available actions:\n"
                    f"* {available_actions_list_str}"
                )
        # otherwise, apply the actions:
        battles = []
        atype, *aargs = upper_action
        if atype == "THROW":
            s, x = aargs
            self.board[x].append(s.upper())
            self.throws["upper"] += 1
            battles.append(x)
        else:
            x, y = aargs
            # remove ONE UPPER-CASE SYMBOL from self.board[x] (all the same)
            s = self.board[x][0].upper()
            self.board[x].remove(s)
            self.board[y].append(s)
            # add it to self.board[y]
            battles.append(y)
        atype, *aargs = lower_action
        if atype == "THROW":
            s, x = aargs
            self.board[x].append(s.lower())
            self.throws["lower"] += 1
            battles.append(x)
        else:
            x, y = aargs
            # remove ONE LOWER-CASE SYMBOL from self.board[x] (all the same)
            s = self.board[x][0].lower()
            self.board[x].remove(s)
            self.board[y].append(s)
            # add it to self.board[y]
            battles.append(y)
        # resolve hexes with new tokens:
        upper_defeated_cnt = 0
        lower_defeated_cnt = 0
        for x in battles:
            # TODO: include summary of battles in output?
            self.board[x], upper_defeated, lower_defeated = self._BATTLE(self.board[x])
            upper_defeated_cnt += upper_defeated
            lower_defeated_cnt += lower_defeated

        self.nturns += 1
        return upper_defeated_cnt, lower_defeated_cnt

    def half_update(self, action, colour):
        battles = []
        atype, *aargs = action
        if atype == "THROW":
            s, x = aargs
            if colour == "upper":
                self.board[x].append(s.upper())
                self.throws["upper"] += 1
            else:
                self.board[x].append(s.lower())
                self.throws["lower"] += 1
            battles.append(x)
        else: # Slide or Swing
            x, y = aargs
            if colour == "upper":
                s = self.board[x][0].upper()
            else:
                s = self.board[x][0].lower()
            self.board[x].remove(s)
            self.board[y].append(s)
            # add it to self.board[y]
            battles.append(y)
        # resolve hexes with new tokens:
        for x in battles:
            # TODO: include summary of battles in output?
            self.board[x], upper_defeated, lower_defeated = self._BATTLE(self.board[x])

def _FORMAT_ACTION(action):
    atype, *aargs = action
    if atype == "THROW":
        return "THROW symbol {} to {}".format(*aargs)
    else:  # atype == "SLIDE" or "SWING":
        return "{} from {} to {}".format(atype, *aargs)            
