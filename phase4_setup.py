#!/usr/bin/env python3
"""
PHASE 4: ML Model Development & Training
=========================================

Builds machine learning models for:
1. Churn Prediction (Classification)
2. Customer Segmentation (Clustering)
3. Revenue Forecasting (Regression)
4. Engagement Prediction (Classification)

Models are trained on engineered features from Phase 3.
"""

import logging
import sys
import os
import pickle
from datetime import datetime
from typing import Tuple, Dict, Any, List

import pandas as pd
import numpy as np
import psycopg2
from psycopg2 import sql

# ML Libraries
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score, roc_curve,
    silhouette_score, mean_squared_error, mean_absolute_error, r2_score
)
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MLPipeline:
    """Machine Learning Pipeline for Customer Intelligence"""
    
    def __init__(self, db_host='localhost', db_port=5432, db_name='customer_intelligence',
                 db_user='postgres', db_password=None):
        """Initialize ML Pipeline with database connection"""
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password or os.environ.get('PGPASSWORD', 'sushanth123')
        
        self.conn = None
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.results = {}
    
    def connect_database(self) -> bool:
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
            logger.info(f"✓ Connected to {self.db_name}")
            return True
        except Exception as e:
            logger.error(f"✗ Database connection failed: {e}")
            return False
    
    def close_database(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("✓ Database connection closed")
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute SQL query and return as DataFrame"""
        try:
            df = pd.read_sql_query(query, self.conn)
            return df
        except Exception as e:
            logger.error(f"✗ Query execution failed: {e}")
            return pd.DataFrame()
    
    def load_features(self) -> pd.DataFrame:
        """Load all engineered features from database"""
        logger.info("\n[1/5] Loading engineered features...")
        
        query = """
        SELECT 
            c.customer_id,
            c.country,
            c.industry,
            c.acquisition_channel,
            rf.rfm_score,
            rf.rfm_segment,
            rf.recency_days,
            rf.frequency_transactions,
            rf.monetary_value,
            bh.total_events,
            bh.unique_event_types,
            bh.unique_features_used,
            bh.avg_session_duration,
            bh.login_frequency,
            bh.feature_usage_premium_pct,
            en.engagement_score,
            en.days_since_signup,
            en.days_active,
            en.is_active_last_30days::INT,
            en.is_active_last_7days::INT,
            rv.total_revenue,
            rv.subscription_plan,
            rv.avg_transaction_value,
            rv.transaction_frequency,
            rv.failed_payment_count,
            rv.subscription_tenure_days,
            sp.total_tickets,
            sp.avg_resolution_hours,
            sp.avg_satisfaction_score,
            sp.critical_priority_count,
            sp.issue_resolution_rate,
            cr.churn_risk_score,
            cr.churn_risk_category,
            cr.days_inactive
        FROM customers c
        LEFT JOIN feature_rfm rf ON rf.customer_id = c.customer_id
        LEFT JOIN feature_behavioral bh ON bh.customer_id = c.customer_id
        LEFT JOIN feature_engagement en ON en.customer_id = c.customer_id
        LEFT JOIN feature_revenue rv ON rv.customer_id = c.customer_id
        LEFT JOIN feature_support sp ON sp.customer_id = c.customer_id
        LEFT JOIN feature_churn_risk cr ON cr.customer_id = c.customer_id
        ORDER BY c.customer_id
        """
        
        df = self.execute_query(query)
        
        if df.empty:
            logger.error("✗ No features loaded from database")
            return df
        
        logger.info(f"✓ Loaded {len(df):,} customer records with {len(df.columns)} features")
        logger.info(f"  Features: {', '.join(df.columns[:5])}...")
        
        return df
    
    def prepare_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Prepare data for ML models"""
        logger.info("\n[2/5] Preparing data for modeling...")
        
        # Fill missing values
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].fillna(df[numeric_columns].median())
        
        categorical_columns = ['country', 'industry', 'acquisition_channel', 
                               'rfm_segment', 'subscription_plan']
        for col in categorical_columns:
            if col in df.columns:
                df[col] = df[col].fillna('Unknown')
        
        logger.info(f"✓ Data prepared: {df.shape[0]} records, {df.shape[1]} features")
        logger.info(f"  Missing values: {df.isnull().sum().sum()}")
        
        return df, df.copy()
    
    def build_churn_model(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Build churn prediction model"""
        logger.info("\n[3/5] Building Churn Prediction Model...")
        
        # Create binary churn target using percentile (top 30% at churn risk)
        churn_threshold = df['churn_risk_score'].quantile(0.70)
        y = (df['churn_risk_score'] >= churn_threshold).astype(int)
        
        # Select features for model (exclude target and related fields)
        feature_cols = [col for col in df.columns if col not in 
                       ['customer_id', 'churn_risk_category', 'churn_risk_score', 
                        'rfm_segment', 'subscription_plan', 'activity_trend']]
        
        X = df[feature_cols].copy()
        
        # Fit encoders on FULL data before splitting
        for col in ['country', 'industry', 'acquisition_channel']:
            if col in X.columns:
                le = LabelEncoder()
                le.fit(X[col].astype(str))  # Fit on full column first
                self.encoders[f'churn_{col}'] = le
                X[col] = le.transform(X[col].astype(str))  # Then transform
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        self.scalers['churn'] = scaler
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train model
        logger.info("  Training Random Forest Classifier...")
        model = RandomForestClassifier(n_estimators=100, max_depth=15, 
                                      random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        self.models['churn'] = model
        
        # Evaluate
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        auc_score = roc_auc_score(y_test, y_pred_proba)
        
        results = {
            'model': model,
            'scaler': scaler,
            'features': feature_cols,
            'train_size': len(X_train),
            'test_size': len(X_test),
            'auc_score': auc_score,
            'accuracy': model.score(X_test, y_test),
            'classification_report': classification_report(y_test, y_pred),
            'feature_importance': dict(zip(feature_cols, model.feature_importances_))
        }
        
        self.results['churn'] = results
        
        logger.info(f"  ✓ Model trained: AUC={auc_score:.4f}, Accuracy={results['accuracy']:.4f}")
        logger.info(f"    Churn threshold (70th percentile): {churn_threshold:.2f}")
        logger.info(f"    Positive class (High Risk): {y.sum()} customers ({y.mean()*100:.1f}%)")
        logger.info(f"    Top 3 important features: {sorted(results['feature_importance'].items(), key=lambda x: x[1], reverse=True)[:3]}")
    
    def build_segmentation_model(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Build customer segmentation model"""
        logger.info("\n[3/5] Building Customer Segmentation Model...")
        
        # Select features for clustering
        feature_cols = ['rfm_score', 'engagement_score', 'total_revenue', 
                       'login_frequency', 'days_active']
        
        X = df[feature_cols].dropna().copy()
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        self.scalers['segmentation'] = scaler
        
        # Find optimal number of clusters (using elbow method)
        logger.info("  Finding optimal cluster count...")
        inertias = []
        silhouette_scores = []
        K_range = range(2, 8)
        
        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(X_scaled)
            inertias.append(kmeans.inertia_)
            silhouette_scores.append(silhouette_score(X_scaled, kmeans.labels_))
        
        # Use k=4 (reasonable for business segments)
        optimal_k = 4
        logger.info(f"  Using k={optimal_k} clusters (CUSTOMER/DORMANT/AT_RISK/VIP)")
        
        model = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
        clusters = model.fit_predict(X_scaled)
        
        self.models['segmentation'] = model
        
        results = {
            'model': model,
            'scaler': scaler,
            'features': feature_cols,
            'n_clusters': optimal_k,
            'silhouette_scores': silhouette_scores,
            'cluster_centers': model.cluster_centers_,
            'inertia': model.inertia_,
            'n_samples': len(X)
        }
        
        self.results['segmentation'] = results
        
        logger.info(f"  ✓ Model trained: {optimal_k} clusters, Silhouette={silhouette_scores[2]:.4f}")
        logger.info(f"    Cluster distribution: {np.bincount(clusters)}")
        
        return results
    
    def build_revenue_forecast_model(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Build revenue forecasting model"""
        logger.info("\n[3/5] Building Revenue Forecasting Model...")
        
        # Create revenue bands for learning
        feature_cols = ['rfm_score', 'engagement_score', 'frequency_transactions',
                       'login_frequency', 'days_active', 'subscription_tenure_days']
        
        X = df[feature_cols].dropna().copy()
        y = df.loc[X.index, 'total_revenue']
        
        # Remove outliers
        Q1 = y.quantile(0.25)
        Q3 = y.quantile(0.75)
        IQR = Q3 - Q1
        mask = (y >= Q1 - 1.5*IQR) & (y <= Q3 + 1.5*IQR)
        X = X[mask]
        y = y[mask]
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        self.scalers['revenue'] = scaler
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        # Train model
        logger.info("  Training Random Forest Regressor...")
        model = RandomForestRegressor(n_estimators=100, max_depth=15, 
                                     random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        self.models['revenue'] = model
        
        # Evaluate
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        results = {
            'model': model,
            'scaler': scaler,
            'features': feature_cols,
            'train_size': len(X_train),
            'test_size': len(X_test),
            'mae': mae,
            'rmse': rmse,
            'r2_score': r2,
            'feature_importance': dict(zip(feature_cols, model.feature_importances_))
        }
        
        self.results['revenue'] = results
        
        logger.info(f"  ✓ Model trained: R²={r2:.4f}, RMSE=${rmse:.2f}, MAE=${mae:.2f}")
        logger.info(f"    Top 3 important features: {sorted(results['feature_importance'].items(), key=lambda x: x[1], reverse=True)[:3]}")
        
        return results
    
    def build_engagement_model(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Build engagement prediction model"""
        logger.info("\n[3/5] Building Engagement Prediction Model...")
        
        # Use engagement_score as continuous target (0-100)
        # This is more meaningful than binary classification given data distribution
        y = df['engagement_score'].copy()
        
        # Select features (exclude engagement-related fields)
        feature_cols = [col for col in df.columns if col not in 
                       ['customer_id', 'engagement_score', 'days_since_signup', 'days_active',
                        'is_active_last_30days', 'is_active_last_7days', 'activity_trend',
                        'churn_risk_category', 'churn_risk_score']]
        
        X = df[feature_cols].copy()
        
        # Fit encoders on FULL data before splitting
        for col in ['country', 'industry', 'acquisition_channel', 'rfm_segment', 'subscription_plan']:
            if col in X.columns:
                le = LabelEncoder()
                le.fit(X[col].astype(str))  # Fit on full column first
                self.encoders[f'engagement_{col}'] = le
                X[col] = le.transform(X[col].astype(str))  # Then transform
        
        # Remove rows with NaN target
        mask = ~y.isna()
        X = X[mask]
        y = y[mask]
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        self.scalers['engagement'] = scaler
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        # Train model (regression instead of classification)
        logger.info("  Training Random Forest Regressor...")
        model = RandomForestRegressor(n_estimators=100, max_depth=15,
                                      random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        self.models['engagement'] = model
        
        # Evaluate
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        results = {
            'model': model,
            'scaler': scaler,
            'features': feature_cols,
            'train_size': len(X_train),
            'test_size': len(X_test),
            'mae': mae,
            'rmse': rmse,
            'r2_score': r2,
            'feature_importance': dict(zip(feature_cols, model.feature_importances_))
        }
        
        self.results['engagement'] = results
        
        logger.info(f"  ✓ Model trained: R²={r2:.4f}, RMSE={rmse:.2f}, MAE={mae:.2f}")
        logger.info(f"    Predicting engagement score (0-100)")
        logger.info(f"    Top 3 important features: {sorted(results['feature_importance'].items(), key=lambda x: x[1], reverse=True)[:3]}")
        
        return results
    
    def save_models(self) -> bool:
        """Save trained models to disk"""
        logger.info("\n[4/5] Saving trained models...")
        
        try:
            os.makedirs('models', exist_ok=True)
            
            for model_name, model in self.models.items():
                filepath = f'models/{model_name}_model.pkl'
                with open(filepath, 'wb') as f:
                    pickle.dump(model, f)
                logger.info(f"  ✓ Saved {model_name} model")
            
            # Save scalers
            for scaler_name, scaler in self.scalers.items():
                filepath = f'models/{scaler_name}_scaler.pkl'
                with open(filepath, 'wb') as f:
                    pickle.dump(scaler, f)
                logger.info(f"  ✓ Saved {scaler_name} scaler")
            
            # Save results summary
            results_summary = {
                'timestamp': datetime.now().isoformat(),
                'churn_auc': self.results['churn'].get('auc_score', 'N/A'),
                'churn_accuracy': self.results['churn'].get('accuracy', 'N/A'),
                'revenue_r2': self.results['revenue'].get('r2_score', 'N/A'),
                'revenue_rmse': self.results['revenue'].get('rmse', 'N/A'),
                'engagement_r2': self.results['engagement'].get('r2_score', 'N/A'),
                'engagement_rmse': self.results['engagement'].get('rmse', 'N/A'),
                'segmentation_clusters': self.results['segmentation'].get('n_clusters', 'N/A')
            }
            
            with open('models/results_summary.txt', 'w') as f:
                for key, value in results_summary.items():
                    f.write(f"{key}: {value}\n")
            
            logger.info("  ✓ Models saved to ./models/ directory")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to save models: {e}")
            return False
    
    def generate_predictions(self, df: pd.DataFrame) -> bool:
        """Generate predictions for all customers"""
        logger.info("\n[5/5] Generating predictions...")
        
        try:
            predictions_df = df[['customer_id']].copy()
            
            # Helper function to fill NaNs (numeric with median, categorical with 'Unknown')
            def fill_missing(X):
                X = X.copy()
                numeric_cols = X.select_dtypes(include=[np.number]).columns
                categorical_cols = X.select_dtypes(include=['object']).columns
                
                for col in numeric_cols:
                    X[col] = X[col].fillna(X[col].median())
                for col in categorical_cols:
                    X[col] = X[col].fillna('Unknown')
                
                return X
            
            # Churn predictions
            if 'churn' in self.models:
                feature_cols = self.results['churn']['features']
                X = fill_missing(df[feature_cols])
                
                # Encode
                for col in ['country', 'industry', 'acquisition_channel']:
                    if col in X.columns and f'churn_{col}' in self.encoders:
                        X[col] = self.encoders[f'churn_{col}'].transform(X[col].astype(str))
                
                X_scaled = self.scalers['churn'].transform(X)
                predictions_df['churn_probability'] = self.models['churn'].predict_proba(X_scaled)[:, 1]
                predictions_df['churn_prediction'] = self.models['churn'].predict(X_scaled)
            
            # Revenue predictions
            if 'revenue' in self.models:
                feature_cols = self.results['revenue']['features']
                X = fill_missing(df[feature_cols])
                X_scaled = self.scalers['revenue'].transform(X)
                predictions_df['revenue_forecast'] = self.models['revenue'].predict(X_scaled)
            
            # Engagement predictions
            if 'engagement' in self.models:
                feature_cols = self.results['engagement']['features']
                X = fill_missing(df[feature_cols])
                
                # Encode
                for col in ['country', 'industry', 'acquisition_channel', 'rfm_segment', 'subscription_plan']:
                    if col in X.columns and f'engagement_{col}' in self.encoders:
                        X[col] = self.encoders[f'engagement_{col}'].transform(X[col].astype(str))
                
                X_scaled = self.scalers['engagement'].transform(X)
                predictions_df['engagement_score_pred'] = self.models['engagement'].predict(X_scaled)
                # Cap at 100 and floor at 0
                predictions_df['engagement_score_pred'] = predictions_df['engagement_score_pred'].clip(0, 100)
            
            # Save predictions
            predictions_df.to_csv('data/predictions.csv', index=False)
            logger.info(f"  ✓ Predictions generated for {len(predictions_df):,} customers")
            logger.info(f"    Saved to data/predictions.csv")
            
            return True
        except Exception as e:
            logger.error(f"✗ Prediction generation failed: {e}")
            return False
    
    def run_phase4(self) -> bool:
        """Execute complete Phase 4 ML pipeline"""
        print("\n" + "=" * 70)
        print("PHASE 4: ML Model Development & Training")
        print("=" * 70)
        
        # Connect to database
        if not self.connect_database():
            return False
        
        try:
            # Load features
            df = self.load_features()
            if df.empty:
                return False
            
            # Prepare data
            df_prepared, df_backup = self.prepare_data(df)
            
            # Build models
            self.build_churn_model(df_prepared)
            self.build_segmentation_model(df_prepared)
            self.build_revenue_forecast_model(df_prepared)
            self.build_engagement_model(df_prepared)
            
            # Save models
            self.save_models()
            
            # Generate predictions
            self.generate_predictions(df_prepared)
            
            # Print summary
            print("\n" + "=" * 70)
            print("✅ SUCCESS - Phase 4 ML Model Development Complete!")
            print("\nModels Trained:")
            print("  ✓ Churn Prediction (AUC: {:.4f})".format(self.results['churn']['auc_score']))
            print("  ✓ Customer Segmentation ({} clusters)".format(self.results['segmentation']['n_clusters']))
            print("  ✓ Revenue Forecasting (R²: {:.4f})".format(self.results['revenue']['r2_score']))
            print("  ✓ Engagement Prediction (R²: {:.4f})".format(self.results['engagement']['r2_score']))
            print("\nNext Steps:")
            print("  1. Review model performance metrics")
            print("  2. Deploy models to production API")
            print("  3. Set up real-time prediction pipeline")
            print("  4. Configure monitoring & alerts")
            print("=" * 70)
            
            return True
        
        except Exception as e:
            logger.error(f"✗ Phase 4 failed: {e}")
            return False
        
        finally:
            self.close_database()


if __name__ == '__main__':
    pipeline = MLPipeline()
    success = pipeline.run_phase4()
    sys.exit(0 if success else 1)
