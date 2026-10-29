# Reasoning Request Interface

This is a complete Flask-based reasoning request interface that allows users to submit complex tasks and receive both the reasoning process and the final answer.

## Project Structure
- `app.py`: The main Flask application containing the backend logic and API endpoints.
- `app/templates/index.html`: The frontend user interface.
- `app/static/css/style.css`: Modern professional styling for the interface.
- `app/static/js/script.js`: Frontend logic to handle API requests and DOM updates.

## API Endpoint
### POST `/reason`
Accepts a JSON object containing the task to be reasoned.

**Request Body:**
```json
{
    "task": "Your reasoning task here"
}
```

**Response Body:**
```json
{
    "reasoning": "Detailed step-by-step reasoning process...",
    "answer": "The final synthesized answer..."
}
```

## How to Run the App
1. Install Flask:
   ```bash
   pip install flask
   ```
2. Run the application:
   ```bash
   python app.py
   ```
3. Open your browser and navigate to `http://127.0.0.1:5000`.
