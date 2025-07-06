import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);
  const [recentAnalyses, setRecentAnalyses] = useState([]);

  // Load recent analyses on component mount
  useEffect(() => {
    loadRecentAnalyses();
  }, []);

  const loadRecentAnalyses = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/analyses`);
      setRecentAnalyses(response.data.slice(0, 5)); // Show last 5 analyses
    } catch (err) {
      console.error('Error loading recent analyses:', err);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setAnalysisResult(null);
      setError(null);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const file = e.dataTransfer.files[0];
    if (file && (file.type === 'image/jpeg' || file.type === 'image/png')) {
      setSelectedFile(file);
      setAnalysisResult(null);
      setError(null);
    } else {
      setError('Please select a valid JPG or PNG image file.');
    }
  };

  const analyzeDocument = async () => {
    if (!selectedFile) {
      setError('Please select a file first.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await axios.post(`${BACKEND_URL}/api/analyze`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success) {
        setAnalysisResult(response.data.data);
        loadRecentAnalyses(); // Refresh recent analyses
      } else {
        setError(response.data.message || 'Analysis failed');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze document. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const downloadReport = async (analysisId) => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/generate-report/${analysisId}`, {
        responseType: 'blob',
      });

      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `forgery_report_${analysisId}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to download report. Please try again.');
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 90) return 'text-green-600';
    if (confidence >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getVerdictColor = (verdict) => {
    return verdict === 'Genuine' ? 'text-green-600' : 'text-red-600';
  };

  const getVerdictBgColor = (verdict) => {
    return verdict === 'Genuine' ? 'bg-green-50' : 'bg-red-50';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-3xl font-bold text-gray-900">
                  🔍 Document Forgery Detector
                </h1>
              </div>
            </div>
            <div className="text-sm text-gray-500">
              AI-Powered Document Analysis
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Upload Section */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">
                Upload Document for Analysis
              </h2>
              
              {/* File Upload Area */}
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  dragActive
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <div className="space-y-4">
                  <div className="text-4xl">📄</div>
                  <div>
                    <p className="text-lg font-medium text-gray-900">
                      Drop your document here or click to browse
                    </p>
                    <p className="text-sm text-gray-500 mt-2">
                      Supports JPG and PNG files (max 10MB)
                    </p>
                  </div>
                  <input
                    type="file"
                    accept=".jpg,.jpeg,.png"
                    onChange={handleFileSelect}
                    className="hidden"
                    id="fileInput"
                  />
                  <label
                    htmlFor="fileInput"
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 cursor-pointer"
                  >
                    Choose File
                  </label>
                </div>
              </div>

              {/* Selected File Preview */}
              {selectedFile && (
                <div className="mt-6 bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="text-2xl mr-3">📎</div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {selectedFile.name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => setSelectedFile(null)}
                      className="text-red-500 hover:text-red-700"
                    >
                      ✕
                    </button>
                  </div>
                  
                  {/* Image Preview */}
                  <div className="mt-4">
                    <img
                      src={URL.createObjectURL(selectedFile)}
                      alt="Document preview"
                      className="max-w-full h-48 object-contain rounded-lg border"
                    />
                  </div>
                </div>
              )}

              {/* Analyze Button */}
              <div className="mt-6 flex justify-center">
                <button
                  onClick={analyzeDocument}
                  disabled={!selectedFile || isLoading}
                  className={`px-8 py-3 rounded-lg font-medium text-white transition-colors ${
                    !selectedFile || isLoading
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700'
                  }`}
                >
                  {isLoading ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                      Analyzing...
                    </div>
                  ) : (
                    'Analyze Document'
                  )}
                </button>
              </div>

              {/* Error Message */}
              {error && (
                <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-red-700 text-sm">{error}</p>
                </div>
              )}
            </div>
          </div>

          {/* Results Section */}
          <div className="lg:col-span-1">
            {/* Analysis Results */}
            {analysisResult && (
              <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
                <h3 className="text-xl font-bold text-gray-900 mb-4">
                  Analysis Results
                </h3>
                
                <div className="space-y-4">
                  {/* Verdict */}
                  <div className={`p-4 rounded-lg ${getVerdictBgColor(analysisResult.verdict)}`}>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">
                        Verdict:
                      </span>
                      <span className={`text-lg font-bold ${getVerdictColor(analysisResult.verdict)}`}>
                        {analysisResult.verdict}
                      </span>
                    </div>
                  </div>

                  {/* Confidence Score */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">
                        Confidence Score:
                      </span>
                      <span className={`text-lg font-bold ${getConfidenceColor(analysisResult.confidence)}`}>
                        {analysisResult.confidence}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${analysisResult.confidence}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* Additional Info */}
                  <div className="text-xs text-gray-500 space-y-1">
                    <p>ELA Processed: {analysisResult.ela_processed ? 'Yes' : 'No'}</p>
                    <p>Analysis ID: {analysisResult.id}</p>
                    <p>Date: {new Date(analysisResult.timestamp).toLocaleString()}</p>
                  </div>

                  {/* Download Report Button */}
                  <button
                    onClick={() => downloadReport(analysisResult.id)}
                    className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                  >
                    📄 Download PDF Report
                  </button>
                </div>
              </div>
            )}

            {/* Recent Analyses */}
            {recentAnalyses.length > 0 && (
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 mb-4">
                  Recent Analyses
                </h3>
                
                <div className="space-y-3">
                  {recentAnalyses.map((analysis) => (
                    <div
                      key={analysis.id}
                      className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-900 truncate">
                          {analysis.filename}
                        </span>
                        <span className={`text-xs font-medium ${getVerdictColor(analysis.verdict)}`}>
                          {analysis.verdict}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span>{analysis.confidence}% confidence</span>
                        <button
                          onClick={() => downloadReport(analysis.id)}
                          className="text-blue-600 hover:text-blue-800"
                        >
                          📄 Report
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Info Section */}
        <div className="mt-12 bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            How It Works
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-4xl mb-3">📤</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Upload Document
              </h3>
              <p className="text-sm text-gray-600">
                Upload your scanned document (ID cards, certificates, etc.) in JPG or PNG format.
              </p>
            </div>
            
            <div className="text-center">
              <div className="text-4xl mb-3">🤖</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                AI Analysis
              </h3>
              <p className="text-sm text-gray-600">
                Our AI performs Error Level Analysis (ELA) and uses a CNN model to detect forgery indicators.
              </p>
            </div>
            
            <div className="text-center">
              <div className="text-4xl mb-3">📊</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Get Results
              </h3>
              <p className="text-sm text-gray-600">
                Receive a detailed analysis with verdict, confidence score, and downloadable PDF report.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;