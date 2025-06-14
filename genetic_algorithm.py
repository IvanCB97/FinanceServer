import argparse
import configparser
import os
import random
from dataclasses import dataclass
from typing import List, Optional

from influxdb_client import InfluxDBClient, Point

@dataclass
class Asset:
    name: str
    expected_return: float
    risk: float

class GeneticAlgorithm:
    def __init__(self, assets: List[Asset], population_size: int = 50,
                 generations: int = 200, crossover_rate: float = 0.7,
                 mutation_rate: float = 0.1, elitism: int = 2,
                 selection_type: str = "roulette",
                 influx_client: Optional[InfluxDBClient] = None,
                 bucket: str = "",
                 org: str = ""):
        self.assets = assets
        self.population_size = population_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elitism = elitism
        self.selection_type = selection_type
        self.influx_client = influx_client
        self.bucket = bucket
        self.org = org
        self.write_api = influx_client.write_api() if influx_client else None
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

    def _log_generation(self, generation: int, best: List[float], score: float):
        if not self.write_api:
            return
        point = Point("genetic_algorithm").tag("generation", generation)
        for asset, weight in zip(self.assets, best):
            point.field(asset.name, float(weight))
        point.field("score", float(score))
        try:
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
        except Exception:
            pass
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
        for gen in range(self.generations):
            graded = sorted(population, key=self._fitness, reverse=True)
            best = graded[0]
            self._log_generation(gen, best, self._fitness(best))
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
        self._log_generation(self.generations, best, self._fitness(best))
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
    parser.add_argument("--influxdb-url", default="http://localhost:8086")
    parser.add_argument("--influxdb-token", default="mytoken")
    parser.add_argument("--influxdb-org", default="myorg")
    parser.add_argument("--influxdb-bucket", default="finance")
    return parser.parse_args()


def main():
    args = parse_args()
    # defaults for GA parameters
    population = args.population
    generations = args.generations
    crossover = args.crossover
    mutation = args.mutation
    elitism = args.elitism
    selection = args.selection
    # Load configuration file if present
    config = configparser.ConfigParser()
    if os.path.exists(args.config):
        config.read(args.config)
        if 'GA' in config:
            section = config['GA']
            population = int(section.get('population', population))
            generations = int(section.get('generations', generations))
            crossover = float(section.get('crossover_rate', crossover))
            mutation = float(section.get('mutation_rate', mutation))
            selection = section.get('selection', selection)
            elitism = int(section.get('elitism', elitism))
        if 'INFLUXDB' in config:
            section = config['INFLUXDB']
            args.influxdb_url = section.get('url', args.influxdb_url)
            args.influxdb_token = section.get('token', args.influxdb_token)
            args.influxdb_org = section.get('org', args.influxdb_org)
            args.influxdb_bucket = section.get('bucket', args.influxdb_bucket)
    assets = [
        Asset("VUSA", args.vusa_return, args.vusa_risk),
        Asset("CNDX", args.cndx_return, args.cndx_risk),
        Asset("AIQ", args.aiq_return, args.aiq_risk),
        Asset("VanEckDefense", args.vaneckdefense_return, args.vaneckdefense_risk),
        Asset("EIMI", args.eimi_return, args.eimi_risk),
    ]

    influx = None
    try:
        influx = InfluxDBClient(
            url=args.influxdb_url,
            token=args.influxdb_token,
            org=args.influxdb_org,
        )
    except Exception:
        influx = None

    ga = GeneticAlgorithm(
        assets,
        population_size=population,
        generations=generations,
        crossover_rate=crossover,
        mutation_rate=mutation,
        elitism=elitism,
        selection_type=selection,
        influx_client=influx,
        bucket=args.influxdb_bucket,
        org=args.influxdb_org,
    )

    best, score = ga.run()
    print("Best allocation:")
    for asset, weight in zip(assets, best):
        print(f"  {asset.name}: {weight:.4f}")
    print(f"Optimized score: {score:.6f}")

if __name__ == "__main__":
    main()

