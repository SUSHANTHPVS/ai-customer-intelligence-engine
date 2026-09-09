"""
Data generation module for synthetic customer behavior data
"""
import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
from typing import Tuple, Dict
from pathlib import Path

from ..utils.logger import get_logger
from ..utils.config import RAW_DATA_DIR, CUSTOMERS_COUNT, SYNTHETIC_DATA_SIZE, DATE_RANGE_DAYS

logger = get_logger(__name__)

class SyntheticDataGenerator:
    """Generate realistic synthetic customer behavior data"""
    
    def __init__(self, 
                 num_customers: int = CUSTOMERS_COUNT,
                 num_events: int = SYNTHETIC_DATA_SIZE,
                 days_range: int = DATE_RANGE_DAYS,
                 seed: int = 42):
        """
        Initialize the data generator
        
        Args:
            num_customers: Number of customers to generate
            num_events: Number of events to generate
            days_range: Date range in days (from today backwards)
            seed: Random seed for reproducibility
        """
        self.num_customers = num_customers
        self.num_events = num_events
        self.days_range = days_range
        self.seed = seed
        
        np.random.seed(seed)
        self.fake = Faker()
        Faker.seed(seed)
        
        logger.info(f"Initialized SyntheticDataGenerator: {num_customers} customers, {num_events} events, {days_range} days")
    
    def generate_customers(self) -> pd.DataFrame:
        """Generate customer dimension data"""
        logger.info(f"Generating {self.num_customers} customers...")
        
        industries = ['FinTech', 'SaaS', 'E-commerce', 'Healthcare', 'Education', 'Retail', 'Manufacturing']
        channels = ['Google', 'LinkedIn', 'Referral', 'Email', 'Direct', 'Partner']
        countries = ['USA', 'India', 'UK', 'Canada', 'Germany', 'France', 'Australia']
        
        customers = []
        for i in range(self.num_customers):
            customer_id = f"C{i+1:06d}"
            signup_date = datetime.now() - timedelta(days=np.random.randint(1, self.days_range))
            
            customers.append({
                'customer_id': customer_id,
                'first_name': self.fake.first_name(),
                'last_name': self.fake.last_name(),
                'email': self.fake.email(),
                'country': np.random.choice(countries),
                'industry': np.random.choice(industries),
                'acquisition_channel': np.random.choice(channels),
                'signup_date': signup_date,
            })
        
        df_customers = pd.DataFrame(customers)
        logger.info(f"Generated {len(df_customers)} customers")
        return df_customers
    
    def generate_events(self, customers_df: pd.DataFrame) -> pd.DataFrame:
        """Generate customer event data"""
        logger.info(f"Generating {self.num_events} events...")
        
        event_types = ['login', 'feature_usage', 'page_view', 'download', 'report_view', 'settings_change']
        features = ['dashboard', 'reports', 'analytics', 'settings', 'help', 'premium_feature']
        
        events = []
        for _ in range(self.num_events):
            customer = customers_df.sample(1).iloc[0]
            event_time = customer['signup_date'] + timedelta(
                days=np.random.randint(0, self.days_range),
                hours=np.random.randint(0, 24),
                minutes=np.random.randint(0, 60)
            )
            
            if event_time > datetime.now():
                event_time = datetime.now()
            
            events.append({
                'event_id': f"E{len(events)+1:08d}",
                'customer_id': customer['customer_id'],
                'event_type': np.random.choice(event_types),
                'feature': np.random.choice(features),
                'event_timestamp': event_time,
                'session_duration_seconds': int(np.random.exponential(300)),  # Average 5 minutes
                'event_value': np.random.exponential(50) if np.random.random() > 0.9 else 0,
            })
        
        df_events = pd.DataFrame(events)
        df_events = df_events.sort_values('event_timestamp').reset_index(drop=True)
        logger.info(f"Generated {len(df_events)} events")
        return df_events
    
    def generate_transactions(self, customers_df: pd.DataFrame) -> pd.DataFrame:
        """Generate transaction data"""
        logger.info(f"Generating transactions...")
        
        plans = ['Starter', 'Professional', 'Enterprise']
        transaction_types = ['subscription', 'upgrade', 'downgrade', 'renewal', 'refund']
        payment_methods = ['credit_card', 'bank_transfer', 'paypal']
        
        transactions = []
        for customer in customers_df.itertuples():
            # Each customer has 0-20 transactions
            num_transactions = np.random.poisson(2)
            
            for i in range(num_transactions):
                trans_date = customer.signup_date + timedelta(
                    days=np.random.randint(0, self.days_range)
                )
                
                if trans_date > datetime.now():
                    trans_date = datetime.now()
                
                transactions.append({
                    'transaction_id': f"T{len(transactions)+1:08d}",
                    'customer_id': customer.customer_id,
                    'transaction_type': np.random.choice(transaction_types),
                    'subscription_plan': np.random.choice(plans),
                    'amount': np.random.choice([99, 299, 999]),  # Based on plan
                    'currency': 'USD',
                    'payment_method': np.random.choice(payment_methods),
                    'payment_status': 'completed' if np.random.random() > 0.05 else 'failed',
                    'transaction_timestamp': trans_date,
                })
        
        df_transactions = pd.DataFrame(transactions)
        logger.info(f"Generated {len(df_transactions)} transactions")
        return df_transactions
    
    def generate_support_tickets(self, customers_df: pd.DataFrame) -> pd.DataFrame:
        """Generate support ticket data"""
        logger.info(f"Generating support tickets...")
        
        categories = ['technical', 'billing', 'feature_request', 'complaint', 'general_inquiry']
        priorities = ['low', 'medium', 'high', 'critical']
        
        tickets = []
        for customer in customers_df.itertuples():
            # Each customer has 0-5 support tickets
            num_tickets = np.random.poisson(0.5)
            
            for i in range(num_tickets):
                created_date = customer.signup_date + timedelta(
                    days=np.random.randint(0, self.days_range)
                )
                
                if created_date > datetime.now():
                    created_date = datetime.now()
                
                tickets.append({
                    'ticket_id': f"TKT{len(tickets)+1:08d}",
                    'customer_id': customer.customer_id,
                    'category': np.random.choice(categories),
                    'priority': np.random.choice(priorities),
                    'resolution_time_hours': np.random.exponential(48),
                    'satisfaction_score': np.random.choice([1, 2, 3, 4, 5], p=[0.1, 0.15, 0.25, 0.3, 0.2]),
                    'created_at': created_date,
                })
        
        df_tickets = pd.DataFrame(tickets)
        logger.info(f"Generated {len(df_tickets)} support tickets")
        return df_tickets
    
    def save_to_csv(self, **dataframes) -> Dict[str, Path]:
        """Save generated dataframes to CSV files"""
        logger.info(f"Saving data to {RAW_DATA_DIR}...")
        
        file_paths = {}
        for name, df in dataframes.items():
            file_path = RAW_DATA_DIR / f"{name}.csv"
            df.to_csv(file_path, index=False)
            file_paths[name] = file_path
            logger.info(f"Saved {len(df)} rows to {file_path}")
        
        return file_paths
    
    def generate_all(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Generate all datasets"""
        logger.info("Starting data generation pipeline...")
        
        customers = self.generate_customers()
        events = self.generate_events(customers)
        transactions = self.generate_transactions(customers)
        tickets = self.generate_support_tickets(customers)
        
        self.save_to_csv(
            customers=customers,
            events=events,
            transactions=transactions,
            support_tickets=tickets
        )
        
        logger.info("Data generation complete!")
        return customers, events, transactions, tickets


def main():
    """Main function for standalone execution"""
    generator = SyntheticDataGenerator()
    generator.generate_all()


if __name__ == '__main__':
    main()
