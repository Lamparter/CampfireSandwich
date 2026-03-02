"""
Helper functions
"""

import pygame, math, random, glob, numpy
import models, audio
from constants import *

def space_obstacle() -> int:
	return random.randint(OBSTACLE_SPACING_MIN, OBSTACLE_SPACING_MAX)

def get_timing_judgement(clock: models.BeatTracker): # returns a string judgement based on how close the jump was to the beat
	t = clock.last_beat_time
	dist = min(abs(t), abs(clock.interval - t))

	if dist <= BEAT_TOLERANCE_PERFECT:
		return "Perfect!"
	elif dist <= BEAT_TOLERANCE_GOOD:
		return "Good!"
	else:
		# early vs late
		if t < clock.interval / 2:
			return "Early!"
		else:
			return "Late!"

def get_accuracy_percent(accurate_jumps: int, total_jumps: int):
	if total_jumps == 0:
		return 0
	return int((accurate_jumps / total_jumps) * 100)

def get_rank(accuracy : int):
	if accuracy >= 95: return "S"
	if accuracy >= 85: return "A"
	if accuracy >= 70: return "B"
	return "C"

def play_ui_sound(audioManager: audio.AudioManager):
	audioManager.play_sfx("ui_" + str(random.randint(1, 5)))

def get_themed(asset : str, theme : str = DEFAULT_THEME.lower(), folder : str = SPRITES_DIR):
	return os.path.join(folder, theme, asset)

def load_parallax_layers(folder : str = os.path.join(SPRITES_DIR, DEFAULT_THEME.lower()), pattern : str = "bg_*", max_value : float = 0.60):
	files = sorted(
		glob.glob(os.path.join(folder, pattern)),
		key=lambda f: int(os.path.basename(f).split("_")[1].split(".")[0])
	)
	
	count = len(files)
	if count == 0:
		return []
	
	original_curve = numpy.array([0.1333, 0.3000, 0.5833, 1.0])
	x_old = numpy.linspace(0, 1, len(original_curve))
	x_new = numpy.linspace(0, 1, count)
	values = numpy.interp(x_new, x_old, original_curve) * max_value

	layers = [
		models.ParallaxLayer(f, float(v))
		for f, v in zip(files, values)
	]

	return layers

def _with_click_sfx(cb, audioManager: audio.AudioManager):
	def wrapper(btn):
		play_ui_sound(audioManager)
		cb(btn)
	return wrapper

def _draw_rounded_image(surf : pygame.Surface, img, rect : pygame.Rect, radius=12):
	mask = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
	pygame.draw.rect(mask, (255,255,255), mask.get_rect(), border_radius=radius)
	img_scaled = pygame.transform.smoothscale(img, (rect.w, rect.h))
	img_scaled.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
	surf.blit(img_scaled, rect.topleft)