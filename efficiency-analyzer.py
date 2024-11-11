import pandas as pd
import numpy as np
import openai
from datetime import datetime, timedelta
from prophet import Prophet
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler
import json
import warnings
warnings.filterwarnings('ignore')

class OperationalEfficiencyAnalyzer:
    def __init__(self, api_key):
        self.api_key = api_key
        openai.api_key = api_key
        self.generate_sample_data()
        
    def generate_sample_data(self):
        """Generate realistic operational data"""
        # Generate dates for one year
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        departments = ['IT', 'Sales', 'Operations', 'HR', 'Marketing']
        
        data = []
        for dept in departments:
            # Generate realistic resource utilization patterns
            base_staff_hours = np.random.normal(loc=80, scale=10, size=len(dates))
            base_budget = np.random.normal(loc=10000, scale=1000, size=len(dates))
            resource_usage = np.random.normal(loc=75, scale=15, size=len(dates))
            
            # Add seasonal patterns
            seasonal_factor = np.sin(np.linspace(0, 2*np.pi, len(dates))) * 10
            
            for i, date in enumerate(dates):
                data.append({
                    'date': date,
                    'department': dept,
                    'staff_hours': max(0, base_staff_hours[i] + seasonal_factor[i]),
                    'budget_spent': max(0, base_budget[i] + seasonal_factor[i] * 100),
                    'resource_utilization': min(100, max(0, resource_usage[i] + seasonal_factor[i])),
                    'productivity_score': np.random.normal(loc=85, scale=5)
                })
        
        self.df = pd.DataFrame(data)
        
    def analyze_with_gpt(self, metrics_summary):
        """Use GPT to analyze operational metrics and provide recommendations"""
        prompt = f"""Analyze these operational metrics and provide recommendations in JSON format:
        1. identified_inefficiencies: (list of specific inefficiencies)
        2. optimization_suggestions: (list of actionable recommendations)
        3. potential_savings: (estimated percentage savings)
        4. priority_actions: (list of top 3 priority actions)

        Metrics Summary: {metrics_summary}

        Return only valid JSON."""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an operational efficiency expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        return json.loads(response.choices[0].message.content)

    def detect_anomalies(self):
        """Detect anomalies in resource utilization"""
        anomalies = []
        
        for dept in self.df['department'].unique():
            dept_data = self.df[self.df['department'] == dept]
            
            # Calculate z-scores for key metrics
            for metric in ['staff_hours', 'budget_spent', 'resource_utilization']:
                z_scores = np.abs((dept_data[metric] - dept_data[metric].mean()) / dept_data[metric].std())
                anomaly_dates = dept_data[z_scores > 2]['date']
                
                for date in anomaly_dates:
                    anomalies.append({
                        'department': dept,
                        'date': date,
                        'metric': metric,
                        'value': dept_data[dept_data['date'] == date][metric].iloc[0]
                    })
        
        return pd.DataFrame(anomalies)

    def forecast_resources(self):
        """Forecast future resource needs using Prophet"""
        forecasts = {}
        
        for dept in self.df['department'].unique():
            dept_data = self.df[self.df['department'] == dept]
            
            # Prepare data for Prophet
            df_prophet = pd.DataFrame({
                'ds': dept_data['date'],
                'y': dept_data['resource_utilization']
            })
            
            model = Prophet(yearly_seasonality=True, weekly_seasonality=True)
            model.fit(df_prophet)
            
            future = model.make_future_dataframe(periods=90)
            forecast = model.predict(future)
            
            forecasts[dept] = forecast
            
        return forecasts

    def generate_insights_report(self):
        """Generate comprehensive insights report"""
        # Calculate key metrics
        metrics_summary = {
            'avg_utilization': self.df['resource_utilization'].mean(),
            'total_budget': self.df['budget_spent'].sum(),
            'productivity_correlation': self.df['resource_utilization'].corr(self.df['productivity_score']),
            'department_metrics': self.df.groupby('department').agg({
                'resource_utilization': 'mean',
                'budget_spent': 'sum',
                'productivity_score': 'mean'
            }).to_dict()
        }
        
        # Get AI recommendations
        ai_analysis = self.analyze_with_gpt(str(metrics_summary))
        
        # Generate visualizations
        util_by_dept = px.box(self.df, x='department', y='resource_utilization',
                            title='Resource Utilization by Department')
        util_by_dept.write_html("utilization_by_dept.html")
        
        budget_trend = px.line(self.df.groupby('date')['budget_spent'].sum().reset_index(),
                             x='date', y='budget_spent', title='Budget Trend Over Time')
        budget_trend.write_html("budget_trend.html")
        
        # Calculate potential savings
        potential_annual_savings = (100 - metrics_summary['avg_utilization']) * \
                                 metrics_summary['total_budget'] * \
                                 float(ai_analysis['potential_savings'].strip('%')) / 10000
        
        return {
            'metrics_summary': metrics_summary,
            'ai_recommendations': ai_analysis,
            'anomalies': len(self.detect_anomalies()),
            'potential_annual_savings': potential_annual_savings,
            'analysis_date': datetime.now().strftime("%Y-%m-%d")
        }

def main():
    api_key = "your-api-key-here"  # Replace with actual OpenAI API key
    
    print("Initializing Operational Efficiency Analyzer...")
    analyzer = OperationalEfficiencyAnalyzer(api_key)
    
    print("Generating insights and forecasts...")
    insights = analyzer.generate_insights_report()
    forecasts = analyzer.forecast_resources()
    
    print("\nAnalysis Complete! Key Findings:")
    print(f"Average Resource Utilization: {insights['metrics_summary']['avg_utilization']:.1f}%")
    print(f"Potential Annual Savings: ${insights['potential_annual_savings']:,.2f}")
    print(f"Anomalies Detected: {insights['anomalies']}")
    print("\nTop Priority Actions:")
    for i, action in enumerate(insights['ai_recommendations']['priority_actions'], 1):
        print(f"{i}. {action}")
    
    print("\nFiles generated:")
    print("- utilization_by_dept.html")
    print("- budget_trend.html")

if __name__ == "__main__":
    main()
