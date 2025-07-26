from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty, StringProperty
import pickle
import os

filepath = os.path.join(os.path.dirname(__file__), 'solution.pkl')

with open(filepath, 'rb') as f:
    PLAY_VALUE: dict = pickle.load(f)

def main():
    app = CheatApp() 
    app.run()

class CheatApp(App):
    def build(self):
        return CheatSheet()

class CheatSheet(BoxLayout):
    plus = NumericProperty(0)
    ones = NumericProperty(0)
    twos = NumericProperty(0)
    mult = NumericProperty(0)
    stop_value = NumericProperty(0)
    play_value = NumericProperty(0)
    response = StringProperty('')

    def on_ones_toggle(self, value, other=None):
        self.ones = value 
        self.on_solve() 

    def on_twos_toggle(self, value, other=None):
        self.twos = value  
        self.on_solve()

    def on_mult_toggle(self, value, other=None):
        self.mult = value  
        self.on_solve()

    def on_solve(self):
        state = (self.plus, self.ones, self.twos, self.mult)
        self.stop_value = stop_value(state)

        if state not in PLAY_VALUE:
            self.response = 'Invalid'
            return

        self.play_value = PLAY_VALUE[state]
        if self.play_value > self.stop_value:
            self.response = 'Play'
        else:
            self.response = 'Stop'

def stop_value(state):
    """Obtained score when stopping"""
    t, r1, r2, c = state
    return t + (r1 + 2*r2)*(c+1)

if __name__ == "__main__":
    main()