
import json, math
from pathlib import Path
import requests
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

VERSION='V13'
ROOT=Path(__file__).parent
GREEN='#00D77A'; RED='#FF255B'; GREY='#9BB5C9'; CYAN='#7AC9FF'; ORANGE='#FFB000'
DEFAULT={'default_counters':'TSLA, RKLB, ASTS, SPCX, NVDA, EOSE, ORCL, MU, SKHY, GOOGL, SNDK, AMD, INTC, OKLO','long_entry':35,'long_exit':-20,'short_entry':-25,'short_exit':15,'scores':{'gap_up':18,'high_gap_up':30,'super_gap_up':35,'gap_down':-18,'high_gap_down':-30,'bb_buy':20,'bb_sell':-20,'pivot_buy':30,'up_flag':24,'down_flag':-24,'rsi_bull':20,'rsi_bear':-20,'macd_bull':20,'macd_bear':-20,'pocket_pivot':28,'ma_up':8,'ma_down':-8,'rs_up':5,'rs_down':-5,'macd_pos':3,'macd_neg':-3,'above_ma200':4,'below_ma200':-4}}
try:
    CFG=DEFAULT | json.loads((ROOT/'rules_config.json').read_text(encoding='utf-8'))
    CFG['scores']=DEFAULT['scores'] | CFG.get('scores',{})
except Exception: CFG=DEFAULT
for k,v in {'page':'Cover','lang':'English','selected_ticker':'TSLA','scanner_results':[],'backtest_result':None}.items():
    if k not in st.session_state: st.session_state[k]=v
st.set_page_config(page_title=f'TSLA23T {VERSION}',page_icon='📈',layout='wide')
st.markdown(f"""<style>:root{{--g:{GREEN};--r:{RED};--n:{GREY}}}.stApp{{background:#030911;color:#d6e4ef}}.cover{{text-align:center;padding:2px 12px 8px}}.title{{font-size:58px;font-weight:900;color:#ffe36d;letter-spacing:12px;line-height:1}}.sub{{color:#7ac9ff;letter-spacing:8px}}.author{{border:1px solid #e7b900;color:#e7b900;max-width:600px;margin:10px auto 0;padding:8px}}.copy{{color:#b9e4ff;font-size:13px;margin:0}}div[data-testid="stButton"]{{margin-top:2px!important;margin-bottom:6px!important}}.card{{background:#08111f;border:1px solid #25415d;border-radius:18px;padding:15px;margin:12px 0}}.ticker{{font-size:24px;font-weight:900;color:#f6c72d}}.price{{font-size:30px;font-weight:900}}.badge{{display:inline-block;border:1px solid currentColor;border-radius:999px;padding:6px 13px;margin-left:12px;font-weight:900}}.signal{{display:inline-block;border:1px solid currentColor;border-radius:999px;padding:5px 10px;margin:3px;font-weight:700}}</style>""",unsafe_allow_html=True)

def color(v): return GREEN if v>0 else RED if v<0 else GREY
def suggestion(score):
    if score>=80:return 'STRONG BUY',GREEN
    if score>=60:return 'BUY',GREEN
    if score>=20:return 'WATCH / HOLD',CYAN
    if score>=-19:return 'NEUTRAL',GREY
    if score>=-29:return 'REDUCE / WATCH',ORANGE
    if score>=-39:return 'SELL / CLOSE LONG',RED
    return 'STRONG SELL / SHORT WATCH',RED

def indicators(df):
    df=df.copy()
    for n in [5,10,20,50,60,200,240]: df[f'MA{n}']=df.Close.rolling(n).mean()
    delta=df.Close.diff(); gain=delta.clip(lower=0); loss=-delta.clip(upper=0); rs=gain.ewm(alpha=1/14,adjust=False).mean()/loss.ewm(alpha=1/14,adjust=False).mean().replace(0,np.nan); df['RSI14']=100-100/(1+rs)
    e12=df.Close.ewm(span=12,adjust=False).mean(); e26=df.Close.ewm(span=26,adjust=False).mean(); df['MACD']=e12-e26; df['MACD_signal']=df.MACD.ewm(span=9,adjust=False).mean(); df['MACD_hist']=df.MACD-df.MACD_signal; df['Volume20']=df.Volume.rolling(20).mean(); return df

@st.cache_data(ttl=180,max_entries=40,show_spinner=False)
def fetch(symbol,period='2y'):
    try:
        r=requests.get(f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}',params={'range':period,'interval':'1d'},headers={'User-Agent':'Mozilla/5.0 TSLA23T'},timeout=15); r.raise_for_status(); x=r.json()['chart']['result'][0]; ts=x['timestamp']; q=x['indicators']['quote'][0]; n=len(ts)
        def c(k): return (q.get(k,[])[:n]+[None]*n)[:n]
        df=pd.DataFrame({'Open':c('open'),'High':c('high'),'Low':c('low'),'Close':c('close'),'Volume':c('volume')},index=pd.to_datetime(ts,unit='s',utc=True).tz_convert(None)); df=df.apply(pd.to_numeric,errors='coerce').dropna(subset=['Open','High','Low','Close']); df.Volume=df.Volume.fillna(0); return indicators(df)
    except Exception:return pd.DataFrame()

def add(rows,key,detail): rows.append({'Signal':key,'Score':int(CFG['scores'][key]),'Details':detail})
def signal_rows(df,i,bench=None):
    rows=[]
    if i<25:return rows
    r=df.iloc[i]; p=df.iloc[i-1]; gap=(r.Open-p.Close)/p.Close*100 if p.Close else 0; vm=r.Volume/r.Volume20 if not pd.isna(r.Volume20) and r.Volume20 else np.nan
    if r.Open>p.High and gap>=5:
        add(rows,'super_gap_up',f'Gap {gap:.1f}%, volume {vm:.1f}x') if not pd.isna(vm) and vm>=2.5 else add(rows,'high_gap_up',f'Gap {gap:.1f}%, volume {vm:.1f}x') if not pd.isna(vm) and vm>=1.5 else add(rows,'gap_up',f'Gap {gap:.1f}%')
    if r.Open<p.Low and gap<=-5:add(rows,'high_gap_down' if not pd.isna(vm) and vm>=1.5 else 'gap_down',f'Gap {gap:.1f}%')
    if i>=200:
        old=df.iloc[i-200:i-30]; cur=df.iloc[max(0,i-4):i+1]; pl,ph=old.Low.min(),old.High.max()
        if pl and abs(cur.Low.min()-pl)/pl<=.08:add(rows,'bb_buy','Current low near historical low')
        if ph and abs(cur.High.max()-ph)/ph<=.08:add(rows,'bb_sell','Current high near historical high')
    if i>=60:
        old=df.iloc[i-60:i-20]; cur=df.iloc[i-10:i+1]; oli,cli=old.Low.idxmin(),cur.Low.idxmin(); ohi,chi=old.High.idxmax(),cur.High.idxmax()
        if df.loc[cli,'Low']<df.loc[oli,'Low'] and df.loc[cli,'RSI14']>df.loc[oli,'RSI14']:add(rows,'rsi_bull','Lower price low, higher RSI')
        if df.loc[chi,'High']>df.loc[ohi,'High'] and df.loc[chi,'RSI14']<df.loc[ohi,'RSI14']:add(rows,'rsi_bear','Higher price high, lower RSI')
        if df.loc[cli,'Low']<df.loc[oli,'Low'] and df.loc[cli,'MACD']>df.loc[oli,'MACD']:add(rows,'macd_bull','Lower price low, higher MACD')
        if df.loc[chi,'High']>df.loc[ohi,'High'] and df.loc[chi,'MACD']<df.loc[ohi,'MACD']:add(rows,'macd_bear','Higher price high, lower MACD')
    if i>=12:
        z=df.iloc[i-11:i]; down=z[z.Close<z.Open].Volume; mx=down.max() if len(down) else z.Volume.max()
        if r.Close>r.Open and r.Volume>mx and r.Close>r.MA10:add(rows,'pocket_pivot','Up volume exceeds recent down volume')
    if not any(pd.isna([r.MA5,r.MA10,r.MA20])):
        if r.MA5>r.MA10>r.MA20 and r.Close>r.MA5:add(rows,'ma_up','MA5 > MA10 > MA20')
        if r.MA5<r.MA10<r.MA20 and r.Close<r.MA5:add(rows,'ma_down','MA5 < MA10 < MA20')
    add(rows,'macd_pos' if r.MACD>0 else 'macd_neg',f'MACD {r.MACD:.2f}')
    if not pd.isna(r.MA200):add(rows,'above_ma200' if r.Close>r.MA200 else 'below_ma200',f'MA200 {r.MA200:.2f}')
    return rows

def score_at(df,i): return int(sum(x['Score'] for x in signal_rows(df,i)))
def marker_events(df,long_entry=35,long_exit=-20,short_entry=-25,short_exit=15):
    events=[]; state='Flat'; start=max(200,60)
    for i in range(start,len(df)):
        sc=score_at(df,i); date=df.index[i]; price=float(df.Close.iloc[i]); rules=', '.join(x['Signal'] for x in signal_rows(df,i))
        if state=='Flat' and sc>=long_entry:state='Long';events.append({'Date':date,'Price':price,'Score':sc,'Action':'BUY / LONG ENTRY','Side':'buy','Rules':rules})
        elif state=='Long' and sc<=long_exit:state='Flat';events.append({'Date':date,'Price':price,'Score':sc,'Action':'SELL / CLOSE LONG','Side':'sell','Rules':rules})
        elif state=='Flat' and sc<=short_entry:state='Short';events.append({'Date':date,'Price':price,'Score':sc,'Action':'SHORT ENTRY','Side':'sell','Rules':rules})
        elif state=='Short' and sc>=short_exit:state='Flat';events.append({'Date':date,'Price':price,'Score':sc,'Action':'COVER SHORT','Side':'buy','Rules':rules})
    return events

def chart(df,ticker,height=700,events=None):
    d=df.tail(220); fig=make_subplots(rows=4,cols=1,shared_xaxes=True,vertical_spacing=.025,row_heights=[.56,.16,.16,.12],subplot_titles=(ticker,'Volume','MACD','RSI'))
    fig.add_trace(go.Candlestick(x=d.index,open=d.Open,high=d.High,low=d.Low,close=d.Close,increasing_line_color=GREEN,decreasing_line_color=RED),row=1,col=1)
    for n,c in [(10,GREEN),(20,CYAN),(50,'#ffffff'),(200,'#ff7ac9'),(240,'#ffb000')]:fig.add_trace(go.Scatter(x=d.index,y=d[f'MA{n}'],line=dict(color=c,width=1),name=f'MA{n}'),row=1,col=1)
    fig.add_trace(go.Bar(x=d.index,y=d.Volume,marker_color=np.where(d.Close>=d.Open,GREEN,RED)),row=2,col=1);fig.add_trace(go.Bar(x=d.index,y=d.MACD_hist,marker_color=np.where(d.MACD_hist>=0,GREEN,RED)),row=3,col=1);fig.add_trace(go.Scatter(x=d.index,y=d.MACD,line=dict(color=CYAN)),row=3,col=1);fig.add_trace(go.Scatter(x=d.index,y=d.MACD_signal,line=dict(color='#f6c72d')),row=3,col=1);fig.add_trace(go.Scatter(x=d.index,y=d.RSI14,line=dict(color='#f6c72d')),row=4,col=1)
    visible=[e for e in (events or marker_events(df)) if e['Date'] in d.index]
    for side,symbol,col in [('buy','triangle-up',GREEN),('sell','triangle-down',RED)]:
        ev=[e for e in visible if e['Side']==side]
        if ev:fig.add_trace(go.Scatter(x=[e['Date'] for e in ev],y=[e['Price'] for e in ev],mode='markers',marker=dict(symbol=symbol,size=14,color=col,line=dict(color='white',width=1)),text=[f"{e['Action']}<br>Date: {e['Date'].date()}<br>Price: ${e['Price']:.2f}<br>Score: {e['Score']:+d}<br>{e['Rules']}" for e in ev],hovertemplate='%{text}<extra></extra>',name=side),row=1,col=1)
    fig.update_layout(template='plotly_dark',height=height,showlegend=False,xaxis_rangeslider_visible=False,dragmode='pan',hovermode='x unified');fig.update_yaxes(range=[0,100],row=4,col=1);return fig

def backtest(df,mode,capital,allocation,le,lx,se,sx):
    events=marker_events(df,le,lx,se,sx); trades=[]; equity=capital; open_trade=None
    for e in events:
        if e['Action']=='BUY / LONG ENTRY' and mode in ['Long','Both'] and open_trade is None:open_trade=e|{'Position':'Long','Entry Equity':equity}
        elif e['Action']=='SHORT ENTRY' and mode in ['Short','Both'] and open_trade is None:open_trade=e|{'Position':'Short','Entry Equity':equity}
        elif open_trade and open_trade['Position']=='Long' and e['Action']=='SELL / CLOSE LONG':
            ret=(e['Price']-open_trade['Price'])/open_trade['Price']; pnl=equity*allocation/100*ret; equity+=pnl; trades.append({'Position':'Long','Entry Date':open_trade['Date'].date(),'Entry Price':open_trade['Price'],'Entry Score':open_trade['Score'],'Exit Date':e['Date'].date(),'Exit Price':e['Price'],'Exit Score':e['Score'],'Return %':ret*100,'Profit/Loss $':pnl,'Equity':equity});open_trade=None
        elif open_trade and open_trade['Position']=='Short' and e['Action']=='COVER SHORT':
            ret=(open_trade['Price']-e['Price'])/open_trade['Price']; pnl=equity*allocation/100*ret; equity+=pnl; trades.append({'Position':'Short','Entry Date':open_trade['Date'].date(),'Entry Price':open_trade['Price'],'Entry Score':open_trade['Score'],'Exit Date':e['Date'].date(),'Exit Price':e['Price'],'Exit Score':e['Score'],'Return %':ret*100,'Profit/Loss $':pnl,'Equity':equity});open_trade=None
    return pd.DataFrame(trades),events,equity

def open_chart(ticker):st.session_state.selected_ticker=ticker;st.session_state.page='Chart'
def back_scanner():st.session_state.page='Scanner'
with st.sidebar:
    page=st.radio('Page',['Cover','Scanner','Chart','Backtesting','Portfolio','Guide'],index=['Cover','Scanner','Chart','Backtesting','Portfolio','Guide'].index(st.session_state.page));st.session_state.page=page
    tickers_raw=st.text_area('Counters',CFG['default_counters']);period=st.selectbox('Data period',['6mo','1y','2y','5y'],index=2)
tickers=[x.strip().upper() for x in tickers_raw.replace('\n',',').split(',') if x.strip()]; pcfg={'displaylogo':False,'scrollZoom':True,'responsive':True}
if st.session_state.page=='Cover':
    st.markdown(f"<div class='cover'><div class='title'>TSLA23T</div><div class='sub'>TRADING RULE SYSTEM</div><h3>{VERSION}</h3><div class='author'>Developed by TSLA23T<div class='copy'>© 2026 TSLA23T</div></div></div>",unsafe_allow_html=True)
    if st.button('Enter System',type='primary',use_container_width=True):st.session_state.page='Scanner';st.rerun()
elif st.session_state.page=='Scanner':
    st.header('Scanner')
    if st.button('Run Scanner',type='primary'):
        out=[];bar=st.progress(0)
        for n,t in enumerate(tickers,1):
            bar.progress(n/max(1,len(tickers)),text=t);df=fetch(t,period)
            if not df.empty:
                rs=signal_rows(df,len(df)-1);r,p=df.iloc[-1],df.iloc[-2];out.append({'Ticker':t,'Price':float(r.Close),'Change $':float(r.Close-p.Close),'Change %':float((r.Close/p.Close-1)*100),'Score':int(sum(x['Score'] for x in rs)),'Signals':rs})
        bar.empty();st.session_state.scanner_results=out
    for x in sorted(st.session_state.scanner_results,key=lambda q:q['Score'],reverse=True):
        sg,sgc=suggestion(x['Score']);pc=GREEN if x['Change $']>=0 else RED;sign='+' if x['Change $']>=0 else ''
        st.markdown(f"<div class='card'><div class='ticker'>{x['Ticker']}</div><span class='price'>${x['Price']:.2f}</span><span class='badge' style='color:{sgc}'>{sg}</span><div style='color:{pc}'>{sign}${x['Change $']:.2f} ({sign}{x['Change %']:.2f}%)</div><div style='color:{color(x['Score'])};font-weight:900'>Score: {x['Score']:+d}</div></div>",unsafe_allow_html=True)
        st.markdown(' '.join(f"<span class='signal' style='color:{color(r['Score'])}'>{r['Signal']} ({r['Score']:+d})</span>" for r in x['Signals']),unsafe_allow_html=True)
        df=fetch(x['Ticker'],period)
        with st.expander(f"Chart with Buy/Sell Triangles - {x['Ticker']}"):
            st.plotly_chart(chart(df,x['Ticker'],520),use_container_width=True,config=pcfg)
        st.button(f"View Full Chart - {x['Ticker']}",key='view_'+x['Ticker'],on_click=open_chart,args=(x['Ticker'],))
elif st.session_state.page=='Chart':
    st.header(f"Chart: {st.session_state.selected_ticker}")
    st.button('← Back to Scanner',type='primary',on_click=back_scanner)
    options=tickers or [st.session_state.selected_ticker];idx=options.index(st.session_state.selected_ticker) if st.session_state.selected_ticker in options else 0;tk=st.selectbox('Ticker',options,index=idx);st.session_state.selected_ticker=tk;df=fetch(tk,period)
    if df.empty:st.error('No data found')
    else:st.plotly_chart(chart(df,tk,760),use_container_width=True,config=pcfg)
elif st.session_state.page=='Backtesting':
    st.header('Backtesting Results')
    c1,c2,c3=st.columns(3)
    with c1:bt=st.text_input('Ticker','TSLA').upper();bp=st.selectbox('Backtest period',['1y','2y','5y','10y','max'],index=1);mode=st.selectbox('Mode',['Long','Short','Both'])
    with c2:le=st.number_input('Long Entry',value=35,step=5);lx=st.number_input('Long Exit',value=-20,step=5);se=st.number_input('Short Entry',value=-25,step=5);sx=st.number_input('Short Exit',value=15,step=5)
    with c3:capital=st.number_input('Initial Capital',value=10000.0,step=500.0);allocation=st.number_input('Capital Used per Trade (%)',value=100.0,min_value=1.0,max_value=100.0,step=5.0)
    if st.button('Run Backtest',type='primary'):
        df=fetch(bt,bp)
        if df.empty:st.error('No historical data found')
        else:trades,events,final=backtest(df,mode,capital,allocation,le,lx,se,sx);st.session_state.backtest_result=(bt,df,trades,events,final,capital)
    if st.session_state.backtest_result:
        bt,df,trades,events,final,capital=st.session_state.backtest_result;net=final-capital;ret=net/capital*100 if capital else 0;wins=int((trades['Profit/Loss $']>0).sum()) if not trades.empty else 0;losses=len(trades)-wins if not trades.empty else 0
        m=st.columns(6);m[0].metric('Initial Capital',f'${capital:,.2f}');m[1].metric('Final Equity',f'${final:,.2f}',f'{net:+,.2f}');m[2].metric('Net Profit/Loss',f'${net:+,.2f}');m[3].metric('Total Return',f'{ret:+.2f}%');m[4].metric('Winning Trades',wins);m[5].metric('Losing Trades',losses)
        st.plotly_chart(chart(df,bt,720,events),use_container_width=True,config=pcfg)
        if trades.empty:st.warning('No completed trades matched these thresholds. Try a longer period or lower entry thresholds.')
        else:
            st.dataframe(trades.style.format({'Entry Price':'${:,.2f}','Exit Price':'${:,.2f}','Return %':'{:+.2f}%','Profit/Loss $':'${:+,.2f}','Equity':'${:,.2f}'}),use_container_width=True)
            st.download_button('Download Backtest Results CSV',trades.to_csv(index=False).encode('utf-8-sig'),f'{bt}_V13_backtest.csv')
elif st.session_state.page=='Portfolio':st.header('Portfolio Dashboard');st.info('Portfolio feature retained for the next full merge package.')
else:
    st.header('V13 Guide');st.markdown((ROOT/'TSLA23T_V13_Guidebook.md').read_text(encoding='utf-8'))
