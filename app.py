"""
Streamlit App for ENG vs IND Full Series Analysis
------------------------------------------------

This application loads ball-by-ball cricket data from the ENG vs IND series
and provides interactive visualizations and summaries. Users can filter
by innings, players, bowlers and over range using sidebar widgets. The
app then displays key metrics such as total runs, wickets, boundaries and
sixes, and generates charts to highlight runs scored per over, top run
scorers, and top wicket takers. A detailed ball-by-ball table is also
available for further exploration.

To run this application, install Streamlit (if not already installed)
and execute `streamlit run app.py` from the command line.
"""

import streamlit as st
import pandas as pd
import altair as alt
from typing import List


@st.cache_data(show_spinner=True)
def load_data(file_path: str) -> pd.DataFrame:
    """Load the cricket data from a CSV file and pre-process it.

    This function is cached by Streamlit to avoid reloading the data on
    every interaction. It fills missing values in the `runsScored` column
    with zeros and creates an `is_wicket` column that flags whether a
    dismissal occurred on each delivery.

    Args:
        file_path: Path to the CSV file containing ball-by-ball data.

    Returns:
        A pandas DataFrame with the processed data.
    """
    df = pd.read_csv(file_path)

    # Ensure runsScored is numeric and fill NaNs with 0 for aggregation
    if 'runsScored' in df.columns:
        df['runsScored'] = pd.to_numeric(df['runsScored'], errors='coerce').fillna(0)
    else:
        # If runsScored column is missing, fall back to runs column
        df['runsScored'] = pd.to_numeric(df.get('runs', 0), errors='coerce').fillna(0)

    # Flag whether a wicket fell on this ball. Consider all cases where
    # appealDismissalTypeId is not 'NotOut' or related variants as a wicket.
    dismissal_col = 'appealDismissalTypeId'
    def flag_wicket(val: str) -> int:
        if pd.isna(val):
            return 0
        # Treat any NotOut variants or 'Null' as no wicket
        not_out_values = {"NotOut", "NotOut1stUmpire", "NotOut2ndUmpire",
                          "NotOut3rdUmpire", "Null"}
        return 0 if str(val) in not_out_values else 1

    df['is_wicket'] = df[dismissal_col].apply(flag_wicket)

    return df


def filter_data(
    df: pd.DataFrame,
    innings: List[int],
    batting_players: List[str],
    bowlers: List[str],
    over_range: tuple,
) -> pd.DataFrame:
    """Apply user-selected filters to the DataFrame.

    Args:
        df: The full ball-by-ball DataFrame.
        innings: List of innings numbers to include.
        batting_players: List of batting players to include; empty list means
            no filtering on batting players.
        bowlers: List of bowlers to include; empty list means no filtering on bowlers.
        over_range: Tuple (min_over, max_over) specifying the over number range.

    Returns:
        A DataFrame filtered according to the selections.
    """
    # Filter by innings
    filtered = df[df['inningNumber'].isin(innings)]

    # Filter by batting players if any selected
    if batting_players:
        filtered = filtered[filtered['battingPlayer'].isin(batting_players)]

    # Filter by bowlers if any selected
    if bowlers:
        filtered = filtered[filtered['bowlerPlayer'].isin(bowlers)]

    # Filter by over range
    min_over, max_over = over_range
    filtered = filtered[(filtered['overNumber'] >= min_over) & (filtered['overNumber'] <= max_over)]

    return filtered


def display_metrics(df: pd.DataFrame) -> None:
    """Display key cricket metrics in a row of Streamlit metric widgets.

    Args:
        df: Filtered DataFrame for which metrics will be calculated.
    """
    total_runs = int(df['runsScored'].sum())
    total_wickets = int(df['is_wicket'].sum())
    boundaries = int((df['runsScored'] == 4).sum())
    sixes = int((df['runsScored'] == 6).sum())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Runs", f"{total_runs}")
    col2.metric("Wickets", f"{total_wickets}")
    col3.metric("Boundaries (4s)", f"{boundaries}")
    col4.metric("Sixes (6s)", f"{sixes}")


def main() -> None:
    """Main entry point for the Streamlit app."""
    st.set_page_config(page_title="ENG vs IND Series Analysis", layout="wide")
    st.title("ENG vs IND Full Series Analysis")
    st.markdown(
        """
        Explore ball-by-ball data from the England vs India cricket series.
        Use the sidebar filters to narrow down the data by innings, players,
        bowlers, and over ranges. Below you will find summary metrics,
        visualizations, and a detailed table of the selected deliveries.
        """
    )

    # Load data once
    data_path = "ENG vs IND Full Series.csv"
    df = load_data(data_path)

    # Sidebar filters
    with st.sidebar:
        st.header("Filters")
        # Innings selection
        innings_options = sorted(df['inningNumber'].unique())
        default_innings = innings_options.copy()  # select all by default
        selected_innings = st.multiselect(
            "Select Innings", options=innings_options, default=default_innings
        )

        # Batting players selection
        batting_players_options = sorted(df['battingPlayer'].dropna().unique())
        selected_batting_players = st.multiselect(
            "Select Batting Players", options=batting_players_options, default=[]
        )

        # Bowling players selection
        bowler_options = sorted(df['bowlerPlayer'].dropna().unique())
        selected_bowlers = st.multiselect(
            "Select Bowlers", options=bowler_options, default=[]
        )

        # Over range slider
        min_over_num = int(df['overNumber'].min())
        max_over_num = int(df['overNumber'].max())
        selected_over_range = st.slider(
            "Select Over Range", min_value=min_over_num, max_value=max_over_num,
            value=(min_over_num, max_over_num)
        )

    # Filter the data based on selections
    filtered_df = filter_data(
        df,
        innings=selected_innings if selected_innings else innings_options,
        batting_players=selected_batting_players,
        bowlers=selected_bowlers,
        over_range=selected_over_range,
    )

    # Display key metrics
    display_metrics(filtered_df)

    # Visualize runs per over
    st.markdown("### Runs per Over")
    runs_per_over = (
        filtered_df.groupby('overNumber')['runsScored']
        .sum()
        .reset_index()
        .rename(columns={'runsScored': 'total_runs'})
    )
    chart1 = (
        alt.Chart(runs_per_over)
        .mark_bar()
        .encode(
            x=alt.X('overNumber:O', title='Over Number'),
            y=alt.Y('total_runs:Q', title='Runs'),
        )
        .properties(title='Total Runs per Over')
    )
    st.altair_chart(chart1, use_container_width=True)

    # Top run scorers
    st.markdown("### Top 10 Run Scorers")
    top_runs = (
        filtered_df.groupby('battingPlayer')['runsScored']
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
        .rename(columns={'runsScored': 'total_runs'})
    )
    chart2 = (
        alt.Chart(top_runs)
        .mark_bar()
        .encode(
            x=alt.X('battingPlayer:N', sort='-y', title='Player'),
            y=alt.Y('total_runs:Q', title='Runs'),
        )
        .properties(title='Top 10 Run Scorers')
    )
    st.altair_chart(chart2, use_container_width=True)

    # Top wicket takers
    st.markdown("### Top 10 Wicket Takers")
    top_wickets = (
        filtered_df.groupby('bowlerPlayer')['is_wicket']
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
        .rename(columns={'is_wicket': 'total_wickets'})
    )
    chart3 = (
        alt.Chart(top_wickets)
        .mark_bar()
        .encode(
            x=alt.X('bowlerPlayer:N', sort='-y', title='Bowler'),
            y=alt.Y('total_wickets:Q', title='Wickets'),
        )
        .properties(title='Top 10 Wicket Takers')
    )
    st.altair_chart(chart3, use_container_width=True)

    # Display ball-by-ball table
    st.markdown("### Ball-by-Ball Data")
    st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)


if __name__ == "__main__":
    main()
