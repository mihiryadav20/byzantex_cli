# BYZANTEX

⚡ Regression Triage in 30 Seconds

Analyzes simulation log files, parses failures, and classifies them by category.

---

## Option A: Docker (no Python needed)

```bash
# Build
docker build -t byzantex .

# Run with a log file
docker run -v /path/to/your/logs:/logs byzantex analyze /logs/sim.log
```

### Docker Hub (if published)

```bash
docker pull yourusername/byzantex
docker run -v /path/to/your/logs:/logs yourusername/byzantex analyze /logs/sim.log
```

---

## Option B: pip install from GitHub (Python 3.9+)

```bash
pip install git+https://github.com/yourusername/byzantex.git

byzantex analyze sim.log
```

---

## Usage

```
byzantex                        # interactive log selector
byzantex analyze sim.log        # analyze a specific log file
byzantex version                # show version
byzantex --help
```
