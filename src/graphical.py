import pygame
import threading
from models import UI, GameState
from src.gamestate import UserGameState
import time

"""TODO:
 - Give each rect in the roll an <active> parameter
 
"""

class GraphicalUI(UI):
    MAX_FPS = 30
    N_DICE = 7

    def __init__(self, width=800, height=600):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Konijnenhokken")

        self.running = True
        self.clock = pygame.time.Clock()

        self.dice_rects = self.create_dice_rects(100)
        self.rabbit_rects = self.create_dice_rects(250)
        self.cage_rects = self.create_dice_rects(400)
        self.lock_button_rect = pygame.Rect(330, 500, 100, 50)
        self.roll_again_rect = pygame.Rect(200, 500, 80, 50)
        self.stop_rect = pygame.Rect(500, 500, 80, 50)
        self.score_rect = pygame.Rect(220, 20, 150, 50)
        self.game_score_rect = pygame.Rect(410, 20, 150, 50)

        # Initialize game state
        self.gs = UserGameState(7)

        # Initialize selection state
        self.roll_iselection = []
        self.rabbit_selection = []
        self.cage_selection = []
        self.selection_state(0)

        self.gui_thread = threading.Thread(target=self.run, daemon=True)
        self.gui_thread.start()

    """ ==== Core ===="""

    def run(self):
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(self.MAX_FPS)
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button

                    # - Clicking dice
                    for i, rect in enumerate(self.dice_rects):
                        if rect.collidepoint(event.pos):
                            self.on_click_dice(i)

                    # - Clicking lock
                    if self.lock_button_active and self.lock_button_rect.collidepoint(event.pos):
                        self.on_lock()

                    # - Clicking roll
                    if self.roll_again_active and self.roll_again_rect.collidepoint(event.pos):
                        self.on_roll()

                    # - Clicking stop
                    if self.stop_active and self.stop_rect.collidepoint(event.pos):
                        self.on_stop()

    def create_dice_rects(self, y, spacing=10, rect_width=50, rect_height=50):
        total_width = self.N_DICE * rect_width + (self.N_DICE - 1) * spacing
        x0 = (self.width - total_width) // 2

        rects = []
        for i in range(7):
            x = x0 + i * (rect_width + spacing)
            rects.append(pygame.Rect(x, y, rect_width, rect_height))
        return rects

    """ ==== engine interface ===="""

    def on_turn_start(self, gs: GameState=None):
        print(f"\n\nStarting a new round")
        self.gs = gs
        self.selection_state(0)

    def on_dice_roll(self, gs: GameState=None):
        print(f'You rolled: {gs.roll}')
        self.gs = gs  # update roll info
        self.selection_state(0)

    def on_decide_allocation(self, gs: GameState=None):
        print('Allocating...')
        self.gs = gs
        self.selection_state(1)

        # wait untill a selection is made
        while not self.selection_locked:
            pygame.event.pump()  
            self.clock.tick(self.MAX_FPS)

        rabbits, cages = self.rabbit_selection.copy(), self.cage_selection.copy()
        print(f" -> {rabbits = }, {cages = }")
        self.selection_state(0)
        return rabbits, cages

    def on_point_allocation(self, gs: GameState=None):
        print(' - on_point_allocation: ')
        self.gs = gs  # update point information
        self.selection_state(0)

    def on_decide_continue(self, gs: GameState=None):
        print(f" - on_decide_continue: ")
        self.gs = gs
        self.selection_state(3)

        # wait untill a selection is made
        while not self.decision_locked:
            pygame.event.pump()
            self.clock.tick(self.MAX_FPS)

        roll_again = self.roll_again
        self.selection_state(0)
        return roll_again

    def on_turn_lost(self, gs: GameState=None):
        print(f' => Oh dear, no rabbits')
        self.gs = gs
        self.selection_state(0)
        time.sleep(1)

    def on_run_completed(self, gs: GameState=None):
        print(f" => Nice, you finished the dice!")
        self.gs = gs
        self.selection_state(0)

    def on_next_roll(self, gs: GameState=None):
        print(f" - Going to roll again...")
        self.gs = gs
        self.selection_state(0)

    def on_end_turn(self, gs: GameState=None):
        print(f" => Ending the turn now")
        self.gs = gs
        self.selection_state(0)
        print(f"{self.gs.game_score}")

    def on_game_over(self, gs: GameState=None):
        self.gs = gs
        self.running = False
        self.selection_state(0)

    """ ==== Selection ===="""

    def selection_state(self, state):
        # Idle
        if state == 0:
            self.highlighted_area = 0

            self.lock_button_active = False
            self.roll_again_active = False
            self.stop_active = False

            self.selection_locked = True
            self.decision_locked = True

            self.cage_selection = []
            self.rabbit_selection = []

        # Select rabbits
        if state == 1:
            self.highlighted_area = 1

            self.lock_button_active = False
            self.roll_again_active = False
            self.stop_active = False

            self.selection_locked = False

        # Select cages
        if state == 2:
            self.highlighted_area = 2

            self.lock_button_active = True
            self.roll_again_active = False
            self.stop_active = False

            self.selection_locked = False

        # Select continue
        if state == 3:
            self.highlighted_area = 3

            self.lock_button_active = False
            self.roll_again_active = True
            self.stop_active = True

            self.decision_locked = False

    def on_click_dice(self, i_selected):
        roll = self.gs.roll
        selected = roll[i_selected]

        # == Selecting rabbits
        if self.highlighted_area == 1 and selected in [1, 2]:

            # - Select
            if i_selected not in self.roll_iselection:
                self.roll_iselection.append(i_selected)
                self.rabbit_selection.append(selected)
                self.lock_button_active = True

            # - Deselect
            else:
                self.roll_iselection.remove(i_selected)
                self.rabbit_selection.remove(selected)

                if not self.roll_iselection:
                    self.lock_button_active = False

        # == Selecting cages
        elif self.highlighted_area == 2 and selected in [2, 3, 4, 5]:

            # - Select
            if i_selected not in self.roll_iselection:
                next_cage = len(self.gs.cages) + 2 + len(self.roll_iselection)
                if selected == next_cage and selected <= 5:
                    self.roll_iselection.append(i_selected)
                    self.cage_selection.append(selected)

            # - Deselect
            else:
                to_remove = []
                for j in self.roll_iselection:
                    if roll[j] >= selected:
                        to_remove.append(j)
                        
                for j in to_remove:
                    self.roll_iselection.remove(j)
                    self.cage_selection.remove(roll[j])

    def on_lock(self):
        # Inactive state
        if self.highlighted_area == 0: ...

        # Select Rabbits
        elif self.highlighted_area == 1:
            # - Delete rabbits from board
            self.roll_iselection.sort(reverse=True)
            for i in self.roll_iselection:
                del self.gs.roll[i]
            self.roll_iselection = []
            self.selection_state(2)
            
        # Select Cages
        elif self.highlighted_area == 2:
            self.roll_iselection.sort(reverse=True)
            for i in self.roll_iselection:
                del self.gs.roll[i]
            self.roll_iselection = []
            # self.selection_state(0)
            self.selection_locked = True

    def on_roll(self):
        self.roll_again = True
        self.decision_locked = True
        # self.to_state(0)

    def on_stop(self):
        self.roll_again = False
        self.decision_locked = True

        self.cage_selection = []
        self.rabbit_selection = []

    """ ==== Visualization ==== """

    def draw(self):
        # Background
        self.screen.fill((255, 255, 255))

        # Dice area
        if self.highlighted_area == 0:
            allowed = []
        elif self.highlighted_area == 1:
            allowed = [1, 2]
        elif self.highlighted_area == 2:
            allowed = [2, 3, 4, 5]
        elif self.highlighted_area == 3:
            allowed = []

        self.draw_dice_area(
            self.dice_rects,
            self.gs.roll,
            (200, 200, 200),
            selected_indices=self.roll_iselection,
            allowed=allowed,
        )

        # Area 1: Rabbits
        self.draw_dice_area(
            self.rabbit_rects, 
            self.gs.rabbits + self.rabbit_selection, 
            (180, 240, 180) if self.highlighted_area == 1 else (220, 220, 220),
            allowed=allowed,
            )

        # Area 2: Cages
        self.draw_dice_area(
            self.cage_rects, 
            self.gs.cages + self.cage_selection, 
            (180, 240, 180) if self.highlighted_area == 2 else (220, 220, 220),
            allowed=allowed,
            )

        # Lock button
        lock_color = (0, 200, 0) if self.lock_button_active else (150, 150, 150)
        pygame.draw.rect(self.screen, lock_color, self.lock_button_rect)
        font = pygame.font.Font(None, 36)
        text = font.render("Lock", True, (255, 255, 255))
        text_rect = text.get_rect(center=self.lock_button_rect.center)
        self.screen.blit(text, text_rect)

        # Roll again
        lock_color = (0, 200, 0) if self.roll_again_active else (150, 150, 150)
        pygame.draw.rect(self.screen, lock_color, self.roll_again_rect)
        text = font.render("Roll", True, (255, 255, 255))
        text_rect = text.get_rect(center=self.roll_again_rect.center)
        self.screen.blit(text, text_rect)

        # Stop button
        lock_color = (0, 200, 0) if self.stop_active else (150, 150, 150)
        pygame.draw.rect(self.screen, lock_color, self.stop_rect)
        text = font.render("Stop", True, (255, 255, 255))
        text_rect = text.get_rect(center=self.stop_rect.center)
        self.screen.blit(text, text_rect)  

        # Score Label
        pygame.draw.rect(
            self.screen, 
            (150, 150, 150), 
            self.score_rect
        )
        text = font.render(f"Turn: {self.gs.run_score + self.gs.turn_score}", True, (255, 255, 255))
        self.screen.blit(text, text.get_rect(center=self.score_rect.center))      

        # Game Score Label
        pygame.draw.rect(
            self.screen, 
            (150, 150, 150), 
            self.game_score_rect
        )
        text = font.render(f"Game: {self.gs.game_score}", True, (255, 255, 255))
        self.screen.blit(text, text.get_rect(center=self.game_score_rect.center))    

        pygame.display.flip()
        return

    def draw_dice_area(self, rects, values, bg_color, selected_indices=None, allowed=None):
        font = pygame.font.Font(None, 36)

        for i, rect in enumerate(rects):

            # - Dice is empty.
            if i >= len(values):
                pygame.draw.rect(self.screen, bg_color, rect)  # Background
                pygame.draw.rect(self.screen, (0, 0, 0), rect, 2)  # Black border
                continue

            dice_value = values[i]
           
            # - Dice is selected.
            if selected_indices and i in selected_indices:
                pygame.draw.rect(self.screen, (0, 255, 0), rect)  # Green for selection
                pygame.draw.rect(self.screen, (0, 0, 0), rect, 2)  # Black border
                text = font.render(
                    str(dice_value), True, 
                    (0, 0, 0) if dice_value in allowed else (150, 150, 150)
                    )
                self.screen.blit(text, text.get_rect(center=rect.center))

            # - Dice is deselected.
            else:
                pygame.draw.rect(self.screen, bg_color, rect)  # Background
                pygame.draw.rect(self.screen, (0, 0, 0), rect, 2)  # Black border
                text = font.render(
                    str(dice_value), True, 
                    (0, 0, 0) if dice_value in allowed else (150, 150, 150)
                    )
                self.screen.blit(text, text.get_rect(center=rect.center))

    def error_message(self, message):
        print(f"ERROR: {message}")


if __name__ == "__main__":
    import time
    gui = GraphicalUI()
    print('ended')