# About & further reading

## What Telemachus is

A small, open, vendor-agnostic data format for high-frequency mobility
and telematics. It does **one thing well**: define how raw device
output (D0) and its enriched downstream layers (D1, D2) are encoded,
so that pipelines, datasets and tooling can interoperate.

It does **not** define:

- Which algorithm computes D1/D2 columns
- Which metrics constitute "good driving"
- Which business decisions to make from the data

These belong to the consumer.

## What Telemachus is *not*

- A scoring product
- A commercial dashboard
- A method library

For applied science (papers, methods, benchmarks), see the **research
companion site**: [research.roadsimulator3.fr](https://research.roadsimulator3.fr).

## Typology of related projects

| Project | Role | Repo / site |
|---------|------|-------------|
| **Telemachus** | Open data format & SDK & CLI | this site / [GitHub](https://github.com/telemachus3/telemachus) |
| **RoadSimulator3** | Synthetic D0 generator (simulation) | [github.com/SebE585/RoadSimulator3](https://github.com/SebE585/RoadSimulator3) |
| **Research vitrine** | Papers, methods, benchmarks | [research.roadsimulator3.fr](https://research.roadsimulator3.fr) |

## Citation

```
S. Edet (2025). Telemachus Specification.
Zenodo. https://doi.org/10.5281/zenodo.17228092
```

## License

MIT — applies to the spec, the JSON Schemas, the SDK, the CLI, the
adapter examples and the documentation. Datasets shipped under
`datasets/` carry their own licenses (CC-BY, CC0, etc.) — see each
dataset's `manifest.yaml`.

## Contributing

Contributions of all sizes are welcome:

- **Found a bug in the spec?** Open an issue.
- **Want to add an adapter for vendor X?** Send a PR under `python-cli/adapters/`.
- **Want to propose a new RFC?** See [RFCs → How to propose](rfcs.md#how-to-propose-an-rfc).
- **Want to fix a doc typo?** Use the pencil icon on the top right of any page (it deep-links to the source on GitHub).
