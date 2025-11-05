# BFSK Reference Modem

Binary frequency shift keying (BFSK) modem used as the baseline transport in AMW. It converts bits into two audio tones and performs a simplistic detector on receive. The implementation is intentionally straightforward so that new plugins can iterate from a working example.

## Parameters

Parameters are defined in `schema.json` with defaults in `defaults.json`. Update those files if you add new tuning knobs.

## TODO

- Improve decoder robustness (windowing, matched filters, soft decisions)
- Add CRC verification hook and richer metrics
- Supply golden vector waveforms under `tests/data/golden_vectors`
