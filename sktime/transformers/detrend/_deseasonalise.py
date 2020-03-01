#!/usr/bin/env python3 -u
# coding: utf-8

__author__ = ["Markus Löning"]
__all__ = [
    "Deseasonaliser",
    "Deseasonalizer"
]

import numpy as np
from sktime.transformers.detrend._base import BaseSeriesToSeriesTransformer
from sktime.utils.seasonality import seasonality_test
from sktime.utils.validation.forecasting import check_sp, check_y, check_time_index
from statsmodels.tsa.seasonal import seasonal_decompose


class Deseasonaliser(BaseSeriesToSeriesTransformer):
    """A transformer that removes a seasonal and trend components from time series

    Parameters
    ----------
    sp : int, optional (default=1)
        Seasonal periodicity
    model : str {"additive", "multiplicative"}, optional (default="additive")
        Model to use for estimating seasonal component
    """

    def __init__(self, sp=1, model="additive", test_seasonality=True):
        self.sp = check_sp(sp)
        allowed_models = ("additive", "multiplicative")
        if model not in allowed_models:
            raise ValueError(f"`model` must be one of {allowed_models}, "
                             f"but found: {model}")
        self.model = model
        self.test_seasonality = test_seasonality
        self._oh_index = None
        self._seasonal = None
        self._is_seasonal = None
        super(Deseasonaliser, self).__init__()

    def _set_oh_index(self, y):
        self._oh_index = check_time_index(y.index)

    def _align_seasonal(self, y):
        """Helper function to align seasonal components with y's time index"""
        shift = -(y.index[0] - self._oh_index[0]) % self.sp
        return np.resize(np.roll(self._seasonal, shift=shift), y.shape[0])

    def _check_is_seasonal(self, y):
        if self.sp == 1:
            self._is_seasonal = False
        elif self.test_seasonality:
            self._is_seasonal = seasonality_test(y, self.sp)
        else:
            self._is_seasonal = True

    def fit(self, y, **fit_params):
        y = check_y(y)
        self._set_oh_index(y)
        self._check_is_seasonal(y)

        if self._is_seasonal:
            self._seasonal = seasonal_decompose(y, model=self.model, period=self.sp, filt=None, two_sided=True,
                                                extrapolate_trend=0).seasonal.iloc[:self.sp]
        else:
            self._seasonal = np.zeros(self.sp) if self.model == "additive" else np.ones(self.sp)

        self._is_fitted = True
        return self

    def _detrend(self, y, seasonal):
        if self.model == "additive":
            return y - seasonal
        else:
            return y / seasonal

    def _retrend(self, y, seasonal):
        if self.model == "additive":
            return y + seasonal
        else:
            return y * seasonal

    def transform(self, y, **transform_params):
        self._check_is_fitted()
        y = check_y(y)
        seasonal = self._align_seasonal(y)
        return self._detrend(y, seasonal)

    def inverse_transform(self, y, **transform_params):
        self._check_is_fitted()
        y = check_y(y)
        seasonal = self._align_seasonal(y)
        return self._retrend(y, seasonal)


Deseasonalizer = Deseasonaliser
