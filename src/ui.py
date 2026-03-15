import pygame, pygame.scrap as scrap
import helpers

def draw_panel(
	surf,
	rect,
	bg_colour,
	border_colour,
	*,
	radius=12,
	subtitle=None,
	subtitle_font=None,
	subtitle_colour=(180, 170, 160),
	subtitle_offset=20
):
	# panel border
	pygame.draw.rect(
		surf,
		border_colour,
		rect.inflate(4, 4),
		border_radius=radius
	)

	# panel background
	pygame.draw.rect(
		surf,
		bg_colour,
		rect.inflate(4, 4),
		border_radius=radius
	)

	# optional subtitle
	if subtitle and subtitle_font:
		subtitle_surf = subtitle_font().render(subtitle, True, subtitle_colour)
		subtitle_x = rect.centerx - subtitle_surf.get_width() // 2
		subtitle_y = rect.bottom + subtitle_offset
		surf.blit(subtitle_surf, (subtitle_x, subtitle_y))

def render_text(font, text, colour):
	return font.render(text, True, colour)

class Button:
	def __init__(self, rect, text, font: pygame.font.Font, on_click, *,
			  	bg=(250,244,238), fg=(40,34,30), border=(220,200,190),
				hover_bg=(255,245,235), radius=10, padding=8, id=None):
		self.rect = pygame.Rect(rect)
		self.text = text
		self.font = font
		self.on_click = on_click
		self.bg = bg
		self.fg = fg
		self.border = border
		self.hover_bg = hover_bg
		self.radius = radius
		self.padding = padding
		self.hover = False
		self.focus = False
		self.enabled = True
		self.id = id

		self._render_text()

	def _render_text(self):
		self.text_surf = self.font.render(self.text, True, self.fg)
		self.text_rect = self.text_surf.get_rect(center=self.rect.center)
	
	def set_text(self, text):
		self.text = text
		self._render_text()
	
	def handle_event(self, event):
		if not self.enabled:
			return False
		if event.type == pygame.MOUSEMOTION:
			self.hover = self.rect.collidepoint(event.pos)
		elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			if self.rect.collidepoint(event.pos):
				self._click()
				return True
		elif event.type == pygame.KEYDOWN and self.focus:
			if event.key in (pygame.K_RETURN, pygame.K_SPACE):
				self._click()
				return True
		return False
	
	def _click(self):
		if callable(self.on_click):
			self.on_click(self)
	
	def draw(self, surf):
		# background colour changes when focused or hovered
		if self.focus or self.hover:
			bg = (255, 245, 235) # warmer when focused
			border_col = (255, 200, 120)
		else:
			bg = self.bg
			border_col = self.border
		
		# draw border and background
		pygame.draw.rect(surf, border_col, self.rect.inflate(6,6), border_radius=self.radius)
		pygame.draw.rect(surf, bg, self.rect, border_radius=self.radius)

		# subtle glow when focused
		if self.focus or self.hover:
			glow = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
			glow.fill((255, 220, 160, 40))
			surf.blit(glow, self.rect.topleft, special_flags=pygame.BLEND_RGBA_ADD)

		# text
		self.text_rect = self.text_surf.get_rect(center=self.rect.center)
		surf.blit(self.text_surf, self.text_rect)

		# focus indicator outline
		if self.focus:
			pygame.draw.rect(surf, (255, 210, 140), self.rect, width=3, border_radius=self.radius)

class ToggleSwitch:
	def __init__(self, rect, value=False, radius=10,
			  	on_colour=(200, 160, 120),
				off_colour=(120, 120, 120),
				text_colour=(40, 34, 30),
				font=None):
		self.rect = pygame.Rect(rect)
		self.value = bool(value)
		self.radius = radius
		self.on_colour = on_colour
		self.off_colour = off_colour
		self.text_colour = text_colour
		self.font = font

		self.hover = False
		self.focus = False
		self.on_change = None
	
	def handle_event(self, e):
		if e.type == pygame.MOUSEMOTION:
			self.hover = self.rect.collidepoint(e.pos)
		elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
			if self.rect.collidepoint(e.pos):
				self.toggle()
				return True
		elif e.type == pygame.KEYDOWN and self.focus:
			if e.key in (pygame.K_RETURN, pygame.K_SPACE):
				self.toggle()
				return True
		return False
	
	def toggle(self):
		self.value = not self.value
		print(f"[DEBUG] Value of {self} set to {self.value}")
		if callable(self.on_change):
			self.on_change(self.value)
	
	def draw(self, surf):
		# background colour
		bg = self.on_colour if self.value else self.off_colour

		# draw box
		pygame.draw.rect(surf, bg, self.rect, border_radius=self.radius)

		# focus outline
		if self.focus:
			pygame.draw.rect(surf, (255, 210, 140), self.rect, width=2, border_radius=self.radius)
		
		# ON/OFF text
		if self.font:
			txt = "ON" if self.value else "OFF"
			txt_surf = self.font().render(txt, True, self.text_colour)
			txt_rect = txt_surf.get_rect(center=self.rect.center)
			surf.blit(txt_surf, txt_rect)

class Slider:
	def __init__(self, rect, minv=0.0, maxv=1.0, value=0.0):
		self.rect = pygame.Rect(rect)
		self.minv = float(minv)
		self.maxv = float(maxv)
		self.value = float(value)
		self.dragging = False
		self.focus = False
		self.on_change = None
	
	def handle_event(self, e):
		# mouse down -> start dragging
		if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
			if self.rect.collidepoint(e.pos):
				self.dragging = True
				self._set_from_pos(e.pos[0])
				return True

		# mouse up -> stop dragging
		elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
			self.dragging = False
		
		# mouse move while dragging
		elif e.type == pygame.MOUSEMOTION and self.dragging:
			self._set_from_pos(e.pos[0])
			return True
		
		# keyboard control when focused
		elif e.type == pygame.KEYDOWN and self.focus:
			step = (self.maxv - self.minv) * 0.02
			if e.key == pygame.K_LEFT:
				self.set(self.value - step)
				return True
			elif e.key == pygame.K_RIGHT:
				self.set(self.value + step)
				return True
		return False
	
	def _set_from_pos(self, x):
		t = (x - self.rect.x) / max(1, self.rect.w)
		val = self.minv + t * (self.maxv - self.minv)
		self.set(val)
	
	def set(self, v):
		old = self.value
		self.value = max(self.minv, min(self.maxv, v))
		print(f"[DEBUG] Value of {self} set to {self.value}")
		if self.on_change and self.value != old:
			self.on_change(self.value)
	
	def draw(self, surf):
		# track
		track_rect = pygame.Rect(self.rect.x, self.rect.centery - 4, self.rect.w, 8)
		pygame.draw.rect(surf, (80, 80, 84), track_rect, border_radius=6)

		# thumb
		t = (self.value - self.minv) / (self.maxv - self.minv) if self.maxv != self.minv else 0
		thumb_x = int(self.rect.x + t * self.rect.w)
		thumb_rect = pygame.Rect(thumb_x - 8, self.rect.centery - 12, 16, 24)
		pygame.draw.rect(surf, (200, 160, 120), thumb_rect, border_radius=6)

		# focus outline
		if self.focus:
			pygame.draw.rect(surf, (255, 210, 140), self.rect, width=2, border_radius=8)

class TextInput:
	BLINK_INTERVAL = 500 # ms

	def __init__(self, rect, text="", font=None, placeholder="", max_length=None):
		self.rect = pygame.Rect(rect)
		self.font = font
		self.text = str(text)
		self.placeholder = placeholder
		self.max_length = max_length

		# editing state
		self.focus = False
		self.cursor = len(self.text)
		self.sel_start = None # selection starts index or None

		self.dragging = False

		# visual
		self._last_blink = pygame.time.get_ticks()
		self._show_caret = True
		self.hover = False

		# callback
		self.on_change = None

		# clipboard
		try:
			scrap.init()
			self._scrap = scrap
		except Exception:
			self._scrap = None
	
	def set(self, text):
		self.text = str(text)
		self.cursor = min(len(self.text), self.cursor)
		self._call_change()

	def get(self):
		return self.text
	
	def _clamp_cursor(self):
		self.cursor = max(0, min(len(self.text), self.cursor))
	
	def _delete_selection(self):
		if self.sel_start is None:
			return False
		a, b = sorted((self.sel_start, self.cursor))
		if a == b:
			self.sel_start = None
			return False
		self.text = self.text[:a] + self.text[b:]
		self.cursor = a
		self.sel_start = None
		self._call_change()
		return True
	
	def _call_change(self):
		print(f"[DEBUG] Value of {self} set to \"{self.text}\"")
		if callable(self.on_change):
			try:
				self.on_change(self.text)
			except Exception:
				pass
	
	def _copy_selection_to_clipboard(self):
		if self.sel_start is None:
			return
		a, b = sorted((self.sel_start), self.cursor)
		s = self.text[a:b]
		if self._scrap:
			try:
				self._scrap.put(self._scrap.SCRAP_TEXT, s.encode("utf-8"))
			except Exception:
				pass
	
	def _paste_from_clipboard(self):
		if not self._scrap:
			return
		try:
			raw = self._scrap.get(self._scrap.SCRAP_TEXT)
			if not raw:
				return
		except Exception:
			return
		if self._delete_selection():
			pass
		insert_at = self.cursor
		if self.max_length is not None:
			allowed = self.max_length - len(self.text)
			s = s[:max(0, allowed)]
		self.text = self.text[:insert_at] + s + self.text[insert_at:]
		self.cursor = insert_at + len(s)
		self._call_change()

	def _update_blink(self):
		now = pygame.time.get_ticks()
		if now - self._last_blink >= TextInput.BLINK_INTERVAL:
			self._show_caret = not self._show_caret
			self._last_blink = now
	
	def handle_event(self, e):
		consumed = False

		if e.type == pygame.MOUSEMOTION:
			self.hover = self.rect.collidepoint(e.pos)
		
		if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
			if self.rect.collidepoint(e.pos):
				# focus and position cursor by click x
				self.focus = True
				self._position_cursor_from_x(e.pos[0])
				self.sel_start = None
				self._show_caret = True
				self._last_blink = pygame.time.get_ticks()
				consumed = True
			else:
				# clicking outside unfocuses
				if self.focus:
					self.focus = False
					consumed = True

		if not self.focus:
			return consumed

		# keyboard input
		if e.type == pygame.KEYDOWN:
			mods = pygame.key.get_mods()
			ctrl = mods & pygame.KMOD_CTRL
			shift = mods & pygame.KMOD_SHIFT

			# clipboard shortcuts
			if ctrl and e.key == pygame.K_a:
				# select all
				self.sel_start = 0
				self.cursor = len(self.text)
				consumed = True
			elif ctrl and e.key == pygame.K_c:
				self._copy_selection_to_clipboard()
				consumed = True
			elif ctrl and e.key == pygame.K_x:
				self._copy_selection_to_clipboard()
				self._delete_selection()
				consumed = True

			elif e.key == pygame.K_BACKSPACE:
				if self._delete_selection():
					consumed = True
				else:
					if self.cursor > 0:
						self.text = self.text[:self.cursor-1] + self.text[self.cursor:]
						self.cursor -= 1
						self._call_change()
						consumed = True

			elif e.key == pygame.K_DELETE:
				if self._delete_selection():
					consumed = True
				else:
					if self.cursor < len(self.text):
						self.text = self.text[:self.cursor] + self.text[self.cursor+1:]
						self._call_change()
						consumed = True

			elif e.key == pygame.K_LEFT:
				if shift:
					if self.sel_start is None:
						self.sel_start = self.cursor
					self.cursor = max(0, self.cursor - 1)
				else:
					if self.sel_start is not None:
						# collapse selection to left
						a, b = sorted((self.sel_start, self.cursor))
						self.cursor = a
						self.sel_start = None
					else:
						self.cursor = max(0, self.cursor - 1)
				consumed = True

			elif e.key == pygame.K_RIGHT:
				if shift:
					if self.sel_start is None:
						self.sel_start = self.cursor
					self.cursor = min(len(self.text), self.cursor + 1)
				else:
					if self.sel_start is not None:
						a, b = sorted((self.sel_start, self.cursor))
						self.cursor = b
						self.sel_start = None
					else:
						self.cursor = min(len(self.text), self.cursor + 1)
				consumed = True

			elif e.key == pygame.K_HOME:
				if shift:
					if self.sel_start is None:
						self.sel_start = self.cursor
					self.cursor = 0
				else:
					self.cursor = 0
					self.sel_start = None
				consumed = True

			elif e.key == pygame.K_END:
				if shift:
					if self.sel_start is None:
						self.sel_start = self.cursor
					self.cursor = len(self.text)
				else:
					self.cursor = len(self.text)
					self.sel_start = None
				consumed = True

			elif e.key == pygame.K_RETURN:
				# commit and unfocus
				self.focus = False
				consumed = True

			elif e.key == pygame.K_ESCAPE:
				# cancel editing (unfocus)
				self.focus = False
				consumed = True

			else:
				# text input (use e.unicode)
				if hasattr(e, "unicode") and e.unicode:
					ch = e.unicode
					if self._delete_selection():
						pass
					insert_at = self.cursor
					if self.max_length is not None:
						allowed = self.max_length - len(self.text)
						ch = ch[:max(0, allowed)]
					self.text = self.text[:insert_at] + ch + self.text[insert_at:]
					self.cursor = insert_at + len(ch)
					self._call_change()
					consumed = True

		# keep cursor valid and reset blink on activity
		self._clamp_cursor()
		if consumed:
			self._show_caret = True
			self._last_blink = pygame.time.get_ticks()
		return consumed
	
	def _position_cursor_from_x(self, x):
		# approximate cursor position by measuring text widths
		rel_x = x - (self.rect.x + 8)
		pos = 0
		acc = 0
		for i in range(len(self.text) + 1):
			seg = self.text[:i]
			w = self.font().size(seg)[0]
			if w >= rel_x:
				pos = i
				break
			pos = i
		self.cursor = pos
		self._clamp_cursor()

	def draw(self, surf):
		# background
		pygame.draw.rect(surf, (245, 240, 235), self.rect, border_radius=8)

		# focus outline
		if self.focus:
			pygame.draw.rect(surf, (255, 210, 140), self.rect, width=2, border_radius=8)
		elif self.hover:
			pygame.draw.rect(surf, (220, 210, 190), self.rect, width=1, border_radius=8)

		# prepare text surface clipped to inner area
		inner_x = self.rect.x + 8
		inner_w = max(4, self.rect.w - 16)
		text_to_draw = self.text if self.text else self.placeholder
		colour = (40, 34, 30) if self.text else (140, 130, 120)
		txt_surf = self.font().render(text_to_draw, True, colour)

		# clip and blit
		prev_clip = surf.get_clip()
		surf.set_clip(pygame.Rect(inner_x, self.rect.y, inner_w, self.rect.h))
		surf.blit(txt_surf, (inner_x, self.rect.y + (self.rect.h - txt_surf.get_height()) // 2))

		# caret
		if self.focus:
			self._update_blink()
			if self._show_caret:
				caret_x = inner_x + self.font().size(self.text[:self.cursor])[0]
				caret_rect = pygame.Rect(caret_x, self.rect.y + 6, 2, self.rect.h - 12)
				pygame.draw.rect(surf, (40, 34, 30), caret_rect)
		
		surf.set_clip(prev_clip)