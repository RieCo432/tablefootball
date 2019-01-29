import pygame
from time import sleep
from os import environ
from math import sin, floor, pi, sqrt, tan, atan

parallel_games = 1


class Table:
    # Various properties of the table and its representation
    width = 600
    length = 1200
    edge_hit_cin_energy_efficiency = 0.95

    player_width = 40
    player_thickness = 20
    player_height = 160
    player_border = 2
    player_angle_hit_limit = pi / 6
    player_max_lin_vel = 20
    player_max_rot_vel = 0.2 * pi
    player_hit_cin_energy_efficiency = 0.1

    ball_radius = 20
    ball_color = (255, 255, 255)
    ball_max_vel = 1
    ball_table_friction_coefficient = 0.001

    stick_width = 10
    stick_color = (127, 127, 127)
    stick_border = 2

    goal_color = (0, 255, 0)
    goal_width = 150
    goal_thickness = 5
    goal_border = 2
    
    key_lin_acc = 0.4
    key_rot_acc = pi / 256

    debug = True  # Enables displaying of the collision boxes
    collision_box_color = (200, 255, 0)
    collision_box_border = 3


class PlayerRole:  # Bind player role to an integer
    keeper = 0
    defence = 1
    middle = 2
    attack = 3


def mod2pi(angle):  # Simple function to emulate modulo 2 pi to keep angle value in range for the collision boxes

    while angle < pi:
        angle += 2 * pi
    while angle > pi:
        angle -= 2 * pi

    return angle

def get_dist(x1, y1, x2, y2):
    return sqrt((x2 - x1)**2 + (y2 - y1)**2)


class PlayerStick:

    def __init__(self, opponent_num, player_type, game):
        self.game = game
        self.player_role = player_type
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
        self.rot_pos = pi / 2  # Stick starts at down position (=0 radians)

        if opponent_num == 0:
            self.color = (0, 0, 255)  # Player 1 is blue
        elif opponent_num == 1:
            self.color = (255, 0, 0)  # Player 2 is red


    def update(self):
        # Update linear velocity and limit to 20 pixels
        self.lin_vel += self.lin_acc
        if self.lin_vel > Table.player_max_lin_vel:
            self.lin_vel = Table.player_max_lin_vel
        elif self.lin_vel < - Table.player_max_lin_vel:
            self.lin_vel = - Table.player_max_lin_vel

        # Update linear position and limit to moving range
        self.lin_pos = int(round(self.lin_pos + self.lin_vel))
        if self.lin_pos < -self.lin_range:
            self.lin_pos = -self.lin_range
        elif self.lin_pos > self.lin_range:
            self.lin_pos = self.lin_range

        # Update rotation speed and angle
        self.rot_vel += self.rot_acc
        if self.rot_vel > Table.player_max_rot_vel:
            self.rot_vel = Table.player_max_rot_vel
        elif self.rot_vel < - Table.player_max_rot_vel:
            self.rot_vel = - Table.player_max_rot_vel

        self.rot_pos += self.rot_vel
        self.rot_pos = mod2pi(self.rot_pos)

    def draw(self):
        pygame.draw.rect(screen, Table.stick_color, (self.pos_x - Table.stick_width/2, 0, Table.stick_width, Table.width), Table.stick_border)  # draw the stick
        for player in range(self.players):  # Draw each foosman on the stick taking into account their rotation angles
            pygame.draw.rect(screen, self.color, (self.pos_x - Table.player_thickness / 2 - int(round(Table.player_height / 2 * sin(self.rot_pos))), ((player + 1)/(self.players + 1)) * Table.width - Table.player_width / 2 + self.lin_pos, Table.player_thickness + int(round(Table.player_height * sin(self.rot_pos))), Table.player_width), Table.player_border)


class Opponent:

    def __init__(self, opponent_num, game):
        self.game = game
        self.score = 0
        self.sticks = []
        self.collision_rects = []  # Store collsion rectangles
        for role in range(4):  # Generate 4 sticks with roles 0 to 3 (roles defined as integers in the PlayerRole class)
            self.sticks.append(PlayerStick(opponent_num, role, game))

    def draw(self):
        # Draw all sticks and foosmen
        for stick in self.sticks:
            stick.draw()

        if Table.debug:  # Draw collision boxes
            for collision_rect in self.collision_rects:
                pygame.draw.rect(screen, Table.collision_box_color, collision_rect["pygame_tuple"], Table.collision_box_border)

    def build_collision_boxes(self):  # Generate collision boxes and add them to a list
        self.collision_rects = []     # Collisions are stored with center coordinates and a tuple for pygame drawing
        for stick in self.sticks:
            if abs(stick.rot_pos) < Table.player_angle_hit_limit:
                collision_rect_x = stick.pos_x + Table.player_height / 2 * sin(stick.rot_pos)
                for i in range(stick.players):
                    collision_rect_y = ((i + 1) / (stick.players + 1)) * Table.width + stick.lin_pos
                    collision_rect = {"playerRole": stick.player_role, "center_x": collision_rect_x, "center_y": collision_rect_y, "pygame_tuple": (collision_rect_x - Table.player_thickness / 2, collision_rect_y - Table.player_width / 2, Table.player_thickness, Table.player_width)}
                    self.collision_rects.append(collision_rect)

    def update(self):
        # Update velocities, positions and rotation angles
        for stick in self.sticks:
            stick.update()

        self.build_collision_boxes()


class Ball:

    def __init__(self, game):
        self.pos_x = int(round(Table.length / 2))
        self.pos_y = int(round(Table.width / 2))
        self.acc_x = 0
        self.acc_y = 0
        self.vel_x = 0
        self.vel_y = 0
        self.game = game

    def check_collision(self):
        for opponent in self.game.opponents:
            for collision_box in opponent.collision_rects:
                # print(collision_box)
                # print((collision_box["center_y"] + Table.player_width / 2) <= (self.pos_y + Table.ball_radius))
                # print((self.pos_y - Table.ball_radius) <= (collision_box["center_y"] + Table.player_width / 2))
                if (collision_box["center_y"] - Table.player_width / 2) <= self.pos_y <= (collision_box["center_y"] + Table.player_width / 2):
                    # print("correct height detected")
                    if ((self.pos_x + Table.ball_radius) >= collision_box["center_x"] - Table.player_thickness / 2) and ((self.pos_x - Table.ball_radius) <= (collision_box["center_x"] + Table.player_thickness / 2)):
                        if self.vel_x < opponent.sticks[collision_box["playerRole"]].rot_vel * Table.player_height:  # Ball hit right side of hitbox
                            self.pos_x = collision_box["center_x"] + Table.player_thickness / 2 + Table.ball_radius + 1
                        elif self.vel_x > opponent.sticks[collision_box["playerRole"]].rot_vel * Table.player_height:  # Ball hit left side of hitbox
                            self.pos_x = collision_box["center_x"] - Table.player_thickness / 2 - Table.ball_radius - 1
                        self.vel_x = (- self.vel_x) * Table.player_hit_cin_energy_efficiency + opponent.sticks[collision_box["playerRole"]].rot_vel * Table.player_height  # Change velocity sign and account for energy loss and add player rot speed
                        self.vel_y = self.vel_y * Table.player_hit_cin_energy_efficiency  # Change velocity sign and account for energy loss

                elif (collision_box["center_x"] - Table.player_thickness / 2) <= self.pos_x <= (collision_box["center_x"] + Table.player_thickness / 2):
                    if ((self.pos_y + Table.ball_radius) >= collision_box["center_y"] - Table.player_width / 2) and ((self.pos_y - Table.ball_radius) <= collision_box["center_y"] + Table.player_width / 2):
                        if self.vel_y < opponent.sticks[collision_box["playerRole"]].lin_vel:  # Ball hit lower side of hitbox
                            self.pos_y = collision_box["center_y"] + Table.player_width / 2 + Table.ball_radius + 1
                        elif self.vel_y > opponent.sticks[collision_box["playerRole"]].lin_vel:  # Ball hit upper side of hitbox
                            self.pos_y = collision_box["center_y"] - Table.player_width / 2 - Table.ball_radius - 1
                        self.vel_x = self.vel_x * Table.player_hit_cin_energy_efficiency   # Change velocity sign and account for energy loss
                        self.vel_y = (- self.vel_y) * Table.player_hit_cin_energy_efficiency + opponent.sticks[collision_box["playerRole"]].lin_vel  # Change velocity sign and account for energy loss and add player lin speed

                elif (self.pos_x <= collision_box["center_x"] - Table.player_thickness / 2) and (self.pos_y <= collision_box["center_y"] - Table.player_width / 2):  # Upper left corner
                    if get_dist(self.pos_x, self.pos_y, collision_box["center_x"] - Table.player_thickness / 2, collision_box["center_y"] - Table.player_width / 2) <= Table.ball_radius:  # Collsions
                        x = self.pos_x - (collision_box["center_x"] - Table.player_thickness / 2)
                        y = self.pos_y - (collision_box["center_y"] - Table.player_width / 2)
                        c = - 2 * (self.vel_x * x + self.vel_y * y) / (x**2 + y**2)
                        self.vel_x = (self.vel_x + c * x)  # * Table.player_hit_cin_energy_efficiency
                        self.vel_y = (self.vel_y + c * y)  # * Table.player_hit_cin_energy_efficiency

                elif (self.pos_x <= collision_box["center_x"] - Table.player_thickness / 2) and (self.pos_y >= collision_box["center_y"] + Table.player_width / 2):  # Lower left corner
                    if get_dist(self.pos_x, self.pos_y, collision_box["center_x"] - Table.player_thickness / 2, collision_box["center_y"] + Table.player_width / 2) <= Table.ball_radius:  # Collsions
                        x = self.pos_x - (collision_box["center_x"] - Table.player_thickness / 2)
                        y = self.pos_y - (collision_box["center_y"] + Table.player_width / 2)
                        c = - 2 * (self.vel_x * x + self.vel_y * y) / (x**2 + y**2)
                        self.vel_x = (self.vel_x + c * x)  # * Table.player_hit_cin_energy_efficiency
                        self.vel_y = (self.vel_y + c * y)  # * Table.player_hit_cin_energy_efficiency

                elif (self.pos_x >= collision_box["center_x"] + Table.player_thickness / 2) and (self.pos_y <= collision_box["center_y"] - Table.player_width / 2):  # Upper right corner
                    if get_dist(self.pos_x, self.pos_y, collision_box["center_x"] + Table.player_thickness / 2, collision_box["center_y"] - Table.player_width / 2) <= Table.ball_radius:  # Collsions
                        x = self.pos_x - (collision_box["center_x"] + Table.player_thickness / 2)
                        y = self.pos_y - (collision_box["center_y"] - Table.player_width / 2)
                        c = - 2 * (self.vel_x * x + self.vel_y * y) / (x**2 + y**2)
                        self.vel_x = (self.vel_x + c * x)  # * Table.player_hit_cin_energy_efficiency
                        self.vel_y = (self.vel_y + c * y)  # * Table.player_hit_cin_energy_efficiency
                        tan_a = (self.pos_y - (collision_box["center_y"] - Table.player_width / 2) / ((collision_box["center_x"]) + Table.player_thickness / 2))
                        self.pos_x = (Table.ball_radius + 1) / (sqrt(1 + tan_a**2)) + (collision_box["center_x"] + Table.player_thickness / 2)
                        self.pos_y = ((collision_box["center_x"] + Table.player_thickness / 2) - self.pos_x) * tan_a + (collision_box["center_y"] - Table.player_width / 2)
                        print("x", self.pos_x)
                        print("y", self.pos_y)

                elif (self.pos_x >= collision_box["center_x"] + Table.player_thickness / 2) and (self.pos_y >= collision_box["center_y"] + Table.player_width / 2):  # Lower right corner
                    if get_dist(self.pos_x, self.pos_y, collision_box["center_x"] + Table.player_thickness / 2, collision_box["center_y"] + Table.player_width / 2) <= Table.ball_radius:  # Collsions
                        x = self.pos_x - (collision_box["center_x"] + Table.player_thickness / 2)
                        y = self.pos_y - (collision_box["center_y"] + Table.player_width / 2)
                        c = - 2 * (self.vel_x * x + self.vel_y * y) / (x**2 + y**2)
                        self.vel_x = (self.vel_x + c * x)  # * Table.player_hit_cin_energy_efficiency
                        self.vel_y = (self.vel_y + c * y)  # * Table.player_hit_cin_energy_efficiency

            if self.pos_x - Table.ball_radius <= 0:  # Left edge collision
                self.pos_x = Table.ball_radius + 1
                self.vel_x = (- self.vel_x) * Table.edge_hit_cin_energy_efficiency
                self.vel_y = self.vel_y * Table.edge_hit_cin_energy_efficiency

            if self.pos_x + Table.ball_radius >= Table.length:  # Right edge collision
                self.pos_x = Table.length - Table.ball_radius - 1
                self.vel_x = (- self.vel_x) * Table.edge_hit_cin_energy_efficiency
                self.vel_y = self.vel_y * Table.edge_hit_cin_energy_efficiency

            if self.pos_y - Table.ball_radius <= 0:  # Upper edge collision
                self.pos_y = Table.ball_radius + 1
                self.vel_x = self.vel_x * Table.edge_hit_cin_energy_efficiency
                self.vel_y = (- self.vel_y) * Table.edge_hit_cin_energy_efficiency

            if self.pos_y + Table.ball_radius >= Table.width:  # Lower edge collision
                self.pos_y = Table.width - Table.ball_radius - 1
                self.vel_x = self.vel_x * Table.edge_hit_cin_energy_efficiency
                self.vel_y = (- self.vel_y) * Table.edge_hit_cin_energy_efficiency


    def update(self):
        self.vel_x += self.acc_x
        self.vel_y += self.acc_y

        # Account for friction
        self.vel_x -= Table.ball_table_friction_coefficient * (self.vel_x**2)
        self.vel_y -= Table.ball_table_friction_coefficient * (self.vel_y**2)

        self.pos_x += self.vel_x
        self.pos_y += self.vel_y

        self.check_collision()

    def draw(self):
        pygame.draw.circle(screen, Table.ball_color, (int(round(self.pos_x)), int(round(self.pos_y))), Table.ball_radius, 0)


class Game:

    def __init__(self):
        self.max_score = 0
        self.best_player = 0
        self.ball = Ball(self)
        self.opponents = []  # Generate 2 opponent objects and put them in a list
        for i in range(2):
            self.opponents.append(Opponent(i, self))

    def draw_all(self):
        # Draw all sticks and foosmen
        for op in self.opponents:
            op.draw()

        self.ball.draw()

    def update_all(self):
        # Update velocities, positions and rotation angles
        for op in self.opponents:
            op.update()

        self.ball.update()

        if self.opponents[0].score > self.opponents[1].score:
            self.max_score = self.opponents[0].score
            self.best_player = 0
        else:
            self.max_score = self.opponents[1].score
            self.best_player = 1

        pygame.draw.rect(screen, Table.goal_color, (0, Table.width/2 - Table.goal_width/2, Table.goal_thickness, Table.goal_width), Table.goal_border)  # Draw goal 1
        pygame.draw.rect(screen, Table.goal_color, (Table.length - Table.goal_thickness, Table.width / 2 - Table.goal_width / 2, Table.goal_thickness, Table.goal_width), Table.goal_border)  # Draw goal 2


environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (50, 50)
pygame.init()
screen = pygame.display.set_mode((Table.length, Table.width))
screen.fill(0)

games = []
for game_num in range(parallel_games):
    games.append(Game())

# game = Game()

# opponents = []
# for i in range(2):
#     opponents.append(Opponent(i, game))

for game in games:

    while True and game.max_score < 11:
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
                    game.opponents[0].sticks[0].lin_acc = -Table.key_lin_acc
                elif event.key == pygame.K_x:
                    game.opponents[0].sticks[0].lin_acc = Table.key_lin_acc
                if event.key == pygame.K_z:
                    game.opponents[0].sticks[0].rot_acc = -Table.key_rot_acc
                elif event.key == pygame.K_c:
                    game.opponents[0].sticks[0].rot_acc = Table.key_rot_acc

                if event.key == pygame.K_g:
                    game.opponents[0].sticks[1].lin_acc = -Table.key_lin_acc
                elif event.key == pygame.K_b:
                    game.opponents[0].sticks[1].lin_acc = Table.key_lin_acc
                if event.key == pygame.K_v:
                    game.opponents[0].sticks[1].rot_acc = -Table.key_rot_acc
                elif event.key == pygame.K_n:
                    game.opponents[0].sticks[1].rot_acc = Table.key_rot_acc

                if event.key == pygame.K_k:
                    game.opponents[0].sticks[2].lin_acc = -Table.key_lin_acc
                elif event.key == pygame.K_COMMA:
                    game.opponents[0].sticks[2].lin_acc = Table.key_lin_acc
                if event.key == pygame.K_m:
                    game.opponents[0].sticks[2].rot_acc = -Table.key_rot_acc
                elif event.key == pygame.K_PERIOD:
                    game.opponents[0].sticks[2].rot_acc = Table.key_rot_acc

                if event.key == pygame.K_UP:
                    game.opponents[0].sticks[3].lin_acc = -Table.key_lin_acc
                elif event.key == pygame.K_DOWN:
                    game.opponents[0].sticks[3].lin_acc = Table.key_lin_acc
                if event.key == pygame.K_LEFT:
                    game.opponents[0].sticks[3].rot_acc = -Table.key_rot_acc
                elif event.key == pygame.K_RIGHT:
                    game.opponents[0].sticks[3].rot_acc = Table.key_rot_acc

                    # Player 2 controls

                if event.key == pygame.K_2:
                    game.opponents[1].sticks[3].lin_acc = -Table.key_lin_acc
                elif event.key == pygame.K_w:
                    game.opponents[1].sticks[3].lin_acc = Table.key_lin_acc
                if event.key == pygame.K_q:
                    game.opponents[1].sticks[3].rot_acc = -Table.key_rot_acc
                elif event.key == pygame.K_e:
                    game.opponents[1].sticks[3].rot_acc = Table.key_rot_acc

                if event.key == pygame.K_5:
                    game.opponents[1].sticks[2].lin_acc = -Table.key_lin_acc
                elif event.key == pygame.K_t:
                    game.opponents[1].sticks[2].lin_acc = Table.key_lin_acc
                if event.key == pygame.K_r:
                    game.opponents[1].sticks[2].rot_acc = -Table.key_rot_acc
                elif event.key == pygame.K_y:
                    game.opponents[1].sticks[2].rot_acc = Table.key_rot_acc

                if event.key == pygame.K_8:
                    game.opponents[1].sticks[1].lin_acc = -Table.key_lin_acc
                elif event.key == pygame.K_i:
                    game.opponents[1].sticks[1].lin_acc = Table.key_lin_acc
                if event.key == pygame.K_u:
                    game.opponents[1].sticks[1].rot_acc = -Table.key_rot_acc
                elif event.key == pygame.K_o:
                    game.opponents[1].sticks[1].rot_acc = Table.key_rot_acc

                if event.key == pygame.K_MINUS:
                    game.opponents[1].sticks[0].lin_acc = -Table.key_lin_acc
                elif event.key == pygame.K_LEFTBRACKET:
                    game.opponents[1].sticks[0].lin_acc = Table.key_lin_acc
                if event.key == pygame.K_p:
                    game.opponents[1].sticks[0].rot_acc = -Table.key_rot_acc
                elif event.key == pygame.K_RIGHTBRACKET:
                    game.opponents[1].sticks[0].rot_acc = Table.key_rot_acc

            if event.type == pygame.KEYUP:

                # Player 1 controls

                if event.key == pygame.K_s or event.key == pygame.K_x:
                    game.opponents[0].sticks[0].lin_acc = 0
                    game.opponents[0].sticks[0].lin_vel = 0
                if event.key == pygame.K_z or event.key == pygame.K_c:
                    game.opponents[0].sticks[0].rot_acc = 0
                    game.opponents[0].sticks[0].rot_vel = 0

                if event.key == pygame.K_g or event.key == pygame.K_b:
                    game.opponents[0].sticks[1].lin_acc = 0
                    game.opponents[0].sticks[1].lin_vel = 0
                if event.key == pygame.K_v or event.key == pygame.K_n:
                    game.opponents[0].sticks[1].rot_acc = 0
                    game.opponents[0].sticks[1].rot_vel = 0

                if event.key == pygame.K_k or event.key == pygame.K_COMMA:
                    game.opponents[0].sticks[2].lin_acc = 0
                    game.opponents[0].sticks[2].lin_vel = 0
                if event.key == pygame.K_m or event.key == pygame.K_PERIOD:
                    game.opponents[0].sticks[2].rot_acc = 0
                    game.opponents[0].sticks[2].rot_vel = 0

                if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    game.opponents[0].sticks[3].lin_acc = 0
                    game.opponents[0].sticks[3].lin_vel = 0
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    game.opponents[0].sticks[3].rot_acc = 0
                    game.opponents[0].sticks[3].rot_vel = 0

                    # Player 2 controls

                if event.key == pygame.K_2 or event.key == pygame.K_w:
                    game.opponents[1].sticks[3].lin_acc = 0
                    game.opponents[1].sticks[3].lin_vel = 0
                if event.key == pygame.K_q or event.key == pygame.K_e:
                    game.opponents[1].sticks[3].rot_acc = 0
                    game.opponents[1].sticks[3].rot_vel = 0

                if event.key == pygame.K_5 or event.key == pygame.K_t:
                    game.opponents[1].sticks[2].lin_acc = 0
                    game.opponents[1].sticks[2].lin_vel = 0
                if event.key == pygame.K_r or event.key == pygame.K_y:
                    game.opponents[1].sticks[2].rot_acc = 0
                    game.opponents[1].sticks[2].rot_vel = 0

                if event.key == pygame.K_8 or event.key == pygame.K_i:
                    game.opponents[1].sticks[1].lin_acc = 0
                    game.opponents[1].sticks[1].lin_vel = 0
                if event.key == pygame.K_u or event.key == pygame.K_o:
                    game.opponents[1].sticks[1].rot_acc = 0
                    game.opponents[1].sticks[1].rot_vel = 0

                if event.key == pygame.K_MINUS or event.key == pygame.K_LEFTBRACKET:
                    game.opponents[1].sticks[0].lin_acc = 0
                    game.opponents[1].sticks[0].lin_vel = 0
                if event.key == pygame.K_p or event.key == pygame.K_RIGHTBRACKET:
                    game.opponents[1].sticks[0].rot_acc = 0
                    game.opponents[1].sticks[0].rot_vel = 0

        screen.fill(0)
        game.update_all()
        game.draw_all()
        pygame.display.flip()

        sleep(0.01)
