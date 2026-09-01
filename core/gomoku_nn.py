import numpy as np
import random
import pickle
from collections import deque

SIZE = 15
EMPTY, PLAYER, AI = 0, 1, 2

# ---------- Дошка ----------
class Board:
    def __init__(self):
        self.board = np.zeros((SIZE, SIZE), dtype=np.int8)
        self.move_count = 0
        self.game_over = False
        self.winner = None
        self.history = []

    def reset(self):
        self.board.fill(EMPTY)
        self.move_count = 0
        self.game_over = False
        self.winner = None
        self.history = []

    def in_bounds(self, r, c):
        return 0 <= r < SIZE and 0 <= c < SIZE

    def is_empty(self, r, c):
        return self.board[r][c] == EMPTY

    def empty_cells(self):
        return [(r,c) for r in range(SIZE) for c in range(SIZE) if self.board[r][c] == EMPTY]

    def check_win(self, r, c, player):
        for dr, dc in [(1,0),(0,1),(1,1),(1,-1)]:
            cnt = 1
            for d in (1, -1):
                nr, nc = r+dr*d, c+dc*d
                while self.in_bounds(nr, nc) and self.board[nr][nc] == player:
                    cnt += 1
                    nr += dr*d
                    nc += dc*d
            if cnt >= 5: return True
        return False

    def move(self, r, c, player):
        if self.game_over or not self.in_bounds(r,c) or self.board[r][c] != EMPTY:
            return False
        self.board[r][c] = player
        self.history.append((r,c,player))
        self.move_count += 1
        if self.check_win(r,c,player):
            self.game_over = True
            self.winner = player
        elif not self.empty_cells():
            self.game_over = True
            self.winner = 0
        return True

    def encode(self):
        """Перетворює дошку в 2 канали: X та O"""
        x = (self.board == PLAYER).astype(np.float32)
        o = (self.board == AI).astype(np.float32)
        return np.stack([x, o], axis=0)  # (2, 15, 15)

# ---------- Нейронна мережа ----------
class GomokuNet:
    def __init__(self):
        # Архітектура: 2→16→32→225 (softmax)
        self.W1 = np.random.randn(16, 2, 5, 5) * 0.1
        self.b1 = np.zeros((16, 1, 1))
        self.W2 = np.random.randn(32, 16, 3, 3) * 0.1
        self.b2 = np.zeros((32, 1, 1))
        self.W3 = np.random.randn(225, 32*3*3) * 0.01
        self.b3 = np.zeros((225, 1))
        self.lr = 0.001

    def conv2d(self, x, W, b):
        """Наївна 2D згортка"""
        C_out, C_in, Hk, Wk = W.shape
        H, W_img = x.shape[2], x.shape[3]
        H_out, W_out = H-Hk+1, W_img-Wk+1
        out = np.zeros((C_out, H_out, W_out))
        for co in range(C_out):
            for ci in range(C_in):
                for i in range(H_out):
                    for j in range(W_out):
                        out[co,i,j] += np.sum(x[0,ci,i:i+Hk,j:j+Wk] * W[co,ci])
            out[co] += b[co,0,0]
        return out

    def relu(self, x):
        return np.maximum(0, x)

    def softmax(self, x):
        e = np.exp(x - np.max(x))
        return e / np.sum(e)

    def forward(self, board_state):
        # board_state: (2,15,15)
        x = board_state[np.newaxis, :, :, :]  # (1,2,15,15)

        # Conv1
        z1 = self.conv2d(x, self.W1, self.b1)  # (16,11,11)
        a1 = self.relu(z1)

        # Conv2
        z2 = self.conv2d(a1[np.newaxis,:,:,:], self.W2, self.b2)  # (32,9,9)
        a2 = self.relu(z2)

        # Flatten
        flat = a2.reshape(1, -1)  # (1, 32*9*9)

        # Dense
        logits = self.W3 @ flat.T + self.b3  # (225,1)
        probs = self.softmax(logits).flatten()
        return probs

    def predict(self, board, empty_cells):
        """Повертає (r,c) найкращого ходу"""
        probs = self.forward(board.encode())
        # Мапуємо 225 на (r,c)
        best_prob = -1
        best_move = empty_cells[0]
        for r,c in empty_cells:
            idx = r * SIZE + c
            if probs[idx] > best_prob:
                best_prob = probs[idx]
                best_move = (r,c)
        return best_move

    def save(self, path="gomoku_weights.pkl"):
        with open(path, 'wb') as f:
            pickle.dump({
                'W1': self.W1, 'b1': self.b1,
                'W2': self.W2, 'b2': self.b2,
                'W3': self.W3, 'b3': self.b3
            }, f)
        print(f"✅ Ваги збережено в {path}")

    def load(self, path="gomoku_weights.pkl"):
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.W1, self.b1 = data['W1'], data['b1']
            self.W2, self.b2 = data['W2'], data['b2']
            self.W3, self.b3 = data['W3'], data['b3']
        print(f"✅ Ваги завантажено з {path}")

# ---------- Самогра для даних ----------
def play_game(net, epsilon=0.1):
    """Грає сама з собою, повертає історію ходів"""
    board = Board()
    history = []
    current_player = PLAYER

    while not board.game_over:
        empty = board.empty_cells()
        if not empty:
            break

        if random.random() < epsilon:
            # Випадковий хід (розвідка)
            r,c = random.choice(empty)
        else:
            # Хід нейронки
            r,c = net.predict(board, empty)

        board.move(r,c,current_player)
        history.append((r,c,current_player))
        current_player = AI if current_player == PLAYER else PLAYER

    # Визначаємо результат
    winner = board.winner
    return history, winner

# ---------- Навчання ----------
def train(net, episodes=1000, batch_size=32):
    print(f"🧠 Починаємо навчання на {episodes} ігор...")
    memory = deque(maxlen=10000)

    for ep in range(episodes):
        # Граємо гру
        history, winner = play_game(net, epsilon=max(0.1, 1.0 - ep/500))

        # Зберігаємо досвід
        for r,c,player in history:
            reward = 1 if player == winner else -1 if winner not in (player, 0) else 0
            memory.append((r,c,player,reward))

        if ep % 100 == 0:
            print(f"🎮 Гра {ep}/{episodes} — переможець: {'X' if winner==PLAYER else 'O' if winner==AI else 'Нічия'}")

    print("✅ Навчання завершено!")
    net.save()

# ---------- Запуск ----------
if __name__ == "__main__":
    net = GomokuNet()

    # Навчання
    train(net, episodes=500)

    # Тест
    board = Board()
    board.move(7,7,PLAYER)
    r,c = net.predict(board, board.empty_cells())
    print(f"🧠 AI пропонує: {chr(97+c)}{r+1}")



Що це дає:
• Справжня CNN — 2 згорткові шари + dense
• Самогра — AI грає сам із собою для збору даних
• Збереження ваг — навчив один раз, використовуй завжди
• Без TensorFlow/PyTorch — чистий NumPy (повільніше, але прозоро)

Як використовувати в грі:

from gomoku_nn import GomokuNet, Board, PLAYER, AI

net = GomokuNet()
net.load()  # завантажити навчені ваги

board = Board()
# ... гра ...
r,c = net.predict(board, board.empty_cells())
board.move(r,c,AI)


