const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const SLUG = import.meta.env.VITE_SHOP_SLUG || 'northside';
export async function api(path, options = {}) {
  const res = await fetch(`${BASE}/api/shops/${SLUG}${path}`, {headers:{'Content-Type':'application/json', ...(options.admin ? {'X-Admin-Token':import.meta.env.VITE_DEMO_ADMIN_TOKEN || 'local-demo-only'} : {})}, ...options, admin:undefined});
  const data = await res.json().catch(()=>({}));
  if(!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `Request failed (${res.status})`);
  return data;
}
export const getShop=()=>api('');
export const getSlots=(day,service,barber)=>api(`/availability?day=${day}&service_id=${service}&barber_id=${barber}`);
export const book=(payload)=>api('/appointments',{method:'POST',body:JSON.stringify(payload)});
export const getAppointments=(day)=>api(`/appointments?day=${day}`,{admin:true});
export const saveHours=(days)=>api('/hours',{method:'PUT',admin:true,body:JSON.stringify({days})});
export const saveException=(payload)=>api('/exceptions',{method:'PUT',admin:true,body:JSON.stringify(payload)});
