"""
Main game class
"""

import pygame, sys, os, math, random, asyncio, glob, numpy
import helpers, models, sprites, particles, audio, ui, settings; from constants import *

class RhythmDodgerGame:
	def __init__(self):
		pygame.init()
		self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
		pygame.display.set_caption(NAME)
		self.clock = pygame.time.Clock()

		# fonts (scale with window height)

		self.font_small = pygame.font.Font(FONT_PATH, FONT_SMALL)
		self.font_large = pygame.font.Font(FONT_PATH, FONT_LARGE)

		# settings

		# settings file path
		settings_path = os.path.join(DATA_DIR, "settings.json")
		self.settings = settings.SettingsManager(settings_path)

		# apply immediately to audio and game state
		try:
			# master volume
			self.master_vol = float(self.settings.get("master_volume"))
			pygame.mixer.music.set_volume(self.master_vol)
		except Exception:
			pass

		self.theme = str(self.settings.get("theme")).lower()
		self.music_latency = float(self.settings.get("music_latency"))
		self.debug = bool(self.settings.get("debug"))
		self.beat_sound = bool(self.settings.get("beat_sound"))
		self.idle = bool(self.settings.get("idle"))
		self.intro = bool(self.settings.get("intro"))

		# audio

		self.audio = audio.AudioManager()

		# preload sfx
		
		for sfx in SFX:
			self.audio.load_sfx(sfx, os.path.join(SFX_DIR, f"{sfx}.wav"))

		# sprites

		self.player_sheet = sprites.SpriteSheet(helpers.get_themed(PLAYER, self.theme))
		self.player = models.Player(self.player_sheet, self.font_small)

		self.tileset_native = pygame.image.load(helpers.get_themed(TILESET, self.theme)).convert_alpha()
		self.tiles_native = []
		native_tiles_count = max(3, self.tileset_native.get_width() // NATIVE_TILE)
		for i in range(native_tiles_count):
			surf = pygame.Surface((NATIVE_TILE, NATIVE_TILE), pygame.SRCALPHA)
			surf.blit(self.tileset_native, (0,0), (i * NATIVE_TILE, 0, NATIVE_TILE, NATIVE_TILE))
			self.tiles_native.append(pygame.transform.scale(surf, (TILE_SIZE, TILE_SIZE))) # scale to TILE_SIZE
		
		# obstacles

		self.obstacles_img = pygame.image.load(helpers.get_themed(OBSTACLES, self.theme)).convert_alpha()

		# split obstacles into frames (assume horizontal strip)
		self.obstacle_sprites = []
		count = max(1, self.obstacles_img.get_width() // NATIVE_OBS)
		for i in range(count):
			surf = pygame.Surface((NATIVE_OBS, NATIVE_OBS), pygame.SRCALPHA)
			surf.blit(self.obstacles_img, (0,0), (i * NATIVE_OBS, 0, NATIVE_OBS, NATIVE_OBS))
			self.obstacle_sprites.append(surf)
		
		# mascot

		self.mascot_sheet = sprites.SpriteSheet(helpers.get_themed(MASCOT, self.theme))
		self.mascot = models.Mascot(self.mascot_sheet, self.font_small, self.theme)

		# beat bar

		self.beat_icon_img = None
		self.beat_marker_img = None

		if os.path.exists(helpers.get_themed(HEARTBEAT, self.theme)):
			try:
				img = pygame.image.load(helpers.get_themed(HEARTBEAT, self.theme)).convert_alpha()
				target = HEARTBEAT_SIZE
				self.beat_icon_img = pygame.transform.scale(img, (target, target))
			except Exception:
				self.beat_icon_img = None
		
		# beat bar animation state
		self.beat_icon_scale = BEAT_ICON_SCALE_DEFAULT
		self.beat_icon_target_scale = BEAT_ICON_SCALE_DEFAULT
		self.beat_icon_anim_time = 0.0
		self.beat_icon_anim_duration = 0.22
		self.beat_bar_pulse = 0.0

		# parallax

		self.bg_layers = helpers.load_parallax_layers(os.path.join(SPRITES_DIR, self.theme))

		# particles

		self.particles = particles.ParticleSystem(300)

		# beat / music

		self.current_track = None
		self.beat_tracker = models.BeatTracker(60.0 / DEFAULT_BPM)
		self.music_started = False
		self.music_start_time = 0.0
		self.beats_until_next_obstacle = helpers.space_obstacle()

		# game state

		self.running = True
		self.restarting = False
		self.state = "title"
		self.score = 0
		self.best_score = 0
		self.combo = 0
		self.max_combo = 0

		# judgement

		self.last_judgement = ""
		self.judgement_timer = 0.0

		# accuracy counters

		self.total_jumps = 0
		self.accurate_jumps = 0

		# obstacles

		self.obstacles = []

		# UI / shake

		self.shake_time = 0.0
		self.shake_intensity = 0.0

		# day/night

		self.time_of_day = self.time_raw = random.random()

		# weather

		self.raining = False
		self.rain_timer = 0.0

		# load tracks list

		self.available_tracks = []
		for fn, artist, name, bpm, intro in TRACKS:
			path = os.path.join(MUSIC_DIR, fn)
			self.available_tracks.append((path, artist, name, bpm, intro))

		# start a random track

		self.start_random_track()

		# hud

		self.left_margin = int(WINDOW_WIDTH * UI_MARGIN_FRAC)
		self.top_margin = int(WINDOW_HEIGHT * UI_MARGIN_FRAC)

		pause_size = max(32, int(WINDOW_WIDTH * 0.04))
		pause_x = int(WINDOW_WIDTH * 0.02)
		pause_y = WINDOW_HEIGHT - pause_size - int(WINDOW_HEIGHT * 0.02)

		self.pause_button = ui.Button(
			(pause_x, pause_y, pause_size, pause_size),
			"",
			self.font_small,
			helpers._with_click_sfx(lambda b: self.toggle_pause(), self.audio),
			radius=8
		)

		# pause overlay buttons
		btn_w = 280
		btn_h = max(48, int(WINDOW_HEIGHT * 0.07))
		centre_x = WINDOW_WIDTH // 2
		panel_w = int(WINDOW_WIDTH * 0.6)
		panel_x = WINDOW_WIDTH//2 - panel_w//2

		# resume button (from pause overlay)
		self.pause_resume_btn = ui.Button(
			(centre_x - btn_w//2, int(WINDOW_HEIGHT*0.55), btn_w, btn_h),
			"Resume",
			self.font_large,
			helpers._with_click_sfx(lambda b: self.set_state("playing"), self.audio),
			radius=10
		)

		# back to title button (from pause overlay)
		self.pause_title_btn = ui.Button(
			(centre_x - btn_w//2, int(WINDOW_HEIGHT*0.65), btn_w, btn_h),
			"Back to Title",
			self.font_large,
			lambda b: self.set_state("title"),
			radius=10
		)

		# game over buttons (from gameover)
		go_btn_w = 220
		go_btn_h = max(44, int(WINDOW_HEIGHT * 0.06))
		go_x = WINDOW_WIDTH//2 - go_btn_w//2

		self.gameover_again_btn = ui.Button(
			(go_x, int(WINDOW_HEIGHT*0.6), go_btn_w, go_btn_h),
			"Play Again",
			self.font_small,
			lambda b: self._play_again(),
			radius=8
		)

		self.gameover_title_btn = ui.Button(
			(go_x, int(WINDOW_HEIGHT*0.6) + go_btn_h + 12, go_btn_w, go_btn_h),
			"Title Screen",
			self.font_small,
			lambda b: self.set_state("title"),
			radius=8
		)

		# mascot position in top-left near HUD
		self.mascot.x = self.left_margin
		self.mascot.y = self.top_margin

		# views

		self.title_screen = models.TitleScreen(self)
		self.song_select = models.SongSelectScreen(self)
		self.settings_screen = models.SettingsScreen(self)

	# game state

	def set_state(self, new_state):
		prev = self.state
		self.state = new_state
		# play return sound when going back to title
		if new_state == "title" and prev not in ("title", "song_select", "options"):
			try:
				self.audio.play_sfx("ui_return_title", 0.9)
				if self.title_screen and not self.title_screen.title_music_loaded:
					self.title_screen.enter_title_music()
			except: pass
		if new_state == "gameover" and prev != "gameover":
			try:
				if self.idle:
					self._play_again()
				pygame.mixer.music.set_volume(0.12)
				self.gameover_again_btn.focus = True
				self.gameover_title_btn.focus = False

				print()
				print(f"[REPORT] Score: {self.score}")
				print(f"[REPORT] Best score: {self.best_score}")
				print(f"[REPORT] Max combo: {self.max_combo}")
				print(f"[REPORT] Beat accuracy: {helpers.get_accuracy_percent(self.accurate_jumps, self.total_jumps)}%")
				print(f"[REPORT] Rank: {helpers.get_rank(helpers.get_accuracy_percent(self.accurate_jumps, self.total_jumps))}")
				print()
			except: pass
		if new_state == "playing" and prev != "playing":
			self.title_screen.title_music_loaded = False
			try: pygame.mixer.music.set_volume(self.master_vol)
			except: pass
		if new_state == "paused" and prev != "paused":
			try:
				pygame.mixer.music.set_volume(0.12)
				self.pause_resume_btn.focus = True
				self.pause_title_btn.focus = False
				self.pause_time_ticks = pygame.time.get_ticks()
			except: pass
		if new_state == "playing" and prev == "paused":
			if self.pause_time_ticks:
				elapsed_ms = pygame.time.get_ticks() - self.pause_time_ticks
				self.music_start_time += elapsed_ms / 1000.0
	
	def toggle_pause(self):
		if self.state == "playing":
			self.set_state("paused") # dim and open options overlay
		elif self.state == "paused":
			self.set_state("playing")
	
	def _play_again(self):
		# restart current track and go to playing
		if self.current_track:
			self.start_track(self.current_track)
		self.reset()
		self.set_state("playing")

	# music / beat

	def start_track(self, track):
		self.obstacles.clear()
		self.player.reset()
		self.score = 0
		self.combo = 0
		self.max_combo = 0
		self.total_jumps = 0
		self.accurate_jumps = 0
		self.countin_active = False
		self.countin_timer = 0.0
		self.player_invulnerable_time = 0.6

		self.audio.load_music(track["path"] + ".ogg")
		self.audio.play_music(-1)
		pygame.mixer.music.set_volume(self.master_vol)
		self.music_started = True
		self.music_start_time = pygame.time.get_ticks() / 1000.0 + self.music_latency
		self.beat_tracker = models.BeatTracker(60.0 / track["bpm"])

		# play UI decide sfx
		try:
			self.audio.play_sfx("ui_decide_title", 0.9)
		except Exception:
			pass

		intro = float(track["intro"])
		if intro > 0.0 and self.intro:
			self.countin_active = True
			self.countin_timer = intro
			self._suspend_obstacles = True
		else:
			self._suspend_obstacles = False

	def start_random_track(self):
		if not self.available_tracks:
			return
		path, artist, name, bpm, intro = random.choice(self.available_tracks)
		self.current_track = {"path": path, "artist": artist, "name": name, "bpm": bpm, "intro": intro}
		self.start_track(self.current_track)

	# input handling

	def handle_events(self):
		events = pygame.event.get()
		jump_pressed = False

		for event in events:
			if event.type == pygame.QUIT:
				self.running = False
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_q and (self.state == "title"):
					self.running = False
				elif event.key == pygame.K_ESCAPE:
					# behave contextually: if playing -> pause; if title -> do nothing; if options -> back
					if self.state == "playing" and not self.countin_active:
						self.set_state("paused")
					elif self.state == "playing" and self.countin_active:
						self.set_state("title")
					elif self.state == "paused":
						self.set_state("playing")
					elif self.state == "options":
						self.set_state("title")
				# only allow gameplay jump when playing
				if self.state == "playing" and event.key in (pygame.K_SPACE, pygame.K_UP) and not self.countin_active:
					jump_pressed = True

		# route events to state-specific handlers
		if self.state == "title":
			self.title_screen.handle_input(events)
		elif self.state == "options":
			self.settings_screen.handle_input(events)
		elif self.state == "playing":
			for e in events:
				if self.pause_button.handle_event(e):
					continue
		elif self.state == "paused":
			for e in events:
				if self.pause_resume_btn.handle_event(e):
					continue
				if self.pause_title_btn.handle_event(e):
					continue
				if e.type == pygame.KEYDOWN:
					if e.key in (pygame.K_UP, pygame.K_DOWN):
						# toggle focus
						self.pause_resume_btn.focus, self.pause_title_btn.focus = self.pause_title_btn.focus, self.pause_resume_btn.focus
					elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
						focused = self.pause_resume_btn if self.pause_resume_btn.focus else self.pause_title_btn
						focused._click()
		elif self.state == "song_select":
			self.song_select.handle_input(events)
			return False
		elif self.state == "gameover":
			for e in events:
				if self.gameover_title_btn.handle_event(e):
					continue
				if self.gameover_again_btn.handle_event(e):
					continue
				if e.type == pygame.KEYDOWN:
					if e.key in (pygame.K_LEFT, pygame.K_RIGHT):
						# toggle focus
						self.gameover_title_btn.focus, self.gameover_again_btn.focus = self.gameover_again_btn.focus, self.gameover_title_btn.focus
					elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
						focused = self.gameover_title_btn if self.gameover_title_btn.focus else self.gameover_again_btn
						focused._click()

		return jump_pressed
	
	# game update

	def update(self, dt, jump_pressed):
		# title screen update
		if self.state == "title":
			self.title_screen.update(dt)
			return

		# options screen (placeholder)
		if self.state == "options":
			self.settings_screen.update(dt)
			return

		# song select screen
		if self.state == "song_select":
			#self.song_select.update(dt)
			return

		# pause screen
		if self.state == "paused":
			self.particles.update(dt)
			self.mascot.update(dt)
			return

		# gameover state: keep particles/mascot animating
		if self.state == "gameover":
			self.particles.update(dt)
			self.mascot.update(dt)
			return

		if getattr(self, "player_invulnerable_time", 0.0) > 0.0:
			self.player_invulnerable_time = max(0.0, self.player_invulnerable_time - dt)

		if self.countin_active:
			self.countin_timer -= dt
			if self.countin_timer <= 0.0:
				self.countin_active = False
				self.countin_timer = 0.0
				self._suspend_obstacles = False

		# compute absolute time if music started
		absolute_time = None
		if self.music_started and self.current_track:
			absolute_time = (pygame.time.get_ticks() / 1000.0) - self.music_start_time
			# keep absolute_time positive
			if absolute_time < 0: absolute_time = 0.0

		# update beat tracker with absolute time if available
		beat_triggered = self.beat_tracker.update(dt, absolute_time)

		if beat_triggered:
			print()
			print(f"[DEBUG] Time of day: {self.time_of_day}")
			print(f"[DEBUG] Absolute time in game: {absolute_time}")
			print(f"[DEBUG] Beats until next obstacle: {self.beats_until_next_obstacle}")
			print()

			if self._suspend_obstacles == False:
				if self.beat_sound:
					self.audio.play_sfx("ui_1", 1)

				if self.beats_until_next_obstacle == 0:
					# spawn obstacle
					spawn_x = WINDOW_WIDTH + int(WINDOW_WIDTH * 0.05)
					sprite = random.choice(self.obstacle_sprites)
					self.obstacles.append(models.Obstacle(spawn_x, sprite))

				if (self.beats_until_next_obstacle > -1):
					# count down until next obstacle
					self.beats_until_next_obstacle -= 1
				else:
					if self.idle:
						jump_pressed = True
					# reset spacing
					self.beats_until_next_obstacle = helpers.space_obstacle()

			# cute beat bar reactions

			# icon bounce: set target scale and reset anim timer
			self.beat_icon_target_scale = BEAT_ICON_SCALE_BEAT # pop scale on beat
			self.beat_icon_anim_time = 0.0

			# small pulse for the bar background
			self.beat_bar_pulse = 1.0

		# player jump
		if jump_pressed:
			self.player.try_jump()

			# count jumps
			self.total_jumps += 1

			# determine judgement
			judgement = helpers.get_timing_judgement(self.beat_tracker)
			self.last_judgement = judgement
			self.judgement_timer = 0.6 # show for 0.6s

			if judgement == "Perfect!":
				self.combo += 1
				self.score += 15 + self.combo
				self.accurate_jumps += 1
				self.audio.play_sfx("beat_perfect", 0.9)

				# particles + mascot
				cx = self.player.x + self.player.width / 2
				cy = self.player.y + self.player.height / 2
				self.particles.emit(cx, cy, count = 12, colour = (255, 230, 180))
				self.mascot.react("happy")

				# small extra icon pop
				self.beat_icon_target_scale = BEAT_ICON_SCALE_PERFECT
				self.beat_icon_anim_time = 0.0
			elif judgement == "Good!":
				self.combo += 1
				self.score += 8 + self.combo
				self.accurate_jumps += 1
				self.audio.play_sfx("beat_good", 0.8)
				self.particles.emit(self.player.x + 12, self.player.y + 12, count = 6, colour = (220, 200, 160))
				self.mascot.react("happy")
			else:
				self.combo = 0
				self.audio.play_sfx("beat_miss", 0.6)
				self.mascot.react("sad")
			self.max_combo = max(self.max_combo, self.combo)

		# update player physics
		self.player.update(dt)

		# update obstacles
		for obs in self.obstacles:
			obs.update(dt)
		
		# collision
		player_rect = self.player.rect
		player_mask = self.player.get_mask()

		if self.player_invulnerable_time > 0.0:
			pass
		else:
			for obs in self.obstacles:
				# quick reject by rect
				if not player_rect.colliderect(obs.rect):
					continue

				# ensure obstacle has a mask
				obs_mask = getattr(obs, "mask", None)
				if obs_mask is None:
					# fallback: treat as rect collision if no mask
					self.set_state("gameover")
					self.best_score = max(self.best_score, self.score)
					self.audio.play_sfx("beat_miss", 0.8)
					self.apply_screen_shake(6, 0.18)
					break

				# compute offset from player mask to obstacle mask
				offset_x = int(obs.rect.x - player_rect.x)
				offset_y = int(obs.rect.y - player_rect.y)

				# if either mask is missing, skip
				if player_mask is None:
					# fallback to rect collision
					self.set_state("gameover")
					self.best_score = max(self.best_score, self.score)
					self.audio.play_sfx("beat_miss", 0.8)
					self.apply_screen_shake(6, 0.18)
					break

				# check overlap: returns point or None
				overlap_point = player_mask.overlap(obs_mask, (offset_x, offset_y))
				if overlap_point:
					# pixel-perfect collision detected
					self.set_state("gameover")
					self.best_score = max(self.best_score, self.score)
					self.audio.play_sfx("beat_miss", 0.8)
					self.apply_screen_shake(6, 0.18)
					break
		
		# remove offscreen
		self.obstacles = [o for o in self.obstacles if not o.offscreen()]
		
		# passive score over time
		if self.countin_active is False:
			self.score += dt * 2 * SPRITE_SCALE # small survival score

		# particles and mascot update
		self.particles.update(dt)
		self.mascot.update(dt)

		# judgement timer
		if self.judgement_timer > 0:
			self.judgement_timer -= dt

		# day/night
		self.time_raw += dt * 0.03
		self.time_of_day = 1.0 - abs((self.time_raw % 2.0) - 1.0)

		# toggle rain occasionally
		self.rain_timer -= dt
		if self.rain_timer <= 0:
			self.rain_timer = random.uniform(8.0, 20.0)
			self.raining = random.random() < 0.25
			if self.raining:
				self.particles.emit_rain(WINDOW_WIDTH, WINDOW_HEIGHT, count = 60)
		
		# advance beat icon animation

		if self.beat_icon_anim_time < self.beat_icon_anim_duration:
			self.beat_icon_anim_time += dt
			# when animation completes, return to target scale smoothly
			if self.beat_icon_anim_time >= self.beat_icon_anim_duration:
				self.beat_icon_scale = self.beat_icon_target_scale
				# schedule return to normal
				self.beat_icon_target_scale = BEAT_ICON_SCALE_DEFAULT
				self.beat_icon_anim_time = 0.0
		else:
			# small decay to ensure scale returns to default
			self.beat_icon_scale += (BEAT_ICON_SCALE_DEFAULT - self.beat_icon_scale) * min(1.0, dt * 8.0)
		
		# beat bar pulse decay

		if self.beat_bar_pulse > 0:
			self.beat_bar_pulse = max(0.0, self.beat_bar_pulse - dt * BEAT_BAR_PULSE_DECAY)
	
	# rendering

	def draw_ground(self, surf):
		# tiles_native[0] = ground tile (top soil)
		# tiles_native[1] = grass edge (drawn above ground)
		# tiles_native[2] = shadow/subsoil (drawn below ground repeatedly)

		tiles = self.tiles_native

		# ensure tiles exist
		if not tiles:
			return
		
		# draw grass edge
		if len(tiles) > 1:
			grass = tiles[1]
			x = 0
			while x < WINDOW_WIDTH:
				surf.blit(grass, (x, GROUND_Y))
				x += TILE_SIZE

		# draw tiles below ground to bottom of screen
		if len(tiles) > 2:
			ground = tiles[0]
			y = GROUND_Y + TILE_SIZE
			while y < WINDOW_HEIGHT:
				x = 0
				while x < WINDOW_WIDTH:
					surf.blit(ground, (x, y))
					x += TILE_SIZE
				y += TILE_SIZE
		else:
			pygame.draw.rect(surf, (40, 36, 32), pygame.Rect(0, GROUND_Y + TILE_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT - (GROUND_Y + TILE_SIZE))) # fallback
		
	def draw_beat_bar(self, surf):
		"""
		Cute beat bar:
		- Rounded pastel pill background
		- Soft left-to-right gradient fill showing phase
		- Small icon that bounces on beat
		- Tiny centre marker sprite
		- Compact layout so it fits UI
		"""
		# layout
		bar_w = BEAT_BAR_WIDTH
		bar_h = BEAT_BAR_HEIGHT
		margin = int(WINDOW_WIDTH * UI_MARGIN_FRAC)
		x = WINDOW_WIDTH - bar_w - margin
		y = margin

		# apply pulse scale (cute pop)
		pulse_scale = 1.0 + BEAT_BAR_PULSE_SCALE * self.beat_bar_pulse
		scaled_w = int(bar_w * pulse_scale)
		scaled_h = int(bar_h * pulse_scale)

		# recentre the scaled bar
		x -= (scaled_w - bar_w) // 2
		y -= (scaled_h - bar_h) // 2
		bar_w = scaled_w
		bar_h = scaled_h
		self.beat_bar_w = bar_w
		self.beat_bar_h = bar_h
		self.beat_bar_x = x
		self.beat_bar_y = y

		# base pill background (soft pastel)
		pygame.draw.rect(surf, BEAT_BAR_BORDER_COLOUR, pygame.Rect(x-2, y-2, bar_w+4, bar_h+4), border_radius=bar_h//2)
		pygame.draw.rect(surf, BEAT_BAR_BG_COLOUR, pygame.Rect(x, y, bar_w, bar_h), border_radius=bar_h//2)

		phase = self.beat_tracker.normalised_phase()
		fill_w = int(bar_w * phase)
		colour = (82, 82, 82) if self.theme == "dinosaur" else BEAT_BAR_COLOUR
		pygame.draw.rect(surf, colour, pygame.Rect(x, y, fill_w, bar_h), border_radius = 6)

		# centre marker
		cx = x + bar_w // 2
		pygame.draw.line(surf, BEAT_MARKER_COLOUR, (cx, y-4), (cx, y+bar_h+4), max(1, int(WINDOW_WIDTH * 0.0015)))
		
		# animated beat icon (left side of fill, or if no fill, at left edge)
		icon_x = x + max(6, int(bar_h * 0.2))
		icon_y = y + bar_h//2

		# update animation interpolation
		t = min(1.0, max(0.0, self.beat_icon_anim_time / max(0.0001, self.beat_icon_anim_duration)))

		# ease out bounce
		s = self.beat_icon_scale + (self.beat_icon_target_scale - self.beat_icon_scale) * (1 - (1 - t)**2)
		iw = int(self.beat_icon_img.get_width() * s)
		ih = int(self.beat_icon_img.get_height() * s)
		img = pygame.transform.scale(self.beat_icon_img, (iw, ih))
		surf.blit(img, (icon_x - iw//2, icon_y - ih//2))

		# small label under the bar (tiny, unobtrusive)
		if self.current_track:
			label = ""
			if self.debug:
				label = f"{int(self.clock.get_fps())} FPS - "
			label += f"{self.current_track['bpm']} BPM"
			lbl = self.font_small.render(label, True, (120, 110, 100))
			surf.blit(lbl, (x + bar_w - lbl.get_width(), y + bar_h + int(WINDOW_HEIGHT * 0.006)))

	def draw_judgement(self, surf):
		if self.judgement_timer > 0 and self.last_judgement:
			surf_text = self.font_small.render(self.last_judgement, True, TEXT_COLOUR)
			bar_width = self.beat_bar_w
			bar_height = self.beat_bar_h
			bar_x = self.beat_bar_x
			bar_y = self.beat_bar_y
			x = bar_x + bar_width - surf_text.get_width()
			y = bar_y + bar_height + int(WINDOW_HEIGHT * 0.05)
			colour = (200, 255, 200) if "Perfect" in self.last_judgement else (220, 220, 180) if "Good" in self.last_judgement else (255, 200, 180) # colour code
			surf_text = self.font_small.render(self.last_judgement, True, colour)
			surf.blit(surf_text, (x, y))

	def draw_track_info(self, surf):
		if not self.current_track:
			return
		
		text = f"{self.current_track['path']}.ogg" if self.debug else f"{self.current_track['artist']} - {self.current_track['name']} ({self.current_track['bpm']} BPM)"
		surf_text = self.font_small.render(text, True, TEXT_COLOUR)

		margin = int(WINDOW_WIDTH * UI_MARGIN_FRAC)
		bottom_tile_top = GROUND_Y + TILE_SIZE

		# position: above bottom shadow tiles, aligned to bottom-right tile grid

		x = WINDOW_WIDTH - surf_text.get_width() - margin
		y = max(bottom_tile_top - surf_text.get_height() - int(WINDOW_HEIGHT * 0.01), WINDOW_HEIGHT - surf_text.get_height() - margin)
		surf.blit(surf_text, (x, y))

	def draw_hud(self, surf):
		# mascot, scaled to match text height (left)
		mascot_size = max(MASCOT_SIZE, int(self.font_small.get_height() * 1.2))
		mascot_x = self.left_margin
		mascot_y = self.top_margin
		self.mascot.draw(surf, x=mascot_x, y=mascot_y, size=mascot_size)

		# info cluster (left)
		text_x = mascot_x + mascot_size + int(WINDOW_WIDTH * 0.01)
		line_h = self.font_small.get_height() + int(WINDOW_HEIGHT * 0.008)
		y0 = mascot_y

		# score
		score_surf = self.font_small.render(f"Score: {int(self.score)}", True, TEXT_COLOUR)
		surf.blit(score_surf, (text_x, y0))
		# combo
		combo_surf = self.font_small.render(f"Combo: {self.combo}", True, TEXT_COLOUR)
		surf.blit(combo_surf, (text_x, y0 + line_h))
		# best
		best_surf = self.font_small.render(f"Best: {int(self.best_score)}", True, TEXT_COLOUR)
		surf.blit(best_surf, (text_x, y0 + line_h * 2))

		# beat cluster (right)
		self.draw_beat_bar(surf)
		self.draw_judgement(surf)
		self.draw_track_info(surf)

		# pause button
		self.pause_button.draw(surf)

		if self.pause_button:
			self.pause_button.draw(surf)

			r = self.pause_button.rect
			bar_w = max(3, r.w // 6)
			bar_h = int(r.h * 0.6)
			gap = bar_w

			cx = r.centerx
			cy = r.centery

			left_bar = pygame.Rect(0, 0, bar_w, bar_h)
			right_bar = pygame.Rect(0, 0, bar_w, bar_h)

			left_bar.center = (cx - gap // 2 - bar_w // 2, cy)
			right_bar.center = (cx + gap // 2 + bar_w // 2, cy)

			pygame.draw.rect(surf, BEAT_BAR_BG_COLOUR, left_bar, border_radius=2)
			pygame.draw.rect(surf, BEAT_BAR_BG_COLOUR, right_bar, border_radius=2)

	def apply_screen_shake(self, intensity = 4, duration = 0.12):
		self.shake_time = duration
		self.shake_intensity = intensity

	def draw_game_over(self, surf):
		# dim background
		overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
		overlay.fill((8, 8, 10, 200))
		surf.blit(overlay, (0, 0))

		panel_w = int(WINDOW_WIDTH * 0.6) # centre panel in the middle of the window
		panel_h = int(WINDOW_HEIGHT * 0.45)
		panel_x = (WINDOW_WIDTH - panel_w) // 2
		panel_y = (WINDOW_HEIGHT - panel_h) // 2
		ui.draw_panel(surf, pygame.Rect(panel_x, panel_y, panel_w, panel_h), (40,36,44), (120,100,90))
		title = self.font_large.render("GAME OVER", True, TEXT_COLOUR)
		surf.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, panel_y + int(panel_h * 0.06)))
		score_info = self.font_small.render(f"Score: {int(self.score)}   Best: {int(self.best_score)}   Max Combo: {self.max_combo}", True, TEXT_COLOUR)
		surf.blit(score_info, (WINDOW_WIDTH//2 - score_info.get_width()//2, panel_y + int(panel_h * 0.22)))
		accuracy = helpers.get_accuracy_percent(self.accurate_jumps, self.total_jumps)
		acc_text = self.font_small.render(f"Beat Accuracy: {accuracy}%", True, TEXT_COLOUR)
		surf.blit(acc_text, (WINDOW_WIDTH//2 - acc_text.get_width()//2, panel_y + int(panel_h * 0.34)))
		rank = helpers.get_rank(accuracy)
		rank_text = self.font_small.render(f"Rank: {rank}", True, TEXT_COLOUR)
		surf.blit(rank_text, (WINDOW_WIDTH//2 - rank_text.get_width()//2, panel_y + int(panel_h * 0.44)))
		#hint = self.font_small.render("Press R / Enter / Space to restart", True, TEXT_COLOUR)
		#surf.blit(hint, (WINDOW_WIDTH//2 - hint.get_width()//2, panel_y + int(panel_h * 0.62)))

		# buttons
		btn_w = 220
		btn_h = max(44, int(WINDOW_HEIGHT * 0.06))
		gap = 24
		total_w = btn_w * 2 + gap
		start_x = WINDOW_WIDTH//2 - total_w//2
		y = panel_y + int(panel_h * 0.77)

		self.gameover_again_btn.rect.topleft = (start_x, y)
		self.gameover_again_btn.rect.size = (btn_w, btn_h)
		self.gameover_again_btn._render_text()

		self.gameover_title_btn.rect.topleft = (start_x + btn_w + gap, y)
		self.gameover_title_btn.rect.size = (btn_w, btn_h)
		self.gameover_title_btn._render_text()

		self.gameover_title_btn.draw(surf)
		self.gameover_again_btn.draw(surf)

	# render

	def render(self):
		# title screen
		if self.state == "title":
			self.title_screen.draw()
			pygame.display.flip()
			return

		if self.state == "options":
			self.settings_screen.draw()
			pygame.display.flip()
			return
		
		# ref: 'pause' state handled at bottom of method

		if self.state == "song_select":
			self.song_select.draw()
			pygame.display.flip()
			return

		t = helpers.day_night_tint(self.time_of_day)
		tint = (t, t, t)

		# draw to scene surface for shake
		scene = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
		scene.fill((t, t, t))

		# camera_dx: use obstacle speed as camera reference (pixels/sec)
		camera_dx = OBSTACLE_SPEED

		for layer in self.bg_layers:
			alpha = (255 * ((1 - (t / 255)) ** 4)) if layer.night else None
			layer.update(1.0 / FPS, camera_dx)
			layer.draw(scene, alpha)

		# day/night tint
		overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
		overlay.fill(tint)
		overlay.set_alpha(50)
		scene.blit(overlay, (0, 0))

		# player squash/stretch micro-animations
		scale_x, scale_y = 1.0, 1.0
		if self.player.vy < -50 * SPRITE_SCALE:
			scale_y = 1.06; scale_x = 0.96
		elif self.player.on_ground and self.player.recently_landed:
			scale_y = 0.9; scale_x = 1.12
		self.player.draw(scene, scale_x, scale_y)

		# obstacles
		for obs in self.obstacles:
			obs.draw(scene)

		# ground and tiles (scaled)
		self.draw_ground(scene)

		# mascot
		#self.mascot.draw(scene)

		# particles
		self.particles.draw(scene)

		# subtle rain overlay
		if self.raining:
			rain_overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
			rain_overlay.fill((180, 200, 230, 20))
			scene.blit(rain_overlay, (0, 0))
		
		# HUD (incl. mascot)
		self.draw_hud(scene)

		if self.countin_active:
			# dim the whole screen
			dim = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), flags=pygame.SRCALPHA)
			dim.fill((0, 0, 0, 160))

			scene.blit(dim, (0, 0))

			remaining = max(0.0, self.countin_timer)
			display_num = int(math.ceil(remaining)) if remaining > 0 else 0
			if display_num == 1:
				text = "GO!"
			else:
				text = str(display_num)

			font = self.font_large

			txt_surf = font.render(text, True, (250, 250, 250))
			shadow = font.render(text, True, (20, 20, 20))
			cx = WINDOW_WIDTH // 2
			cy = WINDOW_HEIGHT // 2
			scene.blit(shadow, (cx - shadow.get_width()//2 + 4, cy - shadow.get_height()//2 + 4))
			scene.blit(txt_surf, (cx - txt_surf.get_width()//2, cy - txt_surf.get_height()//2))

		if self.debug:
			debug_colour = (255, 0, 0)
			pygame.draw.rect(scene, debug_colour, self.player.rect, 1)
			if self.obstacles:
				for o in self.obstacles:
					pygame.draw.rect(scene, debug_colour, o.rect, 1)
			#if self.particles:
			#	for p in self.particles:
			#		pygame.draw.rect(self.screen, debug_colour, p.rect, 1)

		# subtle judgement flash on perfect
		if "Perfect" in self.last_judgement and self.judgement_timer > 0:
			flash = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
			alpha = int(120 * (self.judgement_timer / 0.6))
			flash.fill((220, 255, 200, alpha))
			scene.blit(flash, (0, 0))

		# screen shake
		if self.shake_time > 0:
			self.shake_time -= 1.0 / FPS
			dx = random.uniform(-1, 1) * self.shake_intensity
			dy = random.uniform(-1, 1) * self.shake_intensity
			self.screen.blit(scene, (int(dx), int(dy)))
		else:
			self.screen.blit(scene, (0, 0))
		
		# game over overlay
		if self.state == "gameover":
			self.draw_game_over(self.screen)

		if self.state == "paused":
			# then dim
			overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
			overlay.fill((8, 8, 10, 200))
			self.screen.blit(overlay, (0, 0))
			
			# draw options panel centred
			ui.draw_panel(self.screen, pygame.Rect(WINDOW_WIDTH*0.2, WINDOW_HEIGHT*0.2, WINDOW_WIDTH*0.6,  WINDOW_HEIGHT*0.6), (40, 36, 44), (120, 100, 90), subtitle="Press ESC to return", subtitle_font=self.font_small)
			title = self.font_large.render("Paused", True, TEXT_COLOUR)
			self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, int(WINDOW_HEIGHT*0.3)))

			# buttons
			self.pause_resume_btn.draw(self.screen)
			self.pause_title_btn.draw(self.screen)
		
		pygame.display.flip()

	# reset
	
	def reset(self):
		self.player.reset()
		self.obstacles.clear()
		self.beat_tracker = models.BeatTracker(60.0 / (self.current_track['bpm'] if self.current_track else DEFAULT_BPM))
		self.set_state("playing")
		self.score = 0
		self.combo = 0
		self.max_combo = 0
		self.total_jumps = 0
		self.accurate_jumps = 0
		self.beats_until_next_obstacle = helpers.space_obstacle()

		# restart music
		if self.current_track:
			try:
				self.audio.play_music(-1)
				self.music_start_time = pygame.time.get_ticks() / 1000.0 + self.music_latency
				self.music_started = True
			except Exception:
				self.music_started = False

	# main loop

	def run(self):
		while self.running:
			if self.restarting:
				self.__init__()
				self.set_state(self.restart_screen)
			dt_ms = self.clock.tick(FPS)
			dt = dt_ms / 1000.0

			jump_pressed = self.handle_events()
			self.update(dt, jump_pressed)
			self.render()

		pygame.quit()
		sys.exit()

if __name__ == "__main__": # one of the things i hate most about python
	game = RhythmDodgerGame()
	game.run()