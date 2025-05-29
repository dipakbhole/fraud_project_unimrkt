from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine
import pandas as pd
import os
import urllib
import uvicorn
import psycopg2
from pathlib import Path
from rapidfuzz import fuzz
from dotenv import load_dotenv


# Load .env only if present (for local)
# ----------------------------------------
env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print("Loaded environment variables from .env")
else:
    print("Using Azure App Settings or system environment variables")


# Config — Update this to match your DB
# Database configuration
username = "unipaneldev"
raw_password = "Apps123@!@#"
host = "dev-unipaneldb.postgres.database.azure.com"
database = "unipaneldb"

# Encode password
encoded_password = urllib.parse.quote_plus(raw_password)

# Build connection string
# PostgreSQL SQLAlchemy connection string
conn_string = f"postgresql+psycopg2://{username}:{encoded_password}@{host}/{database}"


# Create engine
engine = create_engine(conn_string)

# Load variables from .env file
load_dotenv()

# Read from environment variables 
SIMILARITY_THRESHOLD = int(os.getenv("SIMILARITY_THRESHOLD"))
MATCH_LIMIT = int(os.getenv("MATCH_LIMIT"))


# FastAPI app
app = FastAPI()

# Input schema
class EmailInput(BaseModel):
    email: EmailStr

# Compare function
def check_email_similarity(input_email: str, df_emails: pd.DataFrame):
    matches = []
    for _, row in df_emails.iterrows():
        db_email = row['email'].lower()
        score = fuzz.ratio(input_email.lower(), db_email)
        if score >= SIMILARITY_THRESHOLD:
            matches.append({
                "email": db_email,
                "similarity": score
            })
    return matches

@app.post("/check-email/")
def check_email(input_data: EmailInput):
    try:
        # Connect and fetch emails
        df = pd.read_sql('SELECT email FROM "Panelists"', engine)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    input_email = input_data.email
    matches = check_email_similarity(input_email, df)

    return {
        "input_email": input_email,
        "match_count": len(matches),
        "matches": matches,
        "verdict": "REJECTED" if len(matches) > MATCH_LIMIT else "ACCEPTED"
    }



if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)