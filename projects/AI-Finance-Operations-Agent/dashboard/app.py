import io,json,os,re,time
from pathlib import Path
import pandas as pd
import streamlit as st
from pypdf import PdfReader
from pydantic import BaseModel
from typing import Optional

st.set_page_config(page_title='AI Finance Operations Agent',page_icon='💰',layout='wide')
ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'output'/'dashboard_data.csv'

class Invoice(BaseModel):
    vendor_name:str
    invoice_number:str
    invoice_date:str
    due_date:Optional[str]=None
    currency:str
    subtotal:float
    tax:float
    total:float

COLS=['vendor_name','invoice_number','invoice_date','due_date','currency','subtotal','tax','total','status','valid','duplicate','anomaly','risk_level']

@st.cache_data
def load():
    df=pd.read_csv(DATA)
    for c in COLS:
        if c not in df: df[c]=''
    for c in ['subtotal','tax','total']: df[c]=pd.to_numeric(df[c],errors='coerce').fillna(0)
    for c in ['valid','duplicate','anomaly']: df[c]=df[c].astype(str).str.lower().isin(['true','1','yes'])
    return df[COLS]

def pdf_text(b):
    r=PdfReader(io.BytesIO(b))
    return '\n'.join((p.extract_text() or '') for p in r.pages).strip()

def first(t,patterns):
    for p in patterns:
        m=re.search(p,t,re.I|re.M)
        if m:return m.group(1).strip()
    return ''

def money(x):
    m=re.search(r'-?\d+(?:,\d{3})*(?:\.\d+)?',str(x))
    return float(m.group().replace(',','')) if m else 0.0

def fallback(t):
    v=first(t,[r'Vendor\s*:\s*(.+)',r'Vendor Name\s*:\s*(.+)'])
    n=first(t,[r'Invoice\s*(?:Number|No\.?|#)\s*:\s*([\w./-]+)'])
    d=first(t,[r'Invoice\s*Date\s*:\s*(\d{4}-\d{2}-\d{2})',r'Date\s*:\s*(\d{4}-\d{2}-\d{2})'])
    due=first(t,[r'Due\s*Date\s*:\s*(\d{4}-\d{2}-\d{2})'])
    cur=first(t,[r'Currency\s*:\s*([A-Z]{3})']) or ('EUR' if '€' in t else '')
    sub=first(t,[r'Subtotal\s*:\s*[€$£]?\s*([\d,]+(?:\.\d+)?)'])
    tax=first(t,[r'(?:VAT|Tax)\s*:\s*[€$£]?\s*([\d,]+(?:\.\d+)?)'])
    total=first(t,[r'Total\s*:\s*[€$£]?\s*([\d,]+(?:\.\d+)?)'])
    if not v:
        for line in [x.strip() for x in t.splitlines() if x.strip()][:12]:
            if not re.search(r'invoice|date|due|subtotal|vat|tax|total|currency|description',line,re.I): v=line; break
    if not all([v,n,d,cur]): raise ValueError('Fallback parser could not identify required fields.')
    return Invoice(vendor_name=v,invoice_number=n,invoice_date=d,due_date=due or None,currency=cur,subtotal=money(sub),tax=money(tax),total=money(total))

try:
    from google import genai
    key=os.environ.get('GEMINI_API_KEY')
    client=genai.Client(api_key=key) if key else None
except Exception: client=None

def ai(t):
    if not client: raise RuntimeError('Gemini is not configured.')
    prompt='Extract invoice information and return ONLY JSON with vendor_name, invoice_number, invoice_date, due_date, currency, subtotal, tax and total. Invoice text:\n'+t
    for attempt in range(3):
        try: return client.models.generate_content(model='gemini-3.6-flash',contents=prompt).text
        except Exception as e:
            s=str(e)
            if '429' in s or 'RESOURCE_EXHAUSTED' in s: raise RuntimeError('Gemini daily quota is exhausted.')
            if '503' in s or 'UNAVAILABLE' in s:
                if attempt<2: time.sleep(5*(2**attempt)); continue
                raise RuntimeError('Gemini is temporarily unavailable.')
            raise

def parse(raw):
    m=re.search(r'\{.*\}',re.sub(r'```json\s*|```\s*','',raw.strip(),flags=re.I),re.S)
    if not m: raise ValueError('Invalid AI JSON.')
    return Invoice(**json.loads(m.group()))

def analyze(i,df):
    valid=abs(i.subtotal+i.tax-i.total)<0.01
    dup=bool(((df.vendor_name.str.lower()==i.vendor_name.lower())&(df.invoice_number.str.lower()==i.invoice_number.lower())).any())
    h=df[(df.vendor_name.str.lower()==i.vendor_name.lower())&df.valid&~df.duplicate]
    avg=h.total.mean() if not h.empty else 0
    an=bool(avg and i.total>avg*1.3)
    status='Review Required' if (not valid or dup or an) else 'Approved'
    risk='High' if (not valid or dup) else ('Medium' if an else 'Low')
    return {'invoice':i,'valid':valid,'duplicate':dup,'anomaly':an,'status':status,'risk_level':risk}

def save(r):
    i=r['invoice']; df=load()
    if not df[(df.invoice_number==i.invoice_number)&(df.vendor_name==i.vendor_name)&(df.total==i.total)].empty:return
    row=pd.DataFrame([{'vendor_name':i.vendor_name,'invoice_number':i.invoice_number,'invoice_date':i.invoice_date,'due_date':i.due_date or '','currency':i.currency,'subtotal':i.subtotal,'tax':i.tax,'total':i.total,'status':r['status'],'valid':r['valid'],'duplicate':r['duplicate'],'anomaly':r['anomaly'],'risk_level':r['risk_level']}])
    pd.concat([df,row],ignore_index=True).to_csv(DATA,index=False); st.cache_data.clear()

st.title('💰 AI Finance Operations Agent')
st.caption('Invoice extraction • validation • duplicate detection • anomaly detection • finance analytics')
df=load()
st.sidebar.header('Filters')
sv=st.sidebar.multiselect('Vendor',sorted(df.vendor_name.unique()),default=sorted(df.vendor_name.unique()))
ss=st.sidebar.multiselect('Status',sorted(df.status.unique()),default=sorted(df.status.unique()))
sr=st.sidebar.multiselect('Risk',sorted(df.risk_level.unique()),default=sorted(df.risk_level.unique()))
st.sidebar.markdown('---')
up=st.sidebar.file_uploader('Upload invoice PDF',type=['pdf'])
if up and st.sidebar.button('🤖 Process Invoice',use_container_width=True):
    try:
        text=pdf_text(up.getvalue())
        try: i=parse(ai(text)); method='Gemini AI'
        except Exception as e: st.warning(f'AI unavailable: {e}'); i=fallback(text); method='Fallback parser'
        r=analyze(i,df); save(r); st.session_state['last']=(r,method); st.rerun()
    except Exception as e: st.error(f'Processing failed: {e}')
df=load(); f=df[df.vendor_name.isin(sv)&df.status.isin(ss)&df.risk_level.isin(sr)]
a,b,c,d=st.columns(4)
a.metric('Total Invoices',len(f)); b.metric('Total Value',f'€{f.total.sum():,.2f}'); c.metric('Average',f'€{f.total.mean():,.2f}' if len(f) else '€0.00'); d.metric('Review Rate',f'{(f.status=="Review Required").mean()*100:.1f}%' if len(f) else '0.0%')
x,y=st.columns(2)
with x: st.subheader('Processing Status'); st.bar_chart(f.status.value_counts())
with y: st.subheader('Risk Summary'); st.bar_chart(f.risk_level.value_counts().reindex(['Low','Medium','High'],fill_value=0))
x,y=st.columns(2)
with x:
    st.subheader('Monthly Spending')
    if len(f):
        dates=pd.to_datetime(f.invoice_date,errors='coerce'); st.line_chart(f.assign(month=dates.dt.to_period('M').astype(str)).groupby('month').total.sum())
with y: st.subheader('Spending by Vendor'); st.bar_chart(f.groupby('vendor_name').total.sum())
st.subheader('🤖 Risk Detection')
x,y=st.columns(2)
with x:
    an=f[f.anomaly]; st.warning(f'{len(an)} anomaly invoice(s).') if len(an) else st.success('No anomalies detected.');
    if len(an): st.dataframe(an,use_container_width=True,hide_index=True)
with y:
    du=f[f.duplicate]; st.warning(f'{len(du)} duplicate invoice(s).') if len(du) else st.success('No duplicates detected.');
    if len(du): st.dataframe(du,use_container_width=True,hide_index=True)
st.subheader('🧾 Invoice Analysis'); st.dataframe(f[COLS],use_container_width=True,hide_index=True)
if 'last' in st.session_state:
    r,m=st.session_state['last']; i=r['invoice']; st.subheader('📄 Latest Processed Invoice'); st.write({'Extraction method':m,'Vendor':i.vendor_name,'Invoice':i.invoice_number,'Total':i.total,'Status':r['status'],'Risk':r['risk_level'],'Valid':r['valid'],'Duplicate':r['duplicate'],'Anomaly':r['anomaly']})