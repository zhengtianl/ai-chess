from copy import deepcopy
import random

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
        self.game_in_head = Board()

    def action(self):
        """
        Called at the beginning of each turn. Based on the current state
        of the game, select an action to play this turn.
        """

        # turns is small
        # TODO: throw tokens that will defeat the upper tokens
        if self.game_in_head.nturns <= 6:
            avaliable_acts = list(self.game_in_head.available_actions(self.colour))
            return random.choice(avaliable_acts)

        # assume the smart opponent can always choose the best step
        # Depth First Search
        steps = 2
        stack = [(self.game_in_head, (), 0)]
        maxmin = None
        good_paths = []

        while len(stack) > 0:
            parent_node, path, score = stack.pop(-1)
            if len(path) >= steps*2:
                
                # leaf node in the search tree
                if maxmin is None:
                    maxmin = score
                    good_paths.append(path)
                elif maxmin == score:
                    good_paths.append(path)
                elif maxmin < score:
                    maxmin = score
                    good_paths.clear()
                    good_paths.append(path)
            else:
                # root node, find its leaves
                children_nodes = self.one_step_infe(parent_node, path, score)
                stack += children_nodes

        path_dec = random.choice(good_paths)    
        if self.colour == 'upper':
            return path_dec[0] 
        elif self.colour == 'lower':
            return path_dec[1]    

    def one_step_infe(self, parent_node, path, score):
        children_nodes = []

        if self.colour == 'upper':
            all_upper_act = list(parent_node.available_actions('upper'))
            for upper_act in random.choices(all_upper_act, k=min(10, len(all_upper_act))):
                min_onestep = None
                opponent_acts = []
                all_lower_act = list(parent_node.available_actions('lower'))
                for lower_act in random.choices(all_lower_act, k=min(10, len(all_lower_act))):
                # the smart opponent always make a decision to minimize the score  
                    child_node = deepcopy(parent_node)
                    upper_defeated, lower_defeated = child_node.update(upper_act, lower_act)
                    # simple evaluation function
                    child_score = (score + 1.5*lower_defeated - upper_defeated)
                    if min_onestep is None:
                        min_onestep = child_score 
                        opponent_acts.append((lower_act, child_node))
                    elif min_onestep == child_score:
                        #opponent_acts.append((lower_act, child_node))
                        pass
                    elif min_onestep > child_score:
                        min_onestep = child_score
                        opponent_acts.clear()
                        opponent_acts.append((lower_act, child_node))
                if min_onestep is not None:
                    oppo_dec, child_node = random.choice(opponent_acts)                     
                    children_nodes.append((child_node, path+(upper_act, oppo_dec), min_onestep))
        else:
            all_lower_act = list(parent_node.available_actions('lower'))
            for lower_act in random.choices(all_lower_act, k=min(10, len(all_lower_act))):
                min_onestep = None
                opponent_acts = []
                all_upper_act = list(parent_node.available_actions('upper'))
                for upper_act in random.choices(all_upper_act, k=min(10, len(all_upper_act))):
                    child_node = deepcopy(parent_node)
                    upper_defeated, lower_defeated = child_node.update(upper_act, lower_act)
                    child_score = (score - lower_defeated + 1.5*upper_defeated)
                    if min_onestep is None:
                        min_onestep = child_score 
                        opponent_acts.append((upper_act, child_node))
                    elif min_onestep == child_score:
                        #opponent_acts.append((upper_act, child_node))
                        pass
                    elif min_onestep > child_score:
                        min_onestep = child_score
                        opponent_acts.clear()
                        opponent_acts.append((upper_act, child_node))
                if min_onestep is not None:
                    oppo_dec, child_node = random.choice(opponent_acts)                    
                    children_nodes.append((child_node, path+(oppo_dec, lower_act), min_onestep))        
        
        return children_nodes

    def update(self, opponent_action, player_action):
        """
        Called at the end of each turn to inform this player of both
        players' chosen actions. Update your internal representation
        of the game state.
        The parameter opponent_action is the opponent's chosen action,
        and player_action is this instance's latest chosen action.
        """

        if self.colour == 'upper':
            self.game_in_head.update(player_action, opponent_action)
        else:
            self.game_in_head.update(opponent_action, player_action)

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


def _FORMAT_ACTION(action):
    atype, *aargs = action
    if atype == "THROW":
        return "THROW symbol {} to {}".format(*aargs)
    else:  # atype == "SLIDE" or "SWING":
        return "{} from {} to {}".format(atype, *aargs)            
