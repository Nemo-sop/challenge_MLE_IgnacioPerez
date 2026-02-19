from datetime import datetime
from typing import List, Tuple, Union
import pickle

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from challenge import settings

class DelayModel:
    FEATURES_COLS = [
        "OPERA_Latin American Wings",
        "MES_7",
        "MES_10",
        "OPERA_Grupo LATAM",
        "MES_12",
        "TIPOVUELO_I",
        "MES_4",
        "MES_11",
        "OPERA_Sky Airline",
        "OPERA_Copa Air",
    ]

    MODEL_PATH = settings.MODEL_PATH

    def __init__(
        self
    ):
        self._model = None
        self._load_model()

    def _load_model(self) -> None:
        if self.MODEL_PATH.exists():
            with self.MODEL_PATH.open("rb") as model_file:
                self._model = pickle.load(model_file)

    def _save_model(self) -> None:
        if self._model is None:
            return
        self.MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with self.MODEL_PATH.open("wb") as model_file:
            pickle.dump(self._model, model_file)

    @staticmethod
    def _get_min_diff(row: pd.Series) -> float:
        fecha_o = datetime.strptime(row["Fecha-O"], "%Y-%m-%d %H:%M:%S")
        fecha_i = datetime.strptime(row["Fecha-I"], "%Y-%m-%d %H:%M:%S")
        return (fecha_o - fecha_i).total_seconds() / 60

    def preprocess(
        self,
        data: pd.DataFrame,
        target_column: str = None
    ) -> Union[Tuple[pd.DataFrame, pd.DataFrame], pd.DataFrame]:
        """
        Prepare raw data for training or predict.

        Args:
            data (pd.DataFrame): raw data.
            target_column (str, optional): if set, the target is returned.

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: features and target.
            or
            pd.DataFrame: features.
        """
        features = pd.concat(
            [
                pd.get_dummies(data["OPERA"], prefix="OPERA"),
                pd.get_dummies(data["TIPOVUELO"], prefix="TIPOVUELO"),
                pd.get_dummies(data["MES"], prefix="MES"),
            ],
            axis=1,
        )

        for column in self.FEATURES_COLS:
            if column not in features.columns:
                features[column] = 0

        features = features[self.FEATURES_COLS]

        if target_column is None:
            return features

        processed_data = data.copy()
        if target_column not in processed_data.columns:
            processed_data["min_diff"] = processed_data.apply(self._get_min_diff, axis=1)
            processed_data[target_column] = np.where(processed_data["min_diff"] > 15, 1, 0)

        target = processed_data[[target_column]]
        return features, target

    def fit(
        self,
        features: pd.DataFrame,
        target: pd.DataFrame
    ) -> None:
        """
        Fit model with preprocessed data.

        Args:
            features (pd.DataFrame): preprocessed data.
            target (pd.DataFrame): target.
        """
        self._model = LogisticRegression(class_weight="balanced", max_iter=1000)
        self._model.fit(features, target.values.ravel())
        self._save_model()

    def predict(
        self,
        features: pd.DataFrame
    ) -> List[int]:
        """
        Predict delays for new flights.

        Args:
            features (pd.DataFrame): preprocessed data.
        
        Returns:
            (List[int]): predicted targets.
        """
        if self._model is None:
            raise RuntimeError(
                "Model is not available for prediction. "
                "Train it with fit() or make sure a persisted model artifact exists."
            )

        predictions = self._model.predict(features)
        return predictions.astype(int).tolist()