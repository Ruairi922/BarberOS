export const fmtEUR = cents => cents == null ? 'Price TBC' : `€${(cents / 100).toFixed(cents % 100 ? 2 : 0)}`;
export const todayISO = () => { const d = new Date(); return localISO(d); };
export const localISO = d => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
export const shiftDay = (iso, amount) => { const d = new Date(`${iso}T12:00:00`); d.setDate(d.getDate()+amount); return localISO(d); };
export const prettyDate = (iso, options = { weekday:'long', day:'numeric', month:'long' }) =>
  new Date(`${iso}T12:00:00`).toLocaleDateString('en-IE', options);
export const weekDays = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
export const options15 = Array.from({length:65},(_,i) => {const n = 6*60 + i*15;return `${String(Math.floor(n/60)).padStart(2,'0')}:${String(n%60).padStart(2,'0')}`;});
