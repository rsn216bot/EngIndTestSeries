
import streamlit as st
import pandas as pd

# Title
st.title("ENG vs IND Series: Batting Analysis App")

# Load the dataset
df = pd.read_csv("ENG vs IND Full Series.csv")

# Sidebar filters
st.sidebar.header("Filters")
batting_players = st.sidebar.multiselect("Select Batting Player(s)", df["battingPlayer"].dropna().unique())
bowling_types = st.sidebar.multiselect("Select Bowling Type(s)", df["bowlingTypeId"].dropna().unique())
bowlers = st.sidebar.multiselect("Select Bowler(s)", df["bowlerPlayer"].dropna().unique())
over_range = st.sidebar.slider("Over Range", 0, int(df["overNumber"].max()), (0, 10))

# Apply filters
filtered_df = df.copy()
if batting_players:
    filtered_df = filtered_df[filtered_df["battingPlayer"].isin(batting_players)]
if bowling_types:
    filtered_df = filtered_df[filtered_df["bowlingTypeId"].isin(bowling_types)]
if bowlers:
    filtered_df = filtered_df[filtered_df["bowlerPlayer"].isin(bowlers)]
filtered_df = filtered_df[(filtered_df["overNumber"] >= over_range[0]) & (filtered_df["overNumber"] <= over_range[1])]

def make_group_table(df, group_by_col):
    group = df.groupby(group_by_col)["runsScored"].agg(["sum", "count"]).reset_index()
    group.columns = [group_by_col, "Total Runs", "Balls Faced"]
    group["Strike Rate"] = round((group["Total Runs"] / group["Balls Faced"]) * 100, 2)
    return group.sort_values(by="Strike Rate", ascending=False)

# Display Tables
st.header("📊 BattingFeetId Summary")
st.dataframe(make_group_table(filtered_df, "battingFeetId"))

st.header("📊 LengthTypeId Summary")
st.dataframe(make_group_table(filtered_df, "lengthTypeId"))

st.header("📊 LineTypeId Summary")
st.dataframe(make_group_table(filtered_df, "lineTypeId"))
