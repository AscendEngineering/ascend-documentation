# Ascend Engineering Documentation

Source for the Ascend Engineering documentation site, published at
**<https://docs.ascendengineer.com>**.

Built with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) from
the Markdown in [`docs/`](docs/). Pushes to `main` auto-deploy via GitHub Pages.

## Products

- **[Ascend 8tof](docs/ascend-8tof/index.md)** — 360° time-of-flight
  obstacle-sensing system (up to 8× VL53L8CX sensors on an STM32H5 carrier board):
  hardware overview, power, the UART output protocol, firmware variants, and
  integration guides (with a VOXL2 worked example).

More products will be added as sibling sections under `docs/`.

## Local preview

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
mkdocs serve        # http://127.0.0.1:8000
```

## Contributing

Each product is a folder under `docs/` with its own `index.md`; add a matching
section to the `nav:` in `mkdocs.yml`. Keep customer-facing content only —
integration, usage, interfaces, and specs — not internal build/manufacturing
detail.
