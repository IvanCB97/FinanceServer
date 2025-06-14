import argparse
import configparser
import os
import random
from dataclasses import dataclass
from typing import List

@dataclass
class Asset:
    name: str
    expected_return: float
    risk: float

class GeneticAlgorithm:
    def __init__(self, assets: List[Asset], population_size: int = 50,
                 generations: int = 200, crossover_rate: float = 0.7,
                 mutation_rate: float = 0.1, elitism: int = 2,
                 selection_type: str = "roulette"):
        self.assets = assets
        self.population_size = population_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elitism = elitism
        self.selection_type = selection_type
        self.chromosome_length = len(assets)

    def _random_chromosome(self) -> List[float]:
        weights = [random.random() for _ in range(self.chromosome_length)]
        total = sum(weights)
        return [w / total for w in weights]

    def _fitness(self, chromosome: List[float]) -> float:
        R = sum(w * a.risk for w, a in zip(chromosome, self.assets))
        G = sum(w * a.expected_return for w, a in zip(chromosome, self.assets))
        if (1 - R + G) == 0:
            return float('-inf')  # avoid division by zero
        Opt = (2 * (1 - R) * G) / ((1 - R) + G)
        return Opt

    def _mutate(self, chromosome: List[float]):
        idx = random.randrange(self.chromosome_length)
        change = random.uniform(-0.1, 0.1)
        chromosome[idx] = max(0.0, min(1.0, chromosome[idx] + change))
        total = sum(chromosome)
        if total == 0:
            chromosome[idx] = 1.0
            total = 1.0
        for i in range(self.chromosome_length):
            chromosome[i] /= total

    def _crossover(self, parent1: List[float], parent2: List[float]) -> List[float]:
        if random.random() > self.crossover_rate:
            child = parent1[:]
        else:
            alpha = random.random()
            child = [alpha * g1 + (1 - alpha) * g2 for g1, g2 in zip(parent1, parent2)]
        total = sum(child)
        child = [c / total for c in child]
        return child

    def _select_parent(self, graded: List[List[float]]) -> List[float]:
        if self.selection_type == "tournament":
            competitors = random.sample(graded, k=min(3, len(graded)))
            return max(competitors, key=self._fitness)
        # roulette selection
        fitnesses = [self._fitness(ch) for ch in graded]
        min_f = min(fitnesses)
        weights = [f - min_f + 1e-6 for f in fitnesses]
        return random.choices(graded, weights=weights, k=1)[0]

    def run(self):
        population = [self._random_chromosome() for _ in range(self.population_size)]
        for _ in range(self.generations):
            graded = sorted(population, key=self._fitness, reverse=True)
            next_population = graded[:self.elitism]
            while len(next_population) < self.population_size:
                parent1 = self._select_parent(graded)
                parent2 = self._select_parent(graded)
                child = self._crossover(parent1, parent2)
                if random.random() < self.mutation_rate:
                    self._mutate(child)
                next_population.append(child)
            population = next_population
        best = max(population, key=self._fitness)
        return best, self._fitness(best)

def parse_args():
    parser = argparse.ArgumentParser(description="Genetic optimizer for portfolio allocation")
    for asset in ["vusa", "cndx", "aiq", "vaneckdefense", "eimi"]:
        parser.add_argument(f"--{asset}-return", type=float, required=True)
        parser.add_argument(f"--{asset}-risk", type=float, required=True)
    parser.add_argument("--config", default="gen.conf", help="path to configuration file")
    parser.add_argument("--population", type=int, default=50)
    parser.add_argument("--generations", type=int, default=200)
    parser.add_argument("--crossover", type=float, default=0.7)
    parser.add_argument("--mutation", type=float, default=0.1)
    parser.add_argument("--elitism", type=int, default=2)
    parser.add_argument("--selection", choices=["roulette", "tournament"], default="roulette")
    return parser.parse_args()


def main():
    args = parse_args()
    # Load configuration file if present
    config = configparser.ConfigParser()
    if os.path.exists(args.config):
        config.read(args.config)
        if 'GA' in config:
            section = config['GA']
            args.population = int(section.get('population', args.population))
            args.generations = int(section.get('generations', args.generations))
            args.crossover = float(section.get('crossover_rate', args.crossover))
            args.mutation = float(section.get('mutation_rate', args.mutation))
            args.selection = section.get('selection', args.selection)
            args.elitism = int(section.get('elitism', args.elitism))
    assets = [
        Asset("VUSA", args.vusa_return, args.vusa_risk),
        Asset("CNDX", args.cndx_return, args.cndx_risk),
        Asset("AIQ", args.aiq_return, args.aiq_risk),
        Asset("VanEckDefense", args.vaneckdefense_return, args.vaneckdefense_risk),
        Asset("EIMI", args.eimi_return, args.eimi_risk),
    ]

    ga = GeneticAlgorithm(
        assets,
        population_size=args.population,
        generations=args.generations,
        crossover_rate=args.crossover,
        mutation_rate=args.mutation,
        elitism=args.elitism,
        selection_type=args.selection,
    )

    best, score = ga.run()
    print("Best allocation:")
    for asset, weight in zip(assets, best):
        print(f"  {asset.name}: {weight:.4f}")
    print(f"Optimized score: {score:.6f}")

if __name__ == "__main__":
    main()

