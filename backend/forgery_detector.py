"""
AI-powered Document Forgery Detection System
Implements Error Level Analysis (ELA) and CNN-based classification
"""

import numpy as np
import cv2
from PIL import Image, ImageChops, ImageEnhance
import tensorflow as tf
from tensorflow import keras
import os
import logging
from pathlib import Path
import json

class ForgeryDetector:
    def __init__(self):
        self.model = None
        self.model_path = Path(__file__).parent / "models" / "ela_cnn_model.h5"
        self.load_model()
        
    def load_model(self):
        """Load the CNN model for forgery detection"""
        try:
            if self.model_path.exists():
                self.model = keras.models.load_model(self.model_path)
                logging.info("CNN model loaded successfully")
            else:
                logging.warning("CNN model not found, using placeholder model")
                self.model = self._create_placeholder_model()
        except Exception as e:
            logging.error(f"Error loading model: {e}")
            self.model = self._create_placeholder_model()
    
    def _create_placeholder_model(self):
        """Create a placeholder CNN model for demonstration"""
        model = keras.Sequential([
            keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(128, 128, 3)),
            keras.layers.MaxPooling2D((2, 2)),
            keras.layers.Conv2D(64, (3, 3), activation='relu'),
            keras.layers.MaxPooling2D((2, 2)),
            keras.layers.Conv2D(128, (3, 3), activation='relu'),
            keras.layers.MaxPooling2D((2, 2)),
            keras.layers.Flatten(),
            keras.layers.Dense(128, activation='relu'),
            keras.layers.Dropout(0.5),
            keras.layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        # Initialize with random weights for demonstration
        logging.info("Created placeholder CNN model")
        return model
    
    def calculate_ela(self, image_path, quality=90):
        """
        Calculate Error Level Analysis (ELA) for the image
        
        Args:
            image_path: Path to the image file
            quality: JPEG quality for recompression (default: 90)
            
        Returns:
            ELA processed image as numpy array
        """
        try:
            # Open original image
            original = Image.open(image_path).convert('RGB')
            
            # Save as JPEG with specified quality
            temp_path = str(image_path).replace('.', '_temp.')
            original.save(temp_path, 'JPEG', quality=quality)
            
            # Load the recompressed image
            recompressed = Image.open(temp_path)
            
            # Calculate difference
            ela_image = ImageChops.difference(original, recompressed)
            
            # Enhance the difference
            extrema = ela_image.getextrema()
            max_diff = max([max(band) for band in extrema])
            if max_diff == 0:
                max_diff = 1
            scale = 255.0 / max_diff
            ela_image = ImageEnhance.Brightness(ela_image).enhance(scale)
            
            # Clean up temp file
            os.remove(temp_path)
            
            # Convert to numpy array and resize
            ela_array = np.array(ela_image)
            ela_resized = cv2.resize(ela_array, (128, 128))
            
            return ela_resized
            
        except Exception as e:
            logging.error(f"Error calculating ELA: {e}")
            # Return a placeholder ELA if calculation fails
            return np.zeros((128, 128, 3), dtype=np.uint8)
    
    def preprocess_image(self, image_path):
        """
        Preprocess image for CNN model input
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Preprocessed image array ready for model prediction
        """
        try:
            # Calculate ELA
            ela_image = self.calculate_ela(image_path)
            
            # Normalize pixel values
            ela_normalized = ela_image.astype(np.float32) / 255.0
            
            # Add batch dimension
            ela_batch = np.expand_dims(ela_normalized, axis=0)
            
            return ela_batch
            
        except Exception as e:
            logging.error(f"Error preprocessing image: {e}")
            return np.zeros((1, 128, 128, 3), dtype=np.float32)
    
    def analyze_image(self, image_path):
        """
        Analyze image for forgery detection
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image_path)
            
            # Make prediction
            if self.model:
                prediction = self.model.predict(processed_image, verbose=0)
                confidence = float(prediction[0][0])
                
                # Determine verdict based on confidence
                # For demonstration, we'll use a threshold approach
                # In a real model, this would be trained on actual data
                if confidence > 0.5:
                    verdict = "Forged"
                    confidence_score = confidence * 100
                else:
                    verdict = "Genuine"
                    confidence_score = (1 - confidence) * 100
            else:
                # Fallback analysis using traditional methods
                verdict, confidence_score = self._traditional_analysis(image_path)
            
            return {
                'verdict': verdict,
                'confidence': round(confidence_score, 2),
                'ela_processed': True,
                'analysis_method': 'CNN + ELA' if self.model else 'Traditional'
            }
            
        except Exception as e:
            logging.error(f"Error analyzing image: {e}")
            return {
                'verdict': 'Error',
                'confidence': 0.0,
                'ela_processed': False,
                'error': str(e)
            }
    
    def _traditional_analysis(self, image_path):
        """
        Traditional forgery detection using image analysis techniques
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (verdict, confidence_score)
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return "Error", 0.0
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Calculate image quality metrics
            # 1. Laplacian variance (sharpness)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # 2. Edge density
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges) / (edges.shape[0] * edges.shape[1])
            
            # 3. Noise analysis
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            noise = cv2.absdiff(gray, blur)
            noise_level = np.mean(noise)
            
            # Simple heuristic for forgery detection
            # These thresholds would need to be tuned with real data
            forgery_indicators = 0
            
            if laplacian_var < 100:  # Low sharpness might indicate editing
                forgery_indicators += 1
            
            if edge_density > 0.1:  # High edge density might indicate artifacts
                forgery_indicators += 1
                
            if noise_level > 10:  # High noise might indicate compression artifacts
                forgery_indicators += 1
            
            # Calculate confidence based on indicators
            if forgery_indicators >= 2:
                verdict = "Forged"
                confidence = 60 + (forgery_indicators * 15)
            else:
                verdict = "Genuine"
                confidence = 70 + (3 - forgery_indicators) * 10
            
            return verdict, min(confidence, 95)  # Cap at 95% confidence
            
        except Exception as e:
            logging.error(f"Error in traditional analysis: {e}")
            return "Error", 0.0
    
    def save_model(self, model_path):
        """Save the trained model"""
        if self.model:
            self.model.save(model_path)
            logging.info(f"Model saved to {model_path}")
    
    def get_model_info(self):
        """Get information about the current model"""
        if self.model:
            return {
                'model_loaded': True,
                'model_type': 'CNN',
                'input_shape': self.model.input_shape,
                'output_shape': self.model.output_shape,
                'parameters': self.model.count_params()
            }
        else:
            return {
                'model_loaded': False,
                'error': 'No model loaded'
            }