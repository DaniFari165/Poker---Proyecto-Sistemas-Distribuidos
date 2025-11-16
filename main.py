import pygame, sys
from collections import deque
import numpy as np
from moviepy import VideoFileClip
from net.client import NetClient
import webbrowser

pygame.init()
WIDTH, HEIGHT = 960, 540
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Póker Simplificado")
CLOCK = pygame.time.Clock()
FONT = pygame.font.SysFont("arial", 24)
SMALL = pygame.font.SysFont("arial", 18)

# ---------- Widgets ----------
class Button:
    def __init__(self, rect, text, on_click):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.on_click = on_click
        self.hover = False

    def handle_event(self, e):
        if e.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(e.pos)
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.rect.collidepoint(e.pos):
                self.on_click()

    def draw(self, surf):
        color = (60,120,200) if self.hover else (40,90,160)
        pygame.draw.rect(surf, color, self.rect, border_radius=10)
        pygame.draw.rect(surf, (20,40,80), self.rect, 2, border_radius=10)
        txt = FONT.render(self.text, True, (255,255,255))
        surf.blit(txt, txt.get_rect(center=self.rect.center))


class TextInput:
    def __init__(self, rect, placeholder=""):
        self.rect = pygame.Rect(rect)
        self.text = ""
        self.placeholder = placeholder
        self.active = False
        self.cursor_time = 0
        self.show_cursor = True

    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.active = self.rect.collidepoint(e.pos)
        if not self.active:
            return None
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_RETURN:
                val = self.text
                self.text = ""
                return val
            elif e.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif e.unicode and e.key != pygame.K_RETURN:
                self.text += e.unicode
        return None

    def update(self, dt):
        self.cursor_time += dt
        if self.cursor_time >= 0.5:
            self.cursor_time = 0
            self.show_cursor = not self.show_cursor

    def draw(self, surf):
        pygame.draw.rect(surf, (250,250,250), self.rect, border_radius=8)
        pygame.draw.rect(surf, (180,180,180), self.rect, 2, border_radius=8)
        txt_show = self.text if (self.text or self.active) else self.placeholder
        color = (0,0,0) if (self.text or self.active) else (120,120,120)
        txt = SMALL.render(txt_show, True, color)
        surf.blit(txt, (self.rect.x+10, self.rect.y+10))
        if self.active and self.show_cursor:
            cx = self.rect.x + 10 + txt.get_width() + 2
            cy = self.rect.y + 10
            pygame.draw.line(surf, (0,0,0), (cx, cy), (cx, cy+txt.get_height()), 2)

# ---------- Base de pantallas ----------
class ScreenBase:
    def __init__(self, manager):
        self.mgr = manager
    def handle_event(self, e): pass
    def update(self, dt): pass
    def draw(self, surf): pass

# ---------- Welcome ----------
class WelcomeScreen(ScreenBase):
    def __init__(self, mgr):
        super().__init__(mgr)
        self.buttons = [
            Button((WIDTH//2-120, 220, 240, 44), "Instrucciones", lambda: mgr.goto("instructions")),
            Button((WIDTH//2-120, 274, 240, 44), "Video promocional", lambda: mgr.goto("video")),
            Button((WIDTH//2-120, 328, 240, 44), "Configuración", lambda: mgr.goto("settings")),
            Button((WIDTH//2-120, 382, 240, 44), "Chat", lambda: mgr.goto("chat")),
            Button((WIDTH//2-120, 436, 240, 44), "Juego", lambda: mgr.goto("game")),
            Button((20, HEIGHT-60, 160, 40), "Acerca de", self.open_about),
        ]

    def open_about(self):
        webbrowser.open("http://127.0.0.1:8000")

    def handle_event(self, e):
        for b in self.buttons:
            b.handle_event(e)

    def draw(self, surf):
        surf.fill((15,60,25))
        title = pygame.font.SysFont("arial", 48, bold=True).render("Póker Simplificado", True, (255,255,255))
        surf.blit(title, title.get_rect(center=(WIDTH//2, 130)))
        subtitle = FONT.render("Bienvenido", True, (230,230,230))
        surf.blit(subtitle, subtitle.get_rect(center=(WIDTH//2, 180)))
        for b in self.buttons:
            b.draw(surf)
        tip = SMALL.render("Haz clic en los botones para navegar. ESC vuelve atrás.", True, (220,220,220))
        surf.blit(tip, (20, HEIGHT-30))

# ---------- Instrucciones ----------
class InstructionsScreen(ScreenBase):
    BULLETS = [
        "El juego es una versión simplificada de póker de 5 cartas.",
        "Cada partida tiene 2 a 4 jugadores conectados al servidor.",
        "El servidor reparte 5 cartas privadas a cada jugador.",
        "Cada jugador puede cambiar hasta 3 cartas una vez por ronda.",
        "No hay apuestas complejas, solo comparación de manos.",
        "Gana quien tenga la mejor combinación de 5 cartas.",
        "Valores de las cartas: 2, 3, 4, 5, 6, 7, 8, 9, T, J, Q, K, A.",
        "Manos (Menor a mayor): Carta alta, Par, Doble par, Trío, Escalera, Color, Full, Póker, Escalera de color.",
        "El chat interno permite comunicarse con los demás jugadores."
    ]

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.mgr.goto("welcome")

    def draw(self, surf):
        surf.fill((25,25,35))
        t = pygame.font.SysFont("arial", 40, bold=True).render("Instrucciones", True, (255,255,255))
        surf.blit(t, (40, 40))
        y = 110
        for line in self.BULLETS:
            dot = SMALL.render("• " + line, True, (230,230,230))
            surf.blit(dot, (60, y))
            y += 36
        back = SMALL.render("ESC: Volver", True, (200,200,200))
        surf.blit(back, (40, HEIGHT-40))

# ---------- Video ----------
class VideoScreen(ScreenBase):
    def __init__(self, mgr):
        super().__init__(mgr)
        self.clip = None
        self.playing = False
        self.play_time = 0.0
        self.frame_surf = None
        self.target_size = (640, 360)
        self.btn_play = Button((WIDTH//2-120, HEIGHT-80, 240, 44), "Reproducir / Pausa", self.toggle)

        self.audio_path = "assets/video/promo.mp3"
        self.audio_loaded = False
        self.audio_started = False
        self.audio_paused  = False

        self.preroll = 0.05
        self.preroll_left = 0.0

        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            except Exception as e:
                print("Mixer no disponible:", e)

    def load_clip(self):
        if self.clip is not None:
            return
        self.clip = VideoFileClip("assets/video/promo.mp4")
        self.play_time = 0.0

        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.load(self.audio_path)
                self.audio_loaded = True
            else:
                self.audio_loaded = False
        except Exception as e:
            print("No se pudo cargar el audio externo:", e)
            self.audio_loaded = False

    def toggle(self):
        if self.clip is None:
            try:
                self.load_clip()
            except Exception as e:
                print("Error al cargar video:", e)
                self.playing = False
                return

        self.playing = not self.playing

        if self.playing:
            if self.audio_loaded:
                if not self.audio_started:
                    pygame.mixer.music.play()
                    self.audio_started = True
                    self.audio_paused = False
                elif self.audio_paused:
                    pygame.mixer.music.unpause()
                    self.audio_paused = False
            self.preroll_left = self.preroll
        else:
            if self.audio_loaded and self.audio_started and not self.audio_paused:
                pygame.mixer.music.pause()
                self.audio_paused = True

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.cleanup()
            self.mgr.goto("welcome")
        self.btn_play.handle_event(e)

    def update(self, dt):
        if not self.playing or self.clip is None:
            return

        if self.preroll_left > 0:
            self.preroll_left -= dt
            if self.preroll_left > 0:
                return

        self.play_time += dt
        dur = float(self.clip.duration or 0.0)

        if dur > 0 and self.play_time >= dur:
            self.play_time = 0.0
            if self.audio_loaded:
                pygame.mixer.music.stop()
                pygame.mixer.music.play()
                self.audio_started = True
                self.audio_paused  = False

        try:
            frame = self.clip.get_frame(self.play_time)
        except Exception as e:
            print("Error obteniendo frame:", e)
            self.playing = False
            if self.audio_loaded:
                pygame.mixer.music.pause()
                self.audio_paused = True
            return

        frame_whc = np.swapaxes(frame, 0, 1)
        surf = pygame.surfarray.make_surface(frame_whc)
        self.frame_surf = pygame.transform.smoothscale(surf, self.target_size)

    def draw(self, surf):
        surf.fill((10,10,10))
        title = pygame.font.SysFont("arial", 36, bold=True).render("Video promocional", True, (255,255,255))
        surf.blit(title, (40, 30))
        if self.frame_surf:
            surf.blit(self.frame_surf, self.frame_surf.get_rect(center=(WIDTH//2, HEIGHT//2-20)))
        self.btn_play.draw(surf)
        hint = SMALL.render("ESC: Volver", True, (200,200,200))
        surf.blit(hint, (40, HEIGHT-40))

    def cleanup(self):
        try:
            if self.audio_loaded and pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except:
            pass
        if self.clip is not None:
            try:
                if hasattr(self.clip, "reader") and self.clip.reader is not None:
                    try:
                        self.clip.reader.close()
                    except:
                        pass
                self.clip.close()
            except:
                pass
        self.clip = None
        self.playing = False
        self.play_time = 0.0
        self.frame_surf = None
        self.preroll_left = 0.0
        self.audio_started = False
        self.audio_paused = False

# ---------- Configuración ----------
class SettingsScreen(ScreenBase):
    def __init__(self, mgr):
        super().__init__(mgr)
        self.name_input = TextInput((WIDTH//2-180, 200, 360, 40), "Tu nick...")
        self.server_input = TextInput((WIDTH//2-180, 260, 360, 40), "Servidor (ej: 127.0.0.1:5000)")
        self.save_btn = Button((WIDTH//2-90, 320, 180, 44), "Guardar", self.save)
        self.message = ""

    def save(self):
        self.mgr.config["nick"] = self.name_input.text or "Anon"
        self.mgr.config["server"] = self.server_input.text or "127.0.0.1:5000"
        self.message = "Configuración guardada."

    def handle_event(self, e):
        self.name_input.handle_event(e)
        self.server_input.handle_event(e)
        self.save_btn.handle_event(e)
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.mgr.goto("welcome")

    def update(self, dt):
        self.name_input.update(dt)
        self.server_input.update(dt)

    def draw(self, surf):
        surf.fill((35,30,30))
        t = pygame.font.SysFont("arial", 40, bold=True).render("Configuración", True, (255,255,255))
        surf.blit(t, (40,40))
        self.name_input.draw(surf)
        self.server_input.draw(surf)
        self.save_btn.draw(surf)
        msg = SMALL.render(self.message, True, (210,210,210))
        surf.blit(msg, (WIDTH//2 - msg.get_width()//2, 380))
        hint = SMALL.render("ESC: Volver", True, (200,200,200))
        surf.blit(hint, (40, HEIGHT-40))

# ---------- Chat multijugador ----------
class ChatScreen(ScreenBase):
    def __init__(self, mgr):
        super().__init__(mgr)
        self.input = TextInput((20, HEIGHT-60, WIDTH-40, 40),
                               "Escribe mensaje... (Enter para enviar)")
        self.messages = deque(maxlen=200)
        self.btn_connect = Button((20, 20, 140, 40), "Conectar", self.connect)

    def connect(self):
        net = self.mgr.net_client
        if net.sock:
            self.messages.append(("sistema", "Ya estás conectado."))
            return
        hostport = (self.mgr.config.get("server") or "127.0.0.1:5000").split(":")
        host, port = hostport[0], int(hostport[1])
        nick = self.mgr.config.get("nick") or "Anon"
        try:
            net.connect(host, port, nick)
            self.messages.append(("sistema", f"Conectado a {host}:{port} como {nick}"))
        except Exception as e:
            self.messages.append(("sistema", f"Error de conexión: {e}"))

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.mgr.goto("welcome")
        self.btn_connect.handle_event(e)
        text = self.input.handle_event(e)
        if text is not None:
            self.send_message(text)

    def send_message(self, text):
        text = text.strip()
        if not text:
            return
        net = self.mgr.net_client
        if net.sock:
            net.send({"type": "chat", "msg": text})
        else:
            self.messages.append(("sistema", "No conectado. Usa 'Conectar'."))

    def update(self, dt):
        self.input.update(dt)
        net = self.mgr.net_client
        while True:
            msg = net.get_nowait()
            if msg is None:
                break
            mtype = msg.get("type")
            if mtype == "chat":
                sender = msg.get("from", "?")
                text = msg.get("msg", "")
                self.messages.append(("chat", f"{sender}: {text}"))
            elif mtype == "info":
                self.messages.append(("sistema", msg.get("text", "")))

    def draw(self, surf):
        surf.fill((20,20,28))
        self.btn_connect.draw(surf)

        area = pygame.Rect(20, 80, WIDTH-40, HEIGHT-160)
        pygame.draw.rect(surf, (35,35,45), area, border_radius=8)
        pygame.draw.rect(surf, (70,70,90), area, 2, border_radius=8)

        y = area.bottom - 24
        for typ, line in reversed(self.messages):
            color = (210,210,210) if typ == "chat" else (255,210,120)
            txt = SMALL.render(line, True, color)
            y -= txt.get_height() + 6
            if y < area.y + 6:
                break
            surf.blit(txt, (area.x+10, y))

        self.input.draw(surf)
        hint = SMALL.render("ESC: Volver", True, (200,200,200))
        surf.blit(hint, (20, HEIGHT-30))

# ---------- Pantalla de Juego ----------
    
def wrap_text(text, font, max_width):
    words = text.split(" ")
    lines = []
    current = ""
    for w in words:
        test = (current + " " + w).strip()
        if not current:
            current = w
        elif font.size(test)[0] <= max_width:
            current = test
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines
class GameScreen(ScreenBase):
    def __init__(self, mgr):
        super().__init__(mgr)
        self.btn_join = Button((20, 20, 180, 40), "Unirse a la mesa", self.join_game)
        self.btn_draw = Button((20, 70, 180, 40), "Cambiar cartas", self.send_draw)
        self.status_lines = deque(maxlen=8)
        self.cards = []
        self.card_rects = []
        self.card_selected = set()
        self.can_draw = False
        self.phase = "waiting"
        self.players = []
        self.round_number = 0
        self.showdown_info = None

    def log(self, text):
        self.status_lines.append(text)

    def join_game(self):
        net = self.mgr.net_client
        if not net.sock:
            self.log("No estás conectado. Ve al chat y conecta primero.")
            return
        net.send({"type": "join_game"})

    def send_draw(self):
        if not self.can_draw:
            self.log("No puedes cambiar cartas ahora.")
            return
        indices = sorted(list(self.card_selected))
        net = self.mgr.net_client
        net.send({"type": "draw", "cards": indices})
        self.card_selected.clear()

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.mgr.goto("welcome")
        self.btn_join.handle_event(e)
        self.btn_draw.handle_event(e)

        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.phase == "draw" and self.can_draw:
                for i, rect in enumerate(self.card_rects):
                    if rect.collidepoint(e.pos):
                        if i in self.card_selected:
                            self.card_selected.remove(i)
                        else:
                            if len(self.card_selected) < 3:
                                self.card_selected.add(i)
                        break

    def update(self, dt):
        net = self.mgr.net_client
        while True:
            msg = net.get_nowait()
            if msg is None:
                break
            mtype = msg.get("type")
            if mtype == "info":
                self.log(msg.get("text", ""))
            elif mtype == "hand":
                self.cards = msg.get("cards", [])
                self.can_draw = bool(msg.get("can_draw", False))
                self.card_selected.clear()
            elif mtype == "game_state":
                self.phase = msg.get("phase", "waiting")
                self.players = msg.get("players", [])
                self.round_number = msg.get("round", 0)
            elif mtype == "showdown":
                self.showdown_info = msg
                winners = msg.get("winners", [])
                desc = msg.get("description", "")
                self.log(f"Ganador(es): {', '.join(winners)} ({desc})")

    def draw(self, surf):
        surf.fill((0,80,0))
        title = pygame.font.SysFont("arial", 36, bold=True).render("Mesa de juego", True, (255,255,255))
        surf.blit(title, (40, 20))

        self.btn_join.draw(surf)
        self.btn_draw.draw(surf)

        info_text = f"Fase: {self.phase} | Ronda: {self.round_number} | Jugadores: {', '.join(self.players) or 'Ninguno'}"
        tinfo = SMALL.render(info_text, True, (255,255,255))
        surf.blit(tinfo, (40, 130))

        self.card_rects = []
        x0 = 200
        y0 = 200
        w = 80
        h = 120
        gap = 20
        for i, card in enumerate(self.cards):
            rect = pygame.Rect(x0 + i * (w + gap), y0, w, h)
            self.card_rects.append(rect)
            color = (240,240,240)
            if i in self.card_selected:
                color = (255,255,180)
            pygame.draw.rect(surf, color, rect, border_radius=8)
            pygame.draw.rect(surf, (0,0,0), rect, 2, border_radius=8)
            txt = FONT.render(card, True, (0,0,0))
            surf.blit(txt, txt.get_rect(center=rect.center))

        # Mensajes de estado
        area = pygame.Rect(40, HEIGHT-150, WIDTH-80, 110)
        pygame.draw.rect(surf, (0,60,0), area, border_radius=8)
        pygame.draw.rect(surf, (0,100,0), area, 2, border_radius=8)

        max_width = area.width - 20
        wrapped_lines = []
        for line in self.status_lines:
            wrapped_lines.extend(wrap_text(line, SMALL, max_width))

        y = area.y + 10
        for line in wrapped_lines[-20:]:
            txt = SMALL.render(line, True, (230,230,230))
            if y + txt.get_height() > area.bottom - 10:
                break
            surf.blit(txt, (area.x + 10, y))
            y += txt.get_height() + 4

        if self.showdown_info:
            winners = ", ".join(self.showdown_info.get("winners", []))
            desc = self.showdown_info.get("description", "")
            txt = SMALL.render(f"Último resultado: {winners} ({desc})", True, (255,255,0))
            surf.blit(txt, (40, 160))

        hint = SMALL.render("ESC: Volver", True, (230,230,230))
        surf.blit(hint, (40, HEIGHT-30))

# ---------- Gestor de pantallas ----------
class ScreenManager:
    def __init__(self):
        self.config = {"nick": "Anon", "server": "127.0.0.1:5000"}
        self.net_client = NetClient()

        self.screens = {
            "welcome": WelcomeScreen(self),
            "instructions": InstructionsScreen(self),
            "video": VideoScreen(self),
            "settings": SettingsScreen(self),
            "chat": ChatScreen(self),
            "game": GameScreen(self),
        }
        self.current = "welcome"

    def goto(self, name):
        if name in self.screens:
            self.current = name

    def handle_event(self, e):
        self.screens[self.current].handle_event(e)

    def update(self, dt):
        self.screens[self.current].update(dt)

    def draw(self, surf):
        self.screens[self.current].draw(surf)

    def shutdown(self):
        vid = self.screens.get("video")
        if isinstance(vid, VideoScreen):
            vid.cleanup()
        if self.net_client:
            self.net_client.close()

# ---------- Loop principal ----------
def main():
    global SCREEN
    mgr = ScreenManager()
    fullscreen = False

    while True:
        dt = CLOCK.tick(60)/1000.0
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                mgr.shutdown()
                pygame.quit()
                sys.exit(0)
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                fullscreen = not fullscreen
                if fullscreen:
                    SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
                else:
                    SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
            mgr.handle_event(e)

        mgr.update(dt)
        mgr.draw(SCREEN)
        pygame.display.flip()

if __name__ == "__main__":
    main()