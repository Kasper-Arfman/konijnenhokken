from collections import Counter
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.properties import NumericProperty, StringProperty, ObjectProperty
import pickle
import os

filepath = os.path.join(os.path.dirname(__file__), 'solution.pkl')

with open(filepath, 'rb') as f:
    PLAY_VALUE: dict = pickle.load(f)

for i, k in enumerate(PLAY_VALUE):
    if i < 10:
        print(k)




def possible_allocations(state: tuple, roll: dict):
    """All the possible states that can be obtained from a roll"""
    t, r1, r2, c = state
    states = set()
    for d1 in range(roll[1]+1):
        for d2 in range(roll[2]+1):
            # Must add atleast one rabbit
            if (d1, d2) == (0, 0):  continue

            # 1: Add only rabbits
            states.add((t, r1+d1, r2+d2, c))

            # In case all 2s are used up
            if not (roll[2] - d2):  continue

            # 2: Add cages as well
            for dc, cage in enumerate(range(c+2, 6), 1):
                if not roll.get(cage):  break
                states.add((t, r1+d1, r2+d2, c+dc))
    return states

def decide_allocation(state, roll: dict):
    """Find all the states that can be reached from here
    Pick the one with the largest score."""
    # roll = Counter(roll)
    # roll = Counter(roll).copy()  # Better safe than sorry

    # roll = {k: v for k, v in roll.items() if v}


    state_value = lambda state: max(stop_value(state), PLAY_VALUE[state])
    best = max(possible_allocations(state, roll), key=state_value)
    return best



def main():
    app = CheatApp() 
    app.run()

class CheatApp(App):
    def build(self):
        return CheatSheet()

class CheatSheet(BoxLayout):

    # == Roll state
    roll1 = NumericProperty(0)
    roll2 = NumericProperty(0)
    roll3 = NumericProperty(0)
    roll4 = NumericProperty(0)
    roll5 = NumericProperty(0)
    roll = ObjectProperty({
            1: 0, 
            2: 0, 
            3: 0, 
            4: 0, 
            5: 0, 
            6: 7,
            })

    # == Field state
    field_t = NumericProperty(0)
    field_1 = NumericProperty(0)
    field_2 = NumericProperty(0)
    field_c = NumericProperty(0)
    field = ObjectProperty((0, 0, 0, 0))
    

    # == Calculated
    num_dice_field = NumericProperty(0)
    stop_value = NumericProperty(0)
    play_value = NumericProperty(0)
    response = StringProperty('')
    best_move = ObjectProperty((0, 0, 0, 0))

    def on_accept(self):
        print('accept!')

        # - Enters the new state, including turn score
        t, r1, r2, c = self.best_move
        self.field_t = t
        self.field_1 = r1
        self.field_2 = r2
        self.field_c = c
        self.update_field()


        # - Erase the roll
        self.roll1 = 0
        self.roll2 = 0
        self.roll3 = 0
        self.roll4 = 0
        self.roll5 = 0
        self.update_roll()

        







    """ === roll state === """

    def update_roll(self):
        used = sum([self.roll1, self.roll2, self.roll3, self.roll4, self.roll5])
        num_dice_roll = 7 - self.num_dice_field

        self.roll = {
            1: self.roll1, 
            2: self.roll2, 
            3: self.roll3, 
            4: self.roll4, 
            5: self.roll5, 
            6: num_dice_roll - used,
            }
        # self.on_solve()

    def on_roll_ones(self, value, other=None):
        self.roll1 = value
        self.update_roll()

    def on_roll_twos(self, value, other=None):
        self.roll2 = value
        self.update_roll()

    def on_roll3(self, other, value):
        self.roll3 = value
        self.update_roll()
        
    def on_roll4(self, other, value):
        self.roll4 = value
        self.update_roll()

    def on_roll5(self, other, value):
        self.roll5 = value
        self.update_roll()
    

    """ === field state === """

    def update_field(self):
        self.field = (
            self.field_t,
            self.field_1,
            self.field_2,
            self.field_c,
        )
        self.num_dice_field = sum(self.field[1:])
        # self.on_solve()

    def on_field_t(self, other, value):
        self.field_t = value
        self.update_field()

    # def on_field_1(self, other, value):
    #     print('yes', other, value)
    #     self.field_1 = value 
    #     self.update_field()

    def custom_field_1(self, other, value):
        print('yes', other, value)
        self.field_1 = value 
        self.update_field()


    def on_ones_toggle(self, value, other=None):
        self.field_1 = value 
        self.update_field()
        # self.on_solve() 


    def on_twos_toggle(self, value, other=None):
        self.field_2 = value  
        self.update_field()
        # self.on_solve()

    def on_mult_toggle(self, value, other=None):
        self.field_c = value  
        self.update_field()
        # self.on_solve()

    def on_solve(self):
        state = (self.field_t, self.field_1, self.field_2, self.field_c)
        self.stop_value = stop_value(state)

        # == Validate input
        # - Possible field state
        if state not in PLAY_VALUE:
            self.response = 'Invalid'
            return
        # - Dice sum to 7
        if sum(self.roll.values()) > 7:
            print(self.roll)
            exit()
        # if self.num_dice_field +  != 7:
        #     self.response = 'Dice mismatch'
        #     return
        
        # == Decide how to allocate the dice
        pass


        # state = (0, 0, 0, 0)
        # roll = Counter(self.roll)
        # roll = Counter([1, 1, 1, 1, 2, 2, 2])
        # roll = Counter({k: v for k, v in self.roll.items() if v})
        roll = self.roll

        print('Trying:')
        print(f"{state = }")
        print(f"{roll = }")
        dst = decide_allocation(state, roll)
        self.best_move = dst

        print(f"{dst = }")



        # == Decide whether to roll again
        if PLAY_VALUE[dst] > stop_value(dst):
            self.response = 'Play'
        else:
            self.response = 'Stop'

        if self.response == 'Stop':
            return


class FieldButton(Button):
    
    val = NumericProperty(0)

    def on_press(self):
        print(f'Button with val={self.val} pressed!')
        # self.background_color = (1, 0, 0, 1)

        root = self.app


def stop_value(state):
    """Obtained score when stopping"""
    t, r1, r2, c = state
    return t + (r1 + 2*r2)*(c+1)

if __name__ == "__main__":
    main()