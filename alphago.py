import numpy as np
import tensorflow as tf

def generate_random_data(num_samples=1000, board_size=19):
    inputs = np.random.rand(num_samples, board_size, board_size, 1)  # Random board states
    policy_targets = np.random.randint(2, size=(num_samples, board_size * board_size))  # Random move probabilities
    value_targets = np.random.uniform(-1, 1, size=(num_samples, 1))  # Random value predictions
    return {'input': inputs, 'policy_target': policy_targets, 'value_target': value_targets}

def create_policy_network(input_shape):
    model = tf.keras.Sequential([
        tf.keras.layers.Conv2D(32, kernel_size=3, activation='relu', input_shape=input_shape),
        tf.keras.layers.Conv2D(64, kernel_size=3, activation='relu'),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(256, activation='relu'),
        tf.keras.layers.Dense(input_shape[0] * input_shape[1], activation='softmax')
    ])
    return model

def create_value_network(input_shape):
    model = tf.keras.Sequential([
        tf.keras.layers.Conv2D(32, kernel_size=3, activation='relu', input_shape=input_shape),
        tf.keras.layers.Conv2D(64, kernel_size=3, activation='relu'),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(256, activation='relu'),
        tf.keras.layers.Dense(1, activation='tanh')
    ])
    return model

def train_networks(policy_network, value_network, data, epochs=10, batch_size=32):
    policy_network.compile(optimizer='adam', loss='categorical_crossentropy')
    value_network.compile(optimizer='adam', loss='mean_squared_error')

    policy_network.fit(data['input'], data['policy_target'], epochs=epochs, batch_size=batch_size)
    value_network.fit(data['input'], data['value_target'], epochs=epochs, batch_size=batch_size)

class MCTS:
    def __init__(self, policy_network, value_network):
        self.policy_network = policy_network
        self.value_network = value_network

    def select_move(self, game_state):
        policy = self.policy_network.predict(game_state[np.newaxis, :, :, np.newaxis])
        best_move = np.argmax(policy)
        return best_move

class SimpleGameState:
    def __init__(self, board_size=19):
        self.board_size = board_size
        self.board = np.zeros((board_size, board_size), dtype=np.int8)
        self.current_player = 1

    def apply_move(self, move):
        row, col = divmod(move, self.board_size)
        self.board[row, col] = self.current_player
        self.current_player = -self.current_player

    def get_legal_moves(self):
        return np.flatnonzero(self.board == 0)

    def is_game_over(self):
        return len(self.get_legal_moves()) == 0

def play_game(policy_network, value_network, board_size=19):
    game_state = SimpleGameState(board_size)
    mcts = MCTS(policy_network, value_network)

    while not game_state.is_game_over():
        legal_moves = game_state.get_legal_moves()
        if len(legal_moves) == 0:
            break

        move = mcts.select_move(game_state.board)
        game_state.apply_move(move)
        print("Move:", move, "Current Board:\n", game_state.board)

if __name__ == "__main__":
    board_size = 19
    data = generate_random_data(num_samples=1000, board_size=board_size)
    input_shape = (board_size, board_size, 1)

    policy_network = create_policy_network(input_shape)
    value_network = create_value_network(input_shape)

    train_networks(policy_network, value_network, data, epochs=10, batch_size=32)

    play_game(policy_network, value_network, board_size)
