import dash
from dash import html, dcc, Input, Output
import dash_ag_grid as dag
import pandas as pd
import os

# =========================================================
# LOAD DATA
# =========================================================
df = pd.read_excel("2026-02-12 Final Barriers Initiatives.xlsx", sheet_name="Sheet1")

# =========================================================
# PREPROCESS
# =========================================================
df["ID"] = df["ID"].astype(str).str.strip()
df["Timeline"] = df["Timeline"].astype(str)
df["Location Identified"] = df["Location Identified"].fillna("")
df["Filtering-Contributors-Categories"] = df["Filtering-Contributors-Categories"].fillna("")
df["location_tokens"] = df["Location Identified"].apply(lambda x: [v.strip() for v in str(x).split(",") if v.strip()])
df["stakeholder_tokens"] = df["Filtering-Contributors-Categories"].apply(lambda x: [v.strip() for v in str(x).split(",") if v.strip()])
df["has_image"] = df["ID"].apply(lambda x: os.path.exists(f"assets/{x}.png"))
df_all = df.copy()
df_images = df[df["has_image"]]

# =========================================================
# FILTER HELPER
# =========================================================
def apply_filters(df, categories, subcategories, locations, stakeholders):
    filtered = df.copy()
    if categories: filtered = filtered[filtered["Category"].isin(categories)]
    if subcategories: filtered = filtered[filtered["Sub-Category"].isin(subcategories)]
    if locations: filtered = filtered[filtered["location_tokens"].apply(lambda x: any(v in x for v in locations))]
    if stakeholders: filtered = filtered[filtered["stakeholder_tokens"].apply(lambda x: any(v in x for v in stakeholders))]
    return filtered

# =========================================================
# DASH APP
# =========================================================
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# =========================================================
# STATUS CELL STYLE
# =========================================================
status_style = {
    "styleConditions": [
        {"condition": "params.value === '-'", "style": {"backgroundColor": "#f3f4f6", "textAlign": "center"}},
        {"condition": "params.value === 'Pending'", "style": {"backgroundColor": "#fed7aa", "textAlign": "center", "fontWeight": "600"}},
        {"condition": "params.value === 'In progress'", "style": {"backgroundColor": "#fef3c7", "textAlign": "center", "fontWeight": "600"}},
        {"condition": "['Complete','In action','In Action','Complete/ In action'].includes(params.value)",
         "style": {"backgroundColor": "#bbf7d0", "textAlign": "center", "fontWeight": "600"}},
    ]
}

# =========================================================
# LAYOUT
# =========================================================
app.layout = html.Div(
    className="page",
    children=[
        html.Div(
            className="sidebar",
            children=[
                html.H3("Filters"),
                dcc.Dropdown(id="category-filter", multi=True, placeholder="Category", style={"marginBottom": "12px"}),
                dcc.Dropdown(id="subcategory-filter", multi=True, placeholder="Sub-category", style={"marginBottom": "12px"}),
                dcc.Dropdown(id="location-filter", multi=True, placeholder="Location", style={"marginBottom": "12px"}),
                dcc.Dropdown(id="stakeholder-filter", multi=True, placeholder="Owner/Contributor Group", style={"marginBottom": "16px"}),
                html.Button("Clear Filters", id="clear-filters", n_clicks=0,
                            style={"backgroundColor": "#dc2626","color": "white","border": "none",
                                   "padding": "8px 14px","borderRadius": "4px","cursor": "pointer","width": "100%"})
            ],
        ),
        html.Div(
            className="content",
            children=[
                html.H1("Atlantic Housing Innovation Roadmap"),
                dcc.Tabs(id="tabs", value="tracking", children=[
                    dcc.Tab(label="Dashboard View", value="dashboard"),
                    dcc.Tab(label="Initiatives View", value="initiatives"),
                    dcc.Tab(label="Initiatives Tracking", value="tracking"),
                ]),
                html.Div(id="tab-content")
            ],
        ),
    ],
)

# =========================================================
# CASCADING FILTER OPTIONS
# =========================================================
@app.callback(
    Output("category-filter", "options"),
    Output("subcategory-filter", "options"),
    Output("location-filter", "options"),
    Output("stakeholder-filter", "options"),
    Output("category-filter", "value"),
    Output("subcategory-filter", "value"),
    Output("location-filter", "value"),
    Output("stakeholder-filter", "value"),
    Input("category-filter", "value"),
    Input("subcategory-filter", "value"),
    Input("location-filter", "value"),
    Input("stakeholder-filter", "value"),
)
def sync_filter_options(categories, subcategories, locations, stakeholders):
    filtered_df = apply_filters(df_all, categories, subcategories, locations, stakeholders)
    category_opts = sorted(filtered_df["Category"].dropna().unique())
    subcategory_opts = sorted(filtered_df["Sub-Category"].dropna().unique())
    location_opts = sorted({v for t in filtered_df["location_tokens"] for v in t})
    stakeholder_opts = sorted({v for t in filtered_df["stakeholder_tokens"] for v in t})
    categories = [v for v in categories or [] if v in category_opts] or None
    subcategories = [v for v in subcategories or [] if v in subcategory_opts] or None
    locations = [v for v in locations or [] if v in location_opts] or None
    stakeholders = [v for v in stakeholders or [] if v in stakeholder_opts] or None
    return category_opts, subcategory_opts, location_opts, stakeholder_opts, categories, subcategories, locations, stakeholders

# =========================================================
# CLEAR FILTERS
# =========================================================
@app.callback(
    Output("category-filter", "value", allow_duplicate=True),
    Output("subcategory-filter", "value", allow_duplicate=True),
    Output("location-filter", "value", allow_duplicate=True),
    Output("stakeholder-filter", "value", allow_duplicate=True),
    Input("clear-filters", "n_clicks"),
    prevent_initial_call=True,
)
def clear_filters(_):
    return None, None, None, None

# =========================================================
# MAIN RENDER
# =========================================================
@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "value"),
    Input("category-filter", "value"),
    Input("subcategory-filter", "value"),
    Input("location-filter", "value"),
    Input("stakeholder-filter", "value"),
)
def render_tab(tab, categories, subcategories, locations, stakeholders):
    filtered_all = apply_filters(df_all, categories, subcategories, locations, stakeholders)

    if tab == "dashboard":
        filtered_images = filtered_all[filtered_all["has_image"]]
        return html.Div([
            html.Img(
                src=f"/assets/{i}.png",
                style={"width": "100%", "marginBottom": "24px"}
            )
            for i in filtered_images["ID"]
        ])

    elif tab == "initiatives":
        return dag.AgGrid(
            className="ag-theme-alpine",
            columnDefs=[
                {"headerName": "Initiative", "field": "Initiative", "autoHeight": True, "minWidth": 300, "flex": 1},
                {"headerName": "Category", "field": "Category", "autoHeight": True, "minWidth": 160},
                {"headerName": "Location Identified", "field": "Location Identified", "autoHeight": True, "minWidth": 160},
                {"headerName": "Timeline", "field": "Timeline", "width": 130},
            ],
            rowData=filtered_all.to_dict("records"),
            defaultColDef={
                "resizable": True,
                "sortable": True,
                "wrapText": True,
                "autoHeight": True,
                "cellStyle": {"whiteSpace": "normal", "lineHeight": "1.4"}
            },
            dashGridOptions={"domLayout": "normal", "rowHeight": 72},
            style={"height": "520px"},
        )

    elif tab == "tracking":
        return dag.AgGrid(
            className="ag-theme-alpine",
            columnDefs=[
                {"headerName": "Initiative", "field": "Initiative", "autoHeight": True, "minWidth": 230, "flex": 1},
                {"headerName": "Category", "field": "Category", "width": 120},
                {"headerName": "NB", "field": "NB Status", "width": 80, "cellStyle": status_style},
                {"headerName": "NS", "field": "NS Status", "width": 80, "cellStyle": status_style},
                {"headerName": "PEI", "field": "PEI Status", "width": 80, "cellStyle": status_style},
                {"headerName": "NL", "field": "NL Status", "width": 80, "cellStyle": status_style},
                {"headerName": "Regional", "field": "Regional", "width": 100, "cellStyle": status_style},
                {"headerName": "Metric Notes", "field": "Metric Notes", "autoHeight": True, "minWidth": 140, "flex": 1},
            ],
            rowData=filtered_all.to_dict("records"),
            defaultColDef={
                "resizable": True,
                "wrapText": True,
                "autoHeight": True,
                "cellStyle": {"whiteSpace": "normal", "lineHeight": "1.4"}
            },
            dashGridOptions={"rowHeight": 72, "domLayout": "normal"},
            style={"height": "520px"},
        )

# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    app.run(debug=True)
