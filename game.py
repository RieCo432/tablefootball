import pygame
from time import sleep
from os import environ
from math import sin, floor, pi
environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (50, 50)
pygame.init()


class Table:
    # Various properties of the table and its representation
    width = 600
    length = 1200

    player_width = 40
    player_thickness = 20
    player_height = 120
    player_border = 2

    stick_width = 10
    stick_color = (127, 127, 127)
    stick_border = 2

    goal_color = (0, 255, 0)
    goal_width = 150
    goal_thickness = 5
    goal_border = 2
    
    key_lin_acc = 0.4
    key_rot_acc = pi / 256


screen = pygame.display.set_mode((Table.length, Table.width))
screen.fill(0)


class PlayerRole:
    keeper = 0
    defence = 1
    middle = 2
    attack = 3


class PlayerStick:

    def __init__(self, opponent_num, player_type):
        self.opponent = opponent_num  # Player 1 (=0) or 2 (=1)
        if player_type == PlayerRole.keeper:
            self.players = 1  # 1 foosman on goal keeper stick
            if self.opponent == 0:
                self.pos_x = (1/9) * Table.length  # Player 1 keeper is at stick position 1 from left
            elif self.opponent == 1:
                self.pos_x = (8/9) * Table.length  # Player 2 keeper is at stick position 8 from left
        elif player_type == PlayerRole.defence:
            self.players = 2  # 2 foosmen on defence stick
            if self.opponent == 0:
                self.pos_x = (2/9) * Table.length  # Player 1 defence is at stick position 2 from left
            elif self.opponent == 1:
                self.pos_x = (7/9) * Table.length  # Player 2 defence is at stick position 7 from left
        elif player_type == PlayerRole.middle:
            self.players = 5  # 5 foosmen on middlefield stick
            if self.opponent == 0:
                self.pos_x = (4/9) * Table.length  # Player 1 middlefield is at stick position 4 from left
            elif self.opponent == 1:
                self.pos_x = (5/9) * Table.length  # Player 2 middlefield is at stick position 5 from left
        elif player_type == PlayerRole.attack:
            self.players = 3  # 3 foosmen on attacker stick
            if self.opponent == 0:
                self.pos_x = (6/9) * Table.length  # Player 1 attack is at stick position 6 from left
            elif self.opponent == 1:
                self.pos_x = (3/9) * Table.length  # Player 2 attack is at stick position 3 from left

        self.lin_range = int(floor((1/(self.players + 1)) * Table.width - (Table.player_width / 2)))

        self.lin_acc = 0.0  # Stick starts without any linear acceleration
        self.lin_vel = 0.0  # Stick starts without any linear velocity
        self.lin_pos = 0  # Stick starts in middle of total sliding range

        self.rot_acc = 0.0  # Stick starts without any rotational acceleration
        self.rot_vel = 0.0  # Stick starts without any rotational velocity
        self.rot_pos = 0.0  # Stick starts at down position (=0 radians)

        if opponent_num == 0:
            self.color = (0, 0, 255)  # Player 1 is blue
        elif opponent_num == 1:
            self.color = (255, 0, 0)  # Player 2 is red

    def update(self):
        # Update linear velocity and limit to 20 pixels
        self.lin_vel += self.lin_acc
        if self.lin_vel > 20:
            self.lin_vel = 20
        elif self.lin_vel < -20:
            self.lin_vel = -20

        # Update linear position and limit to moving range
        self.lin_pos = int(round(self.lin_pos + self.lin_vel))
        if self.lin_pos < -self.lin_range:
            self.lin_pos = -self.lin_range
        elif self.lin_pos > self.lin_range:
            self.lin_pos = self.lin_range

        # Update rotation speed and angle
        self.rot_vel += self.rot_acc
        self.rot_pos += self.rot_vel

    def draw(self):
        pygame.draw.rect(screen, Table.stick_color, (self.pos_x - Table.stick_width/2, 0, Table.stick_width, Table.width), Table.stick_border)  # draw the stick
        for player in range(self.players):  # Draw each foosman on the stick taking into account their rotation angles
            pygame.draw.rect(screen, self.color, (self.pos_x - Table.player_thickness / 2 - int(round(Table.player_height / 2 * sin(self.rot_pos))), ((player + 1)/(self.players + 1)) * Table.width - Table.player_width / 2 + self.lin_pos, Table.player_thickness + int(round(Table.player_height * sin(self.rot_pos))), Table.player_width), Table.player_border)


class Opponent:

    def __init__(self, opponent_num):
        self.score = 0
        self.sticks = []
        for role in range(4):  # Generate 4 sticks with roles 0 to 3 (roles defined as integers in the PlayerRole class)
            self.sticks.append(PlayerStick(opponent_num, role))

    def draw(self):
        # Draw all sticks and foosmen
        for stick in self.sticks:
            stick.draw()

    def update(self):
        # Update velocities, positions and rotation angles
        for stick in self.sticks:
            stick.update()


def draw_all(opponents_list):
    # Draw all sticks and foosmen
    for op in opponents_list:
        op.draw()


def update_all(opponents_list):
    # Update velocities, positions and rotation angles
    for op in opponents_list:
        op.update()

    pygame.draw.rect(screen, Table.goal_color, (0, Table.width/2 - Table.goal_width/2, Table.goal_thickness, Table.goal_width), Table.goal_border)  # Draw goal 1
    pygame.draw.rect(screen, Table.goal_color, (Table.length - Table.goal_thickness, Table.width / 2 - Table.goal_width / 2, Table.goal_thickness, Table.goal_width), Table.goal_border)  # Draw goal 2


opponents = []  # Generate 2 opponent objects and put them in a list
for i in range(2):
    opponents.append(Opponent(i))


draw_all(opponents)
pygame.display.flip()


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit(0)

            # Controls: pressing and holding various keys subjects the sticks to acceleration, both for shifting
            # and for rotating
            # Releasing the key will instantly stop the current translation or rotation

        if event.type == pygame.KEYDOWN:

            # Player 1 controls

            if event.key == pygame.K_s:
                opponents[0].sticks[0].lin_acc = -Table.key_lin_acc
            elif event.key == pygame.K_x:
                opponents[0].sticks[0].lin_acc = Table.key_lin_acc
            if event.key == pygame.K_z:
                opponents[0].sticks[0].rot_acc = -Table.key_rot_acc
            elif event.key == pygame.K_c:
                opponents[0].sticks[0].rot_acc = Table.key_rot_acc

            if event.key == pygame.K_g:
                opponents[0].sticks[1].lin_acc = -Table.key_lin_acc
            elif event.key == pygame.K_b:
                opponents[0].sticks[1].lin_acc = Table.key_lin_acc
            if event.key == pygame.K_v:
                opponents[0].sticks[1].rot_acc = -Table.key_rot_acc
            elif event.key == pygame.K_n:
                opponents[0].sticks[1].rot_acc = Table.key_rot_acc

            if event.key == pygame.K_k:
                opponents[0].sticks[2].lin_acc = -Table.key_lin_acc
            elif event.key == pygame.K_COMMA:
                opponents[0].sticks[2].lin_acc = Table.key_lin_acc
            if event.key == pygame.K_m:
                opponents[0].sticks[2].rot_acc = -Table.key_rot_acc
            elif event.key == pygame.K_PERIOD:
                opponents[0].sticks[2].rot_acc = Table.key_rot_acc

            if event.key == pygame.K_UP:
                opponents[0].sticks[3].lin_acc = -Table.key_lin_acc
            elif event.key == pygame.K_DOWN:
                opponents[0].sticks[3].lin_acc = Table.key_lin_acc
            if event.key == pygame.K_LEFT:
                opponents[0].sticks[3].rot_acc = -Table.key_rot_acc
            elif event.key == pygame.K_RIGHT:
                opponents[0].sticks[3].rot_acc = Table.key_rot_acc

                # Player 2 controls

            if event.key == pygame.K_2:
                opponents[1].sticks[3].lin_acc = -Table.key_lin_acc
            elif event.key == pygame.K_w:
                opponents[1].sticks[3].lin_acc = Table.key_lin_acc
            if event.key == pygame.K_q:
                opponents[1].sticks[3].rot_acc = -Table.key_rot_acc
            elif event.key == pygame.K_e:
                opponents[1].sticks[3].rot_acc = Table.key_rot_acc

            if event.key == pygame.K_5:
                opponents[1].sticks[2].lin_acc = -Table.key_lin_acc
            elif event.key == pygame.K_t:
                opponents[1].sticks[2].lin_acc = Table.key_lin_acc
            if event.key == pygame.K_r:
                opponents[1].sticks[2].rot_acc = -Table.key_rot_acc
            elif event.key == pygame.K_y:
                opponents[1].sticks[2].rot_acc = Table.key_rot_acc

            if event.key == pygame.K_8:
                opponents[1].sticks[1].lin_acc = -Table.key_lin_acc
            elif event.key == pygame.K_i:
                opponents[1].sticks[1].lin_acc = Table.key_lin_acc
            if event.key == pygame.K_u:
                opponents[1].sticks[1].rot_acc = -Table.key_rot_acc
            elif event.key == pygame.K_o:
                opponents[1].sticks[1].rot_acc = Table.key_rot_acc

            if event.key == pygame.K_MINUS:
                opponents[1].sticks[0].lin_acc = -Table.key_lin_acc
            elif event.key == pygame.K_LEFTBRACKET:
                opponents[1].sticks[0].lin_acc = Table.key_lin_acc
            if event.key == pygame.K_p:
                opponents[1].sticks[0].rot_acc = -Table.key_rot_acc
            elif event.key == pygame.K_RIGHTBRACKET:
                opponents[1].sticks[0].rot_acc = Table.key_rot_acc


        if event.type == pygame.KEYUP:

            # Player 1 controls

            if event.key == pygame.K_s or event.key == pygame.K_x:
                opponents[0].sticks[0].lin_acc = 0
                opponents[0].sticks[0].lin_vel = 0
            if event.key == pygame.K_z or event.key == pygame.K_c:
                opponents[0].sticks[0].rot_acc = 0
                opponents[0].sticks[0].rot_vel = 0

            if event.key == pygame.K_g or event.key == pygame.K_b:
                opponents[0].sticks[1].lin_acc = 0
                opponents[0].sticks[1].lin_vel = 0
            if event.key == pygame.K_v or event.key == pygame.K_n:
                opponents[0].sticks[1].rot_acc = 0
                opponents[0].sticks[1].rot_vel = 0

            if event.key == pygame.K_k or event.key == pygame.K_COMMA:
                opponents[0].sticks[2].lin_acc = 0
                opponents[0].sticks[2].lin_vel = 0
            if event.key == pygame.K_m or event.key == pygame.K_PERIOD:
                opponents[0].sticks[2].rot_acc = 0
                opponents[0].sticks[2].rot_vel = 0

            if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                opponents[0].sticks[3].lin_acc = 0
                opponents[0].sticks[3].lin_vel = 0
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                opponents[0].sticks[3].rot_acc = 0
                opponents[0].sticks[3].rot_vel = 0

                # Player 2 controls

            if event.key == pygame.K_2 or event.key == pygame.K_w:
                opponents[1].sticks[3].lin_acc = 0
                opponents[1].sticks[3].lin_vel = 0
            if event.key == pygame.K_q or event.key == pygame.K_e:
                opponents[1].sticks[3].rot_acc = 0
                opponents[1].sticks[3].rot_vel = 0

            if event.key == pygame.K_5 or event.key == pygame.K_t:
                opponents[1].sticks[2].lin_acc = 0
                opponents[1].sticks[2].lin_vel = 0
            if event.key == pygame.K_r or event.key == pygame.K_y:
                opponents[1].sticks[2].rot_acc = 0
                opponents[1].sticks[2].rot_vel = 0

            if event.key == pygame.K_8 or event.key == pygame.K_i:
                opponents[1].sticks[1].lin_acc = 0
                opponents[1].sticks[1].lin_vel = 0
            if event.key == pygame.K_u or event.key == pygame.K_o:
                opponents[1].sticks[1].rot_acc = 0
                opponents[1].sticks[1].rot_vel = 0

            if event.key == pygame.K_MINUS or event.key == pygame.K_LEFTBRACKET:
                opponents[1].sticks[0].lin_acc = 0
                opponents[1].sticks[0].lin_vel = 0
            if event.key == pygame.K_p or event.key == pygame.K_RIGHTBRACKET:
                opponents[1].sticks[0].rot_acc = 0
                opponents[1].sticks[0].rot_vel = 0

    screen.fill(0)
    update_all(opponents)
    draw_all(opponents)
    pygame.display.flip()

    sleep(0.01)
