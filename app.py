import os
import pandas as pd
import streamlit as st
import requests
import gdown
import pickle as pkl

# Google Drive file URLs
anime_drive_url = 'https://drive.google.com/uc?id=1XDaUhTA64ye4KfGzZLwp90hOOdsqJSwA'
user_based_id_drive_url = 'https://drive.google.com/uc?id=1-3STHYlMdAv8ku52HnkW6Kq8DQzrIOtv'
similarity_drive_url = 'https://drive.google.com/uc?id=1-5ymqzhZ4xdwYBmWaL1WDGnEWs5Wd999'
user_similarity_drive_url = 'https://drive.google.com/uc?id=19ogaYEUeDDxaBCG9MmuengG09X3JVMZV'

# Function to download file from Google Drive if it doesn't exist
def download_if_not_exists(file_url, output_path):
    if not os.path.exists(output_path):
        gdown.download(file_url, output_path, quiet=False)

# Download files if they do not already exist
download_if_not_exists(anime_drive_url, 'anime.pkl')
download_if_not_exists(user_based_id_drive_url, 'u_b_i.pkl')
download_if_not_exists(similarity_drive_url, 'similarity.pkl')
download_if_not_exists(user_similarity_drive_url, 'user_similarity.pkl')

# Cache data loading to speed up repeated access
@st.cache_data
def load_data():
    anime = pd.read_pickle('anime.pkl')
    users_based_id = pd.read_pickle('u_b_i.pkl')
    similarity = pkl.load(open('similarity.pkl', 'rb'))
    users_similarity = pkl.load(open('user_similarity.pkl', 'rb'))
    return anime, similarity, users_based_id, users_similarity

anime, similarity, users_based_id, users_similarity = load_data()

# Cache poster fetching to avoid repeated network requests
@st.cache_data
def fetch_poster(anime_id):
    url = f"https://api.jikan.moe/v4/anime/{anime_id}"
    response = requests.get(url)
    data = response.json()

    if 'data' in data:
        images = data['data']['images']
        image_url = images['jpg']['image_url']
        return image_url
    else:
        return "https://images.app.goo.gl/nraGJmA37NsVeZ9B7"  # Placeholder image URL if not found

# Function to get top N recommendations
def get_top_recommendations(distances, N=5):
    return sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:N+1]

# Content-based recommendation
def recommend(anime_name):
    anime_index = anime[anime['name'] == anime_name].index[0]
    distances = similarity[anime_index]
    anime_list = get_top_recommendations(distances)
    return [anime.iloc[i[0]]['anime_id'] for i in anime_list]

# User-based recommendation
def recommend_user(name_anime):
    anime_index = users_based_id[users_based_id.name == name_anime].index.values[0]
    distances = users_similarity[anime_index]
    anime_list = get_top_recommendations(distances)
    return [users_based_id.iloc[i[0]]['anime_id'] for i in anime_list]

# Create Streamlit app
st.header('What anime to watch next?')
st.write('Anime Recommender System - content based + collaborative filtering')

# Select anime
chosen_anime = st.selectbox(options=anime.name, label='Choose your favourite anime!')

if chosen_anime:
    st.write(f'You have chosen: {chosen_anime}')
    st.image(fetch_poster(anime[anime.name == chosen_anime]['anime_id'].values[0]), width=50)

    if st.button('Recommend'):
        similar_animes_id = recommend(chosen_anime)
        user_liked_anime_id = recommend_user(chosen_anime)

        similar_animes_poster = [fetch_poster(anime_id) for anime_id in similar_animes_id]
        user_liked_anime_poster = [fetch_poster(anime_id) for anime_id in user_liked_anime_id]

        similar_animes = [anime[anime['anime_id'] == i]['name'].values[0] for i in similar_animes_id]
        user_liked_anime = [anime[anime['anime_id'] == i]['name'].values[0] for i in user_liked_anime_id]

        st.text(' ')
        st.text(' ')
        st.write('Similar animes:')
        for i in range(5):
            st.text(similar_animes[i])
            st.image(similar_animes_poster[i])

        st.text(' ')
        st.text(' ')
        st.write(f'Users who liked watching {chosen_anime} also liked:')
        for i in range(5):
            st.text(user_liked_anime[i])
            st.image(user_liked_anime_poster[i])

        st.text(' ')
        st.text(' ')
        st.caption(':) Recommendations by Md Faisal.')
