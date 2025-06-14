# FinanceServer Genetic Algorithm

This repository contains a simple genetic algorithm implementation to optimize
portfolio allocations based on provided return and risk parameters.

## Usage

The script `genetic_algorithm.py` accepts expected returns and risk values for
five assets and searches for an allocation that maximizes the following
objective function:

```
Opt = (2 * (1 - R) * G) / ((1 - R) + G)
```

where

```
R = \sum_{asset} (percentage * risk)
G = \sum_{asset} (percentage * expected_return)
```

### Running the optimizer

Example invocation:

```bash
python3 genetic_algorithm.py \
  --vusa-return 0.1 --vusa-risk 0.3 \
  --cndx-return 0.15 --cndx-risk 0.4 \
  --aiq-return 0.12 --aiq-risk 0.25 \
  --vaneckdefense-return 0.05 --vaneckdefense-risk 0.5 \
  --eimi-return 0.2 --eimi-risk 0.45 \
  --generations 200 --population 50
```

Command line options allow customization of genetic algorithm parameters such as
population size, number of generations, crossover and mutation rates, elitism,
and the selection method (roulette or tournament).

The script outputs the best allocation and its optimized score.


### Configuration file

Algorithm parameters can also be read from a configuration file named `gen.conf`.
The file should contain a `[GA]` section as shown below:

```ini
[GA]
population = 100
generations = 500
crossover_rate = 0.8
mutation_rate = 0.05
selection = tournament
elitism = 2
```

Run the optimizer specifying the config file:

```bash
python3 genetic_algorithm.py --config gen.conf \
  --vusa-return 0.1 --vusa-risk 0.3 \
  --cndx-return 0.15 --cndx-risk 0.4 \
  --aiq-return 0.12 --aiq-risk 0.25 \
  --vaneckdefense-return 0.05 --vaneckdefense-risk 0.5 \
  --eimi-return 0.2 --eimi-risk 0.45
```

Command-line arguments override values from the configuration file.
