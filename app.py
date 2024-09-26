import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px

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

# Load data functions (keep as they were)

def create_bar_chart(df, x, y, title):
    fig = px.bar(df, x=x, y=y, title=title)
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=14)
    )
    return fig

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

    else:
        st.error("Failed to load data. Please check your data directory.")

if __name__ == "__main__":
    main()