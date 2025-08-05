import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import os

# TMDb API key
API_KEY = os.getenv("TMDB_API_KEY")


# Genre lookup dictionary
genre_map = {
    28: 'Action', 12: 'Adventure', 16: 'Animation', 35: 'Comedy',
    80: 'Crime', 99: 'Documentary', 18: 'Drama', 10751: 'Family',
    14: 'Fantasy', 36: 'History', 27: 'Horror', 10402: 'Music',
    9648: 'Mystery', 10749: 'Romance', 878: 'Science Fiction',
    10770: 'TV Movie', 53: 'Thriller', 10752: 'War', 37: 'Western'
}

# Fetch Movies from TMDb
@st.cache_data
def get_movies(endpoint, pages=3):
    all_movies = []
    for page in range(1, pages + 1):
        url = f"https://api.themoviedb.org/3/{endpoint}?api_key={API_KEY}&language=en-US&page={page}"
        response = requests.get(url)
        data = response.json()
        all_movies.extend(data['results'])
    return pd.DataFrame(all_movies)

# Clean and Prepare Movie Data
def clean_movies(df):
    df = df[['id', 'title', 'release_date', 'vote_average', 'vote_count', 'popularity', 'genre_ids', 'poster_path']]
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce').dt.date
    df['year'] = pd.to_datetime(df['release_date'], errors='coerce').dt.year
    df['genre'] = df['genre_ids'].apply(lambda x: genre_map.get(x[0], 'Unknown') if x else 'Unknown')
    df['poster_url'] = df['poster_path'].apply(lambda x: f"https://image.tmdb.org/t/p/w200{x}" if pd.notna(x) else None)
    df['tmdb_url'] = df['id'].apply(lambda x: f"https://www.themoviedb.org/movie/{x}")
    return df

# Display Movies with Posters
def display_movies_with_posters(df, items_per_row=6):
    # CSS styling for the movie cards
    css = """
    <style>
        .movie-card { text-align: center; padding: 10px; color: white; }
        .movie-poster { border-radius: 14px; transition: transform 0.2s; width: 100%; height: auto; cursor: pointer; }
        .movie-poster:hover { transform: scale(1.07); }
        .movie-title { font-weight: bold; margin-top: 6px; font-size: 1rem; }
        .movie-info { font-size: 0.85rem; margin-top: 2px; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

    rows = (len(df) + items_per_row - 1) // items_per_row
    for i in range(rows):
        cols = st.columns(items_per_row)
        for j in range(items_per_row):
            idx = i * items_per_row + j
            if idx >= len(df):
                break
            movie = df.iloc[idx]
            poster = movie['poster_url'] if movie['poster_url'] else ""
            title = movie['title']
            date = movie['release_date']
            rating = f"{movie['vote_average']:.2f}"
            genre = movie['genre']
            tmdb_url = movie['tmdb_url']
            html_card = f"""
            <div class="movie-card">
                <a href="{tmdb_url}" target="_blank">
                    <img src="{poster}" alt="{title} poster" class="movie-poster" />
                </a>
                <div class="movie-title">{title}</div>
                <div class="movie-info">{date} | ⭐ {rating} | 🎭 {genre}</div>
            </div>
            """
            with cols[j]:
                st.markdown(html_card, unsafe_allow_html=True)


# Filtering Function
def filter_movies(df, genre_filter, search_term):
    if genre_filter != "All":
        df = df[df['genre'] == genre_filter]
    if search_term:
        df = df[df['title'].str.contains(search_term, case=False, na=False)]
    return df

# Charts
def show_charts(df):
    if df.empty:
        st.warning("No movies match your filters.")
        return
    tab1, tab2, tab3 = st.tabs(["Ratings Distribution", "Release Year Distribution", "Top Genres"])
    with tab1:
        fig1 = px.histogram(df, x='vote_average', nbins=20,
                            title='Distribution of Movie Ratings',
                            labels={'vote_average': 'Rating'})
        st.plotly_chart(fig1, use_container_width=True)
    with tab2:
        year_counts = df['year'].value_counts().sort_index()
        fig2 = px.bar(x=year_counts.index, y=year_counts.values,
                      labels={'x': 'Release Year', 'y': 'Number of Movies'},
                      title='Number of Movies by Release Year')
        st.plotly_chart(fig2, use_container_width=True)
    with tab3:
        genre_counts = df['genre'].value_counts().reset_index()
        genre_counts.columns = ['Genre', 'Count']
        fig3 = px.bar(genre_counts, x='Genre', y='Count',
                      title='Top Genres',
                      labels={'Count': 'Number of Movies'})
        st.plotly_chart(fig3, use_container_width=True)

# Streamlit App
st.set_page_config(page_title="🎬 Movie Recommendations Dashboard", layout="wide")
st.title("🎬 Movie Recommendations Dashboard")
st.markdown("Data from [TMDb](https://www.themoviedb.org/) - Source Code on [GitHub](https://github.com/tinyKyuu/Movie-Recommendations-Dashboard)")

tab1, tab2 = st.tabs(["⭐ Top Rated", "🔥 Trending Now"])

# Top Rated Tab
with tab1:
    st.subheader("Top 100 Best Rated Movies")
    top_rated_df = clean_movies(get_movies("movie/top_rated", pages=5))
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        genre_filter = st.selectbox("Genre", ["All"] + sorted(top_rated_df['genre'].unique()), key="genre_top")
    with col2:
        search_term = st.text_input("Search Title", key="search_top")
    with col3:
        sort_by = st.selectbox("Sort", ["Rating (High → Low)", "Popularity (High → Low)", "Release Date (Newest First)"], key="sort_top")

    df_display = filter_movies(top_rated_df, genre_filter, search_term)

    with st.expander("📊 Explore the Data"):
        show_charts(df_display)

    # Apply sorting
    if sort_by == "Rating (High → Low)":
        df_display = df_display.sort_values(by="vote_average", ascending=False)
    elif sort_by == "Popularity (High → Low)":
        df_display = df_display.sort_values(by="popularity", ascending=False)
    elif sort_by == "Release Date (Newest First)":
        df_display = df_display.sort_values(by="release_date", ascending=False)

    display_movies_with_posters(df_display, items_per_row=6)




# Trending Tab
with tab2:
    st.subheader("Trending Movies This Week")
    trending_df = clean_movies(get_movies("trending/movie/week", pages=3))
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        genre_filter = st.selectbox("Genre", ["All"] + sorted(trending_df['genre'].unique()), key="genre_trend")
    with col2:
        search_term = st.text_input("Search Title", key="search_trend")
    with col3:
        sort_by = st.selectbox("Sort", ["Rating (High → Low)", "Popularity (High → Low)", "Release Date (Newest First)"], key="sort_trend")

    df_display = filter_movies(trending_df, genre_filter, search_term)

    with st.expander("📊 Explore the Data"):
        show_charts(df_display)

    # Apply sorting
    if sort_by == "Rating (High → Low)":
        df_display = df_display.sort_values(by="vote_average", ascending=False)
    elif sort_by == "Popularity (High → Low)":
        df_display = df_display.sort_values(by="popularity", ascending=False)
    elif sort_by == "Release Date (Newest First)":
        df_display = df_display.sort_values(by="release_date", ascending=False)

    display_movies_with_posters(df_display, items_per_row=6)
