import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router'
import { ArrowLeft, ArrowUpRight, CalendarDays, CarFront, Fuel, Gauge, MapPin, Settings2, ShieldCheck, UserRound } from 'lucide-react'
import { getUsedCarDetails } from '../../services/usedCars'
import './UsedCarDetailsPage.css'

const money = (value) => {
  const amount = Number(value)
  if (!Number.isFinite(amount) || amount <= 0) return 'Price on request'
  if (amount >= 10000000) return `₹${(amount / 10000000).toFixed(2)} Cr`
  return `₹${(amount / 100000).toFixed(2)} Lakh`
}

function getImageUrl(item) {
  if (typeof item === 'string') return item
  if (!item || typeof item !== 'object') return ''
  return item.imageUrl || item.webpImage || item.image || item.url || item.src || ''
}

export default function UsedCarDetailsPage() {
  const { carId } = useParams()
  const [car, setCar] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadedFor, setLoadedFor] = useState('')
  const [error, setError] = useState('')
  const [activeImage, setActiveImage] = useState(0)

  useEffect(() => {
    let active = true
    getUsedCarDetails(carId)
      .then((data) => {
        if (active) { setCar(data); setError('') }
      })
      .catch((requestError) => {
        if (active) setError(requestError.message || 'Unable to load this vehicle.')
      })
      .finally(() => {
        if (active) { setLoading(false); setLoadedFor(carId) }
      })
    return () => { active = false }
  }, [carId])

  const images = useMemo(() => {
    if (!car) return []
    const urls = [car.primary_image, car.images?.primary, car.images?.placeholder]
    const imageData = car.images
    if (Array.isArray(imageData)) {
      urls.push(...imageData.map(getImageUrl))
    } else if (imageData && typeof imageData === 'object') {
      Object.values(imageData).forEach((value) => {
        if (Array.isArray(value)) urls.push(...value.map(getImageUrl))
        else if (typeof value === 'string' && /^https?:\/\//i.test(value)) urls.push(value)
      })
    }
    return [...new Set(urls.filter((url) => typeof url === 'string' && /^https?:\/\//i.test(url)))]
  }, [car])

  if (loading || loadedFor !== carId) return <main className="used-detail-state"><div className="used-detail-spinner" /><h2>Loading vehicle details</h2><p>Getting the listing information.</p></main>
  if (error || !car) return <main className="used-detail-state"><CarFront size={44} /><h2>Vehicle unavailable</h2><p>{error || 'This listing may have been removed.'}</p><Link to="/used-cars" className="used-detail-primary">Back to used cars</Link></main>

  const title = car.title || `${car.year || ''} ${car.make || ''} ${car.model || ''} ${car.variant || ''}`.trim()
  const specs = [
    ['Manufacturing year', car.year], ['Kilometres driven', Number(car.km_driven || 0).toLocaleString('en-IN') + ' km'],
    ['Fuel', car.fuel], ['Transmission', car.transmission], ['Body type', car.body_type],
    ['Ownership', car.owner_slug || (car.owner_count ? `${car.owner_count} owner` : '')],
    ['Seller type', car.seller_type], ['Model version', car.model_name],
  ].filter(([, value]) => value !== null && value !== undefined && value !== '')

  return (
    <main className="used-detail-page">
      <div className="used-detail-container">
        <Link to="/used-cars" className="used-detail-back"><ArrowLeft size={16} /> Back to used cars</Link>
        <div className="used-detail-heading">
          <div><span className="used-detail-eyebrow">PRE-OWNED VEHICLE</span><h1>{title}</h1><p><MapPin size={15} /> {[car.locality, car.city].filter(Boolean).join(', ') || 'Location not available'}</p></div>
          <div className="used-detail-price"><span>Asking price</span><strong>{money(car.price)}</strong></div>
        </div>

        <div className="used-detail-layout">
          <section className="used-detail-gallery-card">
            <div className="used-detail-main-image">
              {images[activeImage] ? <img src={images[activeImage]} alt={title} onError={(event) => { event.currentTarget.style.display = 'none' }} /> : <div className="used-detail-image-placeholder"><CarFront size={64} /><span>Vehicle image unavailable</span></div>}
            </div>
            {images.length > 1 && <div className="used-detail-thumbnails">{images.map((image, index) => <button type="button" key={`${image}-${index}`} className={activeImage === index ? 'active' : ''} onClick={() => setActiveImage(index)}><img src={image} alt={`${title} ${index + 1}`} /></button>)}</div>}
            <div className="used-detail-disclaimer"><ShieldCheck size={17} /><span>Listing information is provided by the catalogue source. Verify vehicle condition and documents before purchase.</span></div>
          </section>

          <aside className="used-detail-side-card">
            <span className="used-detail-eyebrow">VEHICLE OVERVIEW</span>
            <div className="used-detail-highlights">
              <div><CalendarDays /><strong>{car.year || '—'}</strong><span>Year</span></div>
              <div><Gauge /><strong>{Number(car.km_driven || 0).toLocaleString('en-IN')}</strong><span>Kilometres</span></div>
              <div><Fuel /><strong>{car.fuel || '—'}</strong><span>Fuel</span></div>
              <div><Settings2 /><strong>{car.transmission || '—'}</strong><span>Transmission</span></div>
            </div>
            <div className="used-detail-actions">
              {car.source_url && <a href={car.source_url} target="_blank" rel="noreferrer" className="used-detail-primary">View original listing <ArrowUpRight size={16} /></a>}
              {car.map_link && <a href={car.map_link} target="_blank" rel="noreferrer" className="used-detail-secondary"><MapPin size={16} /> View location</a>}
            </div>
            <p className="used-detail-source-note">AutoHub does not directly verify or sell this imported listing. Confirm availability with the original source.</p>
          </aside>
        </div>

        <section className="used-detail-spec-section">
          <div className="used-detail-section-title"><span className="used-detail-eyebrow">THE DETAILS</span><h2>Vehicle information</h2></div>
          <div className="used-detail-spec-grid">{specs.map(([label, value]) => <div key={label}><span>{label}</span><strong>{String(value)}</strong></div>)}</div>
        </section>

        {(Array.isArray(car.trust_tags) && car.trust_tags.length > 0 || Array.isArray(car.ai_tags) && car.ai_tags.length > 0) && <section className="used-detail-spec-section"><div className="used-detail-section-title"><span className="used-detail-eyebrow">LISTING INSIGHTS</span><h2>Additional information</h2></div><div className="used-detail-insights">{[...(car.trust_tags || []), ...(car.ai_tags || [])].map((tag, index) => <div key={index}><UserRound size={16} /><span>{String(tag).replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()}</span></div>)}</div></section>}
      </div>
    </main>
  )
}
