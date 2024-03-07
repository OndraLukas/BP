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

#Enums
class Phases(Enum):
    PickCard = 1
    PickAbilityAND = 2
    PickAbilityOR = 3
    BuildArmy = 4
    BuildCity = 5
    MoveArmy = 6
    DestroyArmy = 7
    SailArmy = 8

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
        self.clickable = False
        self.move_cost = -1

    def make_starting_tile(self):
        self.is_starting_tile = True

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

    def count_cities(self, player_index, tiles):
        citycount = 0
        for row in tiles:
            for tile in row:
                citycount += tile.cities[player_index]
        return citycount

    def movable_tiles(self, target_tile, reserve, original):
        target_tile.clickable = True
        target_tile.set_movecost(original - reserve)
        reserve = reserve - self.selected_armies
        if(reserve >= 0):
            for neihgbour in target_tile.neighbours:
                if not(neihgbour.clickable) and not(neihgbour.tile_type == "water"):
                    self.movable_tiles(neihgbour, reserve, original)

    def sailable_tiles(self, target_tile, reserve, original):
        if target_tile.tile_type == "ground":
            target_tile.clickable = True
            target_tile.set_movecost(original - reserve)
            reserve = reserve - self.selected_armies
            if (reserve >= 0):
                for neihgbour in target_tile.neighbours:
                    if not (neihgbour.clickable):
                        self.sailable_tiles(neihgbour, reserve, original)
        else:
            for neihgbour in target_tile.neighbours:
                if not(neihgbour.clickable) and not(neihgbour.tile_type == "water"):
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
        self.viable_abilities = []
        self.played_card = None
        self.continents = {}
        self.board_layout = layout
        self.create_board()
        self.set_up_starting_armies(starting_armies)
        self.phase = Phases.PickCard
        self.tilemanager = tilemanager
        self.manuevers = 0
        self.abilities_to_select = {}
        self.turn = 1
        self.graphic_manager = None

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
            self.viable_abilities += played_card.abilities
        else:
            self.pick_ability(played_card.abilities[0])
        self.active_cards.remove(played_card)

    def pick_ability(self, picked_ability):
        self.set_manuevers(picked_ability.manuevers)
        if isinstance(picked_ability, BuildArmies):
            self.set_phase(Phases.BuildArmy)
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
        elif isinstance(target_tile, Tile) and target_tile.clickable:
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
        elif isinstance(target_tile, Tile) and target_tile.clickable:
            target_tile.add_armies(self.active_player, self.tilemanager.selected_armies)
            self.set_manuevers(self.manuevers - target_tile.move_cost)
            self.tilemanager.set_selected_armies(0)
            self.tilemanager.reset_movable_tiles(self.tiles)
            self.tilemanager.set_active_tile(None)

    def gameloop(self):
        if self.graphic_manager.clicked_element:
            clicked_element = self.graphic_manager.clicked_element
            if isinstance(clicked_element, Card) and self.phase == Phases.PickCard:
                self.play_card(self.graphic_manager.clicked_element)
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
            elif isinstance(clicked_element, Tile) and self.phase == Phases.SailArmy:
                self.sail_armies(clicked_element)
        self.graphic_manager.prepare_side_menu_elements()

    def end_move_handler(self):
        self.set_manuevers(0)
        self.tilemanager.reset_armies(self.active_player)
        self.tilemanager.reset_movable_tiles(self.tiles)
        if len(self.viable_abilities) > 0:
            self.set_phase(Phases.PickAbilityAND)
        else:
            self.set_phase(Phases.PickCard)
            self.next_player()
        if self.active_player == 0:
            self.turn +=1
        self.graphic_manager.prepare_side_menu_elements()



#Graphics
class GraphicManager:
    def __init__(self, screen_width, screen_height, colors, game):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        self.colors = colors
        self.game = game
        self.game.graphic_manager = self
        self.max_board_height = self.screen_height * 2 / 3
        self.tile_margin = 5
        self.tile_size = self.calculate_tile_size(len(self.game.tiles))
        self.tile_graphics = []
        self.prepare_tile_graphics()
        num_columns = len(self.game.tiles[0])
        board_width = num_columns * self.tile_size + (num_columns + 1) * self.tile_margin
        self.side_menu_x = board_width + 10
        self.side_menu_y_start = 10
        self.side_menu_spacing = 30
        self.side_menu_elements = []
        self.prepare_side_menu_elements()
        self.clicked_element = None
        self.mouse_pos = pygame.mouse.get_pos()
        self.clicked_pos = None

    def calculate_tile_size(self, num_rows):
        available_height = self.max_board_height - (num_rows + 1) * self.tile_margin
        tile_size = available_height / num_rows
        return int(tile_size)

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

        if self.game.phase == Phases.PickCard:
            for card in self.game.active_cards:
                self.side_menu_elements.append(Card_Button(self.side_menu_y_start + len(self.side_menu_elements) * self.side_menu_spacing, card, self))
        if self.game.phase == Phases.PickAbilityAND or self.game.phase == Phases.PickAbilityOR:
            for ability in self.game.viable_abilities:
                self.side_menu_elements.append(Ability_Button(self.side_menu_y_start + len(self.side_menu_elements) * self.side_menu_spacing, ability, self))

    def draw_side_menu(self):
        for element in self.side_menu_elements:
            element.draw()

    def graphics(self):
        self.screen.fill(self.colors.get('background', (0, 0, 0)))
        self.mouse_pos = pygame.mouse.get_pos()
        self.draw_board()
        self.draw_side_menu()
        pygame.display.flip()

    def click_handler(self):
        self.clicked_pos = self.mouse_pos
        clickable_elements = self.side_menu_elements + [tile_graphic for row in self.tile_graphics for tile_graphic in row]
        for element in clickable_elements:
            if isinstance(element, Clickable_Element) and element.clicked():
                self.clicked_element = getattr(element, 'card', None) or getattr(element, 'tile', None) or getattr(element, 'ability', None)
                break

    def reset_clicked_element(self):
        self.clicked_element = None

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
        card_text = f"{self.card.good}({self.card.quantity}): {abilities_text}"

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


class Side_Menu_Title:
    def __init__(self, y, graphic_manager):
        self.y = y
        self.graphic_manager = graphic_manager
        # self.graphic_manager.side_menu_font
        self.font = pygame.font.Font(None, 24)

    def draw(self):
        player_color = self.graphic_manager.game.players[self.graphic_manager.game.active_player].color
        text = f"{self.graphic_manager.game.players[self.graphic_manager.game.active_player].name}:Turn {self.graphic_manager.game.turn}:{self.graphic_manager.game.phase.name}"
        if self.graphic_manager.game.manuevers > 0:
            text +=f" {self.graphic_manager.game.manuevers}"
        text_surface = self.font.render(text, True, self.graphic_manager.colors[player_color])
        self.graphic_manager.screen.blit(text_surface, (self.graphic_manager.side_menu_x, self.y))




#GameSetup
board_layout = [
    "WGGWG",
    "WGGWG",
    "WWSWG",
    "GWGWW",
    "GWGWW"
]

players = []
players.append(Player("Player 1",False,"player_red"))
players.append(Player("Player 2",False,"player_green"))
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
TheGame.set_active_cards(testcards)
TheGraphicManager = GraphicManager(SCREEN_WIDTH, SCREEN_HEIGHT, COLORS, TheGame)


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            TheGraphicManager.click_handler()
            TheGame.gameloop()
            TheGraphicManager.reset_clicked_element()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                TheGame.end_move_handler()
    TheGraphicManager.graphics()

# Quit Pygame
pygame.quit()
sys.exit()