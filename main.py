from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine
import pandas as pd
import urllib
import uvicorn
from rapidfuzz import fuzz

# Config — Update this to match your DB
# Your credentials
username = "unilink"
raw_password = "Apps@!@#"  # Your real password

# Encode password
encoded_password = urllib.parse.quote_plus(raw_password)

# Build connection string
conn_string = (
    f"mssql+pyodbc://{username}:{encoded_password}@unilink.database.windows.net/unilinkdb-dev"
    "?driver=ODBC+Driver+17+for+SQL+Server"
)

# Create engine
engine = create_engine(conn_string)

SIMILARITY_THRESHOLD = 85

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
        df = pd.read_sql("SELECT email FROM fraud_test_data", engine)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    input_email = input_data.email
    matches = check_email_similarity(input_email, df)

    return {
        "input_email": input_email,
        "match_count": len(matches),
        "matches": matches,
        "verdict": "REJECTED" if matches else "ACCEPTED"
    }

# if __name__ == "__main__":
#     uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)