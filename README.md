# siteping

Lightweight uptime monitor that checks a list of URLs on a schedule and sends alerts via email or webhook.

---

## Installation

```bash
pip install siteping
```

Or clone and install locally:

```bash
git clone https://github.com/youruser/siteping.git && cd siteping && pip install .
```

---

## Usage

Create a `config.yml` file:

```yaml
interval: 60  # seconds between checks

urls:
  - https://example.com
  - https://api.myservice.io/health

alerts:
  email:
    to: you@example.com
    smtp_host: smtp.gmail.com
    smtp_user: you@gmail.com
    smtp_pass: secret
  webhook:
    url: https://hooks.slack.com/services/your/webhook/url
```

Then run:

```bash
siteping --config config.yml
```

siteping will poll each URL at the defined interval and fire an alert if a site returns a non-2xx status code or times out.

### CLI Options

| Flag | Description |
|------|-------------|
| `--config` | Path to config file (default: `config.yml`) |
| `--timeout` | Request timeout in seconds (default: `10`) |
| `--verbose` | Print check results to stdout |

---

## License

MIT © 2024 Your Name