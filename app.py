import pandas as pd
import streamlit as st
import altair as alt
from datetime import datetime, timedelta

# Load and prepare data
df = pd.read_csv("all_teams_points_by_time.csv")
df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S')

# Sidebar: team selection
teams = df['Team'].unique()
selected_teams = st.sidebar.multiselect("Select teams", teams, default=[teams[0]])

# Filter selected teams
filtered_df = df[df['Team'].isin(selected_teams)].copy()
filtered_df.sort_values(by=["Team", "Time"], inplace=True)

# Build full time range from 00:00:00 to 24:30:00 with 1-minute steps
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
    filtered_df[filtered_df['Time'] <= selected_time]
    .sort_values(['Team', 'Time'])
    .groupby('Team')
    .last()
    .reset_index()
)

rank_df = (
    df[df['Time'] <= selected_time]
    .sort_values(['Team', 'Time'])
    .groupby('Team')
    .last()
    .reset_index()
)

rank_df['Rank'] = rank_df['Total points'].rank(method='min', ascending=False).astype('Int64').fillna(0).astype(int)

# Merge ranks into main plot data
filtered_ranked_df = pd.merge(filtered_df, rank_df[['Team', 'Rank']], on='Team', how='left')
filtered_ranked_df['Legend'] = filtered_ranked_df['Team'] + " (# " + filtered_ranked_df['Rank'].astype(str) + ")"

# Altair chart
chart = alt.Chart(filtered_ranked_df).mark_line(point=True).encode(
    x=alt.X('Time:T', title='Time'),
    y=alt.Y('Total points', title='Total Points'),
    color=alt.Color('Legend:N', title='Team (Rank at selected time)')
	.legend(
            orient='top',  # 'bottom' also works
            labelLimit=500,  # increase from default 160
            labelFontSize=12,
            titleFontSize=14,
            symbolLimit=0,
	    columns=3
        ),
    tooltip=[
        alt.Tooltip('Team:N', title='Team'),
        alt.Tooltip('Total points:Q', title='Total Points'),
        alt.Tooltip('Time:T', title='Time', format='%H:%M:%S')
    ]
).properties(
    width=1200,
    height=800,
    title=f"Team Progression (Ranking at {selected_time.strftime('%H:%M:%S')})"
)

st.altair_chart(chart, use_container_width=True)

# Optional: Display rankings table
st.subheader(f"Team Rankings at {selected_time.strftime('%H:%M:%S')}")
st.dataframe(rank_df.sort_values('Rank')[['Rank', 'Team', 'Total points']].reset_index(drop=True))
