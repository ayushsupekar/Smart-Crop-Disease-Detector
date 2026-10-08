"""Fruit disease SVM using the feature arrays shipped with the fruit project."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from sklearn.svm import SVC

FRUIT_CLASS_NAMES = ["Black spot", "Canker", "Greening", "healthy", "Scab"]
FRUIT_DATA_DIR = Path(__file__).resolve().parent / "fruit_data"
FEATURES_PATH = FRUIT_DATA_DIR / "features.txt.npy"
LABELS_PATH = FRUIT_DATA_DIR / "labels.txt.npy"
_kmeans_lock = threading.Lock()


class FruitDiseaseModel:
    def __init__(self) -> None:
        self._classifier: SVC | None = None
        self._load_lock = threading.Lock()

    def load(self) -> None:
        self._get_classifier()

    def _get_classifier(self) -> SVC:
        if self._classifier is not None:
            return self._classifier

        with self._load_lock:
            if self._classifier is not None:
                return self._classifier
            if not FEATURES_PATH.is_file() or not LABELS_PATH.is_file():
                logger.error("Fruit classifier training arrays not found: %s, %s", FEATURES_PATH, LABELS_PATH)
                raise RuntimeError(
                    "Fruit classifier training arrays are missing from the deployed project."
                )

            features = np.load(FEATURES_PATH, allow_pickle=False)
            labels = np.load(LABELS_PATH, allow_pickle=False)
            if features.ndim != 2 or features.shape[1] != 128 * 128 * 3:
                raise RuntimeError(f"Unexpected fruit feature shape: {features.shape}")
            if labels.ndim != 1 or len(labels) != len(features):
                raise RuntimeError("Fruit features and labels have incompatible shapes")
            if not np.array_equal(np.unique(labels), np.arange(len(FRUIT_CLASS_NAMES))):
                raise RuntimeError("Fruit training labels do not match the five documented classes")

            from sklearn.svm import SVC

            classifier = SVC(
                C=12,
                gamma="scale",
                kernel="rbf",
                random_state=0,
            )
            classifier.fit(features, labels)
            self._classifier = classifier
            logger.info("Fruit SVM trained from %d examples using %d features", len(features), features.shape[1])
            return classifier

    @staticmethod
    def _extract_features(image_bytes: bytes) -> np.ndarray:
        import cv2

        encoded = np.frombuffer(image_bytes, dtype=np.uint8)
        image_bgr = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if image_bgr is None:
            raise ValueError("Uploaded file is not a valid image")
        image_bgr = cv2.resize(image_bgr, (128, 128))
        image = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

        pixels = np.float32(image.reshape((-1, 3)))
        criteria = (
            cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
            100,
            0.85,
        )
        with _kmeans_lock:
            cv2.setRNGSeed(0)
            _, cluster_labels, centers = cv2.kmeans(
                pixels,
                6,
                None,
                criteria,
                10,
                cv2.KMEANS_RANDOM_CENTERS,
            )

        segmented = np.uint8(centers)[cluster_labels.flatten()]
        return segmented.reshape(1, -1)

    def predict(self, image_bytes: bytes) -> dict[str, Any]:
        logger.info("Fruit image preprocessing started")
        classifier = self._get_classifier()
        features = self._extract_features(image_bytes)
        logger.info("Fruit image preprocessing completed")
        decision_scores = classifier.decision_function(features)[0]
        relative_scores = np.exp(decision_scores - np.max(decision_scores))
        relative_scores /= relative_scores.sum()
        ranked_indices = np.argsort(relative_scores)[::-1][:3]
        predicted_index = int(ranked_indices[0])
        disease_name = FRUIT_CLASS_NAMES[predicted_index]
        confidence = round(float(relative_scores[predicted_index]) * 100, 2)
        logger.info("Fruit prediction class=%s relative_score=%.2f", disease_name, confidence)
        return {
            "class_id": f"Fruit___{disease_name.replace(' ', '_')}",
            "crop_name": "Citrus",
            "disease_name": disease_name.title() if disease_name != "healthy" else "Healthy",
            "confidence": confidence,
            "score_kind": "relative_svm_score",
            "engine": "fruit_svm",
            "detector": "fruit",
            "severity": "Healthy" if disease_name == "healthy" else "Unrated",
            "top_probabilities": [
                {
                    "class_id": f"Fruit___{FRUIT_CLASS_NAMES[int(index)].replace(' ', '_')}",
                    "confidence": round(float(relative_scores[index]) * 100, 2),
                }
                for index in ranked_indices
            ],
        }


fruit_classifier = FruitDiseaseModel()