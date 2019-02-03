from datetime import datetime
from random import uniform, randint, random
from math import e
import json
from os import path
from copy import deepcopy


def sigmoid(x):
    # print("x", x)
    final_val = 2 / (1 + e**(-x)) - 1
    # print("final_val", final_val)
    return final_val


class Node:

    def __init__(self):
        self.input_sum = 0.0
        self.output_value = 0.0
        self.layer = 0
        self.connections = []

    def activate(self):
        self.output_value = sigmoid(self.input_sum)


class Connection:

    def __init__(self, from_node, to_node, weight, conn_num):
        self.from_node = from_node
        self.to_node = to_node
        self.weight = weight
        self.conn_num = conn_num
        self.active = True

    def __str__(self):
        return "conn %d, from %d to %d weight %f" % (self.conn_num, self.from_node, self.to_node, self.weight)


class Brain:

    mutate_change_weight_prob = 0.8
    mutate_new_rand_weight_prob = 0.1
    mutate_new_connection_prob = 0.05
    mutate_new_node_prob = 0.005

    def __init__(self, input_nodes, output_nodes):
        self.node_num = -1
        self.conn_number = 0
        self.input_nodes = input_nodes
        self.output_nodes = output_nodes
        self.fitness = 0
        self.is_best = False
        self.hit_ball = False
        self.scored = False
        self.all_nodes = []
        self.all_connections = []
        # self.all_conn_str_list = []

        for i in range(self.input_nodes):  # Create input nodes (own player's sticks, opponent's sticks, ball, ball_radius, player_thickness, player_width, player_height, player_max_hit_angle)
            self.add_node(autolayer=False)
            self.all_nodes[self.node_num].layer = 0

        # self.add_node(autolayer=False)  # Bias Node
        # self.all_nodes[self.node_num].layer = 0
        # self.all_nodes[self.node_num].output_value = 1

        for i in range(output_nodes):  # Create output nodes
            self.add_node(autolayer=False)
            self.all_nodes[self.node_num].layer = 1

        for i in range(1):
            self.new_rand_connection()

    def calc_fitness(self, goal_difference_ratio, game_duration_ratio, opponent_fitness_ratio):
        if self.hit_ball:
            ball_hit_bonus = 3
        else:
            ball_hit_bonus = 0

        if self.scored:
            scored_goal_bonus = 6
        else:
            scored_goal_bonus = 0

        self.fitness = goal_difference_ratio + game_duration_ratio + opponent_fitness_ratio + ball_hit_bonus + scored_goal_bonus
        # print(self.fitness)

    def put_input(self, input_data):
        for node in self.all_nodes:
            node.input_sum = 0.0
        for i in range(len(input_data)):
            self.all_nodes[i].output_value = input_data[i]

    def get_outputs(self):
        output_list = []
        # for output_node in self.all_nodes[self.input_nodes + 1: self.input_nodes + 1 + self.output_nodes]:  # With bias node
        #     output_list.append(output_node.output_value)

        for output_node in self.all_nodes[self.input_nodes: self.input_nodes + self.output_nodes]:  # No bias node
            output_list.append(output_node.output_value)

        return output_list

    def new_rand_connection(self):
        from_node = randint(0, self.node_num)
        to_node = randint(0, self.node_num)
        conn_already_exists = False
        for conn in self.all_nodes[from_node].connections:
            conn_already_exists = conn_already_exists or self.all_connections[conn].to_node == to_node
        while self.all_nodes[from_node].layer >= self.all_nodes[to_node].layer or conn_already_exists:
            from_node = randint(0, self.node_num)
            to_node = randint(0, self.node_num)
            conn_already_exists = False
            for conn in self.all_nodes[from_node].connections:
                conn_already_exists = conn_already_exists or self.all_connections[conn].to_node == to_node
        self.add_connection(from_node, to_node, uniform(-1, 1))

    def add_node(self, autolayer=True, from_layer=0, to_layer=0):
        new_node = Node()
        if autolayer:
            if to_layer - from_layer <= 1:
                for out_node in self.all_nodes:
                    if out_node.layer > from_layer:
                        out_node.layer += 1
            new_node.layer = from_layer + 1
        self.all_nodes.append(new_node)
        self.node_num += 1

    def add_connection(self, orig, dest, wght):
        new_connection = Connection(orig, dest, wght, self.conn_number)
        self.all_connections.append(new_connection)
        self.all_nodes[orig].connections.append(self.conn_number)
        # print(str(new_connection))
        # for new_connection in self.all_connections:
            # self.all_conn_str_list.append(str(new_connection))
        self.conn_number += 1

    def feed_forward(self):

        output_layer = self.all_nodes[self.input_nodes + 2].layer

        # print(self.all_conn_str_list)

        layers = []
        for i in range(output_layer + 1):
            layers.append([])
        for i in range(len(self.all_nodes)):
            layers[self.all_nodes[i].layer].append(i)

        for layer in layers[:output_layer]:
            for node_index in layer:
                node = self.all_nodes[node_index]

                if node.layer is not 0 and node.layer is not output_layer:  # Don't call activate on input and output nodes
                    node.activate()

                if node.layer is not output_layer:  # Do not feedforward output nodes
                    # print(node.layer, node.output_value)
                    for conn_num in node.connections:
                        # print(len(self.all_connections), conn_num)
                        connection = self.all_connections[conn_num]
                        self.all_nodes[connection.to_node].input_sum += node.output_value * connection.weight

        for node in self.all_nodes[self.input_nodes:self.input_nodes + self.output_nodes]:  # Finally activate output nodes
            node.activate()
            # print(node.layer, node.output_value)

    def mutate(self):

        if random() <= Brain.mutate_new_connection_prob:
            self.new_rand_connection()

        for connection_num in range(0, len(self.all_connections)):
            connection = self.all_connections[connection_num]
            if connection.active:
                if random() <= Brain.mutate_change_weight_prob:
                    if random() <= Brain.mutate_new_rand_weight_prob:
                        connection.weight = uniform(-1, 1)
                    else:
                        change_coefficient = uniform(0.9, 1.1)
                        connection.weight *= change_coefficient
                        if connection.weight > 1:
                            connection.weight = 1
                        elif connection.weight < -1:
                            connection.weight = -1

                if random() <= Brain.mutate_new_node_prob:
                    # connection = self.all_connections[8]
                    from_node = connection.from_node
                    to_node = connection.to_node
                    self.all_nodes[from_node].connections.remove(connection.conn_num)
                    connection.active = False
                    # for i in range(0, len(self.all_connections)):
                    #     if self.all_connections[i].conn_num == connection.conn_num:
                    #         del self.all_connections[i]
                    #         break
                    self.add_node(from_layer=self.all_nodes[from_node].layer,
                                  to_layer=self.all_nodes[to_node].layer)
                    self.add_connection(from_node, self.node_num, uniform(-1, 1))
                    self.add_connection(self.node_num, to_node, uniform(-1, 1))
                    # from_node = connection.from_node
                    # to_node = connection.to_node
                    # self.all_nodes[from_node].connections.remove(connection.conn_num)
                    # self.add_node(splitnode=True, from_layer=self.all_nodes[from_node].layer, to_layer=self.all_nodes[to_node].layer)
                    # self.add_connection(from_node, self.node_num, uniform(-1, 1))
                    # self.add_connection(self.node_num, to_node, uniform(-1, 1))


class Population:

    size = 200

    def __init__(self, filename=None):
        self.all_nets = []
        self.gen = 1
        self.best_fitness = 1
        self.max_fit_index = 0
        self.max_fit_index2 = 0
        self.fitness_sum = 0

        if filename is None:
            date = datetime.now()
            self.filename = "population%d-%d-%d-%d-%d-%d.json" % (date.year, date.month, date.day, date.hour, date.minute, date.second)
        else:
            self.filename = filename

        if path.isfile(self.filename):
            with open(self.filename, "r") as fin:
                population_dict = json.load(fin)

                self.gen = population_dict["gen"]
                nets = deepcopy(population_dict["nets"])
                for net in nets:
                    import_net = Brain(36, 8)
                    import_nodes = []
                    import_net.node_num = net["node_num"]
                    import_net.conn_number = net["conn_number"]
                    for node in net["nodes"]:
                        import_node = Node()
                        import_node.layer = node["layer"]
                        import_node.connections = node["connections"]
                        import_nodes.append(import_node)
                    import_connections = []
                    for connection in net["connections"]:
                        import_connection = Connection(connection["from"], connection["to"], connection["weight"], connection["conn_num"])
                        if connection["active"] == "False":
                            import_connection.active = False
                        import_connections.append(import_connection)
                    import_net.all_connections = deepcopy(import_connections)
                    import_net.all_nodes = deepcopy(import_nodes)
                    self.all_nets.append(import_net)

        else:
            for i in range(Population.size):
                self.all_nets.append(Brain(36, 8))

    def set_best_player(self):
        max_fit = 0
        max_fit2 = 0
        self.max_fit_index = 0
        self.max_fit_index2 = 0
        for i in range(0, self.size):
            if self.all_nets[i].fitness > max_fit:
                max_fit = self.all_nets[i].fitness
                self.max_fit_index = i

        for i in range(0, self.size):
            if self.all_nets[i].fitness > max_fit2 and self.all_nets[i].fitness != max_fit:
                max_fit2 = self.all_nets[i].fitness
                self.max_fit_index2 = i

        self.best_fitness = max_fit
        self.all_nets[self.max_fit_index].is_best = True
        self.all_nets[self.max_fit_index2].is_best = True

    def generate_offspring(self):
        new_nets = []
        self.gen += 1
        for i in range(Population.size):
            new_nets.append(Brain(36, 8))

        new_nets[0].all_nodes = deepcopy(self.all_nets[self.max_fit_index].all_nodes)
        new_nets[0].all_connections = deepcopy(self.all_nets[self.max_fit_index].all_connections)
        new_nets[0].node_num = self.all_nets[self.max_fit_index].node_num
        new_nets[0].conn_number = self.all_nets[self.max_fit_index].conn_number
        # new_nets[0].all_conn_str_list = self.all_nets[self.max_fit_index].all_conn_str_list
        new_nets[0].is_best = True

        # new_nets[1].all_nodes = deepcopy(self.all_nets[self.max_fit_index2].all_nodes)
        # new_nets[1].all_connections = deepcopy(self.all_nets[self.max_fit_index2].all_connections)
        # new_nets[1].node_num = self.all_nets[self.max_fit_index2].node_num
        # new_nets[1].conn_number = self.all_nets[self.max_fit_index2].conn_number
        # # new_nets[1].all_conn_str_list = self.all_nets[self.max_fit_index].all_conn_str_list
        # new_nets[1].is_best = True

        self.fitness_sum = 0
        for net in self.all_nets:
            self.fitness_sum += net.fitness

        for i in range(2, Population.size):
            parent = self.select_parent()
            new_nets[i].all_nodes = deepcopy(self.all_nets[parent].all_nodes)
            new_nets[i].all_connections = deepcopy(self.all_nets[parent].all_connections)
            new_nets[i].node_num = self.all_nets[parent].node_num
            new_nets[i].conn_number = self.all_nets[parent].conn_number
            # new_nets[i].all_conn_str_list = self.all_nets[parent].all_conn_str_list

        self.all_nets = deepcopy(new_nets)

        for i in range(2 % len(self.all_nets), len(self.all_nets)):
            self.all_nets[i].mutate()

    def select_parent(self):
        rand = uniform(0, self.fitness_sum)
        running_sum = 0
        for i in range(0, len(self.all_nets)):
            running_sum += self.all_nets[i].fitness
            if running_sum >= rand:
                return i

    def save_to_file(self):
        net_count = 0
        population_dict = {"gen": self.gen, "nets": []}
        for net in self.all_nets:
            output_layer = net.all_nodes[43].layer
            nodes = []
            for node in net.all_nodes:
                nodes.append({"layer": node.layer, "connections": node.connections})
            connections = []
            for connection in net.all_connections:
                connections.append({"from": connection.from_node, "to": connection.to_node, "weight": connection.weight, "conn_num": connection.conn_num, "active": str(connection.active)})
            final_net_dict = {"last_layer": output_layer,"node_num": net.node_num, "conn_number": net.conn_number, "nodes": nodes, "connections": connections}
            population_dict["nets"].append(final_net_dict)
            net_count += 1

        with open(self.filename, "w") as fout:
            json.dump(population_dict, fout)
