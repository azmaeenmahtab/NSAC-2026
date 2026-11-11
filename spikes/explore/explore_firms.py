"""
Exploration script for FIRMS MODIS and VIIRS datasets for PyroScope (Chunk P02).
Answers questions 1 to 8 in docs/plan/pre/P02-data-exploration.md.
"""
import os
import time

import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")
BBOX = (88.0, 20.5, 92.8, 26.7)  # min_lon, min_lat, max_lon, max_lat
CHT_BBOX = (91.6, 21.2, 92.7, 23.8)

def load_data():
    print("Loading MODIS Archive...")
    m_arch = pd.read_csv(os.path.join(DATA_DIR, "fire_archive_M-C61_842592.csv"))
    print(f"MODIS Archive rows: {len(m_arch):,}")
    
    print("Loading MODIS NRT...")
    m_nrt = pd.read_csv(os.path.join(DATA_DIR, "fire_nrt_M-C61_842592.csv"))
    print(f"MODIS NRT rows: {len(m_nrt):,}")
    
    print("Loading VIIRS Archive...")
    v_arch = pd.read_csv(os.path.join(DATA_DIR, "fire_archive_SV-C2_842593.csv"), low_memory=False)
    print(f"VIIRS Archive rows: {len(v_arch):,}")
    
    print("Loading VIIRS NRT...")
    v_nrt = pd.read_csv(os.path.join(DATA_DIR, "fire_nrt_SV-C2_842593.csv"), low_memory=False)
    print(f"VIIRS NRT rows: {len(v_nrt):,}")
    
    return m_arch, m_nrt, v_arch, v_nrt

def parse_timestamps(df):
    # acq_time format: integer or string HHMM e.g. 52 -> 00:52, 1422 -> 14:22
    time_str = df['acq_time'].astype(str).str.zfill(4)
    dt_str = df['acq_date'].astype(str) + ' ' + time_str.str[:2] + ':' + time_str.str[2:] + ':00'
    df['acq_ts'] = pd.to_datetime(dt_str, utc=True)
    df['year'] = df['acq_ts'].dt.year
    df['month'] = df['acq_ts'].dt.month
    df['year_month'] = df['acq_ts'].dt.to_period('M')
    return df

def run_analysis():
    m_arch, m_nrt, v_arch, v_nrt = load_data()
    
    print("\nParsing timestamps...")
    m_arch = parse_timestamps(m_arch)
    m_nrt = parse_timestamps(m_nrt)
    v_arch = parse_timestamps(v_arch)
    v_nrt = parse_timestamps(v_nrt)
    
    # Check duplicates between archive and NRT
    m_all = pd.concat([m_arch, m_nrt], ignore_index=True)
    v_all = pd.concat([v_arch, v_nrt], ignore_index=True)
    
    # ----------------------------------------------------
    # Q3: Column names, types, acq_time, duplicates, out-of-bounds
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("QUESTION 3: Columns, Types, acq_time, Duplicates, Bounds")
    print("="*50)
    print("MODIS columns:", list(m_all.columns))
    print("VIIRS columns:", list(v_all.columns))
    print("MODIS types:\n", m_all.dtypes)
    print("VIIRS types:\n", v_all.dtypes)
    
    # acq_time checks
    print("MODIS raw acq_time samples:", m_arch['acq_time'].head().tolist())
    print("VIIRS raw acq_time samples:", v_arch['acq_time'].head().tolist())
    m_time_lens = m_arch['acq_time'].astype(str).str.len().value_counts().to_dict()
    v_time_lens = v_arch['acq_time'].astype(str).str.len().value_counts().to_dict()
    print("MODIS raw acq_time string length distribution:", m_time_lens)
    print("VIIRS raw acq_time string length distribution:", v_time_lens)
    
    # Bounds check
    min_lon, min_lat, max_lon, max_lat = BBOX
    m_out = m_all[~((m_all['longitude'] >= min_lon) & (m_all['longitude'] <= max_lon) &
                    (m_all['latitude'] >= min_lat) & (m_all['latitude'] <= max_lat))]
    v_out = v_all[~((v_all['longitude'] >= min_lon) & (v_all['longitude'] <= max_lon) &
                    (v_all['latitude'] >= min_lat) & (v_all['latitude'] <= max_lat))]
    print(f"MODIS rows outside bbox: {len(m_out)}")
    print(f"VIIRS rows outside bbox: {len(v_out)}")
    
    # Duplicate checks
    m_dups = m_all.duplicated(subset=['latitude', 'longitude', 'acq_ts', 'satellite']).sum()
    v_dups = v_all.duplicated(subset=['latitude', 'longitude', 'acq_ts', 'satellite']).sum()
    print(f"MODIS duplicates on (lat, lon, acq_ts, satellite): {m_dups}")
    print(f"VIIRS duplicates on (lat, lon, acq_ts, satellite): {v_dups}")
    
    # Overlap between archive and NRT
    m_arch_nrt_overlap = pd.merge(m_arch, m_nrt, on=['latitude', 'longitude', 'acq_ts', 'satellite'])
    v_arch_nrt_overlap = pd.merge(v_arch, v_nrt, on=['latitude', 'longitude', 'acq_ts', 'satellite'])
    print(f"MODIS Archive & NRT exact duplicate detections: {len(m_arch_nrt_overlap)}")
    print(f"VIIRS Archive & NRT exact duplicate detections: {len(v_arch_nrt_overlap)}")
    
    # Dedup for further analysis
    m_all = m_all.drop_duplicates(subset=['latitude', 'longitude', 'acq_ts', 'satellite'])
    v_all = v_all.drop_duplicates(subset=['latitude', 'longitude', 'acq_ts', 'satellite'])
    
    # ----------------------------------------------------
    # Q2: Confidence field & Filter
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("QUESTION 2: Confidence and Type Filter")
    print("="*50)
    print("MODIS confidence min/max/mean:", m_all['confidence'].min(), m_all['confidence'].max(), m_all['confidence'].mean())
    m_conf_bins = pd.cut(m_all['confidence'], bins=[-1, 29, 79, 100], labels=['low (<30)', 'nominal (30-79)', 'high (80-100)'])
    print("MODIS confidence classes:\n", m_conf_bins.value_counts(dropna=False))
    print("MODIS confidence percentage:\n", m_conf_bins.value_counts(normalize=True, dropna=False) * 100)
    
    print("\nVIIRS confidence value counts:\n", v_all['confidence'].value_counts(dropna=False))
    print("VIIRS confidence percentage:\n", v_all['confidence'].value_counts(normalize=True, dropna=False) * 100)
    
    # Check type column
    print("MODIS type value counts:\n", m_all['type'].value_counts(dropna=False))
    print("VIIRS type value counts:\n", v_all['type'].value_counts(dropna=False))
    
    # Filter rules in PRODUCT_BRIEF section 5:
    # MODIS: confidence >= 30, and type == 0 (where type is not null)
    m_filtered = m_all[(m_all['confidence'] >= 30) & (m_all['type'].isna() | (m_all['type'] == 0))].copy()
    # VIIRS: confidence in ['n', 'h'], and type == 0 (where type is not null)
    v_filtered = v_all[v_all['confidence'].isin(['n', 'h']) & (v_all['type'].isna() | (v_all['type'] == 0))].copy()
    
    print(f"\nMODIS before filter: {len(m_all):,}, after filter: {len(m_filtered):,} (dropped: {len(m_all) - len(m_filtered):,}, {(len(m_all) - len(m_filtered))/len(m_all)*100:.2f}%)")
    print(f"VIIRS before filter: {len(v_all):,}, after filter: {len(v_filtered):,} (dropped: {len(v_all) - len(v_filtered):,}, {(len(v_all) - len(v_filtered))/len(v_all)*100:.2f}%)")
    
    # What if report's >80% filter was used?
    m_rep_filter = m_all[m_all['confidence'] > 80]
    print(f"MODIS with report's >80% filter: {len(m_rep_filter):,} (drops {(len(m_all)-len(m_rep_filter))/len(m_all)*100:.2f}%)")
    
    # ----------------------------------------------------
    # Q1: Row counts per sensor and per year, ratio VIIRS/MODIS
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("QUESTION 1: Annual row counts and VIIRS/MODIS ratio")
    print("="*50)
    m_year_raw = m_all.groupby('year').size()
    v_year_raw = v_all.groupby('year').size()
    m_year_filt = m_filtered.groupby('year').size()
    v_year_filt = v_filtered.groupby('year').size()
    
    years = sorted(set(m_year_raw.index).union(set(v_year_raw.index)))
    q1_rows = []
    for y in years:
        mr = m_year_raw.get(y, 0)
        vr = v_year_raw.get(y, 0)
        mf = m_year_filt.get(y, 0)
        vf = v_year_filt.get(y, 0)
        ratio_raw = (vr / mr) if mr > 0 and vr > 0 else np.nan
        ratio_filt = (vf / mf) if mf > 0 and vf > 0 else np.nan
        q1_rows.append({
            'year': y,
            'modis_raw': mr,
            'viirs_raw': vr,
            'ratio_raw': ratio_raw,
            'modis_filtered': mf,
            'viirs_filtered': vf,
            'ratio_filtered': ratio_filt
        })
    df_q1 = pd.DataFrame(q1_rows)
    print(df_q1.to_string(index=False))
    
    # Average annual counts in overlap complete years (2012-2025)
    overlap_years = df_q1[(df_q1['year'] >= 2012) & (df_q1['year'] <= 2025)]
    print("\nOverlap (2012-2025) annual averages:")
    print(f"MODIS raw mean: {overlap_years['modis_raw'].mean():.1f}")
    print(f"VIIRS raw mean: {overlap_years['viirs_raw'].mean():.1f}")
    print(f"Raw ratio mean: {overlap_years['ratio_raw'].mean():.2f} (min: {overlap_years['ratio_raw'].min():.2f}, max: {overlap_years['ratio_raw'].max():.2f})")
    print(f"MODIS filtered mean: {overlap_years['modis_filtered'].mean():.1f}")
    print(f"VIIRS filtered mean: {overlap_years['viirs_filtered'].mean():.1f}")
    print(f"Filtered ratio mean: {overlap_years['ratio_filtered'].mean():.2f} (min: {overlap_years['ratio_filtered'].min():.2f}, max: {overlap_years['ratio_filtered'].max():.2f})")
    
    # ----------------------------------------------------
    # Q4: Coverage and Overlap
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("QUESTION 4: Coverage, First/Last Dates, Gaps, Overlap")
    print("="*50)
    print("MODIS date range:", m_all['acq_date'].min(), "to", m_all['acq_date'].max())
    print("VIIRS date range:", v_all['acq_date'].min(), "to", v_all['acq_date'].max())
    
    # Daily gaps check
    m_days = pd.date_range(m_all['acq_date'].min(), m_all['acq_date'].max())
    v_days = pd.date_range(v_all['acq_date'].min(), v_all['acq_date'].max())
    m_active_days = set(pd.to_datetime(m_all['acq_date']).dt.strftime('%Y-%m-%d'))
    v_active_days = set(pd.to_datetime(v_all['acq_date']).dt.strftime('%Y-%m-%d'))
    print(f"MODIS total span days: {len(m_days)}, days with at least 1 detection: {len(m_active_days)}")
    print(f"VIIRS total span days: {len(v_days)}, days with at least 1 detection: {len(v_active_days)}")
    
    # First complete month
    print("MODIS first dates:", sorted(m_all['acq_date'].unique())[:5])
    print("VIIRS first dates:", sorted(v_all['acq_date'].unique())[:5])
    
    # Monthly detection counts
    m_months = m_all.groupby('year_month').size()
    v_months = v_all.groupby('year_month').size()
    overlap_months = m_months.index.intersection(v_months.index)
    print(f"Overlap months count: {len(overlap_months)}")
    print(f"Overlap start: {overlap_months.min()}, end: {overlap_months.max()}")
    
    # ----------------------------------------------------
    # Q5: Day/Night split and FRP statistics
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("QUESTION 5: Day/Night Split and FRP Statistics")
    print("="*50)
    print("MODIS Day/Night split:\n", m_all['daynight'].value_counts(dropna=False))
    print("MODIS Day/Night %:\n", m_all['daynight'].value_counts(normalize=True, dropna=False)*100)
    print("VIIRS Day/Night split:\n", v_all['daynight'].value_counts(dropna=False))
    print("VIIRS Day/Night %:\n", v_all['daynight'].value_counts(normalize=True, dropna=False)*100)
    
    def frp_stats(series, name):
        s = series.dropna()
        return {
            'sensor': name,
            'count': len(s),
            'nulls': series.isna().sum(),
            'null_pct': series.isna().mean() * 100,
            'min': s.min(),
            'p25': s.quantile(0.25),
            'median (p50)': s.median(),
            'mean': s.mean(),
            'p75': s.quantile(0.75),
            'p90': s.quantile(0.90),
            'p95': s.quantile(0.95),
            'p99': s.quantile(0.99),
            'max': s.max()
        }
    frp_df = pd.DataFrame([
        frp_stats(m_all['frp'], 'MODIS All'),
        frp_stats(m_all[m_all['daynight']=='D']['frp'], 'MODIS Day'),
        frp_stats(m_all[m_all['daynight']=='N']['frp'], 'MODIS Night'),
        frp_stats(v_all['frp'], 'VIIRS All'),
        frp_stats(v_all[v_all['daynight']=='D']['frp'], 'VIIRS Day'),
        frp_stats(v_all[v_all['daynight']=='N']['frp'], 'VIIRS Night'),
    ])
    print(frp_df.to_string(index=False))
    
    # ----------------------------------------------------
    # Q6: CHT Monthly pattern (91.6 to 92.7 E, 21.2 to 23.8 N)
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("QUESTION 6: Chittagong Hill Tracts Monthly Pattern")
    print("="*50)
    cht_w, cht_s, cht_e, cht_n = CHT_BBOX
    m_cht = m_filtered[(m_filtered['longitude'] >= cht_w) & (m_filtered['longitude'] <= cht_e) &
                       (m_filtered['latitude'] >= cht_s) & (m_filtered['latitude'] <= cht_n)]
    v_cht = v_filtered[(v_filtered['longitude'] >= cht_w) & (v_filtered['longitude'] <= cht_e) &
                       (v_filtered['latitude'] >= cht_s) & (v_filtered['latitude'] <= cht_n)]
    print(f"MODIS filtered in CHT: {len(m_cht):,} ({len(m_cht)/len(m_filtered)*100:.1f}% of Bangladesh)")
    print(f"VIIRS filtered in CHT: {len(v_cht):,} ({len(v_cht)/len(v_filtered)*100:.1f}% of Bangladesh)")
    
    m_cht_m = m_cht.groupby('month').size()
    v_cht_m = v_cht.groupby('month').size()
    cht_monthly = pd.DataFrame({
        'month': range(1, 13),
        'modis_count': [m_cht_m.get(m, 0) for m in range(1, 13)],
        'modis_pct': [m_cht_m.get(m, 0)/len(m_cht)*100 for m in range(1, 13)],
        'viirs_count': [v_cht_m.get(m, 0) for m in range(1, 13)],
        'viirs_pct': [v_cht_m.get(m, 0)/len(v_cht)*100 for m in range(1, 13)]
    })
    print(cht_monthly.to_string(index=False))
    m_mam_pct = cht_monthly[cht_monthly['month'].isin([3, 4, 5])]['modis_pct'].sum()
    v_mam_pct = cht_monthly[cht_monthly['month'].isin([3, 4, 5])]['viirs_pct'].sum()
    print(f"MODIS March-May share in CHT: {m_mam_pct:.2f}%")
    print(f"VIIRS March-May share in CHT: {v_mam_pct:.2f}%")
    
    # ----------------------------------------------------
    # Q7: Sensor Steps (2002 Aqua, 2018/2023 VIIRS)
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("QUESTION 7: Sensor Steps")
    print("="*50)
    print("MODIS satellite breakdown by year (filtered):")
    m_sat_yr = m_filtered.groupby(['year', 'satellite']).size().unstack(fill_value=0)
    print(m_sat_yr.head(10).to_string())
    
    print("\nVIIRS S-NPP annual counts around 2017-2024:")
    print(df_q1[(df_q1['year'] >= 2016) & (df_q1['year'] <= 2024)][['year', 'viirs_raw', 'viirs_filtered']])
    
    # ----------------------------------------------------
    # Q8: ST-DBSCAN Event Count and Runtime Estimate
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("QUESTION 8: ST-DBSCAN Events Estimate")
    print("="*50)
    # Default parameters:
    # spatial eps = 2,700 m
    # temporal eps = 24 hours (86,400 s)
    # min_pts = 2
    # Let's test on 1 year (e.g. 2019) for both MODIS and VIIRS
    
    def run_st_dbscan_sample(df_sub, sensor_name, year):
        t0 = time.time()
        # Coordinates in radians for haversine
        coords_rad = np.radians(df_sub[['latitude', 'longitude']].values)
        times_sec = df_sub['acq_ts'].astype('int64').values // 10**9
        
        EARTH_RADIUS_M = 6371000.0
        spatial_eps_rad = 2700.0 / EARTH_RADIUS_M
        temporal_eps_sec = 24 * 3600
        
        # BallTree spatial search
        tree = BallTree(coords_rad, metric='haversine')
        indices = tree.query_radius(coords_rad, r=spatial_eps_rad)
        
        # Build adjacency with time constraint
        n = len(df_sub)
        neighbors = []
        for i in range(n):
            cand = indices[i]
            t_diff = np.abs(times_sec[cand] - times_sec[i])
            valid = cand[t_diff <= temporal_eps_sec]
            neighbors.append(valid)
        
        # Standard DBSCAN using precomputed graph or standard BFS
        labels = np.full(n, -1, dtype=int)
        cluster_id = 0
        visited = np.zeros(n, dtype=bool)
        
        for i in range(n):
            if visited[i]:
                continue
            visited[i] = True
            nb = neighbors[i]
            if len(nb) < 2:
                labels[i] = -1
            else:
                labels[i] = cluster_id
                queue = list(nb[nb != i])
                while queue:
                    curr = queue.pop(0)
                    if not visited[curr]:
                        visited[curr] = True
                        curr_nb = neighbors[curr]
                        if len(curr_nb) >= 2:
                            for c in curr_nb:
                                if c not in queue and not visited[c]:
                                    queue.append(c)
                    if labels[curr] == -1:
                        labels[curr] = cluster_id
                cluster_id += 1
                
        elapsed = time.time() - t0
        n_clusters = cluster_id
        n_noise = (labels == -1).sum()
        clustered_pts = (labels != -1).sum()
        print(f"[{sensor_name} {year}] Points: {n:,} -> Clusters (Events): {n_clusters:,}, Clustered Pixels: {clustered_pts:,}, Noise: {n_noise:,} ({n_noise/n*100:.1f}%). Time: {elapsed:.2f}s")
        return {
            'sensor': sensor_name,
            'year': year,
            'pixels': n,
            'events': n_clusters,
            'noise': n_noise,
            'noise_pct': n_noise / n * 100,
            'clustered_pixels': clustered_pts,
            'pixels_per_event': clustered_pts / n_clusters if n_clusters > 0 else 0,
            'time_s': elapsed
        }
        
    # Run benchmark on 2019 and 2021
    st_res = []
    for y in [2016, 2019, 2023]:
        m_sub = m_filtered[m_filtered['year'] == y]
        v_sub = v_filtered[v_filtered['year'] == y]
        st_res.append(run_st_dbscan_sample(m_sub, 'MODIS', y))
        st_res.append(run_st_dbscan_sample(v_sub, 'VIIRS', y))
        
    df_st = pd.DataFrame(st_res)
    print("\nST-DBSCAN Sample Results:\n", df_st.to_string(index=False))

if __name__ == '__main__':
    run_analysis()
