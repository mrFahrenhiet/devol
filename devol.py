from datetime import datetime
import numpy as np
from keras.models import Sequential
from keras.utils import np_utils
from keras.datasets import mnist, cifar10
from genome_handler import GenomeHandler
from keras.callbacks import EarlyStopping
import random as rand
import math
import csv

class DEvol:

    def __init__(self, genome_handler, data_path=""):
        self.genome_handler = genome_handler
        self.datafile = data_path or datetime.now().ctime() + '.csv'
        print "Genome encoding and accuracy data stored at", self.datafile

    # Create a population and evolve
    def run(self, dataset, num_generations, pop_size, epochs):
        print "Initial Population..."
        (self.x_train, self.y_train), (self.x_test, self.y_test) = dataset

        # Generate initial random population
        members = [self.genome_handler.generate() for _ in range(pop_size)]
        fit = [self.evaluate(member, epochs)[1] for member in members]
        pop = Population(members, fit)
        fit = np.array(fit)
        print "max:", max(fit), "\taverage:", np.mean(fit), "\tstd:", np.std(fit)

        # Evolve over generations
        for gen in range(1, num_generations):
            print "Population #" + str(gen + 1)
            members = []
            for i in range(int(pop_size*0.95)): # Crossover
                members.append(self.crossover(pop.select(), pop.select()))
            members += pop.getBest(pop_size - int(pop_size*0.95))
            for i in range(len(members)): # Mutation
                members[i] = self.mutate(members[i], gen)
            fit = [self.evaluate(member, epochs)[1] for member in members]
            pop = Population(members, fit)
            fit = np.array(fit)
            print "max:", max(fit), "\taverage:", np.mean(fit), "\tstd:", np.std(fit)

    # Returns the accuracy for a model as 1 / loss
    def evaluate(self, genome, epochs):
        model, datagen = self.genome_handler.decode(genome)
        datagen.fit(self.x_train)
        loss, accuracy = None, None
        # model.fit_generator(datagen.flow(self.x_train, self.y_train, batch_size=200),
        #     steps_per_epoch=300,
        #     validation_data=(self.x_test, self.y_test),
        #     epochs=epochs, 
        #     verbose=1,
        #     callbacks=[EarlyStopping(monitor='val_loss', patience=2, verbose=1)])
        model.fit(self.x_train, self.y_train, validation_data=(self.x_test, self.y_test),
            epochs=epochs,
            verbose=0,
            callbacks=[EarlyStopping(monitor='val_loss', patience=1, verbose=0)])
        loss, accuracy = model.evaluate(self.x_test, self.y_test, verbose=0)

        # Record the stats
        with open(self.datafile, 'a') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            row = list(genome) + [loss, accuracy]
            writer.writerow(row)  

        return loss, accuracy
    
    def crossover(self, genome1, genome2):
        crossIndexA = rand.randint(0, len(genome1))
        child = genome1[:crossIndexA] + genome2[crossIndexA:]
        return child
    
    def mutate(self, genome, generation):
        num_mutations = max(3, generation / 2)
        return self.genome_handler.mutate(genome, num_mutations)

class Population:

    def __len__(self):
        return len(self.members)

    def __init__(self, members, fitnesses):
        self.members = members
        fitnesses -= min(fitnesses)
        fitnesses /= max(fitnesses)
        self.scores = map(self.score, fitnesses)
        self.s_fit = sum(self.scores)

    def score(self, fitness):
        return (fitness * 100)**4

    def getBest(self, n):
        combined = [(self.members[i], self.scores[i]) \
                for i in range(len(self.members))]
        sorted(combined, key=(lambda x: x[1]), reverse=True)
        return map(lambda x: x[0], combined[:n])

    def select(self):
        dart = rand.uniform(0, self.s_fit)
        sum_fits = 0
        for i in range(len(self.members)):
            sum_fits += self.scores[i]
            if sum_fits > dart:
                return self.members[i]