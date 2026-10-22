// One reusable API adapter: swap the slug to onboard another business.
const BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const SLUG = import.meta.env.VITE_SHOP_SLUG || 'aaron-binions';
// Frontend admin token exists ONLY in local dev bundles; production needs real auth.
const DEMO_TOKEN = import.meta.env.DEV ? (import.meta.env.VITE_DEMO_ADMIN_TOKEN || 'local-demo-only') : '';

export async function api(path = '', options = {}) {
  const { admin = false, ...rest } = options;
  const response = await fetch(`${BASE}/api/shops/${encodeURIComponent(SLUG)}${path}`, {
    ...rest,
    headers: {
      'Content-Type': 'application/json',
      ...(admin ? { 'X-Admin-Token': DEMO_TOKEN } : {}),
      ...(rest.headers || {}),
    },
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : `Request failed (${response.status})`);
  return result;
}
export const getShop = () => api();
export const getSlots = (day, serviceId, barberId) => api(`/availability?${new URLSearchParams({day, service_id:serviceId, barber_id:barberId})}`);
export const createBooking = (payload) => api('/appointments', { method:'POST', body:JSON.stringify(payload) });
export const getAppointments = (day) => api(`/appointments?day=${day}`, {admin:true});
export const cancelAppointment = (id) => api(`/appointments/${id}/cancel`, {admin:true,method:'PUT'});
export const saveHours = (days) => api('/hours', {admin:true,method:'PUT',body:JSON.stringify({days})});
export const saveException = (exception) => api('/exceptions', {admin:true,method:'PUT',body:JSON.stringify(exception)});
export const getExceptions = () => api('/exceptions', {admin:true});
export const removeException = (day) => api(`/exceptions/${day}`, {admin:true,method:'DELETE'});
export const addService = (service) => api('/services', {admin:true,method:'POST',body:JSON.stringify(service)});
export const updateService = (id,service) => api(`/services/${id}`, {admin:true,method:'PUT',body:JSON.stringify(service)});

export const getAdminServices = () => api('/admin/services',{admin:true});
