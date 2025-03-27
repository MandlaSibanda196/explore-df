import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots

# Page config and header
st.title(":material/bar_chart: Chart Creator", anchor=False)
st.caption("Create and customize interactive visualizations")

# Initialize session state for storing the chart code
if 'accepted_suggestions' not in st.session_state:
    st.session_state['accepted_suggestions'] = []

df = st.session_state['df']

# Define available chart types and their requirements
CHART_TYPES = {
    "Scatter Plot": {
        "description": "Display relationship between two numeric variables",
        "requirements": {
            "x": {"type": "numeric", "required": True},
            "y": {"type": "numeric", "required": True},
            "color": {"type": "any", "required": False},
            "size": {"type": "numeric", "required": False},
            "hover_data": {"type": "any", "required": False, "multiple": True},
            "facet_col": {"type": "categorical", "required": False},
            "trendline": {"type": "select", "options": ["", "ols", "lowess", "rolling", "ewm", "expanding"], "required": False}
        },
        "function": "px.scatter"
    },
    "3D Scatter": {
        "description": "Show relationships between three numeric variables in 3D space",
        "requirements": {
            "x": {"type": "numeric", "required": True},
            "y": {"type": "numeric", "required": True},
            "z": {"type": "numeric", "required": True},
            "color": {"type": "any", "required": False},
            "size": {"type": "numeric", "required": False},
            "hover_data": {"type": "any", "required": False, "multiple": True},
            "opacity": {"type": "float", "required": False}
        },
        "function": "px.scatter_3d"
    },
    "Line Plot": {
        "description": "Show trends over a continuous variable",
        "requirements": {
            "x": {"type": "any", "required": True},
            "y": {"type": "numeric", "required": True},
            "color": {"type": "any", "required": False},
            "line_dash": {"type": "categorical", "required": False},
            "hover_data": {"type": "any", "required": False, "multiple": True},
            "markers": {"type": "boolean", "required": False}
        },
        "function": "px.line"
    },
    "Bar Chart": {
        "description": "Compare quantities across categories",
        "requirements": {
            "x": {"type": "any", "required": True},
            "y": {"type": "numeric", "required": True},
            "color": {"type": "any", "required": False},
            "pattern_shape": {"type": "categorical", "required": False},
            "hover_data": {"type": "any", "required": False, "multiple": True},
            "barmode": {"type": "select", "options": ["group", "stack", "relative"], "required": False}
        },
        "function": "px.bar"
    },
    "Histogram": {
        "description": "Show distribution of a numeric variable",
        "requirements": {
            "x": {"type": "numeric", "required": True},
            "color": {"type": "categorical", "required": False},
            "nbins": {"type": "integer", "required": False},
            "histnorm": {"type": "select", "options": ["", "percent", "probability", "density"], "required": False},
            "marginal": {"type": "select", "options": ["box", "violin", "rug"], "required": False}
        },
        "function": "px.histogram"
    },
    "Box Plot": {
        "description": "Show distribution statistics and outliers",
        "requirements": {
            "x": {"type": "any", "required": True},
            "y": {"type": "numeric", "required": True},
            "color": {"type": "categorical", "required": False},
            "notched": {"type": "boolean", "required": False},
            "points": {"type": "select", "options": ["all", "outliers", "suspected", "none"], "required": False}
        },
        "function": "px.box"
    },
    "Violin Plot": {
        "description": "Show distribution shape across categories",
        "requirements": {
            "x": {"type": "any", "required": True},
            "y": {"type": "numeric", "required": True},
            "color": {"type": "categorical", "required": False},
            "box": {"type": "boolean", "required": False},
            "points": {"type": "select", "options": ["all", "outliers", "none"], "required": False}
        },
        "function": "px.violin"
    },
    "Pie Chart": {
        "description": "Show part-to-whole relationships",
        "requirements": {
            "values": {"type": "numeric", "required": True},
            "names": {"type": "any", "required": True},
            "color": {"type": "any", "required": False},
            "hole": {"type": "float", "required": False},
            "hover_data": {"type": "any", "required": False, "multiple": True}
        },
        "function": "px.pie"
    },
    "Heatmap": {
        "description": "Show patterns between two categorical variables",
        "requirements": {
            "x": {"type": "any", "required": True},
            "y": {"type": "any", "required": True},
            "values": {"type": "numeric", "required": True},
            "color_continuous_scale": {"type": "select", "options": ["Viridis", "Plasma", "Inferno", "Magma", "RdBu"], "required": False},
            "text_auto": {"type": "boolean", "required": False}
        },
        "function": "px.density_heatmap" if df.shape[0] > 1000 else "px.imshow"
    },
    "Bubble Chart": {
        "description": "Show relationships between three numeric variables",
        "requirements": {
            "x": {"type": "numeric", "required": True},
            "y": {"type": "numeric", "required": True},
            "size": {"type": "numeric", "required": True},
            "color": {"type": "any", "required": False},
            "hover_data": {"type": "any", "required": False, "multiple": True},
            "text": {"type": "any", "required": False}
        },
        "function": "px.scatter"
    },
    "Area Plot": {
        "description": "Show cumulative totals over time",
        "requirements": {
            "x": {"type": "any", "required": True},
            "y": {"type": "numeric", "required": True},
            "color": {"type": "categorical", "required": False},
            "line_shape": {"type": "select", "options": ["linear", "spline"], "required": False},
            "groupnorm": {"type": "select", "options": ["", "fraction", "percent"], "required": False}
        },
        "function": "px.area"
    },
    "Sunburst": {
        "description": "Show hierarchical data in a circular layout",
        "requirements": {
            "path": {"type": "any", "required": True, "multiple": True},
            "values": {"type": "numeric", "required": True},
            "color": {"type": "any", "required": False},
            "hover_data": {"type": "any", "required": False, "multiple": True}
        },
        "function": "px.sunburst"
    },
    "Treemap": {
        "description": "Show hierarchical data as nested rectangles",
        "requirements": {
            "path": {"type": "any", "required": True, "multiple": True},
            "values": {"type": "numeric", "required": True},
            "color": {"type": "any", "required": False},
            "hover_data": {"type": "any", "required": False, "multiple": True}
        },
        "function": "px.treemap"
    },
    "Density Contour": {
        "description": "Show density estimation of numeric variables",
        "requirements": {
            "x": {"type": "numeric", "required": True},
            "y": {"type": "numeric", "required": True},
            "color": {"type": "categorical", "required": False},
            "nbinsx": {"type": "integer", "required": False},
            "nbinsy": {"type": "integer", "required": False},
            "histfunc": {"type": "select", "options": ["count", "sum", "avg", "min", "max"], "required": False}
        },
        "function": "px.density_contour"
    },
    "Parallel Coordinates": {
        "description": "Compare multiple numeric variables across observations",
        "requirements": {
            "dimensions": {"type": "numeric", "required": True, "multiple": True},
            "color": {"type": "any", "required": False},
            "hover_data": {"type": "any", "required": False, "multiple": True}
        },
        "function": "px.parallel_coordinates"
    },
    "Parallel Categories": {
        "description": "Show relationships between categorical variables",
        "requirements": {
            "dimensions": {"type": "categorical", "required": True, "multiple": True},
            "color": {"type": "numeric", "required": False},
            "hover_data": {"type": "any", "required": False, "multiple": True}
        },
        "function": "px.parallel_categories"
    },
    "Radar Chart": {
        "description": "Compare multiple variables in a circular layout",
        "requirements": {
            "r": {"type": "numeric", "required": True},
            "theta": {"type": "categorical", "required": True},
            "color": {"type": "categorical", "required": False},
            "line_close": {"type": "boolean", "required": False},
            "hover_data": {"type": "any", "required": False, "multiple": True}
        },
        "function": "px.line_polar"
    },
    "Candlestick": {
        "description": "Show stock price movement over time",
        "requirements": {
            "date": {"type": "any", "required": True},
            "open": {"type": "numeric", "required": True},
            "high": {"type": "numeric", "required": True},
            "low": {"type": "numeric", "required": True},
            "close": {"type": "numeric", "required": True}
        },
        "function": "go.Figure(go.Candlestick)"
    },
    "OHLC Chart": {
        "description": "Show stock price movement with OHLC bars",
        "requirements": {
            "date": {"type": "any", "required": True},
            "open": {"type": "numeric", "required": True},
            "high": {"type": "numeric", "required": True},
            "low": {"type": "numeric", "required": True},
            "close": {"type": "numeric", "required": True}
        },
        "function": "go.Figure(go.Ohlc)"
    },
    "Funnel Chart": {
        "description": "Show values decreasing through stages",
        "requirements": {
            "values": {"type": "numeric", "required": True},
            "stages": {"type": "any", "required": True},
            "color": {"type": "any", "required": False},
            "hover_data": {"type": "any", "required": False, "multiple": True}
        },
        "function": "go.Figure(go.Funnel)"
    },
    "Waterfall Chart": {
        "description": "Show cumulative effect of sequential values",
        "requirements": {
            "x": {"type": "any", "required": True},
            "y": {"type": "numeric", "required": True},
            "color": {"type": "categorical", "required": False},
            "connector": {"type": "boolean", "required": False}
        },
        "function": "go.Figure(go.Waterfall)"
    },
    "Ridgeline Plot": {
        "description": "Show distribution evolution over categories",
        "requirements": {
            "x": {"type": "numeric", "required": True},
            "y": {"type": "categorical", "required": True},
            "color": {"type": "categorical", "required": False},
            "overlap": {"type": "float", "required": False}
        },
        "function": "ff.create_distplot"
    },
    "Ternary Plot": {
        "description": "Show composition of three components",
        "requirements": {
            "a": {"type": "numeric", "required": True},
            "b": {"type": "numeric", "required": True},
            "c": {"type": "numeric", "required": True},
            "color": {"type": "any", "required": False},
            "hover_data": {"type": "any", "required": False, "multiple": True}
        },
        "function": "px.scatter_ternary"
    }
}

def get_column_type(series):
    """Determine the type of a column."""
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    elif pd.api.types.is_categorical_dtype(series) or series.nunique() / len(series) < 0.05:
        return "categorical"
    else:
        return "any"

def get_eligible_columns(requirement_type):
    """Get columns that match the required type."""
    if requirement_type == "numeric":
        return df.select_dtypes(include=[np.number]).columns.tolist()
    elif requirement_type == "categorical":
        return [col for col in df.columns if get_column_type(df[col]) == "categorical"]
    else:
        return df.columns.tolist()

def generate_chart_code(chart_type, params):
    """Generate the code for creating the chart."""
    function = CHART_TYPES[chart_type]["function"]
    
    # Special handling for different chart types
    if chart_type in ["Candlestick", "OHLC Chart"]:
        # Generate code for financial charts
        code = [
            f"# Create {chart_type.lower()}",
            f"fig = go.Figure(data=[{function}(",
            f"    x=df[{repr(params['date'])}],",
            f"    open=df[{repr(params['open'])}],",
            f"    high=df[{repr(params['high'])}],",
            f"    low=df[{repr(params['low'])}],",
            f"    close=df[{repr(params['close'])}]",
            ")])"
        ]
    elif chart_type == "Funnel Chart":
        # Generate code for funnel chart
        code = [
            "# Create funnel chart",
            "fig = go.Figure(data=[go.Funnel(",
            f"    y=df[{repr(params['stages'])}],",
            f"    x=df[{repr(params['values'])}]",
            f"    {', name=' + repr(params['color']) if params.get('color') else ''}",
            ")])"
        ]
    elif chart_type == "Waterfall Chart":
        # Generate code for waterfall chart
        code = [
            "# Create waterfall chart",
            "fig = go.Figure(go.Waterfall(",
            '    name="20",',
            '    orientation="v",',
            f"    measure=['relative'] * len(df[{repr(params['x'])}]),",
            f"    x=df[{repr(params['x'])}],",
            f"    y=df[{repr(params['y'])}],",
            f"    connector={{'line':{{'color':'rgb(63, 63, 63)'}}}} if {params.get('connector', False)} else None",
            "))"
        ]
    elif chart_type == "Ridgeline Plot":
        # Generate code for ridgeline plot using distplot
        code = [
            "# Create ridgeline plot",
            f"categories = df[{repr(params['y'])}].unique()",
            "fig = go.Figure()",
            "for cat in categories:",
            f"    cat_data = df[df[{repr(params['y'])}] == cat][{repr(params['x'])}]",
            "    fig.add_trace(go.Violin(",
            "        x=cat_data,",
            "        name=str(cat),",
            '        orientation="h",',
            '        side="positive",',
            "        width=2",
            "    ))",
            "fig.update_traces(points=False)",
            "fig.update_layout(showlegend=False)"
        ]
    elif chart_type == "Parallel Coordinates":
        # Generate code for parallel coordinates plot
        dimensions = [f"dict(range=[df[col].min(), df[col].max()], label=col, values=df[col])" 
                     for col in params['dimensions']]
        code = [
            "# Create parallel coordinates plot",
            "fig = go.Figure(data=go.Parcoords(",
            f"    line=dict(color=df[{repr(params['color'])}]) if {repr(params.get('color'))} else dict(),",
            f"    dimensions=[{', '.join(dimensions)}]",
            "))"
        ]
    elif chart_type == "Parallel Categories":
        # Generate code for parallel categories plot
        code = [
            "# Create parallel categories plot",
            "fig = px.parallel_categories(",
            "    df,",
            f"    dimensions={repr(params['dimensions'])},",
            f"    color={repr(params['color']) if params.get('color') else None}",
            ")"
        ]
    else:
        # Build the parameter string for standard plotly express charts
        param_strs = ["df"]
        for param, value in params.items():
            if value is not None:
                if isinstance(value, list):
                    param_strs.append(f"{param}=[{', '.join(repr(v) for v in value)}]")
                else:
                    param_strs.append(f"{param}={repr(value)}")
        
        # Generate the code
        code = [
            f"# Create {chart_type.lower()}",
            f"fig = {function}(",
            f"    {', '.join(param_strs)}",
            ")"
        ]
    
    # Add common layout updates
    code.extend([
        "",
        "# Update layout",
        "fig.update_layout(",
        "    showlegend=True,",
        "    margin=dict(t=30, l=50, r=20, b=50),",
        "    plot_bgcolor='white',",
        "    paper_bgcolor='white'",
        ")",
        "",
        "# Show the plot",
        "st.plotly_chart(fig, use_container_width=True)"
    ])
    
    return "\n".join(code)

# Main interface

st.subheader("", anchor=False, divider="grey")

# Chart type selection with categories
CHART_CATEGORIES = {
    "Basic Charts": [
        "Scatter Plot",
        "Line Plot",
        "Bar Chart",
        "Histogram",
        "Box Plot"
    ],
    "Statistical Charts": [
        "Violin Plot",
        "Density Contour",
        "Parallel Coordinates",
        "Parallel Categories",
        "Ridgeline Plot"
    ],
    "Part-to-Whole Charts": [
        "Pie Chart",
        "Treemap",
        "Sunburst",
        "Waterfall Chart",
        "Funnel Chart"
    ],
    "Advanced Charts": [
        "3D Scatter",
        "Bubble Chart",
        "Area Plot",
        "Heatmap",
        "Ternary Plot"
    ],
    "Financial Charts": [
        "Candlestick",
        "OHLC Chart"
    ]
}

# Create tabs for chart categories
CATEGORY_ICONS = {
    "Basic Charts": ":material/bar_chart:",  # Bar icon for basic charts
    "Statistical Charts": ":material/search_insights:",  # Bell curve for statistical charts
    "Part-to-Whole Charts": ":material/pie_chart:",  # Pie chart for part-to-whole
    "Advanced Charts": ":material/scatter_plot:",  # Scatter plot for advanced
    "Financial Charts": ":material/candlestick_chart:"  # Trending up for financial
}

tabs = st.tabs([f"{CATEGORY_ICONS[category]} {category}" for category in CHART_CATEGORIES.keys()])

for tab, (category, chart_types) in zip(tabs, CHART_CATEGORIES.items()):
    with tab:
        st.write("")
        selected_chart = st.selectbox(
            "Select Chart Type",
            options=chart_types,
            key=f"chart_select_{category}"
        )
        
        if selected_chart:
            with st.container(border=True):
                st.subheader("Chart Configuration", anchor=False, divider="grey")
                
                # Initialize parameters dictionary
                params = {}
                
                # Get requirements for selected chart
                requirements = CHART_TYPES[selected_chart]["requirements"]
                
                # Create two columns for parameters
                col1, col2 = st.columns(2)
                
                # Distribute parameters between columns
                params_list = list(requirements.items())
                mid_point = len(params_list) // 2
                
                for i, (param, req) in enumerate(params_list):
                    with col1 if i < mid_point else col2:
                        with st.container(border=True):
                            if req.get("multiple", False):
                                # Multiple selection
                                options = get_eligible_columns(req["type"])
                                params[param] = st.multiselect(
                                    f":material/format_list_bulleted: {param.replace('_', ' ').title()}" + (" ***- required***" if req["required"] else ""),
                                    options=options,
                                    key=f"multi_{selected_chart}_{param}"
                                )
                            elif req["type"] == "boolean":
                                # Boolean selection
                                params[param] = st.checkbox(
                                    f":material/check_box: {param.replace('_', ' ').title()}" + (" ***- required***" if req["required"] else ""),
                                    key=f"bool_{selected_chart}_{param}"
                                )
                            elif req["type"] == "select":
                                # Dropdown selection
                                params[param] = st.selectbox(
                                    f":material/arrow_drop_down: {param.replace('_', ' ').title()}" + (" ***- required***" if req["required"] else ""),
                                    options=[""] + req["options"],
                                    key=f"select_{selected_chart}_{param}"
                                )
                                if params[param] == "":
                                    params[param] = None
                            elif req["type"] == "integer":
                                # Integer input
                                params[param] = st.number_input(
                                    f":material/numbers: {param.replace('_', ' ').title()}" + (" ***- required***" if req["required"] else ""),
                                    min_value=1,
                                    value=30 if param == "nbins" else 1,
                                    key=f"int_{selected_chart}_{param}"
                                )
                            elif req["type"] == "float":
                                # Float input
                                params[param] = st.number_input(
                                    f":material/trending_up: {param.replace('_', ' ').title()}" + (" ***- required***" if req["required"] else ""),
                                    min_value=0.0,
                                    max_value=1.0,
                                    value=0.0,
                                    key=f"float_{selected_chart}_{param}"
                                )
                            else:
                                # Single column selection
                                options = get_eligible_columns(req["type"])
                                params[param] = st.selectbox(
                                    f":material/view_column: {param.replace('_', ' ').title()}" + (" ***- required***" if req["required"] else ""),
                                    options=[""] + options,
                                    key=f"col_{selected_chart}_{param}"
                                )
                                if params[param] == "":
                                    params[param] = None
            
            # Check if all required parameters are provided
            all_required_provided = all(
                params.get(param) is not None
                for param, req in requirements.items()
                if req["required"]
            )
            
            # Generate and display the chart
            if all_required_provided:
                with st.container(border=True):
                    st.subheader("Chart Preview", anchor=False, divider="grey")
                    
                    # Generate the code
                    chart_code = generate_chart_code(selected_chart, params)
                    
                    try:
                        # Execute the code to display the chart
                        exec(chart_code, globals(), {"st": st, "df": df, "px": px})
                        
                        # Show the code and add to suggestions
                        with st.expander(":material/code: Show Code"):
                            st.code(chart_code, language="python")
                            
                            if st.button(":material/check: Add to Accepted Suggestions", use_container_width=True):
                                if chart_code not in st.session_state['accepted_suggestions']:
                                    st.session_state['accepted_suggestions'].append(chart_code)
                                    st.success(":material/check: Code added to accepted suggestions!")
                                else:
                                    st.info(":material/info: This code is already in accepted suggestions.")
                    except Exception as e:
                        st.error(f"Error creating chart: {str(e)}")
            else:
                st.info(":material/info: Please provide all required parameters to generate the chart.") 