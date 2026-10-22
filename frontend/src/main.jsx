import React,{useEffect,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {ArrowUpRight} from 'lucide-react';
import {getShop} from './api';
import Storefront from './pages/Storefront';
import Dashboard from './pages/Dashboard';
import './style.css';
import './blue-refresh.css';

function App(){
  const [data,setData]=useState(null);
  const [page,setPage]=useState('site');
  const [error,setError]=useState('');
  const reload=()=>getShop().then(x=>{setData(x);setError('');return x;}).catch(e=>{setError(e.message);throw e;});
  useEffect(()=>{reload().catch(()=>{});},[]);
  // Never reveal admin demo controls on a non-local frontend build.
  const showDemoSwitch=import.meta.env.DEV && window.location.hostname.match(/^(localhost|127\.0\.0\.1)$/);
  return <>
    {showDemoSwitch&&<div className="dev-switch"><b><span>✳</span> BARBEROS <small>LOCAL PILOT</small></b><div><button className={page==='site'?'active':''} onClick={()=>setPage('site')}>CUSTOMER WEBSITE</button><button className={page==='dashboard'?'active':''} onClick={()=>setPage('dashboard')}>ADMIN DASHBOARD <ArrowUpRight size={12}/></button></div></div>}
    {data?(page==='dashboard'&&showDemoSwitch?<Dashboard data={data} refresh={reload}/>:<Storefront data={data}/>):<div className="loading-page"><b>AB<span>.</span></b><p>{error||'Loading website…'}</p><button onClick={()=>reload().catch(()=>{})}>RETRY CONNECTION</button><small>Check that FastAPI is running on http://127.0.0.1:8000</small></div>}
  </>;
}
createRoot(document.getElementById('root')).render(<App/>);
