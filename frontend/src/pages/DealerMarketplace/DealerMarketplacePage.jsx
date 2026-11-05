import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { ArrowRight, CarFront, ChevronLeft, ChevronRight, Fuel, Gauge, LoaderCircle, MapPin, Search, Settings2, SlidersHorizontal } from 'lucide-react'
import { getDealerMarketplaceFilters, getDealerMarketplaceVehicles } from '../../services/dealerMarketplace'
import './DealerMarketplace.css'

const PAGE_SIZE = 9
const initial = { search: '', make: '', model: '', city: '', fuel: '', transmission: '', body_type: '', min_price: '', max_price: '', min_year: '', max_year: '', ordering: '-published_at' }
const money = (value) => `₹${Number(value || 0).toLocaleString('en-IN')}`

export default function DealerMarketplacePage() {
  const [searchParams] = useSearchParams()
  const [filters, setFilters] = useState({ ...initial, search: searchParams.get('search') || '' })
  const [applied, setApplied] = useState({ ...initial, search: searchParams.get('search') || '' })
  const [options, setOptions] = useState({})
  const [cars, setCars] = useState([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [mobileFilters, setMobileFilters] = useState(false)
  const totalPages = Math.max(1, Math.ceil(count / PAGE_SIZE))

  useEffect(() => {
    let active = true
    getDealerMarketplaceFilters().then((data) => { if (active) setOptions(data || {}) }).catch(() => {})
    return () => { active = false }
  }, [])

  useEffect(() => {
    let active = true
    getDealerMarketplaceVehicles({ ...applied, page, page_size: PAGE_SIZE })
      .then((data) => { if (active) { setCars(data.results || []); setCount(Number(data.count) || 0) } })
      .catch((err) => { if (active) setError(err.message || 'Unable to load dealer vehicles.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [applied, page])

  const update = (event) => setFilters((current) => ({ ...current, [event.target.name]: event.target.value }))
  const apply = (event) => { event.preventDefault(); setLoading(true); setError(''); setApplied({ ...filters }); setPage(1); setMobileFilters(false) }
  const reset = () => { setLoading(true); setError(''); setFilters(initial); setApplied(initial); setPage(1); setMobileFilters(false) }
  const fields = [['make','Manufacturer',options.makes],['model','Model',options.models],['city','City',options.cities],['fuel','Fuel',options.fuels],['transmission','Transmission',options.transmissions],['body_type','Body type',options.body_types]]

  const filterPanel = <form className="dm-filter-form" onSubmit={apply}><div className="dm-filter-heading"><h3>Refine results</h3><button type="button" onClick={reset}>Reset</button></div>{fields.map(([name,label,items]) => <label key={name}>{label}<select name={name} value={filters[name]} onChange={update}><option value="">All {label.toLowerCase()}s</option>{(items || []).map((item) => <option key={item} value={item}>{item}</option>)}</select></label>)}<div className="dm-filter-range"><label>Minimum price<input type="number" name="min_price" min="0" value={filters.min_price} onChange={update} placeholder="₹ Min" /></label><label>Maximum price<input type="number" name="max_price" min="0" value={filters.max_price} onChange={update} placeholder="₹ Max" /></label></div><div className="dm-filter-range"><label>From year<input type="number" name="min_year" min="1886" value={filters.min_year} onChange={update} placeholder="From" /></label><label>To year<input type="number" name="max_year" min="1886" value={filters.max_year} onChange={update} placeholder="To" /></label></div><button className="dm-apply" type="submit"><SlidersHorizontal size={15} /> Apply filters</button></form>

  return <main className="dealer-marketplace-page"><section className="dm-hero"><span>APPROVED AUTOHUB DEALERS</span><h1>Cars from showrooms<br /><em>you can connect with.</em></h1><p>Explore dealer-listed vehicles and send an enquiry directly to the showroom.</p><form onSubmit={apply}><Search size={18} /><input name="search" value={filters.search} onChange={update} placeholder="Search make, model, variant or city" /><button type="submit">Search</button></form></section><section className="dm-main"><header className="dm-main-heading"><div><span>DEALER INVENTORY</span><h2>Available showroom cars</h2><p>{count.toLocaleString('en-IN')} published listings from verified dealers</p></div><button className="dm-mobile-filter" type="button" onClick={() => setMobileFilters(true)}><SlidersHorizontal size={16} /> Filters</button></header><div className="dm-layout"><aside>{filterPanel}</aside><div className="dm-results"><div className="dm-sort"><span>{count.toLocaleString('en-IN')} vehicles</span><label>Sort by <select value={applied.ordering} onChange={(event) => { const value = event.target.value; setLoading(true); setError(''); setFilters((current) => ({ ...current, ordering: value })); setApplied((current) => ({ ...current, ordering: value })); setPage(1) }}><option value="-published_at">Recently added</option><option value="price">Price: Low to high</option><option value="-price">Price: High to low</option><option value="-year">Newest first</option><option value="-km_driven">Lowest kilometres</option></select></label></div>
      {loading ? <div className="dm-state"><LoaderCircle className="dm-spin" /><p>Loading dealer vehicles…</p></div> : error ? <div className="dm-state"><CarFront size={35} /><h3>Could not load listings</h3><p>{error}</p></div> : cars.length ? <><div className="dm-grid">{cars.map((car) => <article className="dm-card" key={car.id}><Link to={`/dealer-marketplace/${car.id}`} className="dm-card-image">{car.primary_image ? <img src={car.primary_image} alt={car.title} /> : <CarFront size={42} />}<span>DEALER LISTED</span></Link><div className="dm-card-content"><span className="dm-dealer-name">{car.dealer_name}</span><Link to={`/dealer-marketplace/${car.id}`}><h3>{car.title}</h3></Link><p><MapPin size={13} /> {[car.locality, car.city].filter(Boolean).join(', ')}</p><div className="dm-specs"><span><Gauge size={14} /> {Number(car.km_driven || 0).toLocaleString('en-IN')} km</span><span><Fuel size={14} /> {car.fuel}</span><span><Settings2 size={14} /> {car.transmission}</span></div><div className="dm-card-bottom"><strong>{money(car.price)}</strong><Link to={`/dealer-marketplace/${car.id}`}>View & enquire <ArrowRight size={14} /></Link></div></div></article>)}</div><div className="dm-pagination"><button type="button" disabled={page <= 1} onClick={() => { setLoading(true); setPage((value) => value - 1) }}><ChevronLeft size={16} /> Previous</button><span>Page {page} of {totalPages}</span><button type="button" disabled={page >= totalPages} onClick={() => { setLoading(true); setPage((value) => value + 1) }}>Next <ChevronRight size={16} /></button></div></> : <div className="dm-state"><CarFront size={40} /><h3>No dealer listings available yet</h3><p>Approved dealers' published vehicles will appear here. You can still explore the imported used-car marketplace.</p><Link to="/used-cars">Browse used cars <ArrowRight size={15} /></Link></div>}</div></div></section>
    {mobileFilters && <div className="dm-drawer-backdrop" onClick={() => setMobileFilters(false)}><div className="dm-drawer" onClick={(event) => event.stopPropagation()}><button className="dm-drawer-close" type="button" onClick={() => setMobileFilters(false)}>Close</button>{filterPanel}</div></div>}
  </main>
}
