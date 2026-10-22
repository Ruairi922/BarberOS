import React,{useEffect,useState} from 'react';
import {ArrowLeft,ArrowRight,Check,ChevronRight,Clock3,Scissors,X,LoaderCircle,CheckCircle2,CalendarDays} from 'lucide-react';
import {createBooking,getSlots} from '../api';
import {fmtEUR,prettyDate,shiftDay,todayISO} from '../utils';

export default function BookingFlow({data,onClose,initialService=null}) {
  const [step,setStep]=useState(initialService ? 1 : 0);
  const [service,setService]=useState(initialService);
  const [day,setDay]=useState(todayISO());
  const [slot,setSlot]=useState(null);
  const [slots,setSlots]=useState([]);
  const [loadingSlots,setLoadingSlots]=useState(false);
  const [bookingBusy,setBookingBusy]=useState(false);
  const [customer,setCustomer]=useState({customer_name:'',customer_email:''});
  const [error,setError]=useState('');
  const [confirmation,setConfirmation]=useState(null);
  const barber=data.barbers[0];

  useEffect(()=>{
    const old=document.body.style.overflow;
    document.body.style.overflow='hidden';
    const key=e=>{if(e.key==='Escape')onClose();};
    document.addEventListener('keydown',key);
    return ()=>{document.body.style.overflow=old;document.removeEventListener('keydown',key);};
  },[onClose]);

  useEffect(()=>{
    if (step!==1 || !service || !barber) return;
    let active=true;setLoadingSlots(true);setSlots([]);setSlot(null);setError('');
    getSlots(day,service.id,barber.id)
      .then(result=>{if(active)setSlots(result.slots||[]);})
      .catch(err=>{if(active)setError(err.message);})
      .finally(()=>{if(active)setLoadingSlots(false);});
    return ()=>{active=false;};
  },[step,day,service,barber?.id]);

  async function submit(event) {
    event.preventDefault();setBookingBusy(true);setError('');
    try {
      const result=await createBooking({service_id:service.id,barber_id:barber.id,day,time:slot,...customer});
      setConfirmation(result);setStep(3);
    } catch(err){
      setError(err.message);
      if(/slot.*available/i.test(err.message)) setStep(1);
    } finally {setBookingBusy(false);}
  }

  return <div className="booking-overlay" onMouseDown={e=>{if(e.target===e.currentTarget)onClose();}}>
    <section className="booking-dialog" role="dialog" aria-modal="true" aria-label="Book with Aaron">
      <div className="book-header"><div><b>AB<span className="lime">.</span></b><span>BOOK AN APPOINTMENT</span></div><button className="bare-icon" aria-label="Close booking" onClick={onClose}><X size={22}/></button></div>
      {step<3&&<div className="book-progress"><span style={{width:`${(step+1)/3*100}%`}}/></div>}
      <div className="book-body">
        {step<3&&<div className="book-heading"><div className="micro dark">0{step+1} / 03 — {['YOUR SERVICE','PICK YOUR TIME','YOUR DETAILS'][step]}</div><h2>{['Choose a service','Choose a date and time','Your details'][step]}</h2><p>{['Select a service below. Prices and durations are unconfirmed demo values.','Select an available appointment time.','Enter your details to complete this test booking. No email is sent.'][step]}</p></div>}
        {step===0&&<div className="book-service-list">{data.services.map(s=><button key={s.id} className="book-service" onClick={()=>{setService(s);setStep(1);}}><span className="book-service-icon"><Scissors size={21}/></span><span className="book-service-text"><b>{s.name}</b><small>{s.duration_min} MIN · {s.description}</small></span><span className="book-service-price">{fmtEUR(s.price_cents)} <ChevronRight size={17}/></span></button>)}</div>}
        {step===1&&<><div className="booking-chosen"><Scissors size={16}/><span>{service.name}</span><strong>{fmtEUR(service.price_cents)}</strong></div><div className="date-strip">{Array.from({length:7},(_,i)=>{const d=shiftDay(todayISO(),i);return <button key={d} className={day===d?'chosen':''} onClick={()=>setDay(d)}><small>{prettyDate(d,{weekday:'short'}).toUpperCase()}</small><strong>{prettyDate(d,{day:'numeric'})}</strong></button>;})}</div><label className="date-inline"><CalendarDays size={16}/> Or choose a date in the next 30 days <input type="date" min={todayISO()} max={shiftDay(todayISO(),30)} value={day} onChange={e=>setDay(e.target.value)}/></label><div className="slot-heading"><b>Available on {prettyDate(day,{weekday:'short',month:'short',day:'numeric'})}</b><small>IRELAND TIME</small></div>{loadingSlots?<div className="slot-empty"><LoaderCircle className="spin"/> Checking availability…</div>:slots.length?<div className="slot-grid">{slots.map(x=><button key={x} className={slot===x?'chosen':''} onClick={()=>setSlot(x)}>{x}</button>)}</div>:<div className="slot-empty"><Clock3/> No slots available this day. Choose another date.</div>}<button className="primary-button wide" disabled={!slot||loadingSlots} onClick={()=>setStep(2)}>CONTINUE <ArrowRight size={17}/></button></>}
        {step===2&&<><div className="booking-chosen"><CalendarDays size={17}/><span>{service.name} · {prettyDate(day)} at {slot}</span><strong>{fmtEUR(service.price_cents)}</strong></div><form className="details-form" onSubmit={submit}><label>FULL NAME<input required minLength={2} maxLength={100} autoComplete="name" placeholder="Your full name" value={customer.customer_name} onChange={e=>setCustomer({...customer,customer_name:e.target.value})}/></label><label>EMAIL ADDRESS<input required type="email" maxLength={250} autoComplete="email" placeholder="you@example.com" value={customer.customer_email} onChange={e=>setCustomer({...customer,customer_email:e.target.value})}/></label><p className="form-note">Local demo only. This booking is stored in your local database; no confirmation email or text is sent. Do not enter real customer details until privacy and security work is completed.</p><button className="primary-button wide" disabled={bookingBusy} type="submit">{bookingBusy?<LoaderCircle className="spin" size={18}/>:<>CONFIRM TEST BOOKING <ArrowRight size={17}/></>}</button></form></>}
        {step===3&&<div className="book-success"><div className="success-symbol"><Check size={39}/></div><div className="micro dark">TEST BOOKING</div><h2>Test booking saved</h2><p>Your test booking has been saved to the BarberOS database.</p><div className="receipt"><b>Booking #{confirmation?.id}</b><span>{service.name} with {barber?.name}</span><span>{prettyDate(day)} · {slot}</span><strong>{fmtEUR(service.price_cents)}</strong></div><div className="notice-line">No email or SMS was sent. This is not a live public reservation.</div><button className="primary-button wide" onClick={onClose}>CLOSE <ArrowRight size={17}/></button></div>}
        {error&&<div className="inline-error">{error}</div>}
        {step>0&&step<3&&<button className="back-action" onClick={()=>{setError('');setStep(step-1);}}><ArrowLeft size={15}/> BACK</button>}
      </div>
    </section>
  </div>;
}
