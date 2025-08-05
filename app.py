
import streamlit as st
import pandas as pd
import numpy as np

# Load Data
df = pd.read_csv("ENG vs IND Full Series.csv")

# Sidebar Filters
st.sidebar.header("Filters")

batting_filter = st.sidebar.multiselect("Select Batter(s)", df['battingPlayer'].dropna().unique())
bowling_type_filter = st.sidebar.multiselect("Select Bowling Type", df['bowlingTypeId'].dropna().unique())
bowler_filter = st.sidebar.multiselect("Select Bowler(s)", df['bowlerPlayer'].dropna().unique())
max_over = int(df['overNumber'].max())
over_filter = st.sidebar.slider("Select Over Range", 0, max_over, (0, max_over))

# Apply Filters
filtered_df = df.copy()
if batting_filter:
    filtered_df = filtered_df[filtered_df['battingPlayer'].isin(batting_filter)]
if bowling_type_filter:
    filtered_df = filtered_df[filtered_df['bowlingTypeId'].isin(bowling_type_filter)]
if bowler_filter:
    filtered_df = filtered_df[filtered_df['bowlerPlayer'].isin(bowler_filter)]
filtered_df = filtered_df[(filtered_df['overNumber'] >= over_filter[0]) & (filtered_df['overNumber'] <= over_filter[1])]

# Helper: calculate False Shot %
def false_shot_percentage(df):
    false_shots = df[~df['battingConnectionId'].isin(['wellTimed', 'Blank', 'Left', 'Middled'])].shape[0]
    total_balls = df.shape[0]
    return round((false_shots / total_balls) * 100, 2) if total_balls > 0 else 0

# Stats table function
def create_stats_table(df, group_col):
    table = df.groupby(group_col).agg(
        Total_Runs=('runsScored', 'sum'),
        Balls_Faced=('runsScored', 'count')
    ).reset_index()
    table['Strike_Rate'] = (table['Total_Runs'] / table['Balls_Faced'] * 100).round(2)
    table['False_Shot_%'] = table[group_col].apply(lambda x: false_shot_percentage(df[df[group_col] == x]))
    return table.sort_values(by='Strike_Rate', ascending=False)

st.title("ENG vs IND Streamlit Analysis")

# Table: Batting Feet ID
st.subheader("Batting Feet ID Stats")
st.dataframe(create_stats_table(filtered_df, 'battingFeetId'))

# Tabs for Matrix views
st.subheader("LengthTypeId vs LineTypeId Matrix Views")
tab1, tab2, tab3 = st.tabs(["Strike Rate View", "False Shot % View", "Combined Heatmap"])

matrix = filtered_df.groupby(['lengthTypeId', 'lineTypeId']).agg(
    Total_Runs=('runsScored', 'sum'),
    Balls_Faced=('runsScored', 'count')
).reset_index()
matrix['Strike_Rate'] = (matrix['Total_Runs'] / matrix['Balls_Faced'] * 100).round(2)
matrix['False_Shot_%'] = matrix.apply(lambda r: false_shot_percentage(
    filtered_df[(filtered_df['lengthTypeId'] == r['lengthTypeId']) & (filtered_df['lineTypeId'] == r['lineTypeId'])]
), axis=1)

matrix_sr = matrix.pivot(index='lengthTypeId', columns='lineTypeId', values='Strike_Rate')
matrix_fs = matrix.pivot(index='lengthTypeId', columns='lineTypeId', values='False_Shot_%')

with tab1:
    st.write("**Strike Rate (Green Gradient)**")
    st.dataframe(matrix_sr.style.background_gradient(cmap='Greens', axis=None))

with tab2:
    st.write("**False Shot % (Red Gradient)**")
    st.dataframe(matrix_fs.style.background_gradient(cmap='Reds', axis=None))

with tab3:
    combined = (matrix_sr - matrix_sr.min().min()) / (matrix_sr.max().max() - matrix_sr.min().min()) - (matrix_fs - matrix_fs.min().min()) / (matrix_fs.max().max() - matrix_fs.min().min())
    st.write("**Combined Heatmap (Green=High SR, Red=High False Shots)**")
    st.dataframe(combined.style.background_gradient(cmap='RdYlGn', axis=None))

# Table: Batting Shot Type ID
st.subheader("Batting Shot Type ID Stats")
st.dataframe(create_stats_table(filtered_df, 'battingShotTypeId'))

# Table: Bowling Detail ID
st.subheader("Bowling Detail ID Stats")
st.dataframe(create_stats_table(filtered_df, 'bowlingDetailId'))
