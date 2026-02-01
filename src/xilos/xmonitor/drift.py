import polars as pl
import polars.selectors as cs
import numpy as np
from scipy.stats import wasserstein_distance
from xilos.xget import DataFetcher
from xilos.settings import logger

class DriftAnalyzer:
    """Analyzes drift between reference and current datasets."""
    
    def __init__(self):
        pass
    
    def _load_data(self, source: str, fetcher: DataFetcher) -> pl.DataFrame:
        """Helper to load data using fetcher and convert to Polars."""
        data = fetcher.fetch(source)
        
        if isinstance(data, pl.DataFrame):
            return data
        
        # If pandas
        try:
            import pandas as pd
            if isinstance(data, pd.DataFrame):
                return pl.from_pandas(data)
        except ImportError:
            pass
            
        # If bytes (assuming csv/parquet)
        if isinstance(data, bytes):
            import io
            try:
                return pl.read_parquet(io.BytesIO(data))
            except Exception:
                pass
            try:
                return pl.read_csv(io.BytesIO(data))
            except Exception:
                pass
        
        raise ValueError(f"Could not convert fetched data from {source} to Polars DataFrame. Type: {type(data)}")

    def _compute_wasserstein(self, ref_col: pl.Series, curr_col: pl.Series) -> float:
        """Compute Wasserstein distance for numerical columns."""
        # Drop nulls before calculation
        u = ref_col.drop_nulls().to_numpy()
        v = curr_col.drop_nulls().to_numpy()
        if len(u) == 0 or len(v) == 0:
            return float("nan")
        return float(wasserstein_distance(u, v))

    def _compute_psi(self, ref_col: pl.Series, curr_col: pl.Series) -> float:
        """Compute Population Stability Index for categorical columns."""
        # 1. Get value counts (frequencies)
        ref_counts = ref_col.value_counts(sort=True).rename({ref_col.name: "value", "count": "ref_count"})
        curr_counts = curr_col.value_counts(sort=True).rename({curr_col.name: "value", "count": "curr_count"})
        
        # 2. Join to align categories
        # Outer join to include all categories from both
        joined = ref_counts.join(curr_counts, on="value", how="outer").fill_null(0)
        
        # 3. Calculate proportions
        total_ref = joined["ref_count"].sum()
        total_curr = joined["curr_count"].sum()
        
        if total_ref == 0 or total_curr == 0:
            return float("nan")

        # Add epsilon to avoid division by zero
        epsilon = 1e-6
        joined = joined.with_columns([
            ((pl.col("ref_count") / total_ref) + epsilon).alias("ref_pct"),
            ((pl.col("curr_count") / total_curr) + epsilon).alias("curr_pct"),
        ])
        
        # 4. Calculate PSI components: (Actual% - Expected%) * ln(Actual% / Expected%)
        # Here Current=Actual, Reference=Expected
        psi_series = (pl.col("curr_pct") - pl.col("ref_pct")) * \
                     (pl.col("curr_pct") / pl.col("ref_pct")).log()
        
        # 5. Sum
        psi = joined.select(psi_series.sum()).item()
        return float(psi)

    def analyze(self, reference_source: str, current_source: str, fetcher: DataFetcher) -> pl.DataFrame:
        """
        Perform drift analysis on variables.
        - Numerical: Wasserstein Distance
        - Categorical: Population Stability Index (PSI)
        
        Returns:
            pl.DataFrame: Report with columns [column, type, metric, value]
        """
        logger.info(f"Loading reference data from {reference_source}...")
        ref_df = self._load_data(reference_source, fetcher)
        
        logger.info(f"Loading current data from {current_source}...")
        curr_df = self._load_data(current_source, fetcher)
        
        results = []

        # --- Numerical Analysis ---
        ref_numerics = ref_df.select(cs.numeric())
        curr_numerics = curr_df.select(cs.numeric())
        common_numerics = set(ref_numerics.columns) & set(curr_numerics.columns)
        
        for col in common_numerics:
            dist = self._compute_wasserstein(ref_df[col], curr_df[col])
            results.append({
                "column": col,
                "type": "numerical",
                "metric": "wasserstein",
                "value": dist
            })

        # --- Categorical Analysis ---
        # Select strings and categoricals
        ref_cats = ref_df.select(cs.string() | cs.categorical())
        curr_cats = curr_df.select(cs.string() | cs.categorical())
        common_cats = set(ref_cats.columns) & set(curr_cats.columns)
        
        for col in common_cats:
            psi = self._compute_psi(ref_df[col], curr_df[col])
            results.append({
                "column": col,
                "type": "categorical",
                "metric": "psi",
                "value": psi
            })
            
        report_df = pl.DataFrame(results)
        logger.info(f"Drift analysis complete. Analyzed {len(results)} columns.")
        return report_df
