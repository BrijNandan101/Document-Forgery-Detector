import numpy as np
import cv2
from PIL import Image, ImageChops, ImageEnhance
import tensorflow as tf
from tensorflow import keras
import os
import logging
from pathlib import Path

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
                logging.info("✅ CNN model loaded successfully")
            else:
                logging.warning("⚠️ CNN model not found, using placeholder model")
                self.model = self._create_placeholder_model()
        except Exception as e:
            logging.error(f"❌ Error loading model: {e}")
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
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        logging.info("✅ Created placeholder CNN model")
        return model

    def calculate_ela(self, image_path, quality=90):
        """Calculate Error Level Analysis (ELA) image"""
        try:
            original = Image.open(image_path).convert('RGB')

            temp_path = Path(image_path).with_name(f"{Path(image_path).stem}_temp.jpg")
            original.save(temp_path, 'JPEG', quality=quality)
            recompressed = Image.open(temp_path)

            ela_image = ImageChops.difference(original, recompressed)
            extrema = ela_image.getextrema()
            max_diff = max([max(band) for band in extrema])
            max_diff = max_diff if max_diff != 0 else 1
            scale = 255.0 / max_diff
            ela_image = ImageEnhance.Brightness(ela_image).enhance(scale)

            os.remove(temp_path)

            ela_array = np.array(ela_image)
            ela_resized = cv2.resize(ela_array, (128, 128))

            logging.info(f"✅ ELA image processed: {image_path}")
            return ela_resized

        except Exception as e:
            logging.error(f"❌ Error calculating ELA: {e}")
            return np.zeros((128, 128, 3), dtype=np.uint8)

    def preprocess_image(self, image_path):
        """Preprocess image for model input"""
        try:
            ela_image = self.calculate_ela(image_path)
            ela_normalized = ela_image.astype(np.float32) / 255.0
            ela_batch = np.expand_dims(ela_normalized, axis=0)

            logging.info(f"📐 Preprocessed shape: {ela_batch.shape}, mean: {np.mean(ela_batch):.4f}")
            return ela_batch

        except Exception as e:
            logging.error(f"❌ Error preprocessing image: {e}")
            return np.zeros((1, 128, 128, 3), dtype=np.float32)

    def analyze_image(self, image_path):
        """Analyze image and return verdict + confidence"""
        try:
            logging.info(f"🧪 Analyzing image: {image_path}")
            processed_image = self.preprocess_image(image_path)

            if self.model:
                prediction = self.model.predict(processed_image, verbose=0)
                logging.info(f"📊 Raw model prediction: {prediction}")

                if prediction.shape != (1, 1):
                    raise ValueError("Unexpected prediction output shape")

                confidence = float(prediction[0][0])
                if confidence > 0.5:
                    verdict = "Forged"
                    confidence_score = confidence * 100
                else:
                    verdict = "Genuine"
                    confidence_score = (1 - confidence) * 100

                return {
                    'verdict': verdict,
                    'confidence': round(confidence_score, 2),
                    'ela_processed': True,
                    'analysis_method': 'CNN + ELA'
                }

            else:
                verdict, confidence_score = self._traditional_analysis(image_path)
                return {
                    'verdict': verdict,
                    'confidence': round(confidence_score, 2),
                    'ela_processed': True,
                    'analysis_method': 'Traditional'
                }

        except Exception as e:
            logging.error(f"❌ Error analyzing image: {e}")
            return {
                'verdict': 'Error',
                'confidence': 0.0,
                'ela_processed': False,
                'error': str(e)
            }
