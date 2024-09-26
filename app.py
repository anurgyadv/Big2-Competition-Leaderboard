import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px
import time

# Set page config
st.set_page_config(page_title="Big Two Game Statistics", page_icon="🃏", layout="wide")

# Custom CSS
st.markdown("""
<style>
    /* Your custom CSS here */
</style>
""", unsafe_allow_html=True)

# Load data functions (as before)
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
    
def create_bar_chart(df, x, y, title):
    fig = px.bar(df, x=x, y=y, title=title)
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=14)
    )
    return fig

# Function to refresh data every 20 minutes
def auto_refresh():
    # Set the interval in seconds (20 minutes = 1200 seconds)
    refresh_interval = 1200  # 20 minutes
    
    # This will reload the page after the set interval
    time.sleep(refresh_interval)
    st.experimental_rerun()

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
            st.plotly_chart(create_bar_chart(filtered_wins, 'team_name', 'wins', 'Wins by Team'), use_container_width=True)

        # Display Leaderboard and Chart
        st.markdown('<p class="medium-font">Leaderboard</p>', unsafe_allow_html=True)
        col1, col2 = st.columns([2, 3])
        with col1:
            display_leaderboard = filtered_leaderboard.copy()
            display_leaderboard['Point Increase'] = leaderboard_increase
            st.dataframe(display_leaderboard[['rank', 'team_name', 'total_points', 'Point Increase']], height=400)
        with col2:
            st.plotly_chart(create_bar_chart(filtered_leaderboard, 'team_name', 'total_points', 'Total Points by Team'), use_container_width=True)

        # Trigger auto-refresh every 20 minutes
        auto_refresh()

    else:
        st.error("Failed to load data. Please check your data directory.")

if __name__ == "__main__":
    main()
