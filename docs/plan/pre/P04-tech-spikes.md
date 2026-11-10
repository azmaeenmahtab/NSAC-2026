# P04 Three tech spikes (throwaway, one person each)

Depends: none. Priority: P0. Window: PRE. Code lives in `spikes/<name>/`, is excluded from the submission build, and exists only to remove risk. Record every result in `docs/SPIKE_RESULTS.md` (versions used, the working snippet, pitfalls, links to the docs pages read).

## Spike A: deck.gl H3 hex map
- Goal: MapLibre base map plus deck.gl `H3HexagonLayer` rendering 30,000 fake hexes (random Bangladesh r7 cells) with color from an Inferno scale, extrusion on and off, hover tooltip, click handler.
- Read first: current deck.gl docs for `H3HexagonLayer` and the react-map-gl MapLibre + deck.gl integration (`MapboxOverlay` or `DeckGL` pattern); VERIFY package names and versions that work together in Next.js App Router (client component, dynamic import with `ssr: false` if needed).
- Measure: frames per second during pan and zoom on a laptop; memory; first render time. Find a free basemap style that needs no key; note its attribution and terms.

## Spike B: DuckDB over Parquet
- Goal: generate a 2 million row fake `monthly_cell` Parquet (UINT64 h3 column), query it from Python with DuckDB: group by h3 for a date range and bbox, percentiles, and return hex strings. Measure query time cold and warm.
- Check: how UINT64 behaves from pandas to Parquet to DuckDB to JSON; the Python-side conversion `format(int(x), "x")`; whether the DuckDB `h3` community extension is needed (the plan avoids it by computing H3 in Python).

## Spike C: LLM function calling
- Goal: a 50-line script with the chosen provider SDK: one stub tool (`get_value(area)`), the model must call it and answer using only the returned number; also a replay stub without network.
- Read first: the current official function-calling docs for the provider; VERIFY the model id to use and the free-tier limits; check the SDK's thread-safety and timeout options.

## Tasks
- [ ] Spike A done with fps numbers and the working snippet
- [ ] Spike B done with timings and the UINT64 handling decision
- [ ] Spike C done with the exact SDK call shape and model id
- [ ] `docs/SPIKE_RESULTS.md` written; update ARCHITECTURE.md section 1 if versions or libraries changed (log in the Deviation Log)
- [ ] Master plan row P04 set to `[x]`
