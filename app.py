import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

def load_latest_data(data_type):
    data_folder = 'data/processed'
    files = [f for f in os.listdir(data_folder) if f.startswith(data_type)]
    if not files:
        return None
    latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(data_folder, x)))
    return pd.read_csv(os.path.join(data_folder, latest_file))

def filter_data(df, time_filter):
    now = datetime.now()
    if time_filter == 'Last 30 minutes':
        threshold = now - timedelta(minutes=30)
    elif time_filter == 'Last 1 hour':
        threshold = now - timedelta(hours=1)
    else:  # All time
        return df
    return df[df['timestamp'] > threshold]

def calculate_point_increase(current_df, previous_df):
    if previous_df is None:
        return pd.Series([0] * len(current_df))
    merged = current_df.merge(previous_df, on='team_name', suffixes=('_current', '_previous'))
    return merged['points_current'] - merged['points_previous']

def main():
    st.title("Big Two Game Statistics")

    # Load data
    wins_df = load_latest_data('wins')
    leaderboard_df = load_latest_data('leaderboard')

    if wins_df is not None and leaderboard_df is not None:
        # Time filter selection
        time_filter = st.selectbox("Select time range", ["All time", "Last 1 hour", "Last 30 minutes"])

        # Filter data based on time selection
        filtered_wins = filter_data(wins_df, time_filter)
        filtered_leaderboard = filter_data(leaderboard_df, time_filter)

        # Calculate point increase
        previous_wins = load_latest_data('wins_previous')  # You need to save the previous state
        previous_leaderboard = load_latest_data('leaderboard_previous')  # You need to save the previous state
        wins_increase = calculate_point_increase(filtered_wins, previous_wins)
        leaderboard_increase = calculate_point_increase(filtered_leaderboard, previous_leaderboard)

        # Display Wins Table
        st.header("Wins Table")
        st.dataframe(pd.concat([filtered_wins, wins_increase.rename('Win Increase')], axis=1))

        # Display Leaderboard
        st.header("Leaderboard")
        st.dataframe(pd.concat([filtered_leaderboard, leaderboard_increase.rename('Point Increase')], axis=1))

        # Display update timer
        last_update = datetime.fromtimestamp(os.path.getmtime(os.path.join('data/processed', max(os.listdir('data/processed')))))
        next_update = last_update + timedelta(minutes=20)
        st.write(f"Last updated: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"Next update in: {(next_update - datetime.now()).seconds // 60} minutes")
    else:
        st.error("Failed to load data. Please check your data directory.")

if __name__ == "__main__":
    main()