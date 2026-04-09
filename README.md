# pipewatch

A lightweight CLI for monitoring and alerting on ETL pipeline health across multiple sources.

---

## Installation

```bash
pip install pipewatch
```

Or install from source:

```bash
git clone https://github.com/youruser/pipewatch.git
cd pipewatch && pip install -e .
```

---

## Usage

```bash
# Check the health of all configured pipelines
pipewatch check

# Monitor a specific source with alerts enabled
pipewatch watch --source my_pipeline --alert email

# View status summary
pipewatch status --format table
```

Configure your pipelines in `pipewatch.yaml`:

```yaml
pipelines:
  - name: my_pipeline
    source: postgres
    schedule: "0 * * * *"
    alert_on: [failure, delay]
```

Then run:

```bash
pipewatch run --config pipewatch.yaml
```

---

## Features

- Monitor ETL pipelines across multiple data sources
- Configurable alerting on failure, delay, or data anomalies
- Simple YAML-based configuration
- Lightweight with minimal dependencies

---

## License

This project is licensed under the [MIT License](LICENSE).