# services/machine_learning.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from database.manager import consultar_historico

class LogisticsMLModel:
    def __init__(self):
        self.rf_model = None
        self.last_training_date = None
        self.mae = 0
        self.rmse = 0
    def prepare_features(self, df_hist):
        if 'fecha_archivo' not in df_hist.columns or 'total_unidades' not in df_hist.columns:
            return pd.DataFrame()
        df = df_hist.copy()
        df['fecha'] = pd.to_datetime(df['fecha_archivo'])
        df['dia_semana'] = df['fecha'].dt.dayofweek
        df['semana'] = df['fecha'].dt.isocalendar().week
        df['mes'] = df['fecha'].dt.month
        df['año'] = df['fecha'].dt.year
        df = df.sort_values('fecha')
        df['lag_7'] = df['total_unidades'].shift(7)
        df['lag_14'] = df['total_unidades'].shift(14)
        df['rolling_mean_7'] = df['total_unidades'].rolling(7).mean()
        df = df.dropna()
        if len(df) < 14: return pd.DataFrame()
        feature_cols = ['dia_semana', 'semana', 'mes', 'año', 'lag_7', 'lag_14', 'rolling_mean_7']
        return df[feature_cols + ['total_unidades', 'fecha']]
    def train(self, df_features):
        X = df_features[['dia_semana', 'semana', 'mes', 'año', 'lag_7', 'lag_14', 'rolling_mean_7']]
        y = df_features['total_unidades']
        if len(X) < 14: return False
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        self.rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.rf_model.fit(X_train, y_train)
        y_pred = self.rf_model.predict(X_test)
        self.mae = mean_absolute_error(y_test, y_pred)
        self.rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        self.last_training_date = datetime.utcnow().isoformat()
        return True
    def predict_next_week(self):
        if not self.rf_model: return pd.DataFrame()
        hist = consultar_historico("dashboard_logistico")
        if not hist: return pd.DataFrame()
        df_hist = pd.DataFrame(hist)
        if 'metricas' in df_hist.columns:
            df_hist['total_unidades'] = df_hist['metricas'].apply(lambda x: x.get('total_unidades', 0) if isinstance(x, dict) else 0)
        df_hist['fecha'] = pd.to_datetime(df_hist['fecha_archivo'])
        df_hist = df_hist.sort_values('fecha')
        
        recent_values = df_hist['total_unidades'].tail(14).tolist()
        if len(recent_values) < 14: return pd.DataFrame()
        
        features = self.prepare_features(df_hist)
        if features.empty: return pd.DataFrame()
        
        current_date = features.iloc[-1]['fecha'] + timedelta(days=1)
        preds = []
        
        for i in range(7):
            lag_7 = recent_values[-7]
            lag_14 = recent_values[-14]
            rolling_mean_7 = np.mean(recent_values[-7:])
            
            next_row = {
                'dia_semana': current_date.dayofweek,
                'semana': current_date.isocalendar().week,
                'mes': current_date.month,
                'año': current_date.year,
                'lag_7': lag_7,
                'lag_14': lag_14,
                'rolling_mean_7': rolling_mean_7
            }
            X = pd.DataFrame([next_row])
            yp = self.rf_model.predict(X)[0]
            preds.append((current_date, yp))
            
            recent_values.append(yp)
            current_date += timedelta(days=1)
            
        df_pred = pd.DataFrame(preds, columns=['fecha', 'prediccion'])
        df_pred['anomalia'] = (df_pred['prediccion'] > 1.5 * df_pred['prediccion'].mean()).astype(int)
        return df_pred
    def get_recommendations(self, preds):
        if preds.empty: return "No hay datos para generar recomendaciones."
        return f"- **Total proyectado próxima semana:** {preds['prediccion'].sum():,.0f} unidades.\n- **Días pico:** {preds.loc[preds['prediccion'].idxmax(), 'fecha'].strftime('%A %d')} con {preds['prediccion'].max():,.0f} unidades.\n- Revisar dotación para esos días."
