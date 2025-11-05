# BFSK Reference Modem

Binary frequency shift keying (BFSK) modem used as the baseline transport in AMW. It converts bits into two audio tones and performs a simplistic detector on receive. The implementation now ships with optional forward error correction to help sustain links under degraded acoustic conditions.

## Parameters

Parameters are defined in `schema.json` with defaults in `defaults.json`. Update those files if you add new tuning knobs.

- `sample_rate`, `freq0`, `freq1`, `bitrate`, `amplitude`, `preamble_bits` – unchanged modulation controls.
- `fec.scheme` – choose from `none`, `repetition`, or `hamming74`.
- `fec.repetition_factor` – odd repeat count when using the repetition code (default `3`).
- `fec.interleave_depth` – columnar interleaver depth applied after FEC encoding (default `1` / disabled).

When a FEC scheme other than `none` is selected, the modem prepends a 32-bit payload length header before encoding and reports correction statistics in the decode metrics.

## TODO

- Improve decoder robustness (windowing, matched filters, soft decisions)
- Add CRC verification hook and richer metrics
- Supply golden vector waveforms under `tests/data/golden_vectors`
