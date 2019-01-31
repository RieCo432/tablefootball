from random import uniform, randint, random
from math import e
import json

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


class Brain:

    mutate_change_weight_prob = 0.8
    mutate_new_rand_weight_prob = 0.1
    mutate_new_connection_prob = 0.05
    mutate_new_node_prob = 0.02

    def __init__(self, input_nodes, output_nodes):
        self.node_num = -1
        self.conn_number = 0
        self.input_nodes = input_nodes
        self.output_nodes = output_nodes
        self.all_nodes = []
        self.all_connections = []

        for i in range(self.input_nodes):  # Create input nodes (own player's sticks, opponent's sticks, ball, ball_radius, player_thickness, player_width, player_height, player_max_hit_angle)
            self.add_node(autolayer=False)
            self.all_nodes[self.node_num].layer = 0

        self.add_node(autolayer=False)  # Bias Node
        self.all_nodes[self.node_num].layer = 0
        self.all_nodes[self.node_num].output_value = 1

        for i in range(output_nodes):  # Create output nodes
            self.add_node(autolayer=False)
            self.all_nodes[self.node_num].layer = 1

        for i in range(37):
            self.new_rand_connection()

    def put_input(self, input_data):
        for node in self.all_nodes:
            node.input_sum = 0.0
        for i in range(len(input_data)):
            self.all_nodes[i].output_value = input_data[i]

    def get_outputs(self):
        output_list = []
        for output_node in self.all_nodes[self.input_nodes + 1: self.input_nodes + 1 + self.output_nodes]:
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

    def add_node(self, autolayer=True, splitnode=False, from_layer=0, to_layer=0):
        new_node = Node()
        flex_from_layer = from_layer
        if autolayer:
            if splitnode:
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
        self.conn_number += 1


    def feed_forward(self):

        output_layer = self.all_nodes[self.input_nodes + 2].layer

        for node in self.all_nodes:

            if node.layer is not 0 and node.layer is not output_layer:  # Don't call activate on input and output nodes
                node.activate()

            if node.layer is not output_layer:  # Do not feedforward output nodes
                for conn_num in node.connections:
                    connection = self.all_connections[conn_num]
                    self.all_nodes[connection.to_node].input_sum += node.output_value * connection.weight

        for node in self.all_nodes[self.input_nodes + 1:self.input_nodes + 1 + self.output_nodes]:  # Finally activate output nodes
            node.activate()

    def mutate(self):

        if random() <= Brain.mutate_new_connection_prob:
            self.new_rand_connection()

        for connection in self.all_connections:
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
                self.add_node(splitnode=True, from_layer=self.all_nodes[from_node].layer, to_layer=self.all_nodes[to_node].layer)
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

    def __init__(self):
        self.all_nets = []
        self.gen = 1
        for i in range(Population.size):
            self.all_nets.append(Brain(36, 8))

    def save_net_to_file(self):
        net_count = 0
        all_nets_dict = {"gen": self.gen, "nets": []}
        for net in self.all_nets:
            output_layer = net.all_nodes[43].layer
            nodes = []
            for node in net.all_nodes:
                nodes.append({"layer": node.layer, "connections": node.connections})
            connections = []
            for connection in net.all_connections:
                connections.append({"from": connection.from_node, "to": connection.to_node, "weight": connection.weight, "conn_num": connection.conn_num})
            final_net_dict = {"last_layer": output_layer, "nodes": nodes, "connections": connections}
            all_nets_dict["nets"].append(final_net_dict)
            net_count += 1

        with open("neuralnet.json", "w") as fout:
            json.dump(all_nets_dict, fout)
