import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# Set page config
st.set_page_config(page_title="Big Two Game Statistics", page_icon="🃏", layout="wide")

def load_latest_data(data_type):
    data_folder = 'data/processed'
    files = [f for f in os.listdir(data_folder) if f.startswith(data_type)]
    if not files:
        return None
    latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(data_folder, x)))
    df = pd.read_csv(os.path.join(data_folder, latest_file))
    df['timestamp'] = pd.to_datetime(os.path.getmtime(os.path.join(data_folder, latest_file)), unit='s')
    return df

def filter_data(df, time_filter):
    if time_filter == 'All time':
        return df
    now = datetime.now()
    threshold = now - timedelta(hours=1 if time_filter == 'Last 1 hour' else 0.5)
    return df[df['timestamp'] > threshold]

def main():
    st.title("🃏 Big Two Game Statistics")

    wins_df = load_latest_data('wins')
    leaderboard_df = load_latest_data('leaderboard')

    if wins_df is not None and leaderboard_df is not None:
        time_filter = st.selectbox("Select time range", ["All time", "Last 1 hour", "Last 30 minutes"])

        last_update = datetime.fromtimestamp(os.path.getmtime(os.path.join('data/processed', max(os.listdir('data/processed')))))
        st.write(f"Last updated: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        next_update = last_update + timedelta(minutes=20)
        st.write(f"Next update in: {(next_update - datetime.now()).seconds // 60} minutes")

        filtered_wins = filter_data(wins_df, time_filter).sort_values('wins', ascending=False)
        filtered_leaderboard = filter_data(leaderboard_df, time_filter).sort_values('total_points', ascending=False)

        st.header("Wins Table")
        st.dataframe(filtered_wins[['team_name', 'wins']], height=400)

        st.header("Leaderboard")
        st.dataframe(filtered_leaderboard[['rank', 'team_name', 'total_points']], height=400)

    else:
        st.error("Failed to load data. Please check your data directory.")

if __name__ == "__main__":
    main()