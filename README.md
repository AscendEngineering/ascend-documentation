# Ascend Engineering Documentation

Source for the Ascend Engineering documentation site, published at
**<https://docs.ascendengineer.com>**.

Built with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) from
the Markdown in [`docs/`](docs/). Pushes to `main` auto-deploy via GitHub Pages.

## Products

- **[Ascend 8tof](docs/ascend-8tof/index.md)** — 360° time-of-flight
  obstacle-sensing system (up to 8× VL53L8CX sensors on an STM32H5 carrier board):
  hardware overview, power, the UART output protocol, firmware variants, and
  integration guides (with a VOXL2 worked example), a versioned firmware/installer
  download, and complete-assembly and electronics STEP files.

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

## Versioned downloads

The 8TOF [installer guide](docs/ascend-8tof/08-install-firmware.md),
[release notes](docs/ascend-8tof/09-firmware-release-notes.md), and
[case files](docs/ascend-8tof/10-case-files.md) are linked from the product nav.
Firmware ZIPs and CAD exports live under `docs/ascend-8tof/downloads/` so MkDocs
copies them to the deployed site. Keep the ZIP checksum paired with its exact
version. The reviewable installer source is in `tools/8tof-installer/` and must
match the files inside the downloadable ZIP.

The 10 Hz / 10 ms image is a bench candidate with hardware validation pending.
Do not remove that status until the exact image has been checked on hardware.
Per-board flash backups and local installation logs are not public assets.
