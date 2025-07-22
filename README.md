# Document Forgery Detector

An AI-powered web application for detecting document forgery using Error Level Analysis (ELA) and a Convolutional Neural Network (CNN). Users can upload scanned documents (JPG/PNG), receive an authenticity verdict, confidence score, and download a detailed PDF report.

---

## Features
- Upload scanned documents (JPG/PNG)
- AI-based forgery detection using ELA + CNN
- Confidence score and verdict (Genuine/Forged)
- Downloadable PDF analysis reports
- Recent analyses history
- REST API (FastAPI backend)
- Modern React frontend

---

## Project Structure

```
Document-Forgery-Detector/
  backend/         # FastAPI backend, forgery detection logic, PDF report generation
  frontend/        # React frontend (user interface)
```

---

## Setup Instructions

### 1. Backend (Python)

#### Requirements
- Python 3.11 (TensorFlow does not support 3.12+)
- MongoDB (local or cloud, set MONGO_URL and DB_NAME in backend/.env)

#### Install dependencies
```sh
cd backend
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On cmd:
venv\Scripts\activate
pip install -r requirements.txt
```

#### Environment Variables
Create a `.env` file in `backend/` with:
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=forgerydb
```

#### (Optional) Model File
- Place your trained CNN model as `backend/models/ela_cnn_model.h5`.
- If missing, a placeholder model is used (results will not be meaningful).

#### Run the backend server
```sh
python server.py
```
- Default: http://localhost:8000
- API docs: http://localhost:8000/docs

---

### 2. Frontend (React)

#### Requirements
- Node.js (v16+ recommended)
- Yarn (or npm)

#### Install dependencies
```sh
cd frontend
yarn install
# or
npm install
```

#### Run the frontend
```sh
yarn start
# or
npm start
```
- Default: http://localhost:3000

#### Configure Backend URL (optional)
- By default, the frontend expects the backend at `http://localhost:8000`.
- To change, set `REACT_APP_BACKEND_URL` in a `.env` file in `frontend/`.

---

## Usage
1. Start both backend and frontend servers.
2. Open the frontend in your browser.
3. Upload a scanned document (JPG/PNG, max 10MB).
4. Wait for analysis. View verdict and confidence.
5. Download the PDF report if desired.

---

## Technical Details

### Backend
- **API Framework:** FastAPI
- **Forgery Detection:**
  - Error Level Analysis (ELA) to highlight tampered regions
  - CNN model (Keras/TensorFlow) for classification
  - If no model is found, a placeholder is used
- **Database:** MongoDB (stores analyses and status checks)
- **PDF Reports:** Generated with FPDF
- **Endpoints:**
  - `POST /api/analyze` — Upload and analyze document
  - `GET /api/generate-report/{analysis_id}` — Download PDF report
  - `GET /api/analyses` — List recent analyses
  - `GET /api/health` — Health check

### Frontend
- **Framework:** React (Create React App)
- **Features:**
  - Drag-and-drop or browse to upload
  - Shows analysis results and recent history
  - Download PDF report
  - Modern, responsive UI

---

## Notes
- Only JPG and PNG images are supported for analysis.
- For real forgery detection, you must provide a trained model at `backend/models/ela_cnn_model.h5`.
- The backend will use a placeholder model if the real model is missing (for demo/testing only).
- MongoDB must be running and accessible as configured in `.env`.

---

## License
This project is for educational and research purposes. See LICENSE file if present.
