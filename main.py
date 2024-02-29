import random
from enum import Enum
import pygame
import sys

# Initialize Pygame
pygame.init()

# Set up the display
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))

# Colors
dark_blue = (0, 0, 139)  # Dark blue for water tiles
dark_green = (0, 100, 0)  # Dark green for ground tiles
light_green = (0, 175, 0)  # Light green for movable for tiles
white = (255, 255, 255)  # Color for the text

# Player colors
player_colors = [
    (255, 0, 0),  # Player 1: Red
    (0, 255, 0),  # Player 2: Green
    (0, 0, 255),  # Player 3: Blue
    (255, 255, 0),  # Player 4: Yellow
    (255, 165, 0),  # Player 5: Orange
]

# Initialize Pygame font
pygame.font.init()  # Initialize the font module
font_size = 24  # Adjust the size as needed to fit your tiles
font = pygame.font.Font(None, font_size)  # Create a Font object from the default font

#Phases enum
class Phases(Enum):
    PickCard = 0
    BuildArmy = 1
    BuildCity = 2
    MoveArmy = 3
    DestroyArmy = 4
    SailArmy = 5

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
        self.tile_type = tile_type  # "water" or "ground"
        self.armies = [0, 0, 0, 0, 0]  # Number of armies for up to 5 players
        self.cities = [0, 0, 0, 0, 0]  # Number of cities for up to 5 players
        self.neighbours = []  # List of neighbouring Tile objects
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

#Game
class Game:
    def __init__(self, layout, players, tilemanager):
        self.players = players
        self.active_player = 0
        self.tiles = []
        self.continents = {}
        self.board_layout = layout
        self.create_board()
        self.SetUpStartingArmies()
        self.phase = Phases.PickCard
        self.tilemanager = tilemanager
        self.manuevers = 5

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

    def next_player(self):
        self.active_player = (self.active_player + 1)%len(self.players)

    def set_manuevers(self, number):
        self.manuevers = 0

    def draw_board(self):
        for y, row in enumerate(self.tiles):
            for x, tile in enumerate(row):
                rect = pygame.Rect(x * (tile_size + margin) + margin, y * (tile_size + margin) + margin, tile_size,
                                   tile_size)
                pygame.draw.rect(screen, dark_blue if tile.tile_type == 'water' else light_green if tile.movable else dark_green, rect)

                #předpřípráva pozic
                city_y = rect.y + 5  # Top part for city
                army_y = rect.y + rect.height / 2 + 5  # Bottom part for army

                #označení startovací lokace
                if tile.is_starting_tile:
                    s_text = font.render('S', True, white)
                    s_x = rect.x + (rect.width - s_text.get_width()) / 2
                    # Position 'S' vertically centered between city and army displays
                    s_y = (city_y + army_y) / 2 - s_text.get_height() / 2
                    screen.blit(s_text, (s_x, s_y))

                #pozice armád a měst
                space_per_player = rect.width / 5
                for player_index in range(len(self.players)):
                    if tile.cities[player_index] > 0:
                        city_text = font.render(str(tile.cities[player_index]), True, self.players[player_index].color)
                        text_x = rect.x + player_index * space_per_player + (
                                    space_per_player - city_text.get_width()) / 2
                        screen.blit(city_text, (text_x, city_y))
                    if tile.armies[player_index] > 0:
                        army_text = font.render(str(tile.armies[player_index]), True, self.players[player_index].color)
                        text_x = rect.x + player_index * space_per_player + (
                                    space_per_player - army_text.get_width()) / 2
                        screen.blit(army_text, (text_x, army_y))

    def set_manuevers(self, number):
        self.manuevers = number

    def SetUpStartingArmies(self):
        for row in self.tiles:
            for tile in row:
                if tile.is_starting_tile:
                    for i in range(len(self.players)):
                        tile.set_armies(i, 3)

    def GetTile(self, x, y, margin):
        row = (y - margin) // (tile_size + margin)
        column = (x - margin) // (tile_size + margin)
        if 0 <= row < board_rows and 0 <= column < board_columns:
            clicked_tile = TheGame.tiles[row][column]
            return clicked_tile

    def BuildArmies(self, target_tile):
        if isinstance(target_tile, Tile) and (target_tile.is_starting_tile or target_tile.cities[self.active_player] > 0) and self.players[self.active_player].armies < 14 and self.manuevers > 0:
            target_tile.add_army(self.active_player)
            players[self.active_player].armies = self.tilemanager.count_armies(self.active_player, self.tiles)
            TheGame.set_manuevers(self.manuevers - 1)

    def BuildCities(self, target_tile):
        if isinstance(target_tile, Tile) and target_tile.armies[self.active_player] > 0 and self.players[self.active_player].cities < 3 and self.manuevers > 0:
            target_tile.add_city(self.active_player)
            players[self.active_player].cities = self.tilemanager.count_cities(self.active_player, self.tiles)
            TheGame.set_manuevers(self.manuevers-1)

    def MoveArmies(self, target_tile):
        if target_tile.armies[self.active_player] > 0 and (self.tilemanager.selected_armies == 0 or target_tile.move_cost == 0):
            self.tilemanager.reset_movable_tiles(self.tiles)
            target_tile.remove_army(self.active_player)
            self.tilemanager.set_selected_armies(self.tilemanager.selected_armies + 1)
            self.tilemanager.movable_tiles(target_tile, self.manuevers, self.manuevers)
            self.tilemanager.set_active_tile(target_tile)
        elif target_tile.movable:
            target_tile.add_armies(self.active_player, self.tilemanager.selected_armies)
            self.set_manuevers(self.manuevers - target_tile.move_cost)
            self.tilemanager.set_selected_armies(0)
            self.tilemanager.reset_movable_tiles(self.tiles)
            self.tilemanager.set_active_tile(None)

    def SailArmies(self, target_tile):
        if target_tile.armies[self.active_player] > 0 and (self.tilemanager.selected_armies == 0 or target_tile.move_cost == 0):
            self.tilemanager.reset_movable_tiles(self.tiles)
            target_tile.remove_army(self.active_player)
            self.tilemanager.set_selected_armies(self.tilemanager.selected_armies + 1)
            self.tilemanager.sailable_tiles(target_tile, self.manuevers, self.manuevers)
            self.tilemanager.set_active_tile(target_tile)
        elif target_tile.movable:
            target_tile.add_armies(self.active_player, self.tilemanager.selected_armies)
            self.set_manuevers(self.manuevers - target_tile.move_cost)
            self.tilemanager.set_selected_armies(0)
            self.tilemanager.reset_movable_tiles(self.tiles)
            self.tilemanager.set_active_tile(None)



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
players.append(Player(False,player_colors[2]))
random.shuffle(players)

TheTileManager = TileManager()

TheGame = Game(board_layout, players, TheTileManager)
TheGame.display_tile_info()

#Board display setup
board_rows = len(board_layout)
board_columns = len(board_layout[0])
margin = 5  # Minimum margin size in pixels between tiles
tile_width = (screen_width - margin * (board_columns + 1)) // board_columns
tile_height = (screen_height - margin * (board_rows + 1)) // board_rows
tile_size = min(tile_width, tile_height)  # Ensure tiles are always square


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
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
            elif event.key == pygame.K_4:
                TheGame.phase = Phases.SailArmy
                print("Sail armies")
            elif event.key == pygame.K_SPACE:
                TheGame.next_player()
                TheGame.set_manuevers(5)
                print("Active player is: " + str(TheGame.active_player))

        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Get mouse position
            mouse_x, mouse_y = pygame.mouse.get_pos()
            clicked_tile = TheGame.GetTile(mouse_x, mouse_y, margin)
            if TheGame.phase == Phases.BuildArmy:
                TheGame.BuildArmies(clicked_tile)
            elif TheGame.phase == Phases.BuildCity:
                TheGame.BuildCities(clicked_tile)
            elif TheGame.phase == Phases.MoveArmy:
                TheGame.MoveArmies(clicked_tile)
            elif TheGame.phase == Phases.SailArmy:
                TheGame.SailArmies(clicked_tile)

    screen.fill((0, 0, 0))  # Fill the background with black
    TheGame.draw_board()  # Draw the board based on the tiles list
    pygame.display.flip()  # Update the display

# Quit Pygame
pygame.quit()
sys.exit()