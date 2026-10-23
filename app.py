
from pathlib import Path

import pandas as pd
import streamlit as st

# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Movie Rating & Genre Analysis",
    page_icon="🎬",
    layout="wide"
)

# Locate the CSV in the same folder as app.py
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "cleaned_movies.csv"


# --------------------------------------------------
# 2. LOAD AND CLEAN DATA
# --------------------------------------------------

@st.cache_data
def load_data(csv_path):
    df = pd.read_csv(csv_path)

    required_columns = [
        "movie_title",
        "genre",
        "release_year",
        "rating",
        "num_votes"
    ]

    missing_columns = [
        col for col in required_columns if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required CSV columns: "
            + ", ".join(missing_columns)
        )

    df = df[required_columns].copy()

    df["movie_title"] = (
        df["movie_title"].fillna("Unknown").astype(str)
    )
    df["genre"] = (
        df["genre"].fillna("Unknown").astype(str)
    )
    df["release_year"] = pd.to_numeric(
        df["release_year"], errors="coerce"
    )
    df["rating"] = pd.to_numeric(
        df["rating"], errors="coerce"
    )
    df["num_votes"] = pd.to_numeric(
        df["num_votes"], errors="coerce"
    )

    df = df.dropna(subset=["rating"])
    df = df[df["rating"].between(0, 10)]

    return df


# Show a helpful error instead of an unclear traceback
if not CSV_PATH.is_file():
    st.error(
        "The file cleaned_movies.csv was not found. "
        "Please upload it to the same GitHub folder as app.py."
    )
    st.write("Expected file location:", str(CSV_PATH))
    st.stop()

try:
    df = load_data(str(CSV_PATH))
except Exception as error:
    st.error(f"Could not load the movie dataset: {error}")
    st.stop()

if df.empty:
    st.error("The CSV does not contain any valid movie ratings.")
    st.stop()


# --------------------------------------------------
# 3. SIDEBAR AND FILTERS
# --------------------------------------------------

st.sidebar.title("🎬 Movie Explorer")
st.sidebar.write("Discover movies through IMDb data.")

search_query = st.sidebar.text_input(
    "Search movie title",
    placeholder="Enter a movie name..."
)

all_genres = sorted({
    genre.strip()
    for values in df["genre"].dropna()
    for genre in str(values).split(",")
    if genre.strip()
})

selected_genres = st.sidebar.multiselect(
    "Filter by genre",
    options=all_genres
)

min_rating = st.sidebar.slider(
    "Minimum IMDb rating",
    min_value=0.0,
    max_value=10.0,
    value=0.0,
    step=0.5
)

valid_years = df["release_year"].dropna()

if not valid_years.empty:
    min_year = int(valid_years.min())
    max_year = int(valid_years.max())

    if min_year < max_year:
        year_range = st.sidebar.slider(
            "Release year",
            min_value=min_year,
            max_value=max_year,
            value=(min_year, max_year)
        )
    else:
        year_range = (min_year, max_year)
        st.sidebar.caption(f"Release year: {min_year}")
else:
    year_range = None

st.sidebar.divider()
st.sidebar.caption("Data source: IMDb dataset")


# --------------------------------------------------
# 4. APPLY FILTERS
# --------------------------------------------------

filtered = df.copy()

if search_query.strip():
    filtered = filtered[
        filtered["movie_title"].str.contains(
            search_query.strip(),
            case=False,
            na=False,
            regex=False
        )
    ]

if selected_genres:
    def matches_genre(value):
        movie_genres = {
            item.strip()
            for item in str(value).split(",")
        }
        return bool(movie_genres.intersection(selected_genres))

    filtered = filtered[
        filtered["genre"].apply(matches_genre)
    ]

filtered = filtered[
    filtered["rating"] >= min_rating
]

if year_range is not None:
    filtered = filtered[
        filtered["release_year"].between(
            year_range[0],
            year_range[1]
        )
    ]


# --------------------------------------------------
# 5. MAIN DASHBOARD
# --------------------------------------------------

st.title("🎬 Movie Rating & Genre Analysis")

st.write(
    "Explore movie ratings, discover popular genres, "
    "and understand trends across release years."
)

st.caption(
    f"Currently analysing {len(filtered):,} movies "
    f"out of {len(df):,} movies in the dataset."
)

# Summary cards
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Movies",
    f"{len(filtered):,}"
)

if not filtered.empty:
    col2.metric(
        "Average Rating",
        f"{filtered['rating'].mean():.2f}/10"
    )

    col3.metric(
        "Highest Rating",
        f"{filtered['rating'].max():.1f}/10"
    )

    col4.metric(
        "Total Votes",
        f"{filtered['num_votes'].sum():,.0f}"
    )
else:
    col2.metric("Average Rating", "—")
    col3.metric("Highest Rating", "—")
    col4.metric("Total Votes", "—")

st.divider()


# --------------------------------------------------
# 6. GENRE ANALYSIS
# --------------------------------------------------

st.header("📊 Genre Analysis")

if filtered.empty:
    st.warning(
        "No movies match these filters. "
        "Try changing your search or filters."
    )
else:
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
        st.subheader("Movies by Genre")
        st.bar_chart(
            genre_summary["Movie_Count"],
            x_label="Genre",
            y_label="Number of Movies"
        )

    with chart2:
        st.subheader("Average Rating by Genre")
        ratings_by_genre = genre_summary[
            "Average_Rating"
        ].sort_values(ascending=False)

        st.bar_chart(
            ratings_by_genre,
            x_label="Genre",
            y_label="Average Rating"
        )

    st.caption(
        "Movies with multiple genres are counted once "
        "in each applicable genre."
    )

    # --------------------------------------------------
    # 7. RELEASE YEAR TRENDS
    # --------------------------------------------------

    st.header("📈 Movie Rating Trends Over Time")

    yearly_data = filtered.dropna(
        subset=["release_year"]
    ).copy()

    if not yearly_data.empty:
        yearly_summary = (
            yearly_data.groupby("release_year")
            .agg(
                Average_Rating=("rating", "mean"),
                Movie_Count=("movie_title", "count")
            )
            .sort_index()
        )

        trend1, trend2 = st.columns(2)

        with trend1:
            st.subheader("Average Rating by Year")
            st.line_chart(
                yearly_summary["Average_Rating"],
                x_label="Release Year",
                y_label="Average Rating"
            )

        with trend2:
            st.subheader("Movies Released by Year")
            st.bar_chart(
                yearly_summary["Movie_Count"],
                x_label="Release Year",
                y_label="Number of Movies"
            )
    else:
        st.info("No valid release-year data is available.")

    # --------------------------------------------------
    # 8. TOP-RATED MOVIES
    # --------------------------------------------------

    st.header("⭐ Top-Rated Movies")

    st.write(
        "Movies with at least 1,000 votes are prioritised "
        "to make ratings more meaningful."
    )

    reliable_movies = filtered[
        filtered["num_votes"] >= 1000
    ]

    if not reliable_movies.empty:
        top_movies = reliable_movies.nlargest(
            10, "rating"
        )
    else:
        st.info(
            "No matching movies have at least 1,000 votes. "
            "Showing the highest-rated matches instead."
        )
        top_movies = filtered.nlargest(10, "rating")

    top_movies = top_movies[
        [
            "movie_title",
            "genre",
            "release_year",
            "rating",
            "num_votes"
        ]
    ].copy()

    st.dataframe(
        top_movies,
        use_container_width=True,
        hide_index=True
    )

    # --------------------------------------------------
    # 9. MOVIE EXPLORER
    # --------------------------------------------------

    st.header("🔎 Explore All Movies")

    sorted_movies = filtered.sort_values(
        "rating",
        ascending=False
    )

    st.dataframe(
        sorted_movies[
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

    # Download the currently filtered results
    csv_data = sorted_movies.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="📥 Download filtered movies as CSV",
        data=csv_data,
        file_name="filtered_movies.csv",
        mime="text/csv"
    )


# --------------------------------------------------
# 10. FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Movie Rating & Genre Analysis | "
    "Built with Python, Pandas and Streamlit | "
    "Dataset: IMDb"
)
