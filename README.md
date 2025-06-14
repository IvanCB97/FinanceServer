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
  --eimi-return 0.2 --eimi-risk 0.45
```

Command line options allow customization of genetic algorithm parameters such as
crossover and mutation rates, elitism, selection method, population size, and
number of generations. These values can also be specified in `gen.conf`, which
overrides the defaults and can be overridden again by command-line arguments.

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

An `[INFLUXDB]` section can configure the connection to the database:

```ini
[INFLUXDB]
url = http://localhost:8086
token = mytoken
org = myorg
bucket = finance
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

### Docker Compose with InfluxDB and Grafana

A `docker-compose.yml` file is provided to spin up an InfluxDB instance and Grafana dashboard. Start the services with:

```bash
docker-compose up -d
```

InfluxDB 2.7 exposes a web UI on `http://localhost:8086` using the credentials `admin/admin`. The instance is preconfigured with organization `myorg`, bucket `finance`, and token `mytoken`. Grafana runs on `http://localhost:3000` (default login `admin/admin`).

Add InfluxDB as a data source in Grafana using URL `http://influxdb:8086`, organization `myorg`, bucket `finance`, and the token `mytoken` to visualize optimizer statistics.

### Storing results in InfluxDB

The optimizer can push the best allocation and score for each generation to InfluxDB. Install dependencies and run the script:

```bash
pip install -r requirements.txt
python3 genetic_algorithm.py --config gen.conf \
  --vusa-return 0.1 --vusa-risk 0.3 \
  --cndx-return 0.15 --cndx-risk 0.4 \
  --aiq-return 0.12 --aiq-risk 0.25 \
  --vaneckdefense-return 0.05 --vaneckdefense-risk 0.5 \
  --eimi-return 0.2 --eimi-risk 0.45
```

The `gen.conf` file also includes an `[INFLUXDB]` section with the server `url`, access `token`, `org`, and `bucket`. Metrics will be written to the `finance` bucket automatically.
