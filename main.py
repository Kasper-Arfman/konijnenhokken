from collections import Counter
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.properties import NumericProperty, StringProperty, ObjectProperty, DictProperty, ListProperty, BooleanProperty
import pickle
import os

filepath = os.path.join(os.path.dirname(__file__), 'solution.pkl')
with open(filepath, 'rb') as f:
    PLAY_VALUE: dict = pickle.load(f)

def stop_value(state):
    """Obtained score when stopping"""
    t, r1, r2, c = state
    return t + (r1 + 2*r2)*(c+1)

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


class CheatApp(App):
    def build(self):
        return CheatSheet()

class CheatSheet(BoxLayout):
    roll = ListProperty([0, 0, 0, 0, 0, 0])
    field = ListProperty([0, 0, 0, 0])
    dst = ListProperty([0, 0, 0, 0])
    play = BooleanProperty(True)
    num_dice = NumericProperty(7)
    stop_value = NumericProperty(0)
    play_value = NumericProperty(PLAY_VALUE[0, 0, 0, 0])

    def update_dice_count(self, *args):
        print('Cheatsheet.update_dice_count:')
        self.num_dice = 7 - sum(self.field[1:])

    def update_sliders(self):
        print('Cheatsheet.update_sliders:')
        self.ids.roll_area.update_sliders()
        self.ids.field_area.update_sliders()

    def on_roll_slider(self):
        self.update_sliders()

    def on_field_slider(self):
        self.update_dice_count()
        self.update_statistics()
        self.update_sliders()

    def on_solve(self):
        print(f"CheatSheet.on_solve:")

        # - Build data format
        self.roll[5] = self.num_dice - sum(self.roll[:5])  # Enforce Dice total
        roll = {k: v for k, v in enumerate(self.roll, 1)}
        src = tuple(self.field)
        print(f"{roll = }")
        print(f"{src = }")

        if src not in PLAY_VALUE:
            print(f'ERROR: impossible state: {src}')
            return

        # - Check if died
        if not sum(self.roll[:2]): 
            print('ERROR: you died.')
            return

        # - Decide point allocation
        self.dst = decide_allocation(src, roll)
        # On a completed hand
        if sum(self.dst[1:]) == 7:
            self.dst = [stop_value(self.dst), 0, 0, 0]


        print(f"{self.dst = }")

        # - Decide play
        dst = tuple(self.dst)
        self.play = PLAY_VALUE[dst] > stop_value(dst)
        print(f"{self.play = }")

    def update_statistics(self):
        state = tuple(self.field)
        self.play_value = PLAY_VALUE[state]
        self.stop_value = stop_value(state)

    def on_accept(self):
        print(f"CheatSheet.on_accept:")
        self.roll = [0]*6
        self.field = self.dst
        self.update_statistics()
        self.update_sliders()

    def on_clear(self):
        print(f"CheatSheet.on_clear:")
        self.roll = [0]*6
        self.field = [0]*4
        self.dst = [0]*4
        self.play = True
        self.num_dice = 7
        self.stop_value = 0
        self.play_value = PLAY_VALUE[0, 0, 0, 0]
        self.update_sliders()


class RollArea(BoxLayout):

    sliders = ListProperty([])
    
    def on_slider(self, *args):
        print('RollArea.on_slider:')

        # Callback
        self.parent.on_roll_slider()

    def update_sliders(self):
        print(f"RollArea.update_sliders()")

        self.ids.s0.val = self.parent.roll[0]  # Calls update buttons automatically
        self.ids.s1.val = self.parent.roll[1]

        for val, btn in enumerate([self.ids.s2, self.ids.s3, self.ids.s4], 2):
            print(f"{btn = } {self.parent.roll[val]}")

            if self.parent.roll[val]:
                print('Selected')
                btn.background_color = (1, 0, 0, 1)  # red

            # elif self._root and btn.val > self._root.num_dice:
            #     # print('Locked')
            #     btn.background_color = (0, 1, 1, 1)  # cyan
            #     btn.disabled = True

            else:
                print('Free')
                btn.background_color = (1, 1, 1, 1)  # white

        self.ids.s0.update()
        self.ids.s1.update()
    
    def on_multiplier(self, btn, target, key):
        print('RollArea.on_multiplier')
        if target is not None:
            target[key] = int(btn.state == 'down')

        self.parent.on_roll_slider()


class FieldArea(BoxLayout):
    def on_slider(self, *args):
        print('FieldArea.on_slider:')
        # self.parent.update_dice_count()

        # Callback
        self.parent.on_field_slider()

    def update_sliders(self):
        print(f"FieldArea.update_sliders()")
        # self.ids.s0.val = self.parent.field[0]
        self.ids.s1.val = self.parent.field[1]
        self.ids.s2.val = self.parent.field[2]
        self.ids.s3.val = self.parent.field[3]

        self.ids.s1.update()
        self.ids.s2.update()
        self.ids.s3.update()


class Sliders(BoxLayout):
    
    buttons = []

    num_buttons = NumericProperty(0)
    val = NumericProperty(0)
    key = ObjectProperty('1')
    
    target = ObjectProperty(None)
    _root = ObjectProperty(None)

    button_labels = ListProperty([])  # <-- New property for optional labels

    def update(self, *args):
        print(f"Slider.update_buttons:")

        for btn in self.buttons:
            btn.disabled = False


            if btn.val <= self.val:
                # print('Selected')
                btn.background_color = (1, 0, 0, 1)  # red

            elif self._root and btn.val > self._root.num_dice:
                # print('Locked')
                btn.background_color = (0, 1, 1, 1)  # cyan
                btn.disabled = True

            elif btn.val > self.val:
                # print('Free')
                btn.background_color = (1, 1, 1, 1)  # white

    def on_num_buttons(self, *args):
        self.buttons = []  # store references to the buttons
        for i in range(self.num_buttons):
            btn = Button(text=str(i))
            btn.val = i  # store index/value
            btn.bind(on_press=self.on_slider_button)
            self.add_widget(btn)
            self.buttons.append(btn)

        # self.on_val(None, self.val)  # Initialize
        self.val = self.val

    def on_button_labels(self, *args):
        for bt, lbl in zip(self.buttons, self.button_labels):
            bt.text = lbl
     
    def on_val(self, instance, value):
        """Link slider.val -> target"""
        print('Sliders.on_val:')
        self.val = value
        if self.target is not None:
            self.target[self.key] = value

    def on_slider_button(self, button):
        print(f"Sliders.on_button:")
        # Update the slider value
        self.val = button.val  # update shared state

        # Callback
        self.parent.on_slider()  




class OutputArea(BoxLayout): ...



def main():
    app = CheatApp() 
    app.run()

if __name__ == "__main__":
    main()