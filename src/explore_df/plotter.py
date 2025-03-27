import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import List, Optional
from scipy import stats

# We'll add plotting functions here in the next step 

def _calculate_monotonicity(data: pd.Series) -> str:
    """Calculate if a series is monotonic."""
    if data.is_monotonic_increasing:
        return "Increasing"
    elif data.is_monotonic_decreasing:
        return "Decreasing"
    return "Non-monotonic"

def _calculate_category_imbalance(value_counts: pd.Series) -> float:
    """Calculate category imbalance ratio."""
    if len(value_counts) <= 1:
        return 0
    return (value_counts.max() - value_counts.min()) / value_counts.sum()

def _calculate_cramers_v_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate Cramer's V correlation matrix for all categorical columns."""
    cat_cols = df.select_dtypes(include=['object', 'category']).columns
    matrix = pd.DataFrame(index=cat_cols, columns=cat_cols)
    
    for i in cat_cols:
        for j in cat_cols:
            matrix.loc[i,j] = _calculate_cramers_v(df[i], df[j])
    return matrix

def _calculate_mutual_info_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate mutual information matrix for all columns."""
    from sklearn.feature_selection import mutual_info_regression
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    matrix = pd.DataFrame(index=numeric_cols, columns=numeric_cols)
    
    for i in numeric_cols:
        for j in numeric_cols:
            matrix.loc[i,j] = mutual_info_regression(
                df[i].values.reshape(-1, 1),
                df[j].values
            )[0]
    return matrix

def _analyze_missing_patterns(df: pd.DataFrame) -> dict:
    """Analyze patterns in missing values."""
    missing = df.isnull()
    patterns = missing.sum(axis=1).value_counts().to_dict()
    return {
        "Common Patterns": patterns,
        "Consecutive Missing": _find_consecutive_missing(df)
    }

def _find_consecutive_missing(df: pd.DataFrame) -> dict:
    """Find consecutive missing values in each column."""
    results = {}
    for col in df.columns:
        mask = df[col].isnull()
        if mask.any():
            consecutive = mask.astype(int).groupby(
                (mask != mask.shift()).cumsum()
            ).sum()
            results[col] = consecutive.max()
    return results

def _detect_seasonality(df: pd.DataFrame, date_col: str, value_col: str) -> dict:
    """Detect seasonality in time series data."""
    from statsmodels.tsa.seasonal import seasonal_decompose
    
    df = df.set_index(date_col)
    result = seasonal_decompose(df[value_col], period=30)
    
    return {
        "Seasonal Strength": np.std(result.seasonal) / np.std(df[value_col]),
        "Period": 30,  # Could be made dynamic
        "Peak Times": pd.Series(result.seasonal).nlargest(3).index.tolist()
    }

def _analyze_trend(values: pd.Series) -> dict:
    """Analyze trend in time series data."""
    from scipy import stats
    
    x = np.arange(len(values))
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
    
    return {
        "Slope": slope,
        "R-squared": r_value**2,
        "P-value": p_value,
        "Trend": "Increasing" if slope > 0 else "Decreasing" if slope < 0 else "No trend"
    }

def _detect_change_points(values: pd.Series) -> dict:
    """Detect change points in time series data."""
    from ruptures import Binseg
    
    algo = Binseg(model="l2").fit(values.values.reshape(-1, 1))
    change_points = algo.predict(n_bkps=3)
    
    return {
        "Change Points": change_points,
        "Segments": len(change_points) + 1
    }

def _suggest_dtype_optimizations(df: pd.DataFrame) -> dict:
    """Suggest optimizations for data types."""
    suggestions = {}
    
    for col in df.columns:
        current_dtype = df[col].dtype
        if pd.api.types.is_integer_dtype(current_dtype):
            min_val, max_val = df[col].min(), df[col].max()
            suggestions[col] = _suggest_integer_dtype(min_val, max_val)
        elif pd.api.types.is_float_dtype(current_dtype):
            if df[col].round().equals(df[col]):
                suggestions[col] = "Consider converting to integer type"
        elif pd.api.types.is_object_dtype(current_dtype):
            if df[col].nunique() / len(df) < 0.5:
                suggestions[col] = "Consider converting to category type"
    
    return suggestions

def _suggest_integer_dtype(min_val: int, max_val: int) -> str:
    """Suggest the most memory-efficient integer dtype."""
    if min_val >= 0:
        if max_val < 255:
            return "uint8"
        elif max_val < 65535:
            return "uint16"
        elif max_val < 4294967295:
            return "uint32"
        return "uint64"
    else:
        if min_val > -128 and max_val < 127:
            return "int8"
        elif min_val > -32768 and max_val < 32767:
            return "int16"
        elif min_val > -2147483648 and max_val < 2147483647:
            return "int32"
        return "int64"

def create_histogram(df: pd.DataFrame, column: str, kde: bool = False) -> go.Figure:
    """Create a histogram for a numeric column."""
    fig = go.Figure()
    
    # Add histogram
    fig.add_trace(go.Histogram(
        x=df[column],
        name='Count',
        nbinsx=30,
        showlegend=True
    ))
    
    if kde:
        # Calculate KDE
        kde_x = np.linspace(df[column].min(), df[column].max(), 100)
        kde = stats.gaussian_kde(df[column].dropna())
        kde_y = kde(kde_x)
        
        # Scale KDE to match histogram height
        hist, bin_edges = np.histogram(df[column].dropna(), bins=30)
        scaling_factor = max(hist) / max(kde_y)
        kde_y = kde_y * scaling_factor
        
        # Add KDE line
        fig.add_trace(go.Scatter(
            x=kde_x,
            y=kde_y,
            name='KDE',
            line=dict(color='red', width=2)
        ))
    
    fig.update_layout(
        title=dict(
            text=f'Distribution of {column}',
            x=0.5,
            y=0.95,
            yanchor='top'
        ),
        xaxis_title=column,
        yaxis_title='Count',
        showlegend=True,
        template='simple_white',
        margin=dict(t=50, l=10, r=10, b=10)
    )
    
    return fig

def create_boxplot(df: pd.DataFrame, column: str) -> go.Figure:
    """Create a simple box plot for numerical data."""
    fig = go.Figure()
    
    fig.add_trace(go.Box(
        y=df[column],
        name=column,
        boxpoints='outliers',
        line=dict(color='rgb(8,81,156)'),
        showlegend=False
    ))
    
    fig.update_layout(
        title=dict(
            text=f'Box Plot of {column}',
            x=0.5,
            y=0.95,
            yanchor='top'
        ),
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=50, l=10, r=10, b=10),
        yaxis=dict(
            title=None,
            showgrid=True,
            gridcolor='rgb(220,220,220)',
            zeroline=False
        ),
        xaxis=dict(
            showticklabels=False,
            zeroline=False
        ),
        modebar=dict(
            remove=['zoom', 'pan', 'select', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']
        )
    )
    
    return fig

def create_bar_chart(df: pd.DataFrame, column: str, limit: int = 10) -> go.Figure:
    """Create a bar chart for categorical data."""
    value_counts = df[column].value_counts().head(limit)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=value_counts.index,
        y=value_counts.values,
        marker_color='rgb(8,81,156)'
    ))
    
    # Calculate dynamic margins based on label length
    max_label_length = max([len(str(label)) for label in value_counts.index])
    bottom_margin = max(10, max_label_length * 4)  # Adjust bottom margin based on label length
    
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=50, l=50, r=20, b=bottom_margin),  # Increased left and bottom margins
        yaxis=dict(
            title='Count',
            showgrid=True,
            gridcolor='rgb(220,220,220)',
            zeroline=False
        ),
        xaxis=dict(
            title=None,
            zeroline=False,
            tickangle=45  # Angle the labels for better readability
        ),
        modebar=dict(
            remove=['zoom', 'pan', 'select', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']
        ),
        height=450,  # Increased height
        width=None,  # Allow width to be set by container
        autosize=True  # Enable autosize for container width
    )
    
    return fig

def create_correlation_heatmap(
    df: pd.DataFrame, 
    columns: Optional[List[str]] = None
) -> go.Figure:
    """Create a correlation heatmap for numerical columns."""
    if columns is None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
    else:
        numeric_cols = columns
    
    corr_matrix = df[numeric_cols].corr()
    
    return px.imshow(
        corr_matrix,
        title='Correlation Heatmap',
        color_continuous_scale='RdBu',
        aspect='auto'
    )

def create_scatter_plot(
    df: pd.DataFrame, 
    x_col: str, 
    y_col: str, 
    color_col: Optional[str] = None
) -> go.Figure:
    """Create a scatter plot between two numerical columns."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode='markers',
        marker=dict(
            color='rgb(8,81,156)',
            size=8,
            opacity=0.6
        ),
        showlegend=False
    ))
    
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=50, l=50, r=20, b=50),
        yaxis=dict(
            title=y_col,
            showgrid=True,
            gridcolor='rgb(220,220,220)',
            zeroline=False
        ),
        xaxis=dict(
            title=x_col,
            showgrid=True,
            gridcolor='rgb(220,220,220)',
            zeroline=False
        ),
        modebar=dict(
            remove=['zoom', 'pan', 'select', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']
        )
    )
    
    return fig

def create_violin_plot(df: pd.DataFrame, column: str, group_by: Optional[str] = None) -> go.Figure:
    """Create an enhanced violin plot with box plot overlay."""
    return px.violin(
        df, y=column, x=group_by, box=True,
        points="outliers", title=f'Distribution of {column}'
    )

def create_pie_chart(df: pd.DataFrame, column: str, limit: int = 10) -> go.Figure:
    """Create a pie chart for categorical data."""
    value_counts = df[column].value_counts().head(limit)
    return px.pie(
        values=value_counts.values,
        names=value_counts.index,
        title=f'Distribution of {column} (Top {limit} Categories)'
    )

def create_missing_values_plot(df: pd.DataFrame) -> go.Figure:
    """Create a bar chart showing missing values per column."""
    missing_data = df.isnull().sum().sort_values(ascending=True)
    missing_data = missing_data[missing_data > 0]
    
    if len(missing_data) == 0:
        return None
        
    return px.bar(
        x=missing_data.values,
        y=missing_data.index,
        orientation='h',
        title='Missing Values by Column',
        labels={'x': 'Number of Missing Values', 'y': 'Column'}
    )

def create_density_plot(df: pd.DataFrame, column: str) -> go.Figure:
    """Create a KDE plot for numerical data."""
    return px.density(df, x=column, title=f'Density Plot of {column}')

def create_time_series_plot(
    df: pd.DataFrame, 
    date_column: str, 
    value_column: str,
    title: Optional[str] = None
) -> go.Figure:
    """Create a time series plot."""
    # Ensure date column is datetime
    df = df.copy()
    df[date_column] = pd.to_datetime(df[date_column])
    
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=df[date_column], y=df[value_column], mode='lines')
    )
    fig.update_layout(
        # title=title,
        xaxis_title=date_column,
        yaxis_title=value_column,
        showlegend=False
    )
    return fig

def create_time_series_decomposition(df: pd.DataFrame, date_col: str, value_col: str) -> dict:
    """Create seasonal decomposition plots for time series data."""
    from statsmodels.tsa.seasonal import seasonal_decompose
    
    # Convert to datetime if needed
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col)
    
    # Perform decomposition
    decomposition = seasonal_decompose(df[value_col], period=30)
    
    # Create individual plots
    plots = {
        'Trend': px.line(y=decomposition.trend, title='Trend'),
        'Seasonal': px.line(y=decomposition.seasonal, title='Seasonal Pattern'),
        'Residual': px.line(y=decomposition.resid, title='Residuals')
    }
    return plots

def create_lag_plot(df: pd.DataFrame, column: str, lag: int = 1) -> go.Figure:
    """Create a lag plot to check for time series autocorrelation."""
    values = df[column].dropna()
    return px.scatter(
        x=values[:-lag],
        y=values[lag:],
        title=f'Lag Plot (lag={lag})',
        labels={'x': f'{column} (t)', 'y': f'{column} (t+{lag})'}
    )

def create_qq_plot(df: pd.DataFrame, column: str) -> go.Figure:
    """Create a Q-Q plot to compare with normal distribution."""
    data = df[column].dropna()
    qq = stats.probplot(data)
    
    return px.scatter(
        x=qq[0][0], 
        y=qq[0][1],
        title=f'Q-Q Plot for {column}',
        labels={'x': 'Theoretical Quantiles', 'y': 'Sample Quantiles'}
    )

def create_distribution_comparison(
    df: pd.DataFrame, 
    columns: List[str]
) -> go.Figure:
    """Create overlaid density plots for multiple columns."""
    fig = go.Figure()
    for col in columns:
        fig.add_trace(
            go.Violin(
                y=df[col],
                name=col,
                box_visible=True,
                meanline_visible=True
            )
        )
    fig.update_layout(title='Distribution Comparison')
    return fig 

def create_scatter_matrix(
    df: pd.DataFrame, 
    columns: Optional[List[str]] = None,
    color_col: Optional[str] = None
) -> go.Figure:
    """Create a scatter plot matrix for multiple variables."""
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns[:4]  # Limit to 4 for readability
    
    return px.scatter_matrix(
        df,
        dimensions=columns,
        color=color_col,
        title='Scatter Plot Matrix'
    )

def create_parallel_coordinates(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    color_col: Optional[str] = None
) -> go.Figure:
    """Create parallel coordinates plot for multivariate analysis."""
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns
    
    return px.parallel_coordinates(
        df,
        dimensions=columns,
        color=color_col,
        title='Parallel Coordinates Plot'
    )

def create_sunburst(
    df: pd.DataFrame,
    hierarchy: List[str]
) -> go.Figure:
    """Create a sunburst chart for hierarchical categorical data."""
    return px.sunburst(
        df,
        path=hierarchy,
        title='Hierarchical View'
    )

def create_categorical_correlation(
    df: pd.DataFrame,
    cat_columns: Optional[List[str]] = None
) -> go.Figure:
    """Create a Cramer's V correlation matrix for categorical variables."""
    from scipy.stats import chi2_contingency
    
    if cat_columns is None:
        cat_columns = df.select_dtypes(include=['object', 'category']).columns
    
    def cramers_v(x, y):
        confusion_matrix = pd.crosstab(x, y)
        chi2 = chi2_contingency(confusion_matrix)[0]
        n = confusion_matrix.sum().sum()
        phi2 = chi2/n
        r,k = confusion_matrix.shape
        phi2corr = max(0, phi2-((k-1)*(r-1))/(n-1))
        rcorr = r-((r-1)**2)/(n-1)
        kcorr = k-((k-1)**2)/(n-1)
        return np.sqrt(phi2corr/min((kcorr-1),(rcorr-1)))
    
    corr_matrix = pd.DataFrame(index=cat_columns, columns=cat_columns)
    for i in cat_columns:
        for j in cat_columns:
            corr_matrix.loc[i,j] = cramers_v(df[i], df[j])
    
    return px.imshow(
        corr_matrix,
        title='Categorical Correlation (Cramer\'s V)',
        color_continuous_scale='RdBu'
    )

def create_data_quality_report(df: pd.DataFrame) -> go.Figure:
    """Create a comprehensive data quality visualization."""
    quality_metrics = pd.DataFrame({
        'Column': df.columns,
        'Missing (%)': (df.isnull().sum() / len(df) * 100).round(2),
        'Unique (%)': (df.nunique() / len(df) * 100).round(2),
        'Zeros (%)': ((df == 0).sum() / len(df) * 100).round(2),
        'Memory (MB)': df.memory_usage(deep=True) / 1024**2
    })
    
    return px.bar(
        quality_metrics.melt(id_vars=['Column']),
        x='Column',
        y='value',
        color='variable',
        barmode='group',
        title='Data Quality Overview'
    )

def create_advanced_stats(df: pd.DataFrame, column: str) -> dict:
    """Create advanced statistical analysis for a column."""
    stats = {}
    
    if pd.api.types.is_numeric_dtype(df[column]):
        data = df[column].dropna()
        stats.update({
            # Existing stats
            "Mean": data.mean(),
            "Median": data.median(),
            "Std Dev": data.std(),
            
            # New stats
            "Monotonicity": _calculate_monotonicity(data),
            "Normality (Shapiro)": stats.shapiro(data)[1] if len(data) < 5000 else None,
            "Coefficient of Variation": data.std() / data.mean() if data.mean() != 0 else None,
            "MAD": stats.median_abs_deviation(data),
            "Quantiles": {
                "1%": data.quantile(0.01),
                "25%": data.quantile(0.25),
                "50%": data.quantile(0.50),
                "75%": data.quantile(0.75),
                "99%": data.quantile(0.99)
            }
        })
    
    # For categorical columns
    else:
        value_counts = df[column].value_counts()
        stats.update({
            "Mode": df[column].mode()[0],
            "Unique Values": df[column].nunique(),
            "Top Categories": value_counts.head(5).to_dict(),
            "Category Imbalance": _calculate_category_imbalance(value_counts)
        })
    
    return stats 

def create_correlation_analysis(df, method='pearson'):
    """
    Calculate correlation matrix using the specified method.
    
    Args:
        df (pd.DataFrame): Input DataFrame
        method (str): Correlation method ('pearson', 'spearman', or 'kendall')
    
    Returns:
        pd.DataFrame: Correlation matrix
    """
    try:
        # Get numeric columns only
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.empty:
            return None
            
        # Calculate correlation matrix
        corr_matrix = numeric_df.corr(method=method.lower())
        
        return corr_matrix
        
    except Exception as e:
        print(f"Error in correlation analysis: {str(e)}")
        return None

def create_data_quality_metrics(df: pd.DataFrame) -> dict:
    """Generate comprehensive data quality metrics."""
    return {
        "Missing Values": {
            "Total": df.isna().sum().sum(),
            "By Column": df.isna().sum().to_dict(),
            "Patterns": _analyze_missing_patterns(df)
        },
        "Duplicates": {
            "Total Rows": df.duplicated().sum(),
            "By Column": {col: df[col].duplicated().sum() for col in df.columns}
        },
        "Zeros": {
            "By Column": ((df == 0).sum() / len(df) * 100).to_dict()
        },
        "Constant Values": {
            "By Column": {col: df[col].nunique() == 1 for col in df.columns}
        },
        "Type Inference": infer_column_types(df)
    } 

def create_time_series_metrics(df: pd.DataFrame, date_col: str, value_col: str) -> dict:
    """Generate time series specific metrics."""
    from statsmodels.tsa.stattools import adfuller, kpss
    
    df = df.sort_values(date_col)
    values = df[value_col].replace([np.inf, -np.inf], np.nan).dropna()
    
    if len(values) == 0:
        return {
            "Stationarity": {
                "ADF Test": (None, None, None, None, None),
                "KPSS Test": (None, None, None, None)
            },
            "Seasonality": {
                "Seasonal Strength": None,
                "Period": None,
                "Peak Times": None
            },
            "Trend": {
                "Slope": None,
                "R-squared": None,
                "P-value": None,
                "Trend": "No data available"
            },
            "Change Points": {
                "Change Points": None,
                "Segments": 0
            }
        }
    
    return {
        "Stationarity": {
            "ADF Test": adfuller(values),
            "KPSS Test": kpss(values)
        },
        "Seasonality": _detect_seasonality(df, date_col, value_col),
        "Trend": _analyze_trend(values),
        "Change Points": _detect_change_points(values)
    } 

def create_text_analysis(df: pd.DataFrame, text_col: str) -> dict:
    """Analyze text data columns."""
    from collections import Counter
    import re
    
    text_data = df[text_col].dropna()
    
    return {
        "Length Stats": {
            "Mean Length": text_data.str.len().mean(),
            "Max Length": text_data.str.len().max(),
            "Min Length": text_data.str.len().min()
        },
        "Word Stats": {
            "Unique Words": len(set(" ".join(text_data).split())),
            "Top Words": Counter(" ".join(text_data).split()).most_common(10)
        },
        "Pattern Analysis": {
            "URLs": text_data.str.contains(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+').sum(),
            "Emails": text_data.str.contains(r'[\w\.-]+@[\w\.-]+').sum(),
            "Numbers": text_data.str.contains(r'\d+').sum()
        }
    } 

def analyze_memory_usage(df: pd.DataFrame) -> dict:
    """Analyze memory usage and suggest optimizations."""
    memory_usage = df.memory_usage(deep=True)
    
    return {
        "Total Memory": memory_usage.sum(),
        "By Column": memory_usage.to_dict(),
        "Optimization Suggestions": _suggest_dtype_optimizations(df)
    } 

def create_density_heatmap(df: pd.DataFrame, x: str, y: str) -> go.Figure:
    """Create a 2D density heatmap."""
    return px.density_heatmap(
        df, x=x, y=y,
        marginal_x="histogram",
        marginal_y="histogram"
    )

def create_parallel_categories(df: pd.DataFrame, columns: List[str]) -> go.Figure:
    """Create parallel categories plot for categorical variables."""
    return px.parallel_categories(
        df, dimensions=columns,
        title='Parallel Categories Plot'
    )

def create_radar_plot(df: pd.DataFrame, columns: List[str]) -> go.Figure:
    """Create a radar plot for numerical columns."""
    normalized_values = (df[columns] - df[columns].min()) / (df[columns].max() - df[columns].min())
    mean_values = normalized_values.mean()
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=mean_values.values,
        theta=mean_values.index,
        fill='toself'
    ))
    return fig

def generate_automated_insights(df: pd.DataFrame) -> dict:
    """Generate automated insights about the dataset."""
    insights = {
        "General": [],
        "Correlations": [],
        "Distributions": [],
        "Anomalies": [],
        "Quality": []
    }
    
    # General insights
    insights["General"].extend([
        f"Dataset has {df.shape[0]} rows and {df.shape[1]} columns",
        f"Memory usage is {df.memory_usage().sum() / 1024**2:.2f} MB",
        f"Contains {len(df.select_dtypes(include=[np.number]).columns)} numeric columns"
    ])
    
    # Correlation insights
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) >= 2:
        corr_matrix = df[numeric_cols].corr()
        high_corr = np.where(np.abs(corr_matrix) > 0.8)
        high_corr = [(corr_matrix.index[x], corr_matrix.columns[y], corr_matrix.iloc[x, y])
                     for x, y in zip(*high_corr) if x != y]
        
        for col1, col2, corr in high_corr:
            insights["Correlations"].append(
                f"Strong {'positive' if corr > 0 else 'negative'} correlation "
                f"({corr:.2f}) between {col1} and {col2}"
            )
    
    # Distribution insights
    for col in numeric_cols:
        skew = df[col].skew()
        if abs(skew) > 1:
            insights["Distributions"].append(
                f"{col} shows {'positive' if skew > 0 else 'negative'} skew ({skew:.2f})"
            )
    
    # Anomaly detection
    for col in numeric_cols:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        outliers = df[col][(df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)]
        if len(outliers) > 0:
            insights["Anomalies"].append(
                f"{col} has {len(outliers)} potential outliers "
                f"({(len(outliers)/len(df)*100):.1f}% of values)"
            )
    
    # Quality insights
    missing = df.isnull().sum()
    if missing.any():
        insights["Quality"].extend([
            f"{col} has {miss} missing values ({miss/len(df)*100:.1f}%)"
            for col, miss in missing[missing > 0].items()
        ])
    
    return insights

def infer_column_types(df: pd.DataFrame) -> dict:
    """Infer detailed column types and provide suggestions."""
    inferred_types = {}
    
    for column in df.columns:
        data = df[column].dropna()
        current_type = str(df[column].dtype)
        
        if pd.api.types.is_numeric_dtype(df[column]):
            if df[column].round().equals(df[column]):
                if df[column].min() >= 0:
                    if df[column].max() <= 1:
                        inferred_types[column] = {
                            "type": "binary",
                            "suggestion": "Consider converting to boolean"
                        }
                    else:
                        inferred_types[column] = {
                            "type": "integer",
                            "suggestion": _suggest_integer_dtype(df[column].min(), df[column].max())
                        }
                else:
                    inferred_types[column] = {
                        "type": "integer",
                        "suggestion": _suggest_integer_dtype(df[column].min(), df[column].max())
                    }
            else:
                inferred_types[column] = {
                    "type": "float",
                    "suggestion": "Consider float32 if precision allows"
                }
        
        elif pd.api.types.is_string_dtype(df[column]):
            unique_ratio = df[column].nunique() / len(df)
            
            if unique_ratio < 0.05:
                inferred_types[column] = {
                    "type": "categorical",
                    "suggestion": "Convert to category type"
                }
            elif data.str.match(r'^\d{4}-\d{2}-\d{2}').all():
                inferred_types[column] = {
                    "type": "date",
                    "suggestion": "Convert to datetime"
                }
            elif data.str.contains(r'@').any():
                inferred_types[column] = {
                    "type": "email",
                    "suggestion": "Consider validation and indexing"
                }
            elif data.str.match(r'^[-+]?[0-9]*\.?[0-9]+$').all():
                inferred_types[column] = {
                    "type": "numeric_string",
                    "suggestion": "Convert to numeric type"
                }
            else:
                inferred_types[column] = {
                    "type": "text",
                    "suggestion": "Consider text analysis"
                }
    
    return inferred_types 

def create_statistical_tests(df: pd.DataFrame, column: str) -> dict:
    """Perform comprehensive statistical tests on a column."""
    from scipy import stats
    
    results = {}
    data = df[column].dropna()
    
    if pd.api.types.is_numeric_dtype(df[column]):
        # Normality tests
        results["Normality"] = {
            "Shapiro-Wilk": stats.shapiro(data) if len(data) < 5000 else None,
            "D'Agostino-Pearson": stats.normaltest(data),
            "Anderson-Darling": stats.anderson(data)
        }
        
        # Distribution fitting
        distributions = [
            stats.norm, stats.lognorm, stats.expon, 
            stats.gamma, stats.beta, stats.uniform
        ]
        
        best_dist = None
        best_p = 0
        
        for dist in distributions:
            try:
                params = dist.fit(data)
                _, p_value = stats.kstest(data, dist.name, params)
                if p_value > best_p:
                    best_p = p_value
                    best_dist = dist.name
            except:
                continue
        
        results["Best Fitting Distribution"] = {
            "distribution": best_dist,
            "p_value": best_p
        }
        
        # Stationarity
        results["Stationarity"] = {
            "Augmented Dickey-Fuller": stats.adfuller(data)[1],
            "KPSS": stats.kpss(data)[1]
        }
    
    return results 

def create_box_plot(df: pd.DataFrame, cat_col: str, num_col: str) -> go.Figure:
    """Create a box plot for categorical vs numeric variables."""
    fig = go.Figure()
    
    categories = df[cat_col].unique()
    for category in categories:
        fig.add_trace(go.Box(
            y=df[df[cat_col] == category][num_col],
            name=str(category),
            boxpoints='outliers',
            line=dict(color='rgb(8,81,156)'),
            showlegend=False
        ))
    
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=20, l=50, r=20, b=50),  # Reduced top margin since no title
        yaxis=dict(
            title=num_col,
            showgrid=True,
            gridcolor='rgb(220,220,220)',
            zeroline=False
        ),
        xaxis=dict(
            title=cat_col,
            zeroline=False
        ),
        modebar=dict(
            remove=['zoom', 'pan', 'select', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']
        )
    )
    
    return fig 