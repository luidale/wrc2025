# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st
import altair as alt
from datetime import datetime, timedelta

# Load and prepare data
df = pd.read_csv("all_teams_points_by_time.csv")
df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S')

# 👇 Define team label using team number + name (update 'Team Number' column if different)
df['TeamLabel'] = df['No'].astype(str) + ' - ' + df['Team']  # Update column if needed

# Sidebar: team selection
team_label_map = df[['Team', 'TeamLabel']].drop_duplicates()

with st.expander("⚙️ Team Selection", expanded=True):
    selected_labels = st.sidebar.multiselect(
        "Select teams",
        team_label_map['TeamLabel'].tolist(),
        default=[team_label_map['TeamLabel'].iloc[0]]
    )

# Get actual team names from labels
selected_teams = team_label_map[team_label_map['TeamLabel'].isin(selected_labels)]['Team']

# Filter selected teams
filtered_df = df[df['Team'].isin(selected_teams)].copy()
filtered_df = pd.merge(filtered_df, team_label_map, on='Team', how='left')
filtered_df.sort_values(by=["Team", "Time"], inplace=True)

# Build full time range from 00:00:00 to 23:59:59
start_time = datetime.strptime("00:00:00", "%H:%M:%S")
end_time = datetime.strptime("23:59:59", "%H:%M:%S")
all_times = [start_time + timedelta(minutes=i) for i in range(0, int((end_time - start_time).total_seconds() // 60) + 1)]

selected_time = st.slider(
    "Select time to rank teams",
    min_value=all_times[0],
    max_value=all_times[-1],
    value=all_times[-1],
    format="HH:mm:ss"
)

# Rank teams at selected time
rank_df = (
    df[df['Time'] <= selected_time]
    .sort_values(['Team', 'Time'])
    .groupby('Team')
    .last()
    .reset_index()
)

rank_df['Total points'] = rank_df['Total points'].fillna(0).astype(int)
rank_df['Rank'] = rank_df['Total points'].rank(method='min', ascending=False).astype('Int64').fillna(0).astype(int)

# Merge rank + label info
#rank_df = pd.merge(rank_df, team_label_map, on='Team', how='left')
rank_df = pd.merge(
    rank_df,
    team_label_map[['Team', 'TeamLabel']],
    on='Team',
    how='left',
    validate='many_to_one'
)
rank_df['TeamLabel'] = rank_df['TeamLabel_y']
rank_df.drop(columns=['TeamLabel_x', 'TeamLabel_y'], inplace=True)

filtered_ranked_df = pd.merge(filtered_df, rank_df[['Team', 'Rank', 'TeamLabel']], on='Team', how='left')

# Create custom legend
filtered_ranked_df['Legend'] = filtered_ranked_df['TeamLabel'] + " (# " + filtered_ranked_df['Rank'].astype(str) + ")"

# Altair chart
chart = alt.Chart(filtered_ranked_df).mark_line(point=True).encode(
    x=alt.X('Time:T', title='Time'),
    y=alt.Y('Total points', title='Total Points'),
    color=alt.Color('Legend:N', title='Team (Rank at selected time)').legend(
        orient='top',
        columns=3,
        labelLimit=1000,
        labelFontSize=12,
        titleFontSize=14
    ),
    tooltip=[
        alt.Tooltip('Team:N', title='Team'),
        alt.Tooltip('No:O', title='Team number'),
        alt.Tooltip('Total points:Q', title='Total Points'),
        alt.Tooltip('Point No:O', title='Aquired point'),
        alt.Tooltip('Time:T', title='Time', format='%H:%M:%S')
    ]
).properties(
    width=1200,
    height=800,
    title=f"Team Progression (Ranking at {selected_time.strftime('%H:%M:%S')})"
)

st.markdown("""
<style>
/* Make sidebar wider */
[data-testid="stSidebar2"] {
    width: 400px !important;
}
[data-testid="stSidebar2"] > div:first-child {
    width: 400px !important;
}
/* Make selected items inside multiselect stretch wider */
div[data-baseweb="tag"] {
    max-width: 100% !important;
    white-space: normal !important;
}
/* Override dynamically generated Streamlit span class */
span.st-cd {
    max-width: 100% !important;
    display: inline-block !important;
}

</style>
""", unsafe_allow_html=True)

st.altair_chart(chart, use_container_width=True)
    
# Optional: Display rankings table
st.subheader(f"Team Rankings at {selected_time.strftime('%H:%M:%S')}")
st.dataframe(rank_df.sort_values('Rank')[['Rank', 'TeamLabel', 'Total points']].reset_index(drop=True))
