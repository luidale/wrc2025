FROM python:3.11-slim

WORKDIR /app

# Copy files
COPY app.py .
COPY all_teams_points_by_time.csv .

# Install dependencies
RUN pip install streamlit pandas matplotlib

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
