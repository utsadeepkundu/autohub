import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'
import { ArrowLeft, CheckCircle2, Gauge, LoaderCircle, MapPin, Send } from 'lucide-react'
import { getDealerMarketplaceVehicle, submitVehicleEnquiry } from '../../services/dealerMarketplace'
import { useAuth } from '../../context/AuthContext'
import './DealerMarketplace.css'

const money = (value) => `₹${Number(value || 0).toLocaleString('en-IN')}`

export default function DealerVehicleDetailsPage() {
  const { vehicleId } = useParams()
  const { user } = useAuth()
  const [vehicle, setVehicle] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadedFor, setLoadedFor] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState('')
  const [form, setForm] = useState({ customer_name: '', phone: '', email: user?.email || '', message: 'I am interested in this vehicle. Please contact me with more details.', preferred_contact_method: 'phone', consent_to_contact: false })

  useEffect(() => {
    let active = true
    getDealerMarketplaceVehicle(vehicleId).then((data) => { if (active) { setVehicle(data); setError('') } }).catch((err) => { if (active) { setVehicle(null); setError(err.message || 'Vehicle not found.') } }).finally(() => { if (active) { setLoading(false); setLoadedFor(vehicleId) } })
    return () => { active = false }
  }, [vehicleId])

  const update = (event) => setForm((current) => ({ ...current, [event.target.name]: event.target.type === 'checkbox' ? event.target.checked : event.target.value }))
  const submit = async (event) => {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    setSuccess('')
    try {
      await submitVehicleEnquiry({ ...form, vehicle_id: vehicleId })
      setSuccess('Your enquiry has been sent to the dealer. They can now contact you using your preferred method.')
      setForm((current) => ({ ...current, message: '' }))
    } catch (err) {
      setError(err.message || 'Unable to submit your enquiry.')
    } finally { setSubmitting(false) }
  }

  if (loading || loadedFor !== vehicleId) return <main className="dm-detail-state"><LoaderCircle className="dm-spin" /> Loading vehicle…</main>
  if (!vehicle) return <main className="dm-detail-state"><h2>Vehicle unavailable</h2><p>{error || 'This dealer listing is no longer available.'}</p><Link to="/dealer-marketplace">Back to dealer listings</Link></main>

  return <main className="dm-detail-page"><div className="dm-detail-container"><Link className="dm-back" to="/dealer-marketplace"><ArrowLeft size={16} /> All dealer cars</Link><div className="dm-detail-heading"><div><span>VERIFIED DEALER LISTING</span><h1>{vehicle.title}</h1><p><MapPin size={15} /> {[vehicle.locality, vehicle.city, vehicle.state].filter(Boolean).join(', ')}</p></div><strong>{money(vehicle.price)}</strong></div><div className="dm-detail-layout"><section className="dm-detail-main"><div className="dm-detail-image">{vehicle.primary_image ? <img src={vehicle.primary_image} alt={vehicle.title} /> : <div><Gauge size={60} /><span>Vehicle image not provided</span></div>}</div><div className="dm-detail-specs">{[['Year',vehicle.year],['Kilometres',`${Number(vehicle.km_driven || 0).toLocaleString('en-IN')} km`],['Fuel',vehicle.fuel],['Transmission',vehicle.transmission],['Body type',vehicle.body_type],['Owners',vehicle.owner_count],['Colour',vehicle.color],['Engine',vehicle.engine_cc ? `${vehicle.engine_cc} cc` : '—']].map(([label,value]) => <div key={label}><span>{label}</span><strong>{value || '—'}</strong></div>)}</div><section className="dm-detail-description"><h2>About this vehicle</h2><p>{vehicle.description || 'The dealer has not provided an additional description for this vehicle.'}</p>{Array.isArray(vehicle.features) && vehicle.features.length > 0 && <div className="dm-feature-tags">{vehicle.features.map((feature) => <span key={feature}>{feature}</span>)}</div>}</section><div className="dm-dealer-card"><div><span>SELLING DEALER</span><h3>{vehicle.dealer_name}</h3><p>{vehicle.city}, {vehicle.state}</p></div><CheckCircle2 size={24} /></div></section><aside className="dm-enquiry-card"><span className="dm-form-eyebrow">CONTACT THE DEALER</span><h2>Interested in this car?</h2><p>Send a quick enquiry and the dealership can get in touch.</p>{success ? <div className="dm-enquiry-success"><CheckCircle2 size={26} /><strong>Enquiry sent</strong><span>{success}</span><button type="button" onClick={() => setSuccess('')}>Send another enquiry</button></div> : <form onSubmit={submit}><label>Your name<input name="customer_name" required minLength={2} value={form.customer_name} onChange={update} placeholder="Full name" /></label><label>Phone number<input name="phone" type="tel" required value={form.phone} onChange={update} placeholder="10-digit mobile number" /></label><label>Email address<input name="email" type="email" required={form.preferred_contact_method === 'email'} value={form.email} onChange={update} placeholder="Optional unless email contact is selected" /></label><label>Preferred contact<select name="preferred_contact_method" value={form.preferred_contact_method} onChange={update}><option value="phone">Phone call</option><option value="whatsapp">WhatsApp</option><option value="email">Email</option></select></label><label>Message<textarea name="message" rows="3" value={form.message} onChange={update} placeholder="Ask about this vehicle…" /></label><label className="dm-consent"><input type="checkbox" name="consent_to_contact" checked={form.consent_to_contact} onChange={update} required /><span>I agree that this dealer may contact me about this vehicle.</span></label>{error && <div className="dm-form-error">{error}</div>}<button type="submit" disabled={submitting}>{submitting ? <LoaderCircle className="dm-spin" size={16} /> : <Send size={16} />} Send enquiry</button></form>}</aside></div></div></main>
}
