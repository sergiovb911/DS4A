#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# Import libraries
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import dash_table
from sqlalchemy import create_engine
import os

user = 'nps_demo_user'
password = 'realmadrid911'
engine = create_engine('postgresql://'+user+':'+password+'@nps-demo-instance.cbm3nqgz4vsm.us-east-2.rds.amazonaws.com/nps_demo_db')
df = pd.read_sql("SELECT * from trades", engine.connect(), parse_dates=('Entry time'))

# Import dataset
df = pd.read_csv("aggr.csv", parse_dates=['Entry time'])
df['YearMonth'] = df['Entry time'].dt.strftime('%Y-%m')

def filter_df(df, exchange, margin, start_date, end_date):

    dff = df[(df['Exchange'] == exchange) & 
                 (df['Margin'] == int(margin)) & 
                 (df['Entry time'] > start_date) & 
                 (df['Entry time'] <= end_date)]
    return dff

# Initial dash configuration
app = dash.Dash(__name__,
                external_stylesheets=[
                    'https://codepen.io/uditagarwal/pen/oNvwKNP.css',
                    'https://codepen.io/uditagarwal/pen/YzKbqyV.css'
                ])

# Configuration of the layout
app.layout = html.Div(children=[
    html.Div(children=[
        html.H2(children="Bitcoin Leveraged Trading Backtest Analysis",
                className="h2.tittle")
    ],
             className="study-browser-banner row"),
    html.Div(
        className="row app-body",
        children=[
            html.Div(
                className="twelve columns card",
                children=[
                    html.Div(
                        className="padding row",
                        children=[
                            html.Div( #Component 1 (Exhange)
                                className="two columns card",
                                children=[
                                    html.H6("Select Exchange"),
                                    dcc.RadioItems(
                                        id="exchange-select",
                                        options=[{
                                            "label": label,
                                            "value": label
                                        } for label in df["Exchange"].unique()
                                                 ],
                                        value="Bitmex",
                                        labelStyle={"display": "inline-block"})
                                    ]),
                            
                            html.Div(   #Component 2 (Leverage)
                                className="two columns card 2",
                                children=[
                                    html.H6("Select Leverage"),
                                    dcc.RadioItems(
                                        id="leverage-select",
                                        options=[{
                                            "label": str(label),
                                            "value": str(label)
                                        } for label in df["Margin"].unique()],
                                        value="1",
                                        labelStyle={"display": "inline-block"})
                                    ]),
                            
                            html.Div(  #Component 3 (Date)
                                className="three columns card",
                                children=[
                                    html.H6("Select date range "),
                                    dcc.DatePickerRange(id='date-range-select',
                                        start_date=df["Entry time"].min(),
                                        end_date= df["Entry time"].min(), 
                                        display_format='MMM YY')
                                    ]),
                            
                            
                             html.Div(
                                id="strat-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-returns", className="indicator_value"),
                                    html.P('Strategy Returns', className="twelve columns indicator_text"),
                                    ]),
                            
                            html.Div(
                                id="market-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="market-returns", className="indicator_value"),
                                    html.P('Market Returns', className="twelve columns indicator_text"),
                                    ]),
                            
                            html.Div(
                                id="strat-vs-market-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-vs-market", className="indicator_value"),
                                    html.P('Strategy vs. Market Returns', className="twelve columns indicator_text"),
                                    ])
                            

                                ])
                    
                        ]),
            #Monthly chart
            html.Div(
            className="twelve columns card",
            children=[
                dcc.Graph(
                    id="monthly-chart",
                    figure={'data': []}
                )
            ]),
            
            #
            html.Div(
            className="padding row",
                children=[
                    html.Div( #Data Table
                        className="six columns card",
                        children=[
                            dash_table.DataTable(
                                id='table',
                                columns=[
                                    {'name': 'Number', 'id': 'Number'},
                                    {'name': 'Trade type', 'id': 'Trade type'},
                                    {'name': 'Exposure', 'id': 'Exposure'},
                                    {'name': 'Entry balance', 'id': 'Entry balance'},
                                    {'name': 'Exit balance', 'id': 'Exit balance'},
                                    {'name': 'Pnl (incl fees)', 'id': 'Pnl (incl fees)'},
                                ],
                                style_cell={'width': '50px'},
                                style_table={
                                    'maxHeight': '450px',
                                    'overflowY': 'scroll'
                                },
                            )
                        ]
                    ),
                    dcc.Graph( #Graph PNL
                        id="pnl-types",
                        className="six columns card",
                        figure={
                        'data': []
                        }
                    )
                ]
            ),
            
            html.Div(
            className="padding row",
                children=[
                    dcc.Graph(
                        id="daily-btc",
                        className="six columns card",
                        figure={
                        'data': []
                        }
                    ),
                    dcc.Graph(
                        id="balance",
                        className="six columns card",
                        figure={
                        'data': []
                        }
                    )
                ]
            )
            
            
            
        ])
])

#Functions




def calc_returns_over_month(dff):
    out = []

    for name, group in dff.groupby('YearMonth'):
        exit_balance = group.head(1)['Exit balance'].values[0]
        entry_balance = group.tail(1)['Entry balance'].values[0]
        monthly_return = (exit_balance*100 / entry_balance)-100
        out.append({
            'month': name,
            'entry': entry_balance,
            'exit': exit_balance,
            'monthly_return': monthly_return
        })
    return out


def calc_btc_returns(dff):
    btc_start_value = dff.tail(1)['BTC Price'].values[0]
    btc_end_value = dff.head(1)['BTC Price'].values[0]
    btc_returns = (btc_end_value * 100/ btc_start_value)-100
    return btc_returns

def calc_strat_returns(dff):
    start_value = dff.tail(1)['Exit balance'].values[0]
    end_value = dff.head(1)['Entry balance'].values[0]
    returns = (end_value * 100/ start_value)-100
    return returns

def pnl_by_type(df, exchange, margin, start_date, end_date):
    data = []
    dff = filter_df(df, exchange, margin, start_date, end_date)

    for name, group in df.groupby('Trade type'):
        grouped = group.groupby('Entry time', as_index=False).mean()
        data.append(
            go.Bar(x=grouped['Entry time'], y=grouped['Pnl (incl fees)'], name=name)
        )
    return data



#Callbacks 


@app.callback([dash.dependencies.Output('date-range-select', 'start_date'),
               dash.dependencies.Output('date-range-select', 'end_date')], 
            [dash.dependencies.Input('exchange-select', 'value'),]             )
                            
def update_startdate (exchange):
    dff_date = df[df['Exchange'] == exchange] # We filter our dataset for the exchange
    
    return dff_date["Entry time"].min(),dff_date["Entry time"].max()



@app.callback(
    [
        dash.dependencies.Output('monthly-chart', 'figure'),
        dash.dependencies.Output('market-returns', 'children'),
        dash.dependencies.Output('strat-returns', 'children'),
        dash.dependencies.Output('strat-vs-market', 'children'),
    ],
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range-select', 'start_date'),
        dash.dependencies.Input('date-range-select', 'end_date'),

    )
)
def update_monthly(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    data = calc_returns_over_month(dff)
    btc_returns = calc_btc_returns(dff)
    strat_returns = calc_strat_returns(dff)
    strat_vs_market = strat_returns - btc_returns

    return {
        'data': [
            go.Candlestick(
                open=[each['entry'] for each in data],
                close=[each['exit'] for each in data],
                x=[each['month'] for each in data],
                low=[each['entry'] for each in data],
                high=[each['exit'] for each in data]
            )
        ],
        'layout': {
            'title': 'Overview of Monthly performance'
        }
    }, f'{btc_returns:0.2f}%', f'{strat_returns:0.2f}%', f'{strat_vs_market:0.2f}%'


@app.callback(
    dash.dependencies.Output('table', 'data'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range-select', 'start_date'),
        dash.dependencies.Input('date-range-select', 'end_date'),
    )
)

def update_table(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    return dff.to_dict('records')

@app.callback(
    dash.dependencies.Output('pnl-types', 'figure'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range-select', 'start_date'),
        dash.dependencies.Input('date-range-select', 'end_date'),
    )
)

def update_pnl(exchange, leverage, start_date, end_date):
    return {
        'data': pnl_by_type(df,exchange, leverage, start_date, end_date),
        'layout': {
            'title': 'PnL vs Trade type',
            'height': 400
        }
    }


@app.callback(
    dash.dependencies.Output('daily-btc', 'figure'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range-select', 'start_date'),
        dash.dependencies.Input('date-range-select', 'end_date'),
    )
)

def update_btc(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    return {
        'data': [go.Scatter(x=dff['Entry time'], y=dff['BTC Price'])],
        'layout': {
            'title': 'Daily BTC Price',
            'height': 400
        }
    }
    
@app.callback(
    dash.dependencies.Output('balance', 'figure'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range-select', 'start_date'),
        dash.dependencies.Input('date-range-select', 'end_date'),
    )
)

def update_balance(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    return {
        'data': [go.Scatter(x=dff['Entry time'], y=dff['Exit balance'])],
        'layout': {
            'title': 'Balance overtime',
            'height': 400
        }
    }
    


if __name__ == "__main__":
    app.run_server(debug=True)

    


# In[ ]:




