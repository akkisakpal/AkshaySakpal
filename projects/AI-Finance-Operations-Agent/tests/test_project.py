from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'output'/'dashboard_data.csv'

def test_demo_dataset():
    df=pd.read_csv(DATA)
    assert len(df)==7
    assert round(df['total'].sum(),2)==20511.50
    assert int((df['status']=='Review Required').sum())==3
    assert int(df['anomaly'].astype(str).str.lower().eq('true').sum())==1
    assert int(df['duplicate'].astype(str).str.lower().eq('true').sum())==1

def test_required_columns():
    df=pd.read_csv(DATA)
    required={'vendor_name','invoice_number','invoice_date','due_date','currency','subtotal','tax','total','status','valid','duplicate','anomaly','risk_level'}
    assert required.issubset(df.columns)
