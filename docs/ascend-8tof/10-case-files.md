# Case and assembly files

Download the supplied v2 assembly files for enclosure fit checks, mounting,
and CAD reference. Both exports are preserved as supplied; the documentation
update does not change their geometry.

| Download | Format | Size | Intended use |
|----------|--------|------|--------------|
| [Complete assembly — STEP](downloads/case/tof8_v2_COMPLETE_assembly.step) | STEP / AP214 | 7.34 MiB | CAD import, assembly inspection, and selecting parts for mechanical work |
| [Assembly mesh — STL](downloads/case/oa_pcb_tof8_v2_assembly.stl) | Binary STL | 4.06 MiB | Mesh inspection and fit-reference workflows |
| [File checksums](downloads/case/SHA256SUMS) | SHA-256 | — | Confirm downloads match the supplied exports |

![Assembled v2 case with the forward-facing A](assets/v2-assembled.jpg){ width="420" }

The tip of the **A** on the lid faces the vehicle nose, aligned with **CH7/J8**.
Use the [hardware overview](01-hardware.md#mechanical-mounting) for connector
orientation and the [bring-up guide](06-bringup-setup.md) to verify it with a
real target.

## Using the files

- **STEP:** the file declares millimetres and contains multiple solids. Import
  it as an assembly/reference model and select the enclosure components you
  need. It is not a single flattened case part.
- **STL:** the export contains 85,168 triangles. STL does not encode units;
  check the import scale against the STEP model. Its bounding box is
  approximately **36.194 × 36.194 × 11.875 model units** (millimetres if imported
  at the intended millimetre scale).
- These are **assembly exports**. Inspect and separate the required enclosure
  pieces before preparing a print. The entire STL has not been validated as
  one printable part, and no print orientation, supports, or material settings
  are specified by this download.

The STEP header/terminator, STL record count, finite mesh coordinates, and file
checksums were checked. Those checks establish file integrity, not mechanical
fit, mesh watertightness, or print readiness.
