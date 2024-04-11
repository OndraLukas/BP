import random
from enum import Enum
import pygame
import sys
import math
import copy

# Initialize Pygame
pygame.init()
pygame.font.init()

def debug_check(game_object, context):
    print(f"Debug Check in {context}:")
    for player in game_object.players:
        print(f"Player {player} armies: {player.armies}")
    game_object.display_tile_info()

#Globální proměnné
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 720
COLORS = {
    "water_tile" : (0, 0, 139),
    "ground_tile" : (0, 100, 0),
    "clickable_tile" : (0, 150, 0),
    "text_default" : (255, 255, 255),
    "text_highlighted" : (250, 250, 0),
    "player_red" : (255, 0, 0),
    "player_green" : (0, 255, 0),
    "player_blue" : (0, 0, 255),
    "player_yellow" : (255, 255, 0),
    "player_orange" : (255, 165, 0)
}
STARTING_ARMIES = 3
MAX_ARMIES = 14
MAX_CITIES = 3

AI_ACTION_EVENT = pygame.USEREVENT + 1


class Phases(Enum):
    PickCard = 1
    PickAbilityAND = 2
    PickAbilityOR = 3
    BuildArmy = 4
    BuildCity = 5
    MoveArmy = 6
    DestroyArmy = 7
    SailArmy = 8
    JokerAssignment = 9
    EndGame = 10

class Deck:
    def __init__(self, goods, default_deck, bonus_deck):
        self.goods = goods
        self.default_deck = default_deck
        self.bonus_deck = bonus_deck

class Good:
    def __init__(self, name, score):
        self.name = name
        self.score1 = score[0]
        self.score2 = score[1]
        self.score3 = score[2]
        self.score5 = score[3]


class Card:
    def __init__(self, abilities, good, quantity, isor):
        self.abilities = abilities
        self.good = good
        self.quantity = quantity
        self.isor = isor
        self.cost = 0

    def set_cost(self, number):
        self.cost = number

class Ability:
    def __init__(self, manuevers):
        self.manuevers = manuevers

class BuildArmies(Ability):
    def __init__(self, manuevers):
        super().__init__(manuevers)
        self.ability_description = "Build Armies(" + str(self.manuevers) + ")"

class BuildCities(Ability):
    def __init__(self, manuevers):
        super().__init__(manuevers)
        self.ability_description = "Build Cities(" + str(self.manuevers) + ")"

class MoveArmies(Ability):
    def __init__(self, manuevers):
        super().__init__(manuevers)
        self.ability_description = "Move Armies(" + str(self.manuevers) + ")"

class DestroyArmies(Ability):
    def __init__(self, manuevers):
        super().__init__(manuevers)
        self.ability_description = "Destroy Armies(" + str(self.manuevers) + ")"

class SailArmies(Ability):
    def __init__(self, manuevers):
        super().__init__(manuevers)
        self.ability_description = "Sail Armies(" + str(self.manuevers) + ")"

class Continent:
    def __init__(self, continent_id, name):
        self.continent_id = continent_id
        self.name = name
        self.tiles = []
        self.armies = [0,0,0,0,0]
        self.cities = [0,0,0,0,0]

    def add_tile(self, tile):
        self.tiles.append(tile)
        tile.continent = self

    def set_armies(self, player_index, number):
        self.armies[player_index] = number

    def set_cities(self, player_index, number):
        self.cities[player_index] = number

class Tile:
    def __init__(self, tile_x, tile_y, tile_type):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.tile_id = f"T{self.tile_x}_{self.tile_y}"
        self.continent = None
        self.tile_type = tile_type
        self.armies = [0, 0, 0, 0, 0]
        self.cities = [0, 0, 0, 0, 0]
        self.neighbours = []
        self.is_starting_tile = False
        self.clickable = False
        self.move_cost = -1

    def __deepcopy__(self, memo):
        new_copy = Tile(self.tile_x, self.tile_y, self.tile_type)
        new_copy.armies = copy.deepcopy(self.armies, memo)
        new_copy.cities = copy.deepcopy(self.cities, memo)
        new_copy.is_starting_tile = self.is_starting_tile
        new_copy.clickable = self.clickable
        new_copy.move_cost = self.move_cost
        new_copy.neighbours = []
        return new_copy

    def make_starting_tile(self):
        self.is_starting_tile = True

    def add_neighbour(self, neighbour):
        if neighbour not in self.neighbours:
            self.neighbours.append(neighbour)
            neighbour.neighbours.append(self)

    def set_armies(self, player_index, number):
        self.armies[player_index] = number

    def add_army(self, player_index):
        self.armies[player_index] += 1

    def add_armies(self, player_index, number):
        self.armies[player_index] += number

    def remove_army(self, player_index):
        if self.armies[player_index] != 0:
            self.armies[player_index] -= 1

    def set_cities(self, player_index, number):
        self.cities[player_index] = number

    def add_city(self, player_index):
        self.cities[player_index] += 1

    def remove_city(self, player_index):
        if self.cities[player_index] != 0:
            self.cities[player_index] -= 1

    def set_movecost(self, number):
        self.move_cost = number

    def set_clickable(self):
        self.clickable = True

    def set_nonclickable(self):
        self.clickable = False

#Tile manager
class TileManager:
    def __init__(self):
        self.active_tile = None
        self.selected_armies = 0

    def set_active_tile(self, target_tile):
        self.active_tile = target_tile

    def set_selected_armies(self, number):
        self.selected_armies = number


    def reset_armies(self, player_index):
        if self.active_tile != None:
            self.active_tile.add_armies(player_index, self.selected_armies)
            self.set_selected_armies(0)

    def count_armies(self, player_index, tiles):
        armycount = 0
        for row in tiles:
            for tile in row:
                armycount += tile.armies[player_index]
        return armycount

    def continent_army_count(self, player_index, continent):
        armycount = 0
        for tile in continent.tiles:
            armycount += tile.armies[player_index]
        return armycount

    def count_cities(self, player_index, tiles):
        citycount = 0
        for row in tiles:
            for tile in row:
                citycount += tile.cities[player_index]
        return citycount

    def continent_city_count(self, player_index, continent):
        citycount = 0
        for tile in continent.tiles:
            citycount += tile.cities[player_index]
        return citycount

    def movable_tiles(self, target_tile, reserve, original):
        target_tile.clickable = True
        target_tile.set_movecost(original - reserve)
        reserve = reserve - self.selected_armies
        if(reserve >= 0):
            for neihgbour in target_tile.neighbours:
                if (neihgbour.clickable == False or neihgbour.move_cost > original - reserve) and not(neihgbour.tile_type == "water"):
                    self.movable_tiles(neihgbour, reserve, original)

    def sailable_tiles(self, target_tile, reserve, original):
        if target_tile.tile_type == "ground":
            target_tile.clickable = True
            target_tile.set_movecost(original - reserve)
            reserve = reserve - self.selected_armies
            if (reserve >= 0):
                for neihgbour in target_tile.neighbours:
                    if (neihgbour.clickable == False or neihgbour.move_cost > original - reserve):
                        self.sailable_tiles(neihgbour, reserve, original)
        else:
            for neihgbour in target_tile.neighbours:
                if (neihgbour.clickable == False or neihgbour.move_cost > original - reserve) and not(neihgbour.tile_type == "water"):
                    self.sailable_tiles(neihgbour, reserve, original)

    def reset_movable_tiles(self, tiles):
        for row in tiles:
            for tile in row:
                tile.set_nonclickable()
                tile.move_cost = -1

#Player
class Player:
    def __init__(self, name, AI, color):
        self.name = name
        self.armies = 0
        self.cities = 0
        self.AI = AI
        self.color = color
        self.goods = {}
        self.coins = 0
        self.score = 0

    def set_armies(self, number):
        self.armies = number

    def set_cities(self, number):
        self.cities = number

    def spend_coins(self, number):
        self.coins -= number

    def set_coins(self, number):
        self.coins = number

#Game
class Game:
    def __init__(self, deck, layout, players, tilemanager, starting_armies, max_armies, max_cities):
        self.max_armies = max_armies
        self.max_cities = max_cities
        self.players = players
        self.active_player = 0
        self.tiles = []
        self.active_cards = []
        self.viable_abilities = []
        self.played_card = None
        self.continents = {}
        self.board_layout = layout
        self.phase = None
        self.tilemanager = tilemanager
        self.manuevers = 0
        self.turn = 1
        self.target_player = None
        self.deck = deck
        self.deck_cards = []
        self.max_turns = 0
        self.winners = []
        self.starting_armies = starting_armies

    def __deepcopy__(self, memo):
        # Create a new instance without calling __init__
        cls = self.__class__
        new_obj = cls.__new__(cls)
        memo[id(self)] = new_obj

        # Copy all attributes but skip 'continents'
        for k, v in self.__dict__.items():
            if k == 'continents':  # Skip copying 'continents'
                setattr(new_obj, k, None)  # Set to None or an appropriate default value
            else:
                setattr(new_obj, k, copy.deepcopy(v, memo))

        return new_obj

    def initialize_game(self):
        self.create_board()
        self.set_up_starting_armies(self.starting_armies)
        self.phase = Phases.PickCard
        self.set_player_coins()
        self.prepare_deck_cards()
        self.set_max_turns()
        while len(self.active_cards) < 6:
            self.draw_card()
        self.set_cards_cost()
        self.thorough_counting()

    def clone_game(self):
        cloned_game = copy.deepcopy(self)

        cloned_game.continents = {}
        cloned_game.add_neighbors(cloned_game.tiles)

        continent_counter = 0
        for row in cloned_game.tiles:
            for tile in row:
                continent_counter = cloned_game.assign_to_continent(tile, cloned_game.continents, cloned_game.tiles, continent_counter)

        cloned_game.thorough_counting()
        return cloned_game


    def add_neighbors(self, tiles):
        for i in range(len(tiles)):
            for j in range(len(tiles[i])):
                tile = tiles[i][j]
                if i > 0: tile.add_neighbour(tiles[i - 1][j])
                if i < len(tiles) - 1: tile.add_neighbour(tiles[i + 1][j])
                if j > 0: tile.add_neighbour(tiles[i][j - 1])
                if j < len(tiles[i]) - 1: tile.add_neighbour(tiles[i][j + 1])

    def assign_to_continent(self, tile, continents, tiles, continent_counter):
        if tile.tile_type == 'ground' and tile.continent is None:
            continent_counter += 1
            continent = Continent(f"C{continent_counter}", f"Continent{continent_counter}")
            continents[continent.continent_id] = continent
            self.explore_and_assign(tile, continent, tiles)
        return continent_counter

    def explore_and_assign(self, tile, continent, tiles):
        if tile.tile_type == 'ground' and tile.continent is None:
            continent.add_tile(tile)
            for neighbour in tile.neighbours:
                self.explore_and_assign(neighbour, continent, tiles)

    def create_board(self):
        self.tiles = []
        continent_counter = 0

        for row_index, row in enumerate(self.board_layout):
            tile_row = []
            for col_index, col in enumerate(row):
                tile_type = 'water' if col == 'W' else 'ground'
                tile = Tile(row_index, col_index, tile_type)
                if col == 'S':
                    tile.make_starting_tile()
                tile_row.append(tile)
            self.tiles.append(tile_row)

        self.add_neighbors(self.tiles)

        for row in self.tiles:
            for tile in row:
                continent_counter = self.assign_to_continent(tile, self.continents, self.tiles, continent_counter)

    def display_tile_info(self):
        for row in self.tiles:
            for tile in row:
                continent_id = tile.continent.continent_id if tile.continent else 'None'
                print(f"Tile ID: {tile.tile_id}, Continent: {continent_id}, Type: {tile.tile_type}, Armies: {tile.armies}, Cities: {tile.cities}" )
        for continent in self.continents:
            print(f"Continent: {continent}, Armies: {self.continents[continent].armies}, Cities: {self.continents[continent].cities}")

    def set_phase(self, phase):
        self.phase = phase

    def thorough_counting(self):
        for player_index in range(len(self.players)):
            self.players[player_index].armies = self.tilemanager.count_armies(player_index, self.tiles)
            self.players[player_index].cities = self.tilemanager.count_cities(player_index, self.tiles)
            for continent in self.continents:
                self.continents[continent].set_armies(player_index, self.tilemanager.continent_army_count(player_index, self.continents[continent]))
                self.continents[continent].set_cities(player_index, self.tilemanager.continent_city_count(player_index, self.continents[continent]))


    def set_player_coins(self):
        if len(self.players) == 5:
            for player in self.players:
                player.set_coins(8)
        if len(self.players) == 4:
            for player in self.players:
                player.set_coins(9)
        if len(self.players) == 3:
            for player in self.players:
                player.set_coins(11)
        else:
            for player in self.players:
                player.set_coins(14)

    def set_max_turns(self):
        if len(self.players) == 5:
            self.max_turns = 7
        if len(self.players) == 4:
            self.max_turns = 8
        if len(self.players) == 3:
            self.max_turns = 10
        else:
            self.max_turns = 13

    def set_cards_cost(self):
        for card_index, card in enumerate(self.active_cards):
            card.set_cost(math.ceil(card_index/2))

    def set_active_cards(self, cards):
        self.active_cards = cards
        self.set_cards_cost()

    def play_card(self, played_card):
        active_player = self.players[self.active_player]
        active_player.spend_coins(played_card.cost)
        if played_card.good != "Joker":
            self.add_good(self.deck.goods[played_card.good], played_card.quantity)
        else:
            self.add_joker(played_card.quantity)
        if len(played_card.abilities) > 1:
            if played_card.isor:
                self.set_phase(Phases.PickAbilityOR)
            else:
                self.set_phase(Phases.PickAbilityAND)
            self.viable_abilities += played_card.abilities
        else:
            self.pick_ability(played_card.abilities[0])
        self.active_cards.remove(played_card)

    def add_good(self, good, quantity):
        active_player = self.players[self.active_player]
        if good.name in active_player.goods:
            active_player.goods[good.name] += quantity
        else:
            active_player.goods[good.name] = quantity

    def add_joker(self, quantity):
        active_player = self.players[self.active_player]
        if "Joker" in active_player.goods:
            active_player.goods["Joker"] += quantity
        else:
            active_player.goods["Joker"] = quantity



    def pick_ability(self, picked_ability):
        self.set_manuevers(picked_ability.manuevers)
        if isinstance(picked_ability, BuildArmies):
            self.set_phase(Phases.BuildArmy)
        elif isinstance(picked_ability, BuildCities):
            self.set_phase(Phases.BuildCity)
        elif isinstance(picked_ability, MoveArmies):
            self.set_phase(Phases.MoveArmy)
        elif isinstance(picked_ability, DestroyArmies):
            viable_targets = []
            viable_targets += self.players
            viable_targets.remove(self.players[self.active_player])
            self.target_player = viable_targets[0]
            self.set_phase(Phases.DestroyArmy)
        elif isinstance(picked_ability, SailArmies):
            self.set_phase(Phases.SailArmy)

    def next_player(self):
        self.active_player = (self.active_player + 1)%len(self.players)

    def set_manuevers(self, number):
        self.manuevers = number

    def set_up_starting_armies(self, number):
        for row in self.tiles:
            for tile in row:
                if tile.is_starting_tile:
                    for i in range(len(self.players)):
                        tile.set_armies(i, number)

    def destroy_armies(self, target_tile):
        player_index = self.players.index(self.target_player)
        if target_tile.armies[player_index] > 0 and self.manuevers > 0:
            target_tile.remove_army(player_index)
            self.players[player_index].armies = self.tilemanager.count_armies(player_index, self.tiles)
            target_tile.continent.set_armies(player_index, self.tilemanager.continent_army_count(player_index, target_tile.continent))
            self.set_manuevers(self.manuevers - 1)

    def build_armies(self, target_tile):
        if (target_tile.is_starting_tile or target_tile.cities[self.active_player] > 0) and self.players[self.active_player].armies < self.max_armies and self.manuevers > 0:
            target_tile.add_army(self.active_player)
            self.players[self.active_player].armies = self.tilemanager.count_armies(self.active_player, self.tiles)
            target_tile.continent.set_armies(self.active_player, self.tilemanager.continent_army_count(self.active_player, target_tile.continent))
            self.set_manuevers(self.manuevers - 1)

    def build_cities(self, target_tile):
        if target_tile.armies[self.active_player] > 0 and self.players[self.active_player].cities < self.max_cities and self.manuevers > 0:
            target_tile.add_city(self.active_player)
            self.players[self.active_player].cities = self.tilemanager.count_cities(self.active_player, self.tiles)
            target_tile.continent.set_cities(self.active_player, self.tilemanager.continent_city_count(self.active_player, target_tile.continent))
            self.set_manuevers(self.manuevers-1)

    def move_armies(self, target_tile):
        if target_tile.armies[self.active_player] > 0 and (self.tilemanager.selected_armies == 0 or target_tile.move_cost == 0):
            self.tilemanager.reset_movable_tiles(self.tiles)
            target_tile.remove_army(self.active_player)
            self.tilemanager.set_selected_armies(self.tilemanager.selected_armies + 1)
            self.tilemanager.movable_tiles(target_tile, self.manuevers, self.manuevers)
            self.tilemanager.set_active_tile(target_tile)
            target_tile.continent.set_armies(self.active_player,
                                             self.tilemanager.continent_army_count(self.active_player,
                                                                                   target_tile.continent))
        elif target_tile.clickable:
            target_tile.add_armies(self.active_player, self.tilemanager.selected_armies)
            self.set_manuevers(self.manuevers - target_tile.move_cost)
            self.tilemanager.set_selected_armies(0)
            self.tilemanager.reset_movable_tiles(self.tiles)
            self.tilemanager.set_active_tile(None)
            target_tile.continent.set_armies(self.active_player, self.tilemanager.continent_army_count(self.active_player,
                                                                                            target_tile.continent))

    def sail_armies(self, target_tile):
        if target_tile.armies[self.active_player] > 0 and (self.tilemanager.selected_armies == 0 or target_tile.move_cost == 0):
            self.tilemanager.reset_movable_tiles(self.tiles)
            target_tile.remove_army(self.active_player)
            self.tilemanager.set_selected_armies(self.tilemanager.selected_armies + 1)
            self.tilemanager.sailable_tiles(target_tile, self.manuevers, self.manuevers)
            self.tilemanager.set_active_tile(target_tile)
            target_tile.continent.set_armies(self.active_player,
                                             self.tilemanager.continent_army_count(self.active_player,
                                                                                   target_tile.continent))
        elif target_tile.clickable:
            target_tile.add_armies(self.active_player, self.tilemanager.selected_armies)
            self.set_manuevers(self.manuevers - target_tile.move_cost)
            self.tilemanager.set_selected_armies(0)
            self.tilemanager.reset_movable_tiles(self.tiles)
            self.tilemanager.set_active_tile(None)
            target_tile.continent.set_armies(self.active_player,
                                             self.tilemanager.continent_army_count(self.active_player,
                                                                                   target_tile.continent))

    def clickloop(self, clicked_element):
        #self.display_tile_info()
        if isinstance(clicked_element, Card) and self.phase == Phases.PickCard and clicked_element.cost <= self.players[self.active_player].coins:
            self.play_card(clicked_element)
        elif isinstance(clicked_element, Ability) and self.phase == Phases.PickAbilityAND:
            self.pick_ability(clicked_element)
            self.viable_abilities.remove(clicked_element)
        elif isinstance(clicked_element, Ability) and self.phase == Phases.PickAbilityOR:
            self.pick_ability(clicked_element)
            self.viable_abilities = []
        elif isinstance(clicked_element, Tile) and self.phase == Phases.BuildArmy:
            self.build_armies(clicked_element)
        elif isinstance(clicked_element, Tile) and self.phase == Phases.BuildCity:
            self.build_cities(clicked_element)
        elif isinstance(clicked_element, Tile) and self.phase == Phases.MoveArmy:
            self.move_armies(clicked_element)
        elif isinstance(clicked_element, Tile) and self.phase == Phases.DestroyArmy:
            self.destroy_armies(clicked_element)
        elif isinstance(clicked_element, Player) and self.phase == Phases.DestroyArmy:
            self.target_player = clicked_element
        elif isinstance(clicked_element, Tile) and self.phase == Phases.SailArmy:
            self.sail_armies(clicked_element)
        elif isinstance(clicked_element, Good) and self.phase == Phases.JokerAssignment and self.manuevers > 0:
            self.add_good(clicked_element, 1)
            self.set_manuevers(self.manuevers-1)
        self.scoring_handler()

    def end_move_handler(self):
        if self.phase == Phases.JokerAssignment:
            self.next_player()
            if self.active_player == 0:
                self.phase = Phases.EndGame
                self.endgame_handler()
                #print(self.winners)
            elif "Joker" in self.players[self.active_player].goods:
                self.set_manuevers(self.players[self.active_player].goods["Joker"])
            else:
                self.set_manuevers(0)
        elif self.phase != Phases.PickCard:
            self.set_manuevers(0)
            self.tilemanager.reset_armies(self.active_player)
            #self.tilemanager.count_armies(self.active_player, self.tiles)
            self.tilemanager.reset_movable_tiles(self.tiles)
            if self.phase == Phases.PickAbilityOR or self.phase == Phases.PickAbilityAND:
                self.viable_abilities = []
            if len(self.viable_abilities) > 0:
                self.set_phase(Phases.PickAbilityAND)
            else:
                self.set_phase(Phases.PickCard)
                self.next_player()
                self.draw_card()
                self.set_cards_cost()
            if self.active_player == 0:
                self.turn += 1
                if self.turn > self.max_turns:
                    if "Joker" in self.players[self.active_player].goods:
                        self.set_manuevers(self.players[self.active_player].goods["Joker"])
                    else:
                        self.set_manuevers(0)
                    self.phase = Phases.JokerAssignment
        self.thorough_counting()
        self.scoring_handler()

    def score_tile_or_continent(self, tile_or_continet):
        top_player_index = 0
        most_armies_and_cities = tile_or_continet.armies[0] + tile_or_continet.cities[0]
        for player_index in range(len(self.players)):
            if tile_or_continet.armies[player_index] + tile_or_continet.cities[player_index] > most_armies_and_cities:
                top_player_index = player_index
                most_armies_and_cities = tile_or_continet.armies[player_index] + tile_or_continet.cities[player_index]
        for player_index in range(len(self.players)):
            if player_index != top_player_index and most_armies_and_cities == tile_or_continet.armies[player_index] + tile_or_continet.cities[player_index]:
                return None
        return top_player_index

    def scoring_handler(self):
        for player in self.players:
            player.score = 0
        for row in self.tiles:
            for tile in row:
                tile_scoring = self.score_tile_or_continent(tile)
                if tile_scoring is not None:
                    self.players[tile_scoring].score += 1
        for continent in self.continents:
            continent_scoring = self.score_tile_or_continent(self.continents[continent])
            if continent_scoring is not None:
                self.players[continent_scoring].score += 1
        self.goods_scoring()

    def goods_scoring(self):
        for player in self.players:
            for player_good in player.goods:
                for object_good in self.deck.goods:
                    if player_good == object_good:
                        if player.goods[player_good] >= self.deck.goods[object_good].score1:
                            player.score += 1
                        if player.goods[player_good] >= self.deck.goods[object_good].score2:
                            player.score += 1
                        if player.goods[player_good] >= self.deck.goods[object_good].score3:
                            player.score += 1
                        if player.goods[player_good] >= self.deck.goods[object_good].score5:
                            player.score += 2

    def endgame_handler(self):
        # Determining the player(s) with the top score
        top_score = max(player.score for player in self.players)
        self.winners = [player for player in self.players if player.score == top_score]

        # If there's a tie on score, check for top coins
        if len(self.winners) > 1:
            top_coins = max(player.coins for player in self.winners)
            # Retain only the players with the top coins count among the tied players
            self.winners = [player for player in self.winners if player.coins == top_coins]

        # If there's still a tie, check for top armies
        if len(self.winners) > 1:
            top_armies = max(player.armies for player in self.winners)
            # Retain only the players with the top armies count among the tied players
            self.winners = [player for player in self.winners if player.armies == top_armies]

        return self.winners

    def prepare_deck_cards(self):
        self.deck_cards += self.deck.default_deck
        if len(players) > 5:
            self.deck_cards += self.deck.bonus_deck

    def draw_card(self):
        drawn_card = random.choice(self.deck_cards)
        self.active_cards.append(drawn_card)
        self.deck_cards.remove(drawn_card)

class AI_manager:
    def __init__(self, sim_length):
        self.real_options = []
        self.sim_options = []
        self.sim_instruction = []
        self.real_instruction = []
        self.weights = []
        self.sim_length = sim_length

    def pass_real_instruction(self):
        instruction = self.real_instruction[0]
        self.real_instruction.pop(0)
        return instruction

    def pass_sim_instruction(self):
        instruction = self.sim_instruction[0]
        self.sim_instruction.pop(0)
        return instruction

    def create_options(self, used_game):
        options = []
        phase = used_game.phase
        active_player = used_game.players[used_game.active_player]
        if phase == Phases.PickCard:
            options = self.CardOptions(used_game)
        elif phase == Phases.PickAbilityOR or phase == Phases.PickAbilityAND:
            options = used_game.viable_abilities
        elif phase == Phases.BuildArmy and used_game.manuevers and active_player.armies < used_game.max_armies:
            options = self.ArmyBuildingOptions(used_game)
        elif phase == Phases.BuildCity and used_game.manuevers and active_player.cities < used_game.max_cities:
            options = self.CityBuildingOptions(used_game)
        elif (phase == Phases.MoveArmy or phase == Phases.SailArmy) and used_game.manuevers:
            options = self.MovingOptions(used_game)
        elif phase == Phases.DestroyArmy and used_game.manuevers:
            options = self.DestroyOptions(used_game)
        elif phase == Phases.JokerAssignment and used_game.manuevers:
            options = list(used_game.deck.goods.values())
        else:
            options.append(None)
        return options

    def CardOptions(self, used_game):
        options = []
        active_player = used_game.players[used_game.active_player]

        for card in used_game.active_cards:
            if card.cost <= active_player.coins:
                options.append(card)

        return options

    def ArmyBuildingOptions(self, used_game):
        options = []
        for row in used_game.tiles:
            for tile in row:
                if tile.cities[used_game.active_player] > 0 or tile.is_starting_tile:
                    options.append(tile)
        #options.append(None)
        return options

    def CityBuildingOptions(self, used_game):
        options = []
        for row in used_game.tiles:
            for tile in row:
                if tile.armies[used_game.active_player] > 0:
                    options.append(tile)
        #options.append(None)
        return options

    def MovingOptions(self, used_game):
        options = []
        for row in used_game.tiles:
            for tile in row:
                if tile.armies[used_game.active_player] > 0:
                    for neighbour in tile.neighbours:
                        if neighbour.tile_type == "ground":
                            options.append([tile, neighbour])
                        elif used_game.phase == Phases.SailArmy and neighbour.tile_type == "water":
                            for water_neighbour in neighbour.neighbours:
                                if water_neighbour.tile_type == "ground" and water_neighbour != tile:
                                    options.append([tile, water_neighbour])
        options.append(None)
        return options

    def DestroyOptions(self, used_game):
        options = []
        players = used_game.players.copy()
        players.pop(used_game.active_player)
        for player in players:
            for row in used_game.tiles:
                for tile in row:
                    if tile.armies[players.index(player)] > 0:
                        options.append([player, tile])
        options.append(None)
        return options

    def pick_random_instruction(self, options):
        if isinstance(options, dict):
            keys = list(options.keys())
            random_key = random.choice(keys)
            instruction = options[random_key]
        else:
            instruction = random.choice(options)
        return instruction

    def pick_best_instruction(self, options, weights):
        if isinstance(options, dict):
            keys = list(options.keys())
            random_key = random.choice(keys)
            instruction = options[random_key]
        else:
            return options[weights.index(max(weights))]
        return instruction

    def AI_loop(self, thegame):
        if len(self.real_instruction) < 1:
            self.real_options = self.create_options(thegame)
            print(thegame.phase)
            print("OPTIONS")
            print(self.real_options)
            self.weights = []
            print(self.weights)
            for i in range(len(self.real_options)):
                self.weights.append(0)
            for option in self.real_options:
                for i in range(self.sim_length):
                    self.weights[self.real_options.index(option)] += self.SimulateGame(thegame, option)
            instruction = self.pick_best_instruction(self.real_options, self.weights)
            if isinstance(instruction, list):
                self.real_instruction = instruction
            else:
                self.real_instruction.append(instruction)
            print("INSTRUCTION")
            print(self.weights)
            print(self.real_instruction)
        elif self.real_instruction[0] == None:
                thegame.end_move_handler()
                self.pass_real_instruction()
                print(self.real_instruction)
        else:
            thegame.clickloop(self.pass_real_instruction())
            print("OPTIONS")
            print(self.real_options)
            print("INSTRUCTION")
            print(self.real_instruction)

    def SimulateGame(self, thegame, initial_instruction):
        sim = thegame.clone_game()
        actual_initial_instruction = []
        if isinstance(initial_instruction, Card):
            actual_initial_instruction.append(sim.active_cards[thegame.active_cards.index(initial_instruction)])
        elif isinstance(initial_instruction, list) and thegame.phase == Phases.DestroyArmy:
            actual_initial_instruction.append(initial_instruction[0])
            actual_initial_instruction.append(sim.tiles[initial_instruction[1].tile_x][initial_instruction[1].tile_y])
        elif isinstance(initial_instruction, list):
            actual_initial_instruction.append(sim.tiles[initial_instruction[0].tile_x][initial_instruction[0].tile_y])
            actual_initial_instruction.append(sim.tiles[initial_instruction[1].tile_x][initial_instruction[1].tile_y])
        elif isinstance(initial_instruction, Tile):
            actual_initial_instruction.append(sim.tiles[initial_instruction.tile_x][initial_instruction.tile_y])
        else:
            actual_initial_instruction.append(initial_instruction)

        self.sim_instruction = actual_initial_instruction
        print(f"SIM_LOOP: {actual_initial_instruction}")

        while sim.phase != Phases.EndGame:
            if len(self.sim_instruction) < 1:
                self.sim_options = self.create_options(sim)
                instruction = self.pick_random_instruction(self.sim_options)
                if isinstance(instruction, list):
                    self.sim_instruction = instruction
                else:
                    self.sim_instruction.append(instruction)
            elif self.sim_instruction[0] == None:
                sim.end_move_handler()
                self.pass_sim_instruction()
            else:
                sim.clickloop(self.pass_sim_instruction())
        if sim.players[thegame.active_player] not in sim.winners:
            return 0
        elif len(sim.winners) == 1:
            return 2 * sim.players[thegame.active_player].score
        else:
            return 1 * sim.players[thegame.active_player].score

#Graphics
class GraphicManager:
    def __init__(self, screen_width, screen_height, colors, game):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        self.colors = colors
        self.game = game
        self.tile_margin = 5
        self.tile_size = 100
        self.tile_graphics = []
        self.prepare_tile_graphics()
        num_columns = len(self.game.tiles[0])
        num_rows = len(self.game.tiles)
        board_width = num_columns * self.tile_size + (num_columns + 1) * self.tile_margin
        board_height = num_rows * self.tile_size + (num_columns + 1) * self.tile_margin
        self.side_menu_x = board_width + 10
        self.side_menu_y_start = 10
        self.side_menu_spacing = 30
        self.side_menu_elements = []
        self.player_list_x = 10
        self.player_list_spacing = 30
        self.player_list_y_start = board_height + 10
        self.player_list_elements = []
        self.prepare_side_menu_elements()
        self.prepare_player_list()
        self.good_list = Good_Scoring(self.game.deck.goods, self)
        self.mouse_pos = pygame.mouse.get_pos()
        self.clicked_pos = None

    def prepare_tile_graphics(self):
        for row_index, row in enumerate(self.game.tiles):
            tile_graphics_row = []
            for col_index, tile in enumerate(row):
                x = col_index * (self.tile_size + self.tile_margin)
                y = row_index * (self.tile_size + self.tile_margin)
                tile_graphic = Tile_Graphic(self.tile_size, x, y, tile, self)
                tile_graphics_row.append(tile_graphic)
            self.tile_graphics.append(tile_graphics_row)

    def draw_board(self):
        for row in self.tile_graphics:
            for tile_graphic in row:
                tile_graphic.draw()

    def prepare_side_menu_elements(self):
        self.side_menu_elements = [Side_Menu_Title(self.side_menu_y_start, self)]

        if self.game.phase == Phases.JokerAssignment:
            for good in self.game.deck.goods:
                self.side_menu_elements.append(
                    JokerAssignmentButton(self.side_menu_y_start + len(self.side_menu_elements) * self.side_menu_spacing, self.game.deck.goods[good], self))
        if self.game.phase == Phases.PickCard:
            for card in self.game.active_cards:
                self.side_menu_elements.append(Card_Button(self.side_menu_y_start + len(self.side_menu_elements) * self.side_menu_spacing, card, self))
        if self.game.phase == Phases.PickAbilityAND or self.game.phase == Phases.PickAbilityOR:
            for ability in self.game.viable_abilities:
                self.side_menu_elements.append(Ability_Button(self.side_menu_y_start + len(self.side_menu_elements) * self.side_menu_spacing, ability, self))
        if self.game.phase == Phases.DestroyArmy and self.game.manuevers > 0:
            viable_players = []
            viable_players += self.game.players
            viable_players.remove(self.game.players[self.game.active_player])
            for target in viable_players:
                self.side_menu_elements.append(Target_Button(self.side_menu_y_start + len(self.side_menu_elements) * self.side_menu_spacing, target, self))

    def draw_side_menu(self):
        for element in self.side_menu_elements:
            element.draw()

    def prepare_player_list(self):
        self.player_list_elements = []
        for player in self.game.players:
            self.player_list_elements.append(Player_List_Element(self.player_list_y_start + len(self.player_list_elements) * self.player_list_spacing, player, self))

    def draw_player_list(self):
        for element in self.player_list_elements:
            element.draw()

    def graphics(self):
        self.screen.fill(self.colors.get('background', (0, 0, 0)))
        self.mouse_pos = pygame.mouse.get_pos()
        self.draw_board()
        self.draw_side_menu()
        self.draw_player_list()
        self.good_list.draw()
        pygame.display.flip()

    def click_handler(self):
        self.clicked_pos = self.mouse_pos
        clickable_elements = self.side_menu_elements + [tile_graphic for row in self.tile_graphics for tile_graphic in row]
        for element in clickable_elements:
            if isinstance(element, Clickable_Element) and element.clicked():
                return getattr(element, 'card', None) or getattr(element, 'tile', None) or getattr(element, 'ability', None) or getattr(element,'player',None) or getattr(element,'good',None)

class Clickable_Element:
    def __init__(self, graphic_manager):
        self.graphic_manager = graphic_manager
        self.rect = None

    def clicked(self):
        if self.rect.collidepoint(self.graphic_manager.clicked_pos):
            return True

class Tile_Graphic(Clickable_Element):
    def __init__(self, tile_size, x, y, tile, graphic_manager):
        super().__init__(graphic_manager)
        self.tile_size = tile_size
        self.x = x
        self.y = y
        self.tile = tile
        self.font = pygame.font.Font(None, int(self.tile_size/4))
        self.rect = pygame.Rect(self.x, self.y, self.tile_size, self.tile_size)

    def draw(self):
        if self.tile.clickable:
            pygame.draw.rect(self.graphic_manager.screen, self.graphic_manager.colors["clickable_tile"], self.rect)
        elif self.tile.tile_type == "water":
            pygame.draw.rect(self.graphic_manager.screen, self.graphic_manager.colors["water_tile"], self.rect)
        elif self.tile.tile_type == "ground":
            pygame.draw.rect(self.graphic_manager.screen, self.graphic_manager.colors["ground_tile"], self.rect)
        if self.tile.is_starting_tile:
            text_surface = self.font.render('S', True, self.graphic_manager.colors["text_default"])
            text_x = self.x + (self.tile_size - text_surface.get_width()) / 2
            text_y = self.y + (self.tile_size - text_surface.get_height()) / 2
            self.graphic_manager.screen.blit(text_surface, (text_x, text_y))
        for player_index, armies in enumerate(self.tile.armies):
            if armies > 0:
                player_color = self.graphic_manager.game.players[player_index].color
                army_text = self.font.render(str(armies), True, self.graphic_manager.colors[player_color])
                army_text_x = + self.x + (player_index * (self.tile_size / 5)) + int(self.tile_size/20)
                army_text_y = self.y + self.tile_size - self.font.get_height() - 5
                self.graphic_manager.screen.blit(army_text, (army_text_x, army_text_y))
        for player_index, cities in enumerate(self.tile.cities):
            if cities > 0:
                player_color = self.graphic_manager.game.players[player_index].color
                city_text = self.font.render(str(cities), True, self.graphic_manager.colors[player_color])
                city_text_x = self.x + (player_index * (self.tile_size / 5)) + int(self.tile_size/20)
                city_text_y = self.y + 5
                self.graphic_manager.screen.blit(city_text, (city_text_x, city_text_y))

class Card_Button(Clickable_Element):
    def __init__(self, y, card, graphic_manager):
        super().__init__(graphic_manager)
        self.y = y
        self.card = card
        # self.graphic_manager.side_menu_font
        self.font = pygame.font.Font(None, 24)
        self.rect = None
        self.text_color = "text_default"

    def draw(self):
        ability_descriptions = [ability.ability_description for ability in self.card.abilities]
        abilities_text = ' AND '.join(ability_descriptions) if not self.card.isor else ' OR '.join(ability_descriptions)
        card_text = f"Cost {self.card.cost}: {self.card.quantity}x {self.card.good} - {abilities_text}"

        text_surface = self.font.render(card_text, True, self.graphic_manager.colors[self.text_color])
        self.rect = text_surface.get_rect(x=self.graphic_manager.side_menu_x, y=self.y)

        if self.rect.collidepoint(self.graphic_manager.mouse_pos):
            self.text_color = "text_highlighted"
        else:
            self.text_color = "text_default"

        self.graphic_manager.screen.blit(text_surface, (self.graphic_manager.side_menu_x, self.y))

class Ability_Button(Clickable_Element):
    def __init__(self, y, ability, graphic_manager):
        super().__init__(graphic_manager)
        self.y = y
        self.ability = ability
        # self.graphic_manager.side_menu_font
        self.font = pygame.font.Font(None, 24)
        self.rect = None
        self.text_color = "text_default"

    def draw(self):
        text_surface = self.font.render(self.ability.ability_description, True, self.graphic_manager.colors[self.text_color])
        self.rect = text_surface.get_rect(x=self.graphic_manager.side_menu_x, y=self.y)
        if self.rect.collidepoint(self.graphic_manager.mouse_pos):
            self.text_color = "text_highlighted"
        else:
            self.text_color = "text_default"

        self.graphic_manager.screen.blit(text_surface, (self.graphic_manager.side_menu_x, self.y))

class JokerAssignmentButton(Clickable_Element):
    def __init__(self, y, good, graphic_manager):
        super().__init__(graphic_manager)
        self.y = y
        self.good = good
        # self.graphic_manager.side_menu_font
        self.font = pygame.font.Font(None, 24)
        self.rect = None
        self.text_color = "text_default"

    def draw(self):
        text_surface = self.font.render(self.good.name, True, self.graphic_manager.colors[self.text_color])
        self.rect = text_surface.get_rect(x=self.graphic_manager.side_menu_x, y=self.y)
        if self.rect.collidepoint(self.graphic_manager.mouse_pos):
            self.text_color = "text_highlighted"
        else:
            self.text_color = "text_default"

        self.graphic_manager.screen.blit(text_surface, (self.graphic_manager.side_menu_x, self.y))

class Target_Button(Clickable_Element):
    def __init__(self, y, player, graphic_manager):
        super().__init__(graphic_manager)
        self.y = y
        self.player = player
        # self.graphic_manager.side_menu_font
        self.font = pygame.font.Font(None, 24)
        self.rect = None
        self.text_color = "text_default"

    def draw(self):
        text_surface = self.font.render(self.player.name, True, self.graphic_manager.colors[self.text_color])
        self.rect = text_surface.get_rect(x=self.graphic_manager.side_menu_x, y=self.y)
        if self.rect.collidepoint(self.graphic_manager.mouse_pos):
            self.text_color = "text_highlighted"
        else:
            self.text_color = self.player.color

        self.graphic_manager.screen.blit(text_surface, (self.graphic_manager.side_menu_x, self.y))

class Side_Menu_Title:
    def __init__(self, y, graphic_manager):
        self.y = y
        self.graphic_manager = graphic_manager
        # self.graphic_manager.side_menu_font
        self.font = pygame.font.Font(None, 24)

    def draw(self):
        winners = self.graphic_manager.game.winners
        if self.graphic_manager.game.phase == Phases.EndGame:
            if len(winners) > 1:
                text = f"DRAW!"
                for winner in winners:
                    text += f" {winner.name}"
                player_color = "text_default"
            else:
                text = f"WINNER: {winners[0].name}"
                player_color = self.graphic_manager.game.winners[0].color
        else:
            player_color = self.graphic_manager.game.players[self.graphic_manager.game.active_player].color
            player_name = self.graphic_manager.game.players[self.graphic_manager.game.active_player].name
            player_coins = self.graphic_manager.game.players[self.graphic_manager.game.active_player].coins
            text = f"{player_name} - Turn {self.graphic_manager.game.turn}/{self.graphic_manager.game.max_turns} - {self.graphic_manager.game.phase.name}"
            if self.graphic_manager.game.phase == Phases.PickCard:
                text += f" - {player_coins} Coins"
            elif self.graphic_manager.game.manuevers > 0:
                text +=f"({self.graphic_manager.game.manuevers})"
                if self.graphic_manager.game.phase == Phases.DestroyArmy:
                    text +=f" (Target {self.graphic_manager.game.target_player.name})"
        text_surface = self.font.render(text, True, self.graphic_manager.colors[player_color])
        self.graphic_manager.screen.blit(text_surface, (self.graphic_manager.side_menu_x, self.y))

class Player_List_Element:
    def __init__(self, y, player, graphic_manager):
        self.y = y
        self.player = player
        self.graphic_manager = graphic_manager
        # self.graphic_manager.side_menu_font
        self.font = pygame.font.Font(None, 24)

    def draw(self):
        text = f"{self.player.name} ({self.player.coins} Coins) ({self.player.armies}/{self.graphic_manager.game.max_armies} Armies) ({self.player.cities}/{self.graphic_manager.game.max_cities} Cities) ({self.player.score} Score) "
        for good in self.player.goods:
            text += str(self.player.goods[good]) + "x" + good + "; "
            
        text_surface = self.font.render(text, True, self.graphic_manager.colors[self.player.color])
        self.graphic_manager.screen.blit(text_surface, (self.graphic_manager.player_list_x, self.y))

class Good_Scoring:
    def __init__(self, goods, graphic_manager):
        self.graphic_manager = graphic_manager
        self.goods = goods
        self.font = pygame.font.Font(None, 24)
        self.right_margin = 10
        self.good_scoring_spacing = 20

    def draw(self):
        total_goods = len(self.goods)
        start_y = self.graphic_manager.screen_height - (total_goods * self.good_scoring_spacing + self.right_margin)
        for index, good in enumerate(self.goods):  # Iterating directly without sorting
            text = f"{good}: {self.goods[good].score1}, {self.goods[good].score2}, {self.goods[good].score3}, {self.goods[good].score5}"
            text_surface = self.font.render(text, True, self.graphic_manager.colors["text_default"])
            text_width = text_surface.get_width()
            x_position = self.graphic_manager.screen_width - text_width - self.right_margin
            y_position = start_y + (index * self.good_scoring_spacing)
            self.graphic_manager.screen.blit(text_surface, (x_position, y_position))

            if y_position + self.good_scoring_spacing > self.graphic_manager.screen_height:
                break





#GameSetup
board_layout = [
    "WGGWG",
    "WGGWG",
    "WWSWG",
    "GWGWW",
    "GWGWW"
]

players = []
players.append(Player("Player",False,"player_red"))
players.append(Player("AI2",True,"player_blue"))
random.shuffle(players)

defualtcards = []
bonuscards = []
default_goods = {
    "Food" : Good("Food", [3,5,7,8]),
    "Wood" : Good("Wood", [2,4,5,6]),
    "Coal" : Good("Coal", [2,3,4,5]),
    "Gem"  : Good("Gem", [1,2,3,4]),
    "Iron" : Good("Iron", [2,4,6,7])
}
ABILITIES = {
    "city" :  BuildCities(1),
    "armies1" : BuildArmies(1),
    "armies2" : BuildArmies(2),
    "armies3" : BuildArmies(3),
    "armies4" : BuildArmies(4),
    "move2" : MoveArmies(2),
    "move3" : MoveArmies(3),
    "move4" : MoveArmies(4),
    "move5" : MoveArmies(5),
    "move6" : MoveArmies(6),
    "sail2" : SailArmies(2),
    "sail3" : SailArmies(3),
    "sail4" : SailArmies(4),
    "destroy" : DestroyArmies(1)
}


#Woodcards
defualtcards.append(Card([ABILITIES["city"]], "Wood", 1, False))
defualtcards.append(Card([ABILITIES["armies3"]], "Wood", 1, False))
defualtcards.append(Card([ABILITIES["move3"]], "Wood", 1, False))
defualtcards.append(Card([ABILITIES["sail3"]], "Wood", 1, False))
defualtcards.append(Card([ABILITIES["sail4"]], "Wood", 1, False))
defualtcards.append(Card([ABILITIES["armies2"], ABILITIES["sail3"]], "Wood", 1, True))
defualtcards.append(Card([ABILITIES["destroy"], ABILITIES["city"]], "Wood", 1, True))
bonuscards.append(Card([ABILITIES["move6"]], "Wood", 1, False))

#Coalcards
defualtcards.append(Card([ABILITIES["armies2"]], "Coal", 1, False))
defualtcards.append(Card([ABILITIES["move2"]], "Coal", 1, False))
defualtcards.append(Card([ABILITIES["move3"]], "Coal", 1, False))
defualtcards.append(Card([ABILITIES["move3"]], "Coal", 1, False))
defualtcards.append(Card([ABILITIES["sail2"]], "Coal", 1, False))
defualtcards.append(Card([ABILITIES["sail3"]], "Coal", 1, False))
bonuscards.append(Card([ABILITIES["sail2"]], "Coal", 1, False))

#Foodcards
defualtcards.append(Card([ABILITIES["city"]], "Food", 1, False))
defualtcards.append(Card([ABILITIES["city"]], "Food", 1, False))
defualtcards.append(Card([ABILITIES["armies3"]], "Food", 1, False))
defualtcards.append(Card([ABILITIES["armies3"]], "Food", 2, False))
defualtcards.append(Card([ABILITIES["move4"]], "Food", 1, False))
defualtcards.append(Card([ABILITIES["move4"]], "Food", 1, False))
defualtcards.append(Card([ABILITIES["move5"]], "Food", 1, False))
defualtcards.append(Card([ABILITIES["sail3"]], "Food", 1, False))
defualtcards.append(Card([ABILITIES["destroy"], ABILITIES["armies1"]], "Food", 1, False))
bonuscards.append(Card([ABILITIES["armies4"], ABILITIES["move2"]], "Food", 1, True))

#Gemcards
defualtcards.append(Card([ABILITIES["armies1"]], "Gem", 1, False))
defualtcards.append(Card([ABILITIES["armies2"]], "Gem", 1, False))
defualtcards.append(Card([ABILITIES["armies2"]], "Gem", 1, False))
defualtcards.append(Card([ABILITIES["move2"]], "Gem", 1, False))
bonuscards.append(Card([ABILITIES["armies2"]], "Gem", 1, False))

#Ironcards
defualtcards.append(Card([ABILITIES["city"]], "Iron", 1, False))
defualtcards.append(Card([ABILITIES["armies3"]], "Iron", 1, False))
defualtcards.append(Card([ABILITIES["armies3"]], "Iron", 1, False))
defualtcards.append(Card([ABILITIES["move4"]], "Iron", 1, False))
defualtcards.append(Card([ABILITIES["move5"]], "Iron", 1, False))
defualtcards.append(Card([ABILITIES["sail3"]], "Iron", 1, False))
defualtcards.append(Card([ABILITIES["armies3"], ABILITIES["move3"]], "Iron", 1, True))
defualtcards.append(Card([ABILITIES["armies3"], ABILITIES["move4"]], "Iron", 1, True))
bonuscards.append(Card([ABILITIES["move4"]], "Iron", 2, False))

#Jokers
defualtcards.append(Card([ABILITIES["armies2"]], "Joker", 1, False))
defualtcards.append(Card([ABILITIES["sail2"]], "Joker", 1, False))
defualtcards.append(Card([ABILITIES["sail2"]], "Joker", 1, False))

TheTileManager = TileManager()

TheAIManager = AI_manager(200)
TheDeck = Deck(default_goods, defualtcards, bonuscards)
TheGame = Game(TheDeck, board_layout, players, TheTileManager, STARTING_ARMIES, MAX_ARMIES, MAX_CITIES)
TheGame.initialize_game()
TheGraphicManager = GraphicManager(SCREEN_WIDTH, SCREEN_HEIGHT, COLORS, TheGame)
#TheGame.display_tile_info()

if TheGame.players[TheGame.active_player].AI:
    pygame.time.set_timer(AI_ACTION_EVENT, 1500)

running = True
while running:
    TheGraphicManager.graphics()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if TheGame.phase != Phases.EndGame:
            if event.type == AI_ACTION_EVENT and TheGame.players[TheGame.active_player].AI:
                TheAIManager.AI_loop(TheGame)
                TheGraphicManager.prepare_side_menu_elements()
            elif event.type == pygame.MOUSEBUTTONDOWN and TheGame.players[TheGame.active_player].AI == False:
                TheGame.clickloop(TheGraphicManager.click_handler())
                TheGraphicManager.prepare_side_menu_elements()
            elif event.type == pygame.KEYDOWN and TheGame.players[TheGame.active_player].AI == False:
                if event.key == pygame.K_SPACE:
                    TheGame.end_move_handler()
                    TheGraphicManager.prepare_side_menu_elements()
            if TheGame.players[TheGame.active_player].AI:
                pygame.time.set_timer(AI_ACTION_EVENT, 500)
            else:
                pygame.time.set_timer(AI_ACTION_EVENT, 0)

# Quit Pygame
pygame.quit()
sys.exit()