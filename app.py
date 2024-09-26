import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# Set page config
st.set_page_config(page_title="Big Two Game Statistics", page_icon="🃏", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6
    }
    .big-font {
        font-size:30px !important;
        font-weight: bold;
    }
    .medium-font {
        font-size:20px !important;
        font-weight: bold;
    }
    .small-font {
        font-size:14px !important;
    }
    .stDataFrame {
        font-size:20px !important;
    }
    .css-1hverof {   /* Style header background */
        background-color: #4e8cff;
        border-radius: 10px;
        padding: 20px;
        color: white !important;
    }
    .css-18e3th9 {  /* Reduce content width */
        padding-top: 0rem;
        padding-bottom: 10rem;
        padding-left: 5rem;
        padding-right: 5rem;
    }
    .css-1d391kg {  /* Style metric boxes */
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

def load_latest_data(data_type):
    data_folder = 'data/processed'
    files = [f for f in os.listdir(data_folder) if f.startswith(data_type)]
    if not files:
        return None
    latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(data_folder, x)))
    df = pd.read_csv(os.path.join(data_folder, latest_file))
    # Add timestamp based on file modification time
    df['timestamp'] = pd.to_datetime(os.path.getmtime(os.path.join(data_folder, latest_file)), unit='s')
    return df

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
    if previous_df is None or current_df is None:
        return pd.Series([0] * len(current_df)) if current_df is not None else pd.Series()
    merged = current_df.merge(previous_df, on='team_name', suffixes=('_current', '_previous'))
    return merged['total_points_current'] - merged['total_points_previous']

def main():
    st.markdown('<p class="big-font">🃏 Big Two Game Statistics</p>', unsafe_allow_html=True)

    # Load data
    wins_df = load_latest_data('wins')
    leaderboard_df = load_latest_data('leaderboard')

    if wins_df is not None and leaderboard_df is not None:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<p class="medium-font">Select time range</p>', unsafe_allow_html=True)
            time_filter = st.selectbox("", ["All time", "Last 1 hour", "Last 30 minutes"])
        
        with col2:
            last_update = datetime.fromtimestamp(os.path.getmtime(os.path.join('data/processed', max(os.listdir('data/processed')))))
            st.markdown('<p class="medium-font">Last updated</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="small-font">{last_update.strftime("%Y-%m-%d %H:%M:%S")}</p>', unsafe_allow_html=True)
        
        with col3:
            next_update = last_update + timedelta(minutes=20)
            st.markdown('<p class="medium-font">Next update in</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="small-font">{(next_update - datetime.now()).seconds // 60} minutes</p>', unsafe_allow_html=True)

        # Filter and process data
        filtered_wins = filter_data(wins_df, time_filter).sort_values('wins', ascending=False)
        filtered_leaderboard = filter_data(leaderboard_df, time_filter).sort_values('total_points', ascending=False)
        
        previous_wins = load_latest_data('wins_previous')
        previous_leaderboard = load_latest_data('leaderboard_previous')
        wins_increase = calculate_point_increase(filtered_wins, previous_wins)
        leaderboard_increase = calculate_point_increase(filtered_leaderboard, previous_leaderboard)

        # Display Wins Table and Chart
        st.markdown('<p class="medium-font">Wins Table</p>', unsafe_allow_html=True)
        col1, col2 = st.columns([2, 3])
        with col1:
            display_wins = filtered_wins.copy()
            display_wins['Win Increase'] = wins_increase
            st.dataframe(display_wins[['team_name', 'wins', 'Win Increase']], height=400)
        with col2:
            st.bar_chart(filtered_wins.set_index('team_name')['wins'])

        # Display Leaderboard and Chart
        st.markdown('<p class="medium-font">Leaderboard</p>', unsafe_allow_html=True)
        col1, col2 = st.columns([2, 3])
        with col1:
            display_leaderboard = filtered_leaderboard.copy()
            display_leaderboard['Point Increase'] = leaderboard_increase
            st.dataframe(display_leaderboard[['rank', 'team_name', 'total_points', 'Point Increase']], height=400)
        with col2:
            st.bar_chart(filtered_leaderboard.set_index('team_name')['total_points'])

    else:
        st.error("Failed to load data. Please check your data directory.")

if __name__ == "__main__":
    main()