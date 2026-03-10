"""
Módulo de predicción con TensorFlow / Keras.
Modelo LSTM por posición que aprende patrones de secuencias históricas.
Cuando no hay suficientes datos, se usa análisis de frecuencia puro.
"""
from __future__ import annotations
import numpy as np
from config import MIN_DRAWS_FOR_ML, SEQUENCE_LEN, ML_EPOCHS, ML_BATCH


class LotteryPredictor:
    """
    Entrena un modelo LSTM por posición.
    Cada modelo toma los últimos SEQUENCE_LEN valores de esa posición y
    produce una distribución de probabilidad sobre todos los números posibles.
    """

    def __init__(self, positions: int, min_number: int, max_number: int):
        self.positions = positions
        self.min_number = min_number
        self.max_number = max_number
        self.num_classes = max_number - min_number + 1
        self.models: list = []
        self.is_trained = False
        self._tf_available = self._check_tf()

    # ──────────────────────────────────────────────────────────────
    @staticmethod
    def _check_tf() -> bool:
        try:
            import tensorflow  # noqa: F401
            return True
        except ImportError:
            return False

    def _build_model(self):
        """Construye un modelo LSTM → Dense(softmax)."""
        import tensorflow as tf
        model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(SEQUENCE_LEN, 1)),
            tf.keras.layers.LSTM(64, return_sequences=True),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.LSTM(32),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(self.num_classes, activation="softmax"),
        ])
        model.compile(optimizer="adam",
                      loss="categorical_crossentropy",
                      metrics=["accuracy"])
        return model

    # ──────────────────────────────────────────────────────────────
    def train(self, draws: list[list[int]],
              progress_callback=None) -> bool:
        """
        Entrena el modelo con los sorteos históricos.
        Devuelve True si el entrenamiento fue exitoso.
        `progress_callback(pos, total_pos)` se llama al completar cada posición.
        """
        if not self._tf_available:
            return False
        if len(draws) < MIN_DRAWS_FOR_ML + SEQUENCE_LEN:
            return False

        import tensorflow as tf
        data = np.array(draws)
        self.models = []

        for pos in range(self.positions):
            col = data[:, pos]

            X, y = [], []
            for i in range(len(col) - SEQUENCE_LEN):
                X.append(col[i: i + SEQUENCE_LEN])
                y.append(col[i + SEQUENCE_LEN])

            X = np.array(X, dtype=np.float32).reshape(-1, SEQUENCE_LEN, 1)
            X = X / self.max_number

            y_idx = np.clip(np.array(y) - self.min_number, 0, self.num_classes - 1)
            y_cat = tf.keras.utils.to_categorical(y_idx, num_classes=self.num_classes)

            model = self._build_model()
            model.fit(X, y_cat,
                      epochs=ML_EPOCHS,
                      batch_size=ML_BATCH,
                      verbose=0,
                      validation_split=0.1)
            self.models.append(model)

            if progress_callback:
                progress_callback(pos + 1, self.positions)

        self.is_trained = True
        return True

    # ──────────────────────────────────────────────────────────────
    def predict_scores(self, recent_draws: list[list[int]]) -> list[dict[int, float]] | None:
        """
        Devuelve scores ML por posición: lista de {número: probabilidad}.
        Requiere al menos SEQUENCE_LEN sorteos recientes.
        Retorna None si el modelo no está entrenado o faltan datos.
        """
        if not self.is_trained or len(recent_draws) < SEQUENCE_LEN:
            return None

        data = np.array(recent_draws[-SEQUENCE_LEN:], dtype=np.float32)
        result = []

        for pos in range(self.positions):
            col = data[:, pos].reshape(1, SEQUENCE_LEN, 1) / self.max_number
            probs = self.models[pos].predict(col, verbose=0)[0]
            scores = {self.min_number + i: float(p)
                      for i, p in enumerate(probs)}
            result.append(scores)

        return result

    # ──────────────────────────────────────────────────────────────
    def get_top_numbers(self, recent_draws: list[list[int]],
                         top_pct: float = 0.5) -> list[list[int]] | None:
        """
        Devuelve, para cada posición, los números con mayor probabilidad ML
        que representan al menos top_pct de la masa de probabilidad.
        """
        scores = self.predict_scores(recent_draws)
        if scores is None:
            return None

        result = []
        for pos_scores in scores:
            sorted_items = sorted(pos_scores.items(), key=lambda x: x[1], reverse=True)
            total = sum(v for _, v in sorted_items) or 1.0
            chosen = []
            cum = 0.0
            pool = self.num_classes
            max_sel = max(2, int(pool * top_pct))
            for n, p in sorted_items:
                chosen.append(n)
                cum += p / total
                if cum >= 0.70 and len(chosen) >= 2:
                    break
                if len(chosen) >= max_sel:
                    break
            result.append(sorted(chosen))
        return result
