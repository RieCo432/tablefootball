class Population:

    all_nets = []
    generation = 0
    size = 4

    def __init__(self):
        for i in range(Population.size):
            Population.all_nets.append(0)
