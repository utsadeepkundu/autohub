import { useCallback, useEffect, useState } from 'react'
import { Building2, CarFront, CheckCircle2, CircleAlert, ClipboardList, FilePlus2, LoaderCircle, LogIn, MessageSquare, RefreshCw, Save, Store, X } from 'lucide-react'
import { Link } from 'react-router'
import { apiRequest } from '../../services/api'
import { useAuth } from '../../context/AuthContext'
import './DealerDashboard.css'

const emptyProfile = { business_name: '', contact_person: '', email: '', phone: '', alternate_phone: '', website: '', business_description: '', address_line1: '', address_line2: '', locality: '', city: '', state: '', pincode: '', gstin: '', logo_url: '' }
const emptyVehicle = { title: '', make: '', model: '', variant: '', year: '', fuel: 'Petrol', transmission: 'Manual', body_type: 'Hatchback', price: '', km_driven: '0', owner_count: '1', color: '', engine_cc: '', seating_capacity: '', description: '', city: '', state: '', locality: '', pincode: '', primary_image: '', images_text: '', features_text: '' }
const money = (value) => `₹${Number(value || 0).toLocaleString('en-IN')}`

function Field({ label, name, value, onChange, required = false, type = 'text', ...props }) {
  return <label className="dealer-field">{label}<input name={name} type={type} value={value ?? ''} onChange={onChange} required={required} {...props} /></label>
}

export default function DealerDashboard() {
  const { user, isAuthenticated, loading: authLoading } = useAuth()
  const [profile, setProfile] = useState(null)
  const [profileForm, setProfileForm] = useState(emptyProfile)
  const [inventory, setInventory] = useState([])
  const [enquiries, setEnquiries] = useState([])
  const [loading, setLoading] = useState(true)
  const [profileMissing, setProfileMissing] = useState(false)
  const [applicationOpen, setApplicationOpen] = useState(false)
  const [vehicleFormOpen, setVehicleFormOpen] = useState(false)
  const [vehicleForm, setVehicleForm] = useState(emptyVehicle)
  const [editingId, setEditingId] = useState(null)
  const [activeTab, setActiveTab] = useState('inventory')
  const [submitting, setSubmitting] = useState(false)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')

  const loadDashboard = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await apiRequest('/dealers/profile/')
      setProfile(data)
      setProfileForm(data)
      setProfileMissing(false)
      const vehicles = await apiRequest('/dealers/inventory/')
      setInventory(Array.isArray(vehicles) ? vehicles : [])
      if (data.verification_status === 'approved') {
        try {
          const leads = await apiRequest('/enquiries/dealer/')
          setEnquiries(Array.isArray(leads) ? leads : [])
        } catch (leadError) {
          setEnquiries([])
          if (leadError.status !== 403) throw leadError
        }
      } else {
        setEnquiries([])
      }
    } catch (err) {
      if (err.status === 404) {
        setProfile(null)
        setProfileMissing(true)
        setInventory([])
        setEnquiries([])
      } else {
        setError(err.message || 'Unable to load the dealer dashboard.')
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!isAuthenticated) return undefined
    let active = true
    Promise.resolve().then(() => {
      if (active) loadDashboard()
    })
    return () => { active = false }
  }, [isAuthenticated, loadDashboard])

  const updateProfile = (event) => setProfileForm((current) => ({ ...current, [event.target.name]: event.target.value }))
  const updateVehicle = (event) => setVehicleForm((current) => ({ ...current, [event.target.name]: event.target.value }))

  const submitApplication = async (event) => {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    setNotice('')
    try {
      const payload = { ...profileForm }
      await apiRequest('/dealers/apply/', { method: 'POST', body: JSON.stringify(payload) })
      setNotice('Your dealer application has been submitted for verification.')
      setApplicationOpen(false)
      await loadDashboard()
    } catch (err) {
      setError(err.message || 'Unable to submit your application.')
    } finally {
      setSubmitting(false)
    }
  }

  const openNewVehicle = () => {
    setEditingId(null)
    setVehicleForm(emptyVehicle)
    setVehicleFormOpen(true)
    setError('')
  }

  const openEditVehicle = (vehicle) => {
    setEditingId(vehicle.id)
    setVehicleForm({ ...emptyVehicle, ...vehicle, images_text: (vehicle.images || []).join('\n'), features_text: (vehicle.features || []).join('\n') })
    setVehicleFormOpen(true)
    setError('')
  }

  const submitVehicle = async (event) => {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    setNotice('')
    const payload = {
      ...vehicleForm,
      year: Number(vehicleForm.year),
      price: Number(vehicleForm.price),
      km_driven: Number(vehicleForm.km_driven),
      owner_count: Number(vehicleForm.owner_count),
      engine_cc: vehicleForm.engine_cc ? Number(vehicleForm.engine_cc) : null,
      seating_capacity: vehicleForm.seating_capacity ? Number(vehicleForm.seating_capacity) : null,
      images: vehicleForm.images_text.split('\n').map((item) => item.trim()).filter(Boolean),
      features: vehicleForm.features_text.split('\n').map((item) => item.trim()).filter(Boolean),
    }
    delete payload.images_text
    delete payload.features_text
    try {
      await apiRequest(editingId ? `/dealers/inventory/${editingId}/` : '/dealers/inventory/', { method: editingId ? 'PATCH' : 'POST', body: JSON.stringify(payload) })
      setNotice(editingId ? 'Listing updated and sent for review again.' : 'Vehicle listing submitted for admin review.')
      setVehicleFormOpen(false)
      await loadDashboard()
    } catch (err) {
      setError(err.message || 'Unable to save this vehicle listing.')
    } finally {
      setSubmitting(false)
    }
  }

  const updateEnquiry = async (enquiryId, event) => {
    const status = event.target.value
    if (!status) return
    setError('')
    try {
      await apiRequest(`/enquiries/dealer/${enquiryId}/`, { method: 'PATCH', body: JSON.stringify({ status }) })
      setEnquiries((current) => current.map((item) => item.id === enquiryId ? { ...item, status } : item))
      setNotice('Enquiry status updated.')
    } catch (err) {
      setError(err.message || 'Unable to update the enquiry.')
    }
  }

  if (authLoading || (isAuthenticated && loading)) return <main className="dealer-state"><LoaderCircle className="dealer-spin" size={32} /><p>Loading dealer workspace…</p></main>
  if (!isAuthenticated) return <main className="dealer-gate"><div><div className="dealer-gate-icon"><Store size={34} /></div><span className="dealer-eyebrow">AUTOHUB FOR BUSINESS</span><h1>Grow your dealership with AutoHub.</h1><p>Sign in with your account to apply as a dealer, manage your inventory and respond to customer enquiries.</p><Link to="/login" className="dealer-primary"><LogIn size={17} /> Sign in to continue</Link><p className="dealer-gate-foot">New to AutoHub? <Link to="/register">Create an account</Link></p></div></main>

  return (
    <main className="dealer-page"><div className="dealer-container"><header className="dealer-welcome"><div><span className="dealer-eyebrow">AUTOHUB BUSINESS DESK</span><h1>Dealer workspace</h1><p>Manage your showroom presence, vehicle listings and customer leads.</p><span className="dealer-account">Signed in as {user?.email}</span></div><button type="button" className="dealer-refresh" onClick={loadDashboard}><RefreshCw size={15} /> Refresh</button></header>
      {notice && <div className="dealer-notice"><CheckCircle2 size={16} />{notice}<button type="button" aria-label="Dismiss notice" onClick={() => setNotice('')}><X size={15} /></button></div>}
      {error && <div className="dealer-error"><CircleAlert size={16} />{error}<button type="button" aria-label="Dismiss error" onClick={() => setError('')}><X size={15} /></button></div>}

      {profileMissing ? <section className="dealer-apply-card"><div className="dealer-apply-icon"><Building2 size={30} /></div><span className="dealer-eyebrow">BECOME AN AUTOHUB PARTNER</span><h2>Bring your dealership online.</h2><p>Submit your business details for verification. Once approved by AutoHub administration, you can publish inventory and manage enquiries.</p><button type="button" className="dealer-primary" onClick={() => setApplicationOpen((open) => !open)}>{applicationOpen ? 'Close application' : 'Apply as a dealer'}</button>{applicationOpen && <form className="dealer-form" onSubmit={submitApplication}><div className="dealer-form-grid">{[
        ['Business name','business_name'],['Contact person','contact_person'],['Business email','email','email'],['Phone number','phone','tel'],['Alternate phone','alternate_phone','tel'],['Website','website','url'],['Address line 1','address_line1'],['Address line 2','address_line2'],['Locality','locality'],['City','city'],['State','state'],['PIN code','pincode'],['GSTIN','gstin'],['Logo URL','logo_url','url'],
      ].map(([label,name,type='text']) => <Field key={name} label={label} name={name} type={type} value={profileForm[name]} onChange={updateProfile} required={['business_name','contact_person','email','phone','address_line1','city','state','pincode'].includes(name)} />)}</div><label className="dealer-field">Business description<textarea name="business_description" value={profileForm.business_description} onChange={updateProfile} rows="3" /></label><button className="dealer-primary" type="submit" disabled={submitting}>{submitting ? <LoaderCircle className="dealer-spin" size={16} /> : <Save size={16} />} Submit application</button></form>}</section> : <>
        <section className="dealer-profile-banner"><div className="dealer-profile-logo"><Building2 size={28} /></div><div className="dealer-profile-text"><span className="dealer-eyebrow">DEALERSHIP PROFILE</span><h2>{profile?.business_name}</h2><p>{[profile?.city, profile?.state].filter(Boolean).join(', ')} · {profile?.email}</p></div><span className={`dealer-status dealer-status-${profile?.verification_status}`}>{profile?.verification_status || 'unknown'}</span></section>
        {profile?.verification_status !== 'approved' && <section className="dealer-pending-card"><CircleAlert size={22} /><div><h3>Application {profile?.verification_status === 'rejected' ? 'requires attention' : 'under verification'}</h3><p>{profile?.verification_status === 'rejected' ? 'Your dealer application was not approved. Contact AutoHub support for next steps.' : 'Your business details have been submitted. Inventory publishing and customer enquiry access will be enabled after admin approval.'}</p></div></section>}
        <div className="dealer-tabs"><button type="button" className={activeTab === 'inventory' ? 'active' : ''} onClick={() => setActiveTab('inventory')}><CarFront size={16} /> Inventory <span>{inventory.length}</span></button><button type="button" className={activeTab === 'enquiries' ? 'active' : ''} onClick={() => setActiveTab('enquiries')}><MessageSquare size={16} /> Enquiries <span>{enquiries.length}</span></button></div>
        {activeTab === 'inventory' && <section className="dealer-panel"><div className="dealer-panel-heading"><div><span className="dealer-eyebrow">YOUR VEHICLES</span><h2>Inventory management</h2></div><button type="button" className="dealer-primary" disabled={profile?.verification_status !== 'approved'} onClick={openNewVehicle}><FilePlus2 size={16} /> Add vehicle</button></div>{profile?.verification_status === 'approved' ? inventory.length ? <div className="dealer-inventory-list">{inventory.map((vehicle) => <article className="dealer-inventory-item" key={vehicle.id}><div className="dealer-inventory-image">{vehicle.primary_image ? <img src={vehicle.primary_image} alt={vehicle.title} /> : <CarFront size={28} />}</div><div className="dealer-inventory-info"><h3>{vehicle.title}</h3><p>{vehicle.year} · {vehicle.fuel} · {vehicle.transmission} · {vehicle.city}</p><strong>{money(vehicle.price)}</strong></div><span className={`dealer-listing-status status-${vehicle.status}`}>{String(vehicle.status || '').replace(/_/g, ' ')}</span><button type="button" className="dealer-outline-button" onClick={() => openEditVehicle(vehicle)}>Edit</button></article>)}</div> : <div className="dealer-empty"><CarFront size={35} /><h3>No inventory yet</h3><p>Add your first vehicle listing to start building your showroom.</p></div> : <div className="dealer-empty"><CircleAlert size={30} /><h3>Inventory tools unlock after approval</h3><p>You can prepare your vehicle details now; publishing is restricted until your dealer profile is approved.</p></div>}</section>}
        {activeTab === 'enquiries' && <section className="dealer-panel"><div className="dealer-panel-heading"><div><span className="dealer-eyebrow">CUSTOMER LEADS</span><h2>Enquiry inbox</h2></div><span className="dealer-enquiry-total">{enquiries.length} total</span></div>{profile?.verification_status !== 'approved' ? <div className="dealer-empty"><CircleAlert size={30} /><h3>Enquiry access is not active</h3><p>Only approved and active dealers can access customer enquiries.</p></div> : enquiries.length ? <div className="dealer-enquiry-list">{enquiries.map((item) => <article className="dealer-enquiry-item" key={item.id}><div className="dealer-enquiry-top"><div><h3>{item.customer_name}</h3><span>{item.vehicle_title}</span></div><select value={item.status} onChange={(event) => updateEnquiry(item.id,event)}><option value="new" disabled>New</option><option value="contacted">Contacted</option><option value="converted">Converted</option><option value="closed">Closed</option></select></div><p>{item.message || 'No additional message.'}</p><div className="dealer-enquiry-contact"><a href={`tel:${item.phone}`}>{item.phone}</a>{item.email && <a href={`mailto:${item.email}`}>{item.email}</a>}<span>{new Date(item.created_at).toLocaleString('en-IN')}</span></div></article>)}</div> : <div className="dealer-empty"><ClipboardList size={34} /><h3>No customer enquiries yet</h3><p>Customer messages about your published vehicles will appear here.</p></div>}</section>}
      </>}

      {vehicleFormOpen && <div className="dealer-modal-backdrop" onClick={() => setVehicleFormOpen(false)}><section className="dealer-modal" onClick={(event) => event.stopPropagation()}><header><div><span className="dealer-eyebrow">SHOWROOM INVENTORY</span><h2>{editingId ? 'Edit vehicle listing' : 'Add a vehicle'}</h2></div><button type="button" onClick={() => setVehicleFormOpen(false)} aria-label="Close"><X size={20} /></button></header><form onSubmit={submitVehicle}><div className="dealer-form-grid">{[
        ['Listing title','title','text',true],['Manufacturer','make','text',true],['Model','model','text',true],['Variant','variant','text',false],['Year','year','number',true],['Price (INR)','price','number',true],['Kilometres driven','km_driven','number',true],['Owners','owner_count','number',true],['Colour','color','text',false],['Engine (cc)','engine_cc','number',false],['Seating capacity','seating_capacity','number',false],['City','city','text',true],['State','state','text',true],['Locality','locality','text',false],['PIN code','pincode','text',true],['Primary image URL','primary_image','url',false],
      ].map(([label,name,type='text',required=false]) => <Field key={name} label={label} name={name} type={type} value={vehicleForm[name]} onChange={updateVehicle} required={required} min={type === 'number' ? 0 : undefined} />)}
      <label className="dealer-field">Fuel<select name="fuel" value={vehicleForm.fuel} onChange={updateVehicle}><option>Petrol</option><option>Diesel</option><option>CNG</option><option>LPG</option><option>Electric</option><option>Hybrid</option><option>Other</option></select></label><label className="dealer-field">Transmission<select name="transmission" value={vehicleForm.transmission} onChange={updateVehicle}><option>Manual</option><option>Automatic</option><option>AMT</option><option>CVT</option><option>DCT</option></select></label><label className="dealer-field">Body type<select name="body_type" value={vehicleForm.body_type} onChange={updateVehicle}><option>Hatchback</option><option>Sedan</option><option>SUV</option><option>MUV</option><option>Coupe</option><option>Convertible</option><option>Pickup</option><option>Van</option><option>Other</option></select></label></div><label className="dealer-field">Description<textarea name="description" value={vehicleForm.description} onChange={updateVehicle} rows="3" /></label><label className="dealer-field">Additional image URLs (one per line)<textarea name="images_text" value={vehicleForm.images_text} onChange={updateVehicle} rows="2" placeholder="https://..." /></label><label className="dealer-field">Features (one per line)<textarea name="features_text" value={vehicleForm.features_text} onChange={updateVehicle} rows="3" placeholder="ABS&#10;Airbags&#10;Reverse camera" /></label><p className="dealer-form-note">New listings and edited listings are sent to AutoHub for admin review. Dealers cannot publish listings directly.</p><button className="dealer-primary" type="submit" disabled={submitting}>{submitting ? <LoaderCircle className="dealer-spin" size={16} /> : <Save size={16} />} {editingId ? 'Save changes' : 'Submit for review'}</button></form></section></div>}
    </div></main>
  )
}
