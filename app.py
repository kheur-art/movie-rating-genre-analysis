import streamlit as st
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Movie Rating & Genre Analysis",
    page_icon="🎬",
    layout="wide"
)

# Load movie data
@st.cache_data
def load_data():
    df = pd.read_csv("cleaned_movies.csv")

    df["movie_title"] = df["movie_title"].fillna("Unknown")
    df["genre"] = df["genre"].fillna("Unknown")
    df["release_year"] = pd.to_numeric(
        df["release_year"], errors="coerce"
    )
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["num_votes"] = pd.to_numeric(
        df["num_votes"], errors="coerce"
    )

    return df.dropna(subset=["rating"])

df = load_data()

# Sidebar
st.sidebar.title("🎬 Movie Explorer")
st.sidebar.write("Explore movie ratings and genres.")

search = st.sidebar.text_input("Search movie title")

genres = sorted({
    genre.strip()
    for values in df["genre"].dropna()
    for genre in str(values).split(",")
    if genre.strip()
})

selected_genres = st.sidebar.multiselect(
    "Select genre",
    genres
)

min_rating = st.sidebar.slider(
    "Minimum rating",
    min_value=0.0,
    max_value=10.0,
    value=0.0,
    step=0.5
)

years = df["release_year"].dropna()

if not years.empty:
    min_year = int(years.min())
    max_year = int(years.max())

    year_range = st.sidebar.slider(
        "Release year",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )
else:
    year_range = None

# Apply filters
filtered = df.copy()

if search:
    filtered = filtered[
        filtered["movie_title"].str.contains(
            search, case=False, na=False
        )
    ]

if selected_genres:
    filtered = filtered[
        filtered["genre"].apply(
            lambda value: any(
                genre in [
                    item.strip()
                    for item in str(value).split(",")
                ]
                for genre in selected_genres
            )
        )
    ]

filtered = filtered[filtered["rating"] >= min_rating]

if year_range is not None:
    filtered = filtered[
        filtered["release_year"].between(
            year_range[0], year_range[1]
        )
    ]

# Main dashboard
st.title("🎬 Movie Rating & Genre Analysis")
st.write(
    "Discover movie trends, compare genres, "
    "and explore IMDb ratings."
)

# Summary metrics
col1, col2, col3 = st.columns(3)

col1.metric("Total Movies", f"{len(filtered):,}")

if not filtered.empty:
    col2.metric(
        "Average Rating",
        f"{filtered['rating'].mean():.2f}/10"
    )

    col3.metric(
        "Highest Rating",
        f"{filtered['rating'].max():.1f}/10"
    )
else:
    col2.metric("Average Rating", "—")
    col3.metric("Highest Rating", "—")

st.divider()

if filtered.empty:
    st.warning("No movies match your selected filters.")
else:
    # Genre analysis
    st.subheader("📊 Genre Analysis")

    genre_data = filtered.assign(
        genre=filtered["genre"].str.split(",")
    ).explode("genre")

    genre_data["genre"] = genre_data["genre"].str.strip()

    genre_summary = (
        genre_data.groupby("genre")
        .agg(
            Movie_Count=("movie_title", "count"),
            Average_Rating=("rating", "mean")
        )
        .sort_values("Movie_Count", ascending=False)
    )

    chart1, chart2 = st.columns(2)

    with chart1:
        st.write("Movies by Genre")
        st.bar_chart(genre_summary["Movie_Count"])

    with chart2:
        st.write("Average Rating by Genre")
        st.bar_chart(genre_summary["Average_Rating"])

    # Release-year trends
    st.subheader("📈 Ratings Over the Years")

    yearly = (
        filtered.dropna(subset=["release_year"])
        .groupby("release_year")["rating"]
        .mean()
        .sort_index()
    )

    if not yearly.empty:
        st.line_chart(yearly)

    # Top-rated movies
    st.subheader("⭐ Top-Rated Movies")

    reliable_movies = filtered[
        filtered["num_votes"] >= 1000
    ]

    if not reliable_movies.empty:
        top_movies = reliable_movies.nlargest(10, "rating")
    else:
        st.info(
            "No movies have at least 1,000 votes "
            "under the current filters."
        )
        top_movies = filtered.nlargest(10, "rating")

    st.dataframe(
        top_movies[
            [
                "movie_title",
                "genre",
                "release_year",
                "rating",
                "num_votes"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    # Movie explorer
    st.subheader("🔎 Explore All Movies")

    st.caption(f"Showing {len(filtered):,} matching movies.")

    st.dataframe(
        filtered[
            [
                "movie_title",
                "genre",
                "release_year",
                "rating",
                "num_votes"
            ]
        ].sort_values("rating", ascending=False),
        use_container_width=True,
        hide_index=True
    )

st.divider()
st.caption("Movie Rating & Genre Analysis | Data source: IMDb")
