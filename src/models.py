"""
Game objects
"""

import os, pygame, random
import sprites, particles, ui, helpers, settings
from constants import *

# Game objects

class Player: # player
	def __init__(self, spritesheet: sprites.SpriteSheet, font):
		# store native frames then scale for rendering
		self.x = PLAYER_X
		self.y = float(GROUND_Y - PLAYER_H)
		self.vy = 0.0
		self.on_ground = True
		self.land_time_remaining = 0.0
		self.recently_landed = False
		self.spritesheet = spritesheet
		self.animations = {}
		self.anim_durations = {}
		frames = 4

		anim_rows = [
			(0, "idle", 6),
			(1, "jump", 4),
			(2, "land", 8),
		]

		# load native frames (24x24) and scale them to PLAYER_W/PLAYER_H
		for row, name, fps in anim_rows:
			native_frames = spritesheet.load_strip((0, row * NATIVE_PLAYER, NATIVE_PLAYER, NATIVE_PLAYER), frames)
			scaled_frames = [pygame.transform.scale(f, (PLAYER_W, PLAYER_H)) for f in native_frames]
			self.animations[name] = sprites.AnimatedSprite(scaled_frames, fps=fps, loop=True)
			self.anim_durations[name] = frames / float(fps)

		self.state = "idle"
		self.font = font
		self.width = PLAYER_W
		self.height = PLAYER_H

		self._mask_cache = {}

	@property
	def rect(self):
		return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
	
	def reset(self):
		self.y = float(GROUND_Y - PLAYER_H)
		self.vy = 0.0
		self.on_ground = True
		self.recently_landed = False
		self.state = "idle"
	
	def try_jump(self):
		if self.on_ground:
			self.vy = JUMP_VELOCITY
			self.on_ground = False
			self.state = "jump"
			self.land_time_remaining = 0.0
	
	def get_mask(self):
		# get the current frame surface from the AnimatedSprite
		img = self.animations[self.state].get_image()
		if img is None:
			return None
		key = id(img)
		mask = self._mask_cache.get(key)
		if mask is None:
			mask = pygame.mask.from_surface(img)
			self._mask_cache[key] = mask
		return mask
	
	def update(self, dt):
		self.vy += GRAVITY * dt
		self.y += self.vy * dt
		ground_y = GROUND_Y - self.height
		if self.y >= ground_y:
			if not self.on_ground:
				self.recently_landed = True
			self.y = ground_y
			self.vy = 0.0
			self.on_ground = True
			if self.recently_landed:
				self.state = "land"
				self.land_time_remaining = self.anim_durations.get("land", 0.25)
		else:
			self.on_ground = False

		self.animations[self.state].update(dt) # animation update

		if self.state == "land":
			# decrement timer
			self.land_time_remaining -= dt
			if self.land_time_remaining <= 0.0:
				self.state = "idle"
				self.land_time_remaining = 0.0

		if self.recently_landed:
			# clear flag after one update so land animation can play briefly
			self.recently_landed = False

	def draw(self, surf, scale_x = 1.0, scale_y = 1.0):
		img = self.animations[self.state].get_image()
		# img already scaled to PLAYER_W/PLAYER_H; apply micro squash/stretch via transform
		w,h = img.get_size()
		sw = max(1, int(w * scale_x))
		sh = max(1, int(h * scale_y))
		img_scaled = pygame.transform.scale(img, (sw, sh))
		draw_x = int(self.x) # anchor bottom left
		draw_y = int(self.y + (h - sh))
		surf.blit(img_scaled, (draw_x, draw_y))

class Obstacle:
	def __init__(self, x, sprite):
		# sprite is native 24x24; scale to OBS_W/OBS_H
		self.x = x
		self.sprite = pygame.transform.scale(sprite, (OBS_W, OBS_H))
		self.width = self.sprite.get_width()
		self.height = self.sprite.get_height()
		self.y = GROUND_Y - self.height
		if random.random() < 0.25: # random vertical offset for variety (floating obstacles)
			self.y -= random.choice([24 * SPRITE_SCALE, 40 * SPRITE_SCALE])
		self.passed = False

		# create a mask from the scaled surface for pixel-perfect collision
		self.mask = pygame.mask.from_surface(self.sprite)

	@property
	def rect(self):
		return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
	
	def update(self, dt):
		self.x -= OBSTACLE_SPEED * dt
	
	def draw(self, surf):
		surf.blit(self.sprite, (int(self.x), int(self.y)))
	
	def offscreen(self):
		return self.x + self.width < 0

class Mascot:
	def __init__(self, sheet: sprites.SpriteSheet, font_small, theme):
		# load native frames and scale to MASCOT_SIZE
		sheet_count = 2 if theme == "dinosaur" else 3
		native_frames = sheet.load_strip((0,0,NATIVE_MASCOT,NATIVE_MASCOT), sheet_count)
		scaled = [pygame.transform.scale(f, (MASCOT_SIZE,MASCOT_SIZE)) for f in native_frames]
		self.anim = sprites.AnimatedSprite(scaled, fps=3) # slower default fps so it doesn't animate too fast
		self.x = int(WINDOW_WIDTH * 0.02)
		self.y = int(WINDOW_HEIGHT * 0.02)
		self.font_small = font_small

	def react(self, mood):
		# mood: "happy", "sad", "idle"
		if mood == "happy":
			self.anim.fps = 5
		elif mood == "sad":
			self.anim.fps = 2
		else:
			self.anim.fps = 3
	
	def update(self, dt):
		self.anim.update(dt)
	
	def draw(self, surf, x = None, y = None, size = None):
		img = self.anim.get_image()
		if size and (img.get_width() != size or img.get_height() != size):
			img = pygame.transform.scale(img, (size, size))
		draw_x = self.x if x is None else x
		draw_y = self.y if y is None else y
		surf.blit(img, (draw_x, draw_y))

class TitleScreen:
	def __init__(self, game):
		self.game = game
		self.screen = game.screen
		self.clock = game.clock
		self.font_small = game.font_small
		self.font_large = game.font_large
		self.bg_layers = getattr(game, "bg_layers", [])
		self.mascot = game.mascot

		# load logo if present
		self.logo = None
		if os.path.exists(TITLE_LOGO):
			try:
				logo_img = pygame.image.load(TITLE_LOGO).convert_alpha()
				target_w = int(WINDOW_WIDTH * 0.3)
				scale = target_w / logo_img.get_width()
				target_h = int(logo_img.get_height() * scale)
				self.logo = pygame.transform.smoothscale(logo_img, (target_w, target_h))
			except Exception:
				self.logo = None

		# load music if present
		self.enter_title_music()

		# UI buttons
		self.menu_buttons = []
		self._create_menu_buttons()

		self.press_text_y = int(WINDOW_HEIGHT * 0.88)

		# pulse for 'press key'
		self.pulse = 0.0
		self.pulse_dir = 1

		# ambient particles
		self.particles = particles.ParticleSystem(200)

		# initial keyboard focus on first button
		if self.menu_buttons:
			self.menu_buttons[0].focus = True

	def enter_title_music(self):
		if os.path.exists(TITLE_MUSIC):
			try:
				pygame.mixer.music.load(TITLE_MUSIC)
				pygame.mixer.music.set_volume(0.32)
				pygame.mixer.music.play(-1)
				self.title_music_loaded = True
			except Exception:
				self.title_music_loaded = False
	
	def _create_menu_buttons(self):
		# compute size and positions
		btn_w = int(WINDOW_WIDTH * 0.28)
		btn_h = max(48, int(WINDOW_HEIGHT * 0.07))
		centre_x = WINDOW_WIDTH // 2
		base_y = int(WINDOW_HEIGHT * 0.48)
		spacing = btn_h + int(WINDOW_HEIGHT * 0.02)

		def make_btn(text, idx, cb):
			rect = (centre_x - btn_w // 2, base_y + idx * spacing, btn_w, btn_h)
			b = ui.Button(rect, text, self.font_large, cb)
			return b
		
		self.menu_buttons.append(make_btn("Start", 0, helpers._with_click_sfx(lambda b: self.open_song_select(), self.game.audio)))
		self.menu_buttons.append(make_btn("Settings", 1, helpers._with_click_sfx(lambda b: self.game.set_state("options"), self.game.audio)))
		self.menu_buttons.append(make_btn("Quit", 2, lambda b: setattr(self.game, "running", False)))
	
	def open_song_select(self):
		self.game.set_state("song_select")
	
	def _focus_next(self):
		if not self.menu_buttons:
			return
		idx = next((i for i, b in enumerate(self.menu_buttons) if b.focus), -1)
		if idx >= 0:
			self.menu_buttons[idx].focus = False
		idx = (idx + 1) % len(self.menu_buttons)
		self.menu_buttons[idx].focus = True
	
	def _focus_prev(self):
		if not self.menu_buttons:
			return
		idx = next((i for i, b in enumerate(self.menu_buttons) if b.focus), -1)
		if idx >= 0:
			self.menu_buttons[idx].focus = False
		idx = (idx - 1) % len(self.menu_buttons)
		self.menu_buttons[idx].focus = True

	def handle_input(self, events):
		for e in events:
			for b in self.menu_buttons:
				if b.handle_event(e):
					return

		for e in events:
			if e.type == pygame.KEYDOWN:
				if e.key == pygame.K_UP:
					self._focus_prev()
				elif e.key == pygame.K_DOWN:
					self._focus_next()
				elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
					focused = next((b for b in self.menu_buttons if b.focus), None)
					if focused:
						focused._click()
				elif e.key == pygame.K_q:
					pass
			elif e.type == pygame.MOUSEMOTION:
				# update hover states so buttons show hover visuals
				for b in self.menu_buttons:
					b.hover = b.rect.collidepoint(e.pos)
	
	def update(self, dt):
		# pulse animation
		self.pulse += dt * 2.0 * self.pulse_dir
		if self.pulse > 1.0:
			self.pulse = 1.0
			self.pulse_dir = -1
		elif self.pulse < 0.0:
			self.pulse = 0.0
			self.pulse_dir = -1
		
		# ambient particles
		if random.random() < 0.02:
			x = random.uniform(WINDOW_WIDTH*0.2, WINDOW_WIDTH*0.8)
			y = random.uniform(WINDOW_HEIGHT*0.2, WINDOW_HEIGHT*0.6)
			self.particles.emit(x,y, count=4, colour=(255,240,200))
		self.particles.update(dt)
		self.mascot.update(dt)

	def draw(self):
		surf = self.screen
		surf.fill(BACKGROUND_COLOUR)

		# draw background layers (static)
		for layer in self.bg_layers:
			layer.draw(surf)

		# dim background to focus UI
		dim = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
		dim.fill((10, 10, 12, 180))
		surf.blit(dim, (0, 0))
		
		# logo or fallback text (because i haven't designed logo yet)
		if self.logo:
			logo_x = WINDOW_WIDTH // 2 - self.logo.get_width() // 2
			logo_y = int(WINDOW_HEIGHT * 0.15)
			surf.blit(self.logo, (logo_x, logo_y))
		else:
			title_text = self.font_large.render(NAME, True, TEXT_COLOUR)
			surf.blit(title_text, (WINDOW_WIDTH//2 - title_text.get_width()//2, int(WINDOW_HEIGHT * 0.10)))

		# menu
		for b in self.menu_buttons:
			b.draw(surf)
		
		# press key text (pulsing alpha)
		press_text = self.font_small.render("Press Enter or Space to select", True, TEXT_COLOUR)
		alpha = int(160 + 95 * self.pulse)
		press_surf = press_text.copy()
		press_surf.set_alpha(alpha)
		surf.blit(press_surf, (WINDOW_WIDTH//2 - press_text.get_width()//2, self.press_text_y))

		# particles
		self.particles.draw(surf)

class SongSelectScreen:
	def __init__(self, game):
		self.game = game
		self.screen = game.screen
		self.font_small = game.font_small
		self.font_large = game.font_large
		self.tracks = game.available_tracks

		self.panel_x = int(WINDOW_WIDTH * 0.08)
		self.panel_y = int(WINDOW_HEIGHT * 0.12)
		self.panel_w = int(WINDOW_WIDTH * 0.84)
		self.panel_h = int(WINDOW_HEIGHT * 0.76)

		self.visible_top = self.panel_y + int(self.panel_h * 0.18)
		self.visible_h = int(self.panel_h * 0.72)
		self.visible_bottom = self.visible_top + self.visible_h

		self.scroll_y = 0
		self.max_scroll = 0
		self.tile_h = max(80, int(WINDOW_HEIGHT * 0.12))
		self.spacing = self.tile_h + int(WINDOW_HEIGHT * 0.03)

		# build tiles from TRACKS constant
		self.tiles = []
		self.selected_index = 0
		self._build_tiles()

		self._compute_max_scroll()
	
	def _build_tiles(self):
		# tile layout: horizontal stretching tiles stacked vertically
		tile_w = int(WINDOW_WIDTH * 0.7)
		tile_h = max(80, int(WINDOW_HEIGHT * 0.12))
		margin_x = int(WINDOW_WIDTH * 0.15)
		base_y = int(WINDOW_HEIGHT * 0.28)
		spacing = tile_h + int(WINDOW_HEIGHT * 0.03)

		for i, t in enumerate(TRACKS):
			rect = pygame.Rect(margin_x, base_y + i * spacing, tile_w, tile_h)
			btn = ui.Button(
				rect,
				"",
				self.font_large,
				lambda b, track=t: self._select_track(track),
				radius=12
			)
			btn.base_rect = rect.copy()
			self.tiles.append((btn, t))
		
		self._apply_focus()

	def _compute_max_scroll(self):
		total_h = len(self.tiles) * self.spacing
		self.max_scroll = max(0, total_h - self.visible_h)

	def _select_track(self, track):
		# set current track and go to playing state (but show confirm menu)
		filename, artist, title, bpm, intro = track
		self.game.current_track = {"path": os.path.join(MUSIC_DIR, filename), "name": title, "bpm": bpm, "artist": artist, "art": os.path.join(ART_DIR, filename), "intro": intro}

		# play decide sfx
		try: self.game.audio.play_sfx("ui_decide_title")
		except: pass

		# start music and go to playing
		self.game.start_track(self.game.current_track)
		self.game.set_state("playing")
	
	def _ensure_selected_visible(self):
		# compute selected tile y and adjust scroll_y to bring it into view
		idx = self.selected_index
		top = idx * self.spacing
		bottom = top + self.tile_h
		if top < self.scroll_y:
			self.scroll_y = max(0, top)
		elif bottom > self.scroll_y + self.visible_h:
			self.scroll_y = min(self.max_scroll, bottom - self.visible_h)

	def _apply_focus(self):
		for i, (btn, _) in enumerate (self.tiles):
			btn.focus = (i == self.selected_index)

	def handle_input(self, events):
		for e in events:
			if e.type == pygame.MOUSEBUTTONDOWN:
				if e.button == 4: # wheel up
					self.scroll_y = max(0, self.scroll_y - int(self.tile_h * 0.5))
				elif e.button == 5: # wheel down
					self.scroll_y = min(self.max_scroll, self.scroll_y + int(self.tile_h * 0.5))
				elif e.button == 1: # left click
					# check click against scrolled tile rects
					for i, (btn, track) in enumerate(self.tiles):
						hit_rect = btn.base_rect.move(0, -self.scroll_y)
						if hit_rect.collidepoint(e.pos):
							self._select_track(track)
			elif e.type == pygame.KEYDOWN:
				if e.key == pygame.K_UP:
					self.selected_index = max(0, self.selected_index - 1)
					self._apply_focus()
					self._ensure_selected_visible()
				elif e.key == pygame.K_DOWN:
					self.selected_index = min(len(self.tiles) - 1, self.selected_index + 1)
					self._apply_focus()
					self._ensure_selected_visible()
				elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
					btn, track = self.tiles[self.selected_index]
					self._select_track(track)
					return
				elif e.key in (pygame.K_ESCAPE, pygame.K_q):
					self.game.set_state("title")
					return
			elif e.type == pygame.MOUSEMOTION:
				# update hover states so buttons show hover visuals
				for b, t in self.tiles:
					b.hover = b.rect.collidepoint(e.pos)
	
	def draw(self):
		surf = self.screen
		surf.fill((20, 20, 24))

		panel_x = int(WINDOW_WIDTH * 0.08)
		panel_y = int(WINDOW_HEIGHT * 0.12)
		panel_w = int(WINDOW_WIDTH * 0.84)
		panel_h = int(WINDOW_HEIGHT * 0.76)
		panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

		ui.draw_panel(
			surf,
			panel_rect,
			(30, 28, 32), # dark interior
			(80, 70, 60),
			subtitle="Press ESC to return",
			subtitle_font=self.font_small
		)

		title = self.font_large.render("Choose a Song", True, TEXT_COLOUR)
		surf.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, panel_y + 12))

		subtitle = self.font_small.render("Select a track to begin playing", True, (180,170,160))
		surf.blit(subtitle, (WINDOW_WIDTH//2 - subtitle.get_width()//2,
					   		panel_y + 12 + title.get_height() + 4))
		
		visible_top = panel_y + int(panel_h * 0.18)
		visible_h = int(panel_h * 0.72)
		visible_bottom = visible_top + visible_h

		clip_rect = pygame.Rect(panel_x, visible_top, panel_w, visible_h)
		prev_clip = surf.get_clip()
		surf.set_clip(clip_rect)

		for i, (btn, track) in enumerate(self.tiles):
			filename, artist, title_text, bpm, intro = track
			art_path = os.path.join(ART_DIR, filename + ".jpg")

			draw_rect = btn.base_rect.move(0, -self.scroll_y)
			btn.rect = draw_rect

			# skip tiles outside visible area
			if draw_rect.bottom < visible_top or draw_rect.top > visible_bottom:
				continue
			btn.draw(surf)
			
			# album art rect
			pad = int(draw_rect.height * 0.12)
			art_size = draw_rect.height - pad * 2
			art_rect = pygame.Rect(draw_rect.x + pad, draw_rect.y + pad, art_size, art_size)

			if os.path.exists(art_path):
				try:
					img = pygame.image.load(art_path).convert_alpha()
					helpers._draw_rounded_image(surf, img, art_rect, radius=12)
				except:
					pass

			# text positions
			text_x = art_rect.right + pad
			title_y = draw_rect.y
			artist_y = title_y + self.font_large.get_height() + 4
	
			title_surf = self.font_large.render(title_text, True, (40, 34, 40))
			surf.blit(title_surf, (text_x, title_y))
	
			sub_surf = self.font_small.render(f"{artist} - {bpm} BPM", True, (100, 90, 80))
			surf.blit(sub_surf, (text_x, artist_y))

		# restore clipping
		surf.set_clip(prev_clip)

class SettingsScreen:
	def __init__(self, game):
		self.game = game
		self.screen = game.screen
		self.font_small = game.font_small
		self.font_large = game.font_large
		self.settings = game.settings

		# layout
		self.panel_x = int(WINDOW_WIDTH * 0.08)
		self.panel_y = int(WINDOW_HEIGHT * 0.12)
		self.panel_w = int(WINDOW_WIDTH * 0.84)
		self.panel_h = int(WINDOW_HEIGHT * 0.76)

		# reset button
		btn_w = 120
		btn_h = 40
		self.reset_button = ui.Button(
			(self.panel_x + self.panel_w - btn_w - 12,
			self.panel_y + 12,
			btn_w,
			btn_h),
			"Reset",
			self.font_small,
			helpers._with_click_sfx(lambda b: self._reset_settings(), self.game.audio),
			radius=8
		)

		# visible scroll area inside panel
		self.visible_top = self.panel_y + int(self.panel_h * 0.22)
		self.visible_h = int(self.panel_h * 0.72)
		self.visible_bottom = self.visible_top + self.visible_h

		# tile geometry
		self.tile_h = max(80, int(WINDOW_HEIGHT * 0.12))
		self.spacing = self.tile_h + int(WINDOW_HEIGHT * 0.03)
		self.tile_w = int(self.panel_w * 0.90)
		self.margin_x = self.panel_x + int(self.panel_w * 0.05)
		self.base_y = self.visible_top

		# key, label, description, control type, control args
		self.schema = [
			("theme", "App theme", "Choose the app's theme", "input", {}),
			("beat_sound", "Beat Sound", "Play a sound on every beat", "toggle", {}),
			("debug", "Debug UI", "Show debug overlay and FPS", "toggle", {}),
			("music_latency", "Music Latency", "Adjust audio timing (seconds)", "slider", {"min": -1.0, "max": 1.0, "step": 0.01}),
			("master_volume", "Master Volume", "Overall music volume", "slider", {"min": 0.0, "max": 1.0, "step": 0.01}),
		]

		self.tiles = []
		for i, (key, label, desc, ctype, args) in enumerate(self.schema):
			base_rect = pygame.Rect(self.margin_x, self.base_y + i * self.spacing, self.tile_w, self.tile_h)
			if ctype == "toggle":
				ctrl_rect = (0, 0, 90, 40)
				ctrl = ui.ToggleSwitch(ctrl_rect, value=self.settings.get(key), font=self.font_small)
				# bind on_change to persist
				ctrl.on_change = (lambda k: helpers._with_click_sfx(lambda v: self._on_change(k, v), self.game.audio))(key)
			elif ctype == "slider":
				ctrl_rect = (0, 0, 240, 28)
				minv = args.get("min", 0.0)
				maxv = args.get("max", 1.0)
				ctrl = ui.Slider(ctrl_rect, minv=minv, maxv=maxv, value=self.settings.get(key))
				ctrl.on_change = (lambda k: (lambda v: self._on_change(k, v)))(key)
			elif ctype == "input":
				ctrl_rect = (0, 0, 200, 36)
				initial = str(self.settings.get(key))
				ctrl = ui.TextInput(ctrl_rect, text=initial, font=self.game.font_small, placeholder=DEFAULT_THEME)
				ctrl.on_change = (lambda k: (lambda v: self._on_change(k, v)))(key)
			else:
				ctrl = None

			self.tiles.append((base_rect, label, desc, ctrl, key))
		
		self.scroll_y = 0
		total_height = len(self.tiles) * self.spacing
		self.max_scroll = max(0, total_height - self.visible_h)

		self.selected_index = 0
		self._apply_focus()

	def _on_change(self, key, value):
		# persist
		self.settings.set(key, value)
		# apply side effects
		if key == "theme":
			if value in ("Classic", "London", "Flagship", "Dinosaur"):
				self.game.theme = str(value).lower()
				self.game.restart_screen = "options"
				self.game.restarting = True
			else:
				self.settings.set(key, str(self.game.theme).capitalize())
		if key == "master_volume":
			try:
				pygame.mixer.music.set_volume(float(value))
			except Exception:
				pass
		if key == "music_latency":
			try:
				self.game.music_latency = float(value)
			except Exception:
				pass
		if key == "debug":
			self.game.debug = bool(value)
		if key == "beat_sound":
			self.game.beat_sound = bool(value)
	
	def _apply_focus(self):
		for i, (_, _, _, ctrl, _) in enumerate(self.tiles):
			if ctrl:
				ctrl.focus = (i == self.selected_index)
	
	def _ensure_selected_visible(self):
		idx = self.selected_index
		top = idx * self.spacing
		bottom = top + self.tile_h

		if top < self.scroll_y:
			self.scroll_y = max(0, top)
		elif bottom > self.scroll_y + self.visible_h:
			self.scroll_y = min(self.max_scroll, bottom - self.visible_h)

	def _reset_settings(self):
		# restore defaults
		for key, default in settings.SettingsManager.DEFAULTS.items():
			self.settings.set(key, default)
		
		# reapply to game
		self.game.theme = self.settings.get("theme").lower()
		self.game.music_latency = self.settings.get("music_latency")
		self.game.debug = self.settings.get("debug")
		self.game.beat_sound = self.settings.get("beat_sound")
		pygame.mixer.music.set_volume(self.settings.get("master_volume"))

		# update controls visually
		for _, _, _, ctrl, key in self.tiles:
			if ctrl:
				ctrl.value = self.settings.get(key)

		self.game.restart_screen = "options"
		self.game.restarting = True
	
	def handle_input(self, events):
		for e in events:
			if self.reset_button.handle_event(e):
				return

			if e.type == pygame.KEYDOWN:
				if e.key == pygame.K_ESCAPE:
					self.game.set_state("title")
					return
				elif e.key == pygame.K_UP:
					self.selected_index = max(0, self.selected_index - 1)
					self._apply_focus()
					self._ensure_selected_visible()
					return
				elif e.key == pygame.K_DOWN:
					self.selected_index = min(len(self.tiles)-1, self.selected_index + 1)
					self._apply_focus()
					self._ensure_selected_visible()
					return
				elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
					_, _, _, ctrl, _ = self.tiles[self.selected_index]
					if isinstance(ctrl, ui.ToggleSwitch):
						ctrl.toggle()
					elif isinstance(ctrl, ui.Slider):
						ctrl.focus = True
					return
			elif e.type == pygame.MOUSEBUTTONDOWN:
				if e.button == 4:
					self.scroll_y = max(0, self.scroll_y - int(self.tile_h * 0.5))
				elif e.button == 5:
					self.scroll_y = min(self.max_scroll, self.scroll_y + int(self.tile_h * 0.5))
			elif e.type == pygame.MOUSEMOTION:
				for base_rect, label, desc, ctrl, key in self.tiles:
					ctrl.focus = ctrl.rect.collidepoint(e.pos)
				
			for base_rect, label, desc, ctrl, key in self.tiles:
				if ctrl and ctrl.handle_event(e):
					return

	def update(self, dt):
		pass

	def draw(self):
		surf = self.screen
		surf.fill((18,18,20))

		panel_rect = pygame.Rect(self.panel_x, self.panel_y, self.panel_w, self.panel_h)
		ui.draw_panel(surf, panel_rect, (30,28,32), (80,70,60), subtitle="Press ESC to return", subtitle_font=self.font_small)

		# header
		title = self.font_large.render("Settings", True, TEXT_COLOUR)
		surf.blit(title, (panel_rect.centerx - title.get_width()//2, panel_rect.y + 12))
		subtitle = self.font_small.render("Configure gameplay and audio", True, (180,170,160))
		surf.blit(subtitle, (panel_rect.centerx - subtitle.get_width()//2, panel_rect.y + 12 + title.get_height() + 4))

		# reset button
		self.reset_button.draw(surf)

		# clip to scroll area
		prev_clip = surf.get_clip()
		surf.set_clip(pygame.Rect(self.panel_x, self.visible_top, self.panel_w, self.visible_h))

		# draw tiles
		for i, (base_rect, label, desc, ctrl, key) in enumerate(self.tiles):
			draw_rect = base_rect.move(0, -self.scroll_y)

			# skip if outside visible area
			if draw_rect.bottom < self.visible_top or draw_rect.top > self.visible_bottom:
				continue

			# tile background
			tile_bg = (245,240,235) if i == self.selected_index else (240,235,230)
			pygame.draw.rect(surf, tile_bg, draw_rect, border_radius=10)

			# text
			lbl = self.font_large.render(label, True, (40,34,30))
			surf.blit(lbl, (draw_rect.x + 12, draw_rect.y + 4))
			d = self.font_small.render(desc, True, (110,100,90))
			surf.blit(d, (draw_rect.x + 12, draw_rect.y + 2 + lbl.get_height()))

			# control positioning
			if ctrl:
				if isinstance(ctrl, ui.ToggleSwitch):
					ctrl.rect.topleft = (draw_rect.right - 110, draw_rect.y + (draw_rect.h - ctrl.rect.h)//2)
				elif isinstance(ctrl, ui.Slider):
					ctrl.rect.topleft = (draw_rect.right - 260, draw_rect.y + (draw_rect.h - ctrl.rect.h)//2)
				elif isinstance(ctrl, ui.TextInput):
					ctrl.rect.topleft = (draw_rect.right - 220, draw_rect.y + (draw_rect.h - ctrl.rect.h)//2)
				ctrl.draw(surf)
		surf.set_clip(prev_clip)

# Helper classes

class ParallaxLayer:
	def __init__(self, path, speed):
		self.image = pygame.image.load(path).convert_alpha()
		self.speed = speed
		self.offset = 0.0
		self.w = self.image.get_width()
	
	def update(self, dt, camera_dx):
		# camera_dx is in pixels per second; multiply by dt for per-frame offset
		self.offset = (self.offset + camera_dx * self.speed * dt) % self.w

	def draw(self, surf):
		x = -int(self.offset)
		surf.blit(self.image, (x, 0))
		if x + self.w < surf.get_width():
			surf.blit(self.image, (x + self.w, 0))

class BeatTracker: # internal clock
	def __init__(self, interval):
		self.interval = interval
		self.last_beat_time = 0.0
		self.beat_count = 0
		self.time_acc = 0.0
	
	def update(self, dt, absolute_time = None):
		"""
		If absolute_time is provided (seconds since music start / global music clock,
		e.g. the current playback position including any MUSIC_LATENCY adjustment),
		align beats to that clock. Otherwise fall back to incremental dt accumulation.
		Returns True if a beat was triggered this update.
		"""
		beat_triggered = False

		if absolute_time is not None:
			# compute phase relative to the interval
			phase = (absolute_time % self.interval)
			# last_beat_time is time since last beat
			self.last_beat_time = phase
			# determine if a beat boundary was crossed during current frame
			# it can be approximated by checking if phase is small (~0) or if dt is large enough to cross boundary
			prev_phase = ((absolute_time - dt) % self.interval)
			# if prev_phase > phase, a beat occurred
			if prev_phase > phase:
				self.beat_count += 1
				beat_triggered = True
		else:
			self.time_acc += dt
			while self.time_acc >= self.interval:
				self.time_acc -= self.interval
				self.last_beat_time = 0.0
				self.beat_count += 1
				beat_triggered = True
			self.last_beat_time += dt

		return beat_triggered
	
	def is_on_beat(self, tolerance: float = BEAT_TOLERANCE_GOOD) -> bool:
		# ~close to the beat moment
		return abs(self.last_beat_time) <= tolerance or \
			abs(self.interval - self.last_beat_time) <= tolerance
	
	def normalised_phase(self) -> float:
		return min(1.0, self.last_beat_time / self.interval)