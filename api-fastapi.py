from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import pandas as pd
import polars as pl
import sqlite3

from lib import dbutil, polarsutil

app = FastAPI()

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Config
# FIXME: make rows to show/fetch configurable
# FIXME: make port configurable

# Other
# FIXME: documentation
# FIXME: logging

# UI
# FIXME: paging
# FIXME: groups like in desktop app
# FIXME: open browser when starting the app
# FIXME: allow choice of database
# FIXME: export list

# Define the path to your SQLite database file
DB_PATH = "tests/fi_gutenberg_70M_100.db"
#DB_PATH = "data/fi_parsebank_5B_20/fi_parsebank_5B_20.db"
CSV_PATH = "tests/gutenberg/wordfreqs_combined.csv"
#CSV_PATH = "data/fi_parsebank_5B_20/tables/wordfreqs_combined.csv"

# Database connection setup with error handling for non-existent database file
def get_db_connection():
    if not os.path.exists(DB_PATH):
        # Raise an HTTPException if the database file does not exist
        raise HTTPException(status_code=500, detail="Database file does not exist.")
    connection = dbutil.DatabaseConnection(DB_PATH)
    return connection


def get_lazyframe():
    if not os.path.exists(CSV_PATH):
        # Raise an HTTPException if the database file does not exist
        raise HTTPException(status_code=500, detail="Database CSV file does not exist.")
    lazy_df = polarsutil.lazy_csv(CSV_PATH)
    return lazy_df


class QueryRequest(BaseModel):
    querytxt: str


# Endpoint to render the HTML UI
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/query")
async def get_frequency(query: QueryRequest, db_connection=Depends(get_db_connection)):
    # Establish the database connection
    # db_connection = get_db_connection()

    try:
        # Call the `get_frequency_dataframe` function with provided query
        newdf, querystatus, querymessage = dbutil.get_frequency_dataframe(
            db_connection,
            query=query.querytxt,
            newconnection=True,
            grams=True,
            lemmas=True
        )

        # Convert the resulting DataFrame to a dictionary
        data = newdf.to_dict(orient="records") if isinstance(newdf, pd.DataFrame) else {}

        return {
            "data": data,
            "status": querystatus,
            "message": querymessage
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        pass
        # db_connection.close()


@app.post("/query-polars")
async def get_polars_frequency(query: QueryRequest, lazy_df=Depends(get_lazyframe)):
    # Query from CSV file
    # lazy_df = get_lazyframe()

    try:
        newdf = polarsutil.query(lazy_df, query.querytxt)
        # print(newdf)

        # FIXME: put something in querystatus/querymessage?
        querystatus = ""
        querymessage = ""
        # Convert the resulting DataFrame to a dictionary
        # data = newdf.to_dict(orient="records") if isinstance(newdf, pl.DataFrame) else {}
        data = newdf.to_dicts() if isinstance(newdf, pl.DataFrame) else {}

        return {
            "data": data,
            "status": querystatus,
            "message": querymessage
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        pass
