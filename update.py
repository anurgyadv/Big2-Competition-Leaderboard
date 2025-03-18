import os
import re
import pandas as pd
import requests
import zipfile
import time
import subprocess
from datetime import datetime

def login():
    login_url = '/api/token/'
    login_payload = {
        'team_name': 'Team Horizon',  # Replace with your team name
        'password': 'Password@123'    # Replace with your password
    }
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    response = requests.post(login_url, json=login_payload, headers=headers)
    if response.ok:
        return response.json().get('access')
    else:
        raise Exception(f"Login failed: {response.status_code}")

def download_logs(auth_token):
    download_url = 'https://bigtwo.codersforcauses.org/api/download_logs_zip/'
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'User-Agent': 'Mozilla/5.0'
    }
    response = requests.get(download_url, headers=headers)
    if response.ok:
        with open('all_logs.zip', 'wb') as f:
            f.write(response.content)
        with zipfile.ZipFile('all_logs.zip', 'r') as zip_ref:
            zip_ref.extractall('extracted_logs')
        os.remove('all_logs.zip')
    else:
        raise Exception(f"Failed to download logs: {response.status_code}")

# Data processing functions
card_rank_map = {'3': 1, '4': 2, '5': 3, '6': 4, '7': 5, '8': 6, '9': 7, 'T': 8, 'J': 9, 'Q': 10, 'K': 11, 'A': 12, '2': 13}

def calculate_hand_features(hand):
    suits = {'C': [], 'D': [], 'H': [], 'S': []}
    values = []
    sorted_hand = sorted(hand, key=lambda x: (card_rank_map[x[:-1]], x[-1]))
    for card in sorted_hand:
        value, suit = card[:-1], card[-1]
        values.append(card_rank_map[value])
        suits[suit].append(card_rank_map[value])
    
    flushes = sum(1 for cards in suits.values() if len(cards) >= 5)
    
    def is_straight(values):
        values = sorted(set(values))
        for i in range(len(values) - 4):
            if values[i:i+5] == list(range(values[i], values[i]+5)):
                return True
        return False
    
    no_of_straights = 1 if is_straight(values) else 0
    no_of_straightflush = sum(1 for suit_cards in suits.values() if len(suit_cards) >= 5 and is_straight(suit_cards))
    pairs = len([v for v in values if values.count(v) == 2]) // 2
    three_of_a_kind = len([v for v in values if values.count(v) == 3]) // 3
    four_of_a_kind = len([v for v in values if values.count(v) == 4]) // 4
    cards_outside_combination = len([card for card in sorted_hand if values.count(card_rank_map[card[:-1]]) == 1])

    return {
        'no_of_flushes': flushes,
        'no_of_pairs': pairs,
        'three_of_a_kind': three_of_a_kind,
        'four_of_a_kind': four_of_a_kind,
        'no_of_straights': no_of_straights,
        'no_of_straightflush': no_of_straightflush,
        'cards_outside_combination': cards_outside_combination
    }

def filter_game_results(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    game_results = []
    current_game_results = []
    current_game_no = 1
    
    for line in lines:
        if "finished with" in line:
            current_game_results.append(line.strip())
        elif "Engine: Starting Game" in line:
            if current_game_results:
                game_results.append((current_game_no, current_game_results))
                current_game_results = []
            current_game_no += 1
    
    if current_game_results:
        game_results.append((current_game_no, current_game_results))

    return game_results

def parse_team_hand(lines, team_name):
    for line in lines:
        if f"{team_name}: You were dealt" in line:
            hand = re.findall(r'\[(.*?)\]', line)
            if hand:
                return hand[0].replace("'", "").split(', ')
    return []

def calculate_rank(results):
    sorted_results = sorted(results.items(), key=lambda x: x[1]['total_points'], reverse=True)
    ranks = {player: idx + 1 for idx, (player, _) in enumerate(sorted_results)}
    return ranks

def process_log_file(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
        
    game_results = filter_game_results(file_path)
    cumulative_scores = {}
    all_team_results = []

    for game_no, results in game_results:
        current_game = {}
        
        for result in results:
            match = re.search(r'Engine: (.*) finished with (\d+) cards in hand. They are now on (-?\d+) points', result)
            if match:
                player = match.group(1)
                cards_left = int(match.group(2))
                points = int(match.group(3))

                game_points = cumulative_scores.get(player, 0) + points
                current_game[player] = {'cards_left': cards_left, 'game_points': points, 'total_points': game_points}
                cumulative_scores[player] = game_points
        
        ranks = calculate_rank(current_game)
        
        for player in current_game.keys():
            hand = parse_team_hand(lines, player)
            hand_features = calculate_hand_features(hand) if hand else {}
            all_team_results.append({
                'game_no': game_no,
                'team_name': player,
                'hand': hand,
                'rank': ranks.get(player, None),
                'cards_left': current_game[player]['cards_left'],
                'game_points': current_game[player]['game_points'],
                'total_points': current_game[player]['total_points'],
                'timestamp': datetime.now(),
                **hand_features
            })

    return all_team_results

def process_data(log_folder):
    all_results = []
    for file in os.listdir(log_folder):
        if file.startswith('Log'):
            file_path = os.path.join(log_folder, file)
            all_results.extend(process_log_file(file_path))
    
    df = pd.DataFrame(all_results)
    
    wins_df = df[df['rank'] == 1].groupby('team_name').size().reset_index(name='wins')
    leaderboard_df = df.groupby('team_name')['game_points'].sum().reset_index(name='total_points')
    leaderboard_df = leaderboard_df.sort_values('total_points', ascending=False).reset_index(drop=True)
    leaderboard_df['rank'] = leaderboard_df.index + 1
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    wins_df.to_csv(f'data/processed/wins_{timestamp}.csv', index=False)
    leaderboard_df.to_csv(f'data/processed/leaderboard_{timestamp}.csv', index=False)
    
    for file in os.listdir(log_folder):
        os.remove(os.path.join(log_folder, file))

def push_to_github():
    try:
        subprocess.run(["git", "add", "data/processed/*.csv"], check=True)
        commit_message = f"Update data {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push"], check=True)
        print("Successfully pushed to GitHub")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while pushing to GitHub: {e}")

def main():
    while True:
        try:
            print("Starting data update process...")
            auth_token = login()
            download_logs(auth_token)
            process_data('extracted_logs')
            push_to_github()
            print("Data update complete. Waiting for next cycle...")
            time.sleep(1200)  # Wait for 20 minutes
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Retrying in 5 minutes...")
            time.sleep(300)  # Wait for 5 minutes before retrying

if __name__ == "__main__":
    main()