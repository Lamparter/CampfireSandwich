"""
Configuration/constants
"""

import os

NAME = "Rhythm Dodger"

# Responsive UI

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60

# Derived layout values (relative)

GROUND_FRACTION = 0.82 # fraction of window height where ground top sits

GROUND_Y = int(WINDOW_HEIGHT * GROUND_FRACTION)

# Base sprite frame sizes (pixel-art native sizes)

NATIVE_TILE = 16
NATIVE_PLAYER = 24
NATIVE_MASCOT = 24
NATIVE_OBS = 24

# Sprite scale factor (integer) derived from window height to keep pixel-art crisp

SPRITE_SCALE = max(1, int(WINDOW_HEIGHT / 240))

# Scaled sizes used for rendering

TILE_SIZE = NATIVE_TILE * SPRITE_SCALE
PLAYER_W = PLAYER_H = NATIVE_PLAYER * SPRITE_SCALE * 1.5
MASCOT_SIZE = NATIVE_MASCOT * SPRITE_SCALE
OBS_W = OBS_H = NATIVE_OBS * SPRITE_SCALE * 1.5

PLAYER_X = int(WINDOW_WIDTH * 0.12) # relative horizontal player position

GRAVITY = 2000.0 * SPRITE_SCALE
JUMP_VELOCITY = -700.0 * SPRITE_SCALE

OBSTACLE_SPEED = 400.0 * SPRITE_SCALE
OBSTACLE_SPACING_MIN = 3 # * SPRITE_SCALE
OBSTACLE_SPACING_MAX = 5 # * SPRITE_SCALE

FONT_SMALL = max(14, int(WINDOW_HEIGHT * 0.035))
FONT_LARGE = max(28, int(WINDOW_HEIGHT * 0.06))

BEAT_ICON_SCALE_DEFAULT = 1
BEAT_ICON_SCALE_BEAT = 1.25
BEAT_ICON_SCALE_PERFECT = 2
BEAT_BAR_PULSE_SCALE = 0.08 # 8% beat bar pop
BEAT_BAR_PULSE_DECAY = 2.8

# Timing / beat

DEFAULT_BPM = 120
BEAT_TOLERANCE_PERFECT = 0.05
BEAT_TOLERANCE_GOOD = 0.10
MUSIC_LATENCY = -0.4

# Assets

ASSET_DIR = ""
FONTS_DIR = os.path.join(ASSET_DIR, "fonts")
MUSIC_DIR = os.path.join(ASSET_DIR, "music")
SFX_DIR = os.path.join(ASSET_DIR, "sfx")
SPRITES_DIR = os.path.join(ASSET_DIR, "sprites")
ART_DIR = os.path.join(ASSET_DIR, "art")
DATA_DIR = "build"

FONT_NAME = "PixelifySans"
FONT_PATH = os.path.join(FONTS_DIR, FONT_NAME, f"{FONT_NAME}.ttf")

DEFAULT_THEME = "Classic"

PLAYER = "player_24x24.png"
TILESET = "tileset_16x16.png"
OBSTACLES = "obstacles_24x24.png"
MASCOT = "mascot_24x24.png"
HEARTBEAT = "heartbeat_48x48.png"

TITLE_LOGO = os.path.join(SPRITES_DIR, "title_logo.png")
TITLE_MUSIC = os.path.join(SFX_DIR, "title_theme.wav")

SFX = [
	("beat_good"),
	("beat_miss"),
	("beat_perfect"),
	("error"),
	("jump"),
	("land"),
	("mascot"),
	("powerup_in"),
	("powerup_out"),
	("rain"),
	("ui_1"),
	("ui_2"),
	("ui_3"),
	("ui_4"),
	("ui_5"),
	("ui_cancel"),
	("ui_decide_title"),
	("ui_return_title"),
	("wind"),
]

# to adjust

TRACKS = [
	("AmericanBoy", "Estelle", "American Boy", 118, 16.3),
	("BackToBlack", "Amy Winehouse", "Back to Black", 123, 16.22),
	("CaliforniaGurls", "Katy Perry", "California Gurls", 125, 7.9),
	("DJGotUsFallinInLove", "Usher", "DJ Got Us Fallin' In Love", 120, 8.14),
	("GimmeGimmeGimme", "ABBA", "Gimme! Gimme! Gimme!", 120, 16.4),
	("Golden", "HUNTR/X", "Golden", 123, 15.25),
	("Illegal", "PinkPantheress", "Illegal", 141, 13.89),
	("ItsRainingMen", "The Weather Girls", "It's Raining Men", 137, 15.35),
	("MoneyMoneyMoney", "ABBA", "Money, Money, Money", 120, 8.62),
	("MurderOnTheDancefloor", "Sophie Ellis-Bextor", "Murder On The Dancefloor", 117, 20.93),
	("OnlySoMuchOilInTheGround", "Stefanie Heinzmann ", "Only So Much Oil In The Ground", 121, 15.3),
	("PartyInTheUSA", "Miley Cyrus", "Party In The U.S.A.", 96, 9.5),
	("Rasputin", "Boney M.", "Rasputin", 126, 12.3),
	("ShizumeruMachi", "YOEKO", "Sinking Town", 125, 15.44),
	("WhereIsMyHusband", "RAYE", "WHERE IS MY HUSBAND!", 116, 21.64), # approx
]

# Colours

BACKGROUND_COLOUR = (30, 34, 45)
GROUND_COLOUR = (120, 100, 80)
TEXT_COLOUR = (240, 240, 235)

BEAT_BAR_BG_COLOUR = (60, 50, 40) # (245, 235, 230) very light cream
BEAT_BAR_BORDER_COLOUR = (220, 200, 190)
BEAT_BAR_COLOUR = (212, 163, 115)
BEAT_MARKER_COLOUR = (255, 255, 255)

# UI relative sizes

BEAT_BAR_WIDTH = int(WINDOW_WIDTH * 0.28)
BEAT_BAR_HEIGHT = max(14, int(WINDOW_HEIGHT * 0.028))

UI_MARGIN_FRAC = 0.025 # fraction of window width for margins

# CAPTION = "One-Button Rhythm Dodger"
# GROUND_Y = WINDOW_HEIGHT - 80
# PLAYER_WIDTH = 40
# PLAYER_HEIGHT = 60
# PLAYER_X = 120

# GRAVITY = 2000.0
# JUMP_VELOCITY = -900.0

# OBSTACLE_WIDTH = 40
# OBSTACLE_MIN_HEIGHT = 40
# OBSTACLE_MAX_HEIGHT = 120
# OBSTACLE_SPEED = 400.0

# OBSTACLE_SPACING_MIN = 3
# OBSTACLE_SPACING_MAX = 5

# BPM = 90
# BEAT_INTERVAL = 60.0 / BPM
# BEAT_TOLERANCE = 0.12 # the time window for 'on beat'/perfect timing

# PERFECT_WINDOW = 0.05
# GOOD_WINDOW = 0.10

# FONT = "PixelifySans"

# BACKGROUND_COLOUR = (15, 15, 15)
# GROUND_COLOUR = (40, 40, 40)
# PLAYER_COLOUR = (80, 200, 255)
# OBSTACLE_COLOUR = (255, 80, 120)
# TEXT_COLOUR = (230, 230, 240)
# BEAT_BAR_COLOUR = (120, 255, 160)
# BEAT_BAR_BG = (40, 70, 60)
# FLASH_COLOUR_PERFECT = (255, 185, 0)
# FLASH_COLOUR_GOOD = (120, 255, 160)
# FLASH_COLOUR_BAD = (231, 72, 86)
# FLASH_ALPHA = 50

# # Music / track selection

# MUSIC_FOLDER = "music"
# TRACKS = [
# 	("BackToBlack.ogg", "Amy Winehouse - Back to Black", 123),
# 	("DJGotUsFallinInLove.ogg", "Usher - DJ Got Us Fallin' In Love", 120),
# 	("GimmeGimmeGimme.ogg", "ABBA - Gimme Gimme Gimme!", 120),
# 	("OnlySoMuchOilInTheGround.ogg", "Stefanie Heinzmann - Only So Much Oil In The Ground", 121),
# 	("ShizumeruMachi.ogg", "YOEKO - Sinking Town", 125),
# ]
# # small calibration offset to compensate for audio playback latency
# MUSIC_LATENCY = 0.0 # to tune