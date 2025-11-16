import socket
import threading
import json

from game.logic import make_deck, deal, best_hand, hand_description

clients = {}
clients_lock = threading.Lock()


class GameRoom:
    def __init__(self):
        self.lock = threading.Lock()
        self.players = []
        self.hands = {}
        self.has_drawn = set()
        self.phase = "waiting"
        self.deck = []
        self.round_number = 0

    def to_state_dict(self):
        return {
            "type": "game_state",
            "phase": self.phase,
            "players": self.players,
            "round": self.round_number,
        }

    def add_player(self, nick):
        with self.lock:
            if nick not in self.players:
                self.players.append(nick)
            if self.phase == "waiting" and len(self.players) >= 2:
                self.start_round()

    def remove_player(self, nick):
        with self.lock:
            if nick in self.players:
                self.players.remove(nick)
                self.hands.pop(nick, None)
                self.has_drawn.discard(nick)
            if len(self.players) < 2:
                self.phase = "waiting"
                self.deck = []
                self.hands.clear()
                self.has_drawn.clear()
                broadcast(self.to_state_dict())

    def start_round(self):
        self.round_number += 1
        self.phase = "draw"
        self.deck = make_deck()
        import random
        random.shuffle(self.deck)
        self.hands = {p: deal(self.deck, 5) for p in self.players}
        self.has_drawn = set()

        for nick, cards in self.hands.items():
            send_to_nick(nick, {
                "type": "hand",
                "cards": cards,
                "can_draw": True,
            })

        broadcast({
            "type": "info",
            "text": f"Comienza la ronda {self.round_number}. Cada jugador tiene 5 cartas.",
        })
        broadcast(self.to_state_dict())

    def player_draw(self, nick, indices):
        with self.lock:
            if self.phase != "draw":
                return
            if nick not in self.players:
                return
            if nick in self.has_drawn:
                send_to_nick(nick, {
                    "type": "info",
                    "text": "Ya has cambiado cartas en esta ronda.",
                })
                return
            indices = sorted(set(i for i in indices if 0 <= i < 5))
            if len(indices) > 3:
                indices = indices[:3]

            cards = self.hands.get(nick)
            if not cards:
                return
            for i in indices:
                if not self.deck:
                    break
                cards[i] = self.deck.pop()
            self.hands[nick] = cards
            self.has_drawn.add(nick)

            send_to_nick(nick, {
                "type": "hand",
                "cards": cards,
                "can_draw": False,
            })

            broadcast({
                "type": "info",
                "text": f"{nick} ha cambiado {len(indices)} carta(s).",
            })

            if self.has_drawn == set(self.players):
                self.showdown()

    def showdown(self):
        self.phase = "showdown"
        score, winners = best_hand(self.hands)
        desc = hand_description(self.hands[winners[0]])
        broadcast({
            "type": "info",
            "text": f"Fin de la ronda. Manos reveladas.",
        })
        broadcast({
            "type": "showdown",
            "winners": winners,
            "description": desc,
            "hands": self.hands,
        })
        broadcast(self.to_state_dict())
        self.phase = "waiting"
        self.deck = []
        self.hands = {}
        self.has_drawn.clear()


game = GameRoom()


def broadcast(obj, omit_sock=None):
    data = (json.dumps(obj) + "\n").encode("utf-8")
    with clients_lock:
        for s in list(clients.keys()):
            if s is omit_sock:
                continue
            try:
                s.sendall(data)
            except:
                try:
                    s.close()
                except:
                    pass
                clients.pop(s, None)


def send_to_nick(nick, obj):
    with clients_lock:
        for s, info in list(clients.items()):
            if info.get("nick") == nick:
                try:
                    s.sendall((json.dumps(obj) + "\n").encode("utf-8"))
                except:
                    try:
                        s.close()
                    except:
                        pass
                    clients.pop(s, None)
                break


def handle_client(sock, addr):
    print("Nuevo cliente", addr)
    f = sock.makefile("r", encoding="utf-8", newline="\n")
    nick = f"{addr[0]}:{addr[1]}"

    try:
        while True:
            try:
                line = f.readline()
            except (ConnectionResetError, OSError):
                break

            if not line:
                break

            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            mtype = msg.get("type")

            if mtype == "hello":
                nick = msg.get("nick", nick)
                with clients_lock:
                    clients[sock] = {"nick": nick}
                broadcast({"type": "info", "text": f"{nick} se ha conectado"})
                broadcast(game.to_state_dict())

            elif mtype == "chat":
                text = msg.get("msg", "")
                broadcast({"type": "chat", "from": nick, "msg": text})

            elif mtype == "join_game":
                game.add_player(nick)
                broadcast({
                    "type": "info",
                    "text": f"{nick} se ha unido a la mesa de juego.",
                })
                broadcast(game.to_state_dict())

            elif mtype == "draw":
                indices = msg.get("cards", [])
                game.player_draw(nick, indices)

    finally:
        print("Cliente desconectado", nick)
        with clients_lock:
            clients.pop(sock, None)
        try:
            sock.close()
        except:
            pass
        broadcast({"type": "info", "text": f"{nick} salió"})
        game.remove_player(nick)


def main():
    HOST, PORT = "0.0.0.0", 5000
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen()
    print(f"Servidor escuchando en {HOST}:{PORT}")

    while True:
        sock, addr = srv.accept()
        t = threading.Thread(target=handle_client, args=(sock, addr), daemon=True)
        t.start()


if __name__ == "__main__":
    main()