import random
from enum import Enum
import pygame
import sys

# Initialize Pygame
pygame.init()
pygame.font.init()

#Globální proměnné
FONT = pygame.font.Font(None, 24)
MARGIN = 2
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
COLORS = {
    "dark_blue" : (0, 0, 139),
    "dark_green" : (0, 100, 0),
    "light_green" : (0, 150, 0),
    "white" : (255, 255, 255),
    "yellow" : (250, 250, 0),
    "player_red" : (255, 0, 0),
    "player_green" : (0, 255, 0),
    "player_blue" : (0, 0, 255),
    "player_yellow" : (255, 255, 0),
    "player_orange" : (255, 165, 0)
}
STARTING_ARMIES = 3

# Player colors
player_colors = [
    (255, 0, 0),  # Player 1: Red
    (0, 255, 0),  # Player 2: Green
    (0, 0, 255),  # Player 3: Blue
    (255, 255, 0),  # Player 4: Yellow
    (255, 165, 0),  # Player 5: Orange
]

#Enums
class Phases(Enum):
    PickCard = 0
    PickAbilityAND = 1
    PickAbilityOR = 2
    BuildArmy = 3
    BuildCity = 4
    MoveArmy = 5
    DestroyArmy = 5
    SailArmy = 7

#Card
class Card:
    def __init__(self, abilities, good, quantity, isor):
        self.abilities = abilities
        self.good = good
        self.quantity = quantity
        self.isor = isor

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

#Continents
class Continent:
    def __init__(self, continent_id, name):
        self.continent_id = continent_id
        self.name = name
        self.tiles = []

    def add_tile(self, tile):
        self.tiles.append(tile)
        tile.continent = self

#Tiles
class Tile:
    def __init__(self, tile_id, tile_type):
        self.tile_id = tile_id
        self.continent = None
        self.tile_type = tile_type
        self.armies = [0, 0, 0, 0, 0]
        self.cities = [0, 0, 0, 0, 0]
        self.neighbours = []
        self.is_starting_tile = False
        self.movable = False
        self.move_cost = -1

    def make_starting_tile(self):
        if self.tile_type == "ground":
            self.is_starting_tile = True
        else:
            print("Error: Starting tiles must be ground tiles.")

    def add_neighbour(self, neighbour):
        if neighbour not in self.neighbours:
            self.neighbours.append(neighbour)
            neighbour.neighbours.append(self)  # Ensure the relationship is bidirectional

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

    def set_movable(self):
        self.movable = True

    def set_nonmovable(self):
        self.movable = False

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

    def count_cities(self, player_index, tiles):
        citycount = 0
        for row in tiles:
            for tile in row:
                citycount += tile.cities[player_index]
        return citycount

    def movable_tiles(self, target_tile, reserve, original):
        target_tile.movable = True
        target_tile.set_movecost(original - reserve)
        reserve = reserve - self.selected_armies
        if(reserve >= 0):
            for neihgbour in target_tile.neighbours:
                if not(neihgbour.movable) and not(neihgbour.tile_type == "water"):
                    self.movable_tiles(neihgbour, reserve, original)

    def sailable_tiles(self, target_tile, reserve, original):
        if target_tile.tile_type == "ground":
            target_tile.movable = True
            target_tile.set_movecost(original - reserve)
            reserve = reserve - self.selected_armies
            if (reserve >= 0):
                for neihgbour in target_tile.neighbours:
                    if not (neihgbour.movable):
                        self.sailable_tiles(neihgbour, reserve, original)
        else:
            for neihgbour in target_tile.neighbours:
                if not(neihgbour.movable) and not(neihgbour.tile_type == "water"):
                    self.sailable_tiles(neihgbour, reserve, original)



    def reset_movable_tiles(self, tiles):
        for row in tiles:
            for tile in row:
                tile.set_nonmovable()
                tile.move_cost = -1

#Player
class Player:
    def __init__(self, AI, color):
        self.armies = 3
        self.cities = 0
        self.AI = AI
        self.color = color
        self.goods = {}

#Game
class Game:
    def __init__(self, layout, players, tilemanager, starting_armies):
        self.players = players
        self.active_player = 0
        self.tiles = []
        self.active_cards = []
        self.played_card = None
        self.continents = {}
        self.board_layout = layout
        self.create_board()
        self.set_up_starting_armies(starting_armies)
        self.phase = Phases.PickCard
        self.tilemanager = tilemanager
        self.manuevers = 0
        self.abilities_to_select = {}

    def create_board(self):
        continent_counter = 0

        for row_index, row in enumerate(self.board_layout):
            tile_row = []
            for col_index, col in enumerate(row):
                tile_type = 'water' if col == 'W' else 'ground'
                tile_id = f"T{row_index}_{col_index}"
                tile = Tile(tile_id, tile_type)
                if col == 'S':
                    tile.make_starting_tile()
                tile_row.append(tile)
            self.tiles.append(tile_row)

        def add_neighbors():
            for i in range(len(self.tiles)):
                for j in range(len(self.tiles[i])):
                    tile = self.tiles[i][j]
                    if i > 0: tile.add_neighbour(self.tiles[i - 1][j])
                    if i < len(self.tiles) - 1: tile.add_neighbour(self.tiles[i + 1][j])
                    if j > 0: tile.add_neighbour(self.tiles[i][j - 1])
                    if j < len(self.tiles[i]) - 1: tile.add_neighbour(self.tiles[i][j + 1])

        add_neighbors()

        def assign_to_continent(tile):
            nonlocal continent_counter
            if tile.tile_type == 'ground' and tile.continent is None:
                continent_counter += 1
                continent = Continent(f"C{continent_counter}", f"Continent{continent_counter}")
                self.continents[continent.continent_id] = continent
                explore_and_assign(tile, continent)

        def explore_and_assign(tile, continent):
            if tile.tile_type == 'ground' and tile.continent is None:
                continent.add_tile(tile)
                for neighbour in tile.neighbours:
                    explore_and_assign(neighbour, continent)

        for row in self.tiles:
            for tile in row:
                assign_to_continent(tile)

    def display_tile_info(self):
        for row in self.tiles:
            for tile in row:
                continent_id = tile.continent.continent_id if tile.continent else 'None'
                print(f"Tile ID: {tile.tile_id}, Continent: {continent_id}, Type: {tile.tile_type}")

    def set_phase(self, phase):
        self.phase = phase

    def set_active_cards(self, cards):
        self.active_cards = cards

    def play_card(self, played_card):
        if len(played_card.abilities) > 1:
            if played_card.isor:
                self.set_phase(Phases.PickAbilityOR)
            else:
                self.set_phase(Phases.PickAbilityAND)
        else:
            self.pick_ability(played_card.abilities[0])
        self.active_cards.remove(played_card)

    def pick_ability(self, picked_ability):
        self.set_manuevers(picked_ability.manuevers)
        if isinstance(picked_ability, BuildArmies):
            self.set_phase(Phases.BuildArmy)
            print("test1")
        elif isinstance(picked_ability, BuildCities):
            self.set_phase(Phases.BuildCity)
        elif isinstance(picked_ability, MoveArmies):
            self.set_phase(Phases.MoveArmy)
        elif isinstance(picked_ability, DestroyArmies):
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

    def build_armies(self, target_tile):
        if isinstance(target_tile, Tile) and (target_tile.is_starting_tile or target_tile.cities[self.active_player] > 0) and self.players[self.active_player].armies < 14 and self.manuevers > 0:
            target_tile.add_army(self.active_player)
            players[self.active_player].armies = self.tilemanager.count_armies(self.active_player, self.tiles)
            TheGame.set_manuevers(self.manuevers - 1)

    def build_cities(self, target_tile):
        if isinstance(target_tile, Tile) and target_tile.armies[self.active_player] > 0 and self.players[self.active_player].cities < 3 and self.manuevers > 0:
            target_tile.add_city(self.active_player)
            players[self.active_player].cities = self.tilemanager.count_cities(self.active_player, self.tiles)
            TheGame.set_manuevers(self.manuevers-1)

    def move_armies(self, target_tile):
        if isinstance(target_tile, Tile) and target_tile.armies[self.active_player] > 0 and (self.tilemanager.selected_armies == 0 or target_tile.move_cost == 0):
            self.tilemanager.reset_movable_tiles(self.tiles)
            target_tile.remove_army(self.active_player)
            self.tilemanager.set_selected_armies(self.tilemanager.selected_armies + 1)
            self.tilemanager.movable_tiles(target_tile, self.manuevers, self.manuevers)
            self.tilemanager.set_active_tile(target_tile)
        elif isinstance(target_tile, Tile) and target_tile.movable:
            target_tile.add_armies(self.active_player, self.tilemanager.selected_armies)
            self.set_manuevers(self.manuevers - target_tile.move_cost)
            self.tilemanager.set_selected_armies(0)
            self.tilemanager.reset_movable_tiles(self.tiles)
            self.tilemanager.set_active_tile(None)

    def sail_armies(self, target_tile):
        if isinstance(target_tile, Tile) and target_tile.armies[self.active_player] > 0 and (self.tilemanager.selected_armies == 0 or target_tile.move_cost == 0):
            self.tilemanager.reset_movable_tiles(self.tiles)
            target_tile.remove_army(self.active_player)
            self.tilemanager.set_selected_armies(self.tilemanager.selected_armies + 1)
            self.tilemanager.sailable_tiles(target_tile, self.manuevers, self.manuevers)
            self.tilemanager.set_active_tile(target_tile)
        elif isinstance(target_tile, Tile) and target_tile.movable:
            target_tile.add_armies(self.active_player, self.tilemanager.selected_armies)
            self.set_manuevers(self.manuevers - target_tile.move_cost)
            self.tilemanager.set_selected_armies(0)
            self.tilemanager.reset_movable_tiles(self.tiles)
            self.tilemanager.set_active_tile(None)

    def gameloop(self, graphicmanager):
        if event.type == pygame.MOUSEBUTTONDOWN:
            element_type, element = graphicmanager.get_element()
            if element_type == 'card' and self.phase == Phases.PickCard:
                self.play_card(element)
            elif element_type == 'ability' and self.phase == (Phases.PickAbilityAND or Phases.PickAbilityOR):
                self.pick_ability(element)
            elif element_type == 'tile' and self.phase == Phases.BuildArmy:
                self.build_armies(element)
            elif element_type == 'tile' and self.phase == Phases.BuildCity:
                self.build_cities(element)
            elif element_type == 'tile' and self.phase == Phases.MoveArmy:
                self.move_armies(element)
            elif element_type == 'tile' and self.phase == Phases.SailArmy:
                self.sail_armies(element)


#Graphic manager
class GraphicManager:
    def __init__(self, screen_width, screen_height, colors):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        self.colors = colors
        self.mouse_y = 0
        self.mouse_x = 0
        self.card_info_start_x = 0

        # Update scaling factors based on current screen size
        self.update_scaling_factors()

    def calculate_layout(self):
        # Estimate maximum width required for the board
        board_max_width = self.margin + (self.tile_size + self.margin) * self.board_columns

        # Adjust card information start position based on the board size
        self.card_info_start_x = board_max_width + 10  # Add some buffer space between the board and the card info

        # Ensure card information does not go off screen
        if self.card_info_start_x + 360 > self.screen_width:
            # Adjust the layout dynamically if there is not enough space
            self.tile_size = (self.screen_width - self.margin * (self.board_columns + 1) - 360) / self.board_columns
            self.card_info_start_x = self.screen_width - 350  # Place card info at the right edge

    def update_scaling_factors(self):
        # Base design resolution
        self.base_width = 1920
        self.base_height = 1080

        # Calculate scaling factors
        self.scale_factor_width = self.screen_width / self.base_width
        self.scale_factor_height = self.screen_height / self.base_height

        # Dynamically adjust sizes based on screen size
        self.margin = max(6 * self.scale_factor_width, 1)
        self.tile_size = max(40 * self.scale_factor_width, 20)  # Ensure minimum tile size
        self.font_size = max(int(50 * self.scale_factor_width), 10)  # Ensure minimum font size
        self.font = pygame.font.Font(None, self.font_size)

    def assign_game(self, assigned_game):
        self.active_game = assigned_game
        self.board_rows = len(assigned_game.board_layout)
        self.board_columns = len(assigned_game.board_layout[0])
        self.update_board_tile_size()

    def update_board_tile_size(self):
        # Adjust tile size to fit the board within the screen dynamically
        tile_width = (self.screen_width - self.margin * (self.board_columns + 1)) / self.board_columns
        tile_height = (self.screen_height - self.margin * (self.board_rows + 1)) / self.board_rows
        self.tile_size = min(tile_width, tile_height)

    def get_element(self):
        # First, check if the click is on a tile
        for y, row in enumerate(self.active_game.tiles):
            for x, tile in enumerate(row):
                rect = pygame.Rect(x * (self.tile_size + self.margin) + self.margin,
                                   y * (self.tile_size + self.margin) + self.margin,
                                   self.tile_size, self.tile_size)
                if rect.collidepoint(self.mouse_x, self.mouse_y):
                    return ('tile', tile)

        # Now, check if the click is on a card
        card_info_area_width = 350  # Width of the card info area
        start_x = self.screen_width - card_info_area_width  # Start position for card info
        start_y = 10  # Starting Y position for card info
        card_height = 60  # Adjusted height for cards
        gap_between_cards = 5  # Gap between each card description

        for index, card in enumerate(self.active_game.active_cards):
            card_rect = pygame.Rect(start_x, start_y + (card_height + gap_between_cards) * index,
                                    card_info_area_width - 10, card_height)
            if card_rect.collidepoint(self.mouse_x, self.mouse_y):
                return ('card', card)

        # If the click is neither on a tile nor a card
        return (None, None)

    def graphics(self):
        self.screen.fill(self.colors.get('background', (0, 0, 0)))
        self.calculate_layout()
        self.draw_board()
        self.draw_cards_info()
        pygame.display.flip()

    def draw_board(self):
        for y, row in enumerate(self.active_game.tiles):
            for x, tile in enumerate(row):
                rect = pygame.Rect(x * (self.tile_size + self.margin) + self.margin, y * (self.tile_size + self.margin) + self.margin, self.tile_size, self.tile_size)
                pygame.draw.rect(self.screen, self.colors['dark_blue'] if tile.tile_type == 'water' else self.colors['light_green'] if tile.movable else self.colors['dark_green'], rect)

                city_y = rect.y + 5
                army_y = rect.y + rect.height / 2 + 5

                if tile.is_starting_tile:
                    s_text = self.font.render('S', True, self.colors['white'])
                    s_x = rect.x + (rect.width - s_text.get_width()) / 2
                    s_y = (city_y + army_y) / 2 - s_text.get_height() / 2
                    self.screen.blit(s_text, (s_x, s_y))

                space_per_player = rect.width / 5
                for player_index in range(len(self.active_game.players)):
                    if tile.cities[player_index] > 0:
                        city_text = self.font.render(str(tile.cities[player_index]), True, self.active_game.players[player_index].color)
                        text_x = rect.x + player_index * space_per_player + (space_per_player - city_text.get_width()) / 2
                        self.screen.blit(city_text, (text_x, city_y))
                    if tile.armies[player_index] > 0:
                        army_text = self.font.render(str(tile.armies[player_index]), True, self.active_game.players[player_index].color)
                        text_x = rect.x + player_index * space_per_player + (space_per_player - army_text.get_width()) / 2
                        self.screen.blit(army_text, (text_x, army_y))
        pass

    def draw_cards_info(self):
        card_info_area_width = 350  # Width of the card info area
        start_x = self.screen_width - card_info_area_width  # Adjust to draw on the left side
        start_y = 10  # Start drawing from the top
        card_height = 60  # Increase height for potential multiline text
        gap_between_cards = 5  # Gap between each card description

        # Dynamically adjust font size based on the width of the area
        font_size = int(card_info_area_width / 15)
        local_font = pygame.font.Font(None, font_size)

        if self.active_game.phase == Phases.PickCard:
            for index, card in enumerate(self.active_game.active_cards):
                # Construct card description
                abilities_text = [ability.ability_description for ability in card.abilities]

                if card.isor:
                    abilities_description = " or ".join(abilities_text)
                else:
                    abilities_description = " and ".join(abilities_text)

                card_text = f"{card.good} ({card.quantity}): {abilities_description}"

            # Here you could implement logic to split `card_text` into multiple lines if it's too long
            # This example does not include such logic for simplicity

            # Check if the mouse is over this card
                card_rect = pygame.Rect(start_x, start_y + (card_height + gap_between_cards) * index,
                                        card_info_area_width - 10, card_height)
                if card_rect.collidepoint(self.mouse_x, self.mouse_y):
                    pygame.draw.rect(self.screen, self.colors['yellow'], card_rect)  # Highlight the background

            # Render the card text
                text_surface = local_font.render(card_text, True, self.colors['white'])
                self.screen.blit(text_surface, (start_x + 5, start_y + (card_height + gap_between_cards) * index))


#GameSetup
board_layout = [
    "WGGWG",
    "WGGWG",
    "WWSWG",
    "GWGWW",
    "GWGWW"
]

players = []
players.append(Player(False,player_colors[0]))
players.append(Player(False,player_colors[1]))
random.shuffle(players)

testcards = []
testcards.append(Card([BuildArmies(3)], "Iron", 1, False))
testcards.append(Card([BuildCities(1)], "Wood", 1, False))
testcards.append(Card([MoveArmies(2)], "Gem", 1, False))
testcards.append(Card([SailArmies(2)], "Coal", 1, False))
testcards.append(Card([DestroyArmies(1), BuildArmies(1)], "Food", 1, False))
testcards.append(Card([DestroyArmies(1), BuildCities(1)], "Wood", 1, True))

TheTileManager = TileManager()

TheGame = Game(board_layout, players, TheTileManager, STARTING_ARMIES)
TheGraphicManager = GraphicManager(SCREEN_WIDTH, SCREEN_HEIGHT, COLORS)
TheGraphicManager.assign_game(TheGame)
TheGame.set_active_cards(testcards)


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            # Update screen size
            TheGraphicManager.screen_width, TheGraphicManager.screen_height = event.size
            TheGraphicManager.screen = pygame.display.set_mode(
                (TheGraphicManager.screen_width, TheGraphicManager.screen_height), pygame.RESIZABLE)
            # Update scaling factors and adjust graphics accordingly
            TheGraphicManager.update_scaling_factors()
            TheGraphicManager.update_board_tile_size()
        elif event.type == pygame.KEYDOWN:
            TheGame.tilemanager.reset_armies(TheGame.active_player)
            TheGame.tilemanager.reset_movable_tiles(TheGame.tiles)
            if event.key == pygame.K_1:
                TheGame.phase = Phases.BuildArmy
                print("Build army")
            elif event.key == pygame.K_2:
                TheGame.phase = Phases.BuildCity
                print("Build city")
            elif event.key == pygame.K_3:
                TheGame.phase = Phases.MoveArmy
                print("Move armies")
            elif event.key == pygame.K_5:
                TheGame.phase = Phases.SailArmy
                print("Sail armies")
            elif event.key == pygame.K_SPACE:
                TheGame.next_player()
                TheGame.set_manuevers(5)
                print("Active player is: " + str(TheGame.active_player))
        elif event.type == pygame.MOUSEMOTION:
            # Update mouse position
            TheGraphicManager.mouse_x, TheGraphicManager.mouse_y = event.pos
        TheGame.gameloop(TheGraphicManager)
    TheGraphicManager.graphics()

# Quit Pygame
pygame.quit()
sys.exit()