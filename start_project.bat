@echo off
REM Activate the virtual environment
call .venv\Scripts\activate

REM Run the FastAPI application using uvicorn
uvicorn app:app --reload

REM Pause to keep the terminal open after execution
pause
