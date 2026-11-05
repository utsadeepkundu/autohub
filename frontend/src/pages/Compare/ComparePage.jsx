import { useEffect, useMemo, useRef, useState } from 'react'
import { ArrowRightLeft, CarFront, LoaderCircle, Plus, Scale, Trash2 } from 'lucide-react'
import { getBrandModels, getCarBrands, getCarVariants, compareCarVariants } from '../../services/cars'
import './ComparePage.css'

const emptySlot = (id) => ({ id, variant: null })
const currency = (value) => Number.isFinite(Number(value)) ? `₹${Number(value).toLocaleString('en-IN')}` : 'Not available'
const displayValue = (value) => {
  if (value === null || value === undefined || value === '') return '—'
  if (Array.isArray(value)) return value.map(displayValue).join(', ')
  if (typeof value === 'object') return Object.entries(value).map(([key, item]) => `${key}: ${displayValue(item)}`).join(' · ')
  return String(value)
}

function CompareSlot({ index, brands, selected, onSelect, onRemove, removable }) {
  const [brandSlug, setBrandSlug] = useState('')
  const [models, setModels] = useState([])
  const [modelSlug, setModelSlug] = useState('')
  const [variants, setVariants] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    if (!brandSlug) return undefined
    Promise.resolve().then(() => { if (active) setBusy(true) })
    getBrandModels(brandSlug, { page: 1, page_size: 100 })
      .then((response) => { if (active) setModels(response.results || []) })
      .catch((err) => { if (active) setError(err.message || 'Unable to load models.') })
      .finally(() => { if (active) setBusy(false) })
    return () => { active = false }
  }, [brandSlug])

  useEffect(() => {
    let active = true
    if (!brandSlug || !modelSlug) return undefined
    Promise.resolve().then(() => { if (active) setBusy(true) })
    getCarVariants(brandSlug, modelSlug, { page: 1, page_size: 100 })
      .then((response) => { if (active) setVariants(response.results || []) })
      .catch((err) => { if (active) setError(err.message || 'Unable to load variants.') })
      .finally(() => { if (active) setBusy(false) })
    return () => { active = false }
  }, [brandSlug, modelSlug])

  return (
    <section className="compare-slot">
      <div className="compare-slot-top"><span className="compare-slot-number">0{index + 1}</span><h3>Car {index + 1}</h3>{removable && <button type="button" aria-label={`Remove car ${index + 1}`} onClick={onRemove}><Trash2 size={16} /></button>}</div>
      <label>Manufacturer<select value={brandSlug} onChange={(event) => { setBrandSlug(event.target.value); setModels([]); setModelSlug(''); setVariants([]); onSelect(null); setError('') }}><option value="">Select manufacturer</option>{brands.map((brand) => <option key={brand.id} value={brand.slug}>{brand.name}</option>)}</select></label>
      <label>Model<select value={modelSlug} disabled={!brandSlug || busy} onChange={(event) => { setModelSlug(event.target.value); setVariants([]); onSelect(null); setError('') }}><option value="">Select model</option>{models.map((model) => <option key={model.id} value={model.slug}>{model.name}</option>)}</select></label>
      <label>Variant<select disabled={!modelSlug || busy || variants.length === 0} value={selected?.id || ''} onChange={(event) => onSelect(variants.find((variant) => variant.id === event.target.value) || null)}><option value="">Select variant</option>{variants.map((variant) => <option key={variant.id} value={variant.id}>{variant.name}</option>)}</select></label>
      {busy && <span className="compare-slot-hint">Loading catalogue…</span>}
      {error && <span className="compare-slot-error">{error}</span>}
      {selected && <div className="compare-slot-selected"><CarFront size={19} /><span>{selected.name}</span><strong>{selected.ex_showroom_formatted || currency(selected.ex_showroom_price)}</strong></div>}
    </section>
  )
}

export default function ComparePage() {
  const [brands, setBrands] = useState([])
  const nextSlotId = useRef(3)
  const [slots, setSlots] = useState([emptySlot('slot-1'), emptySlot('slot-2')])
  const [result, setResult] = useState(null)
  const [loadingBrands, setLoadingBrands] = useState(true)
  const [comparing, setComparing] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    getCarBrands().then((data) => { if (active) setBrands(Array.isArray(data) ? data : []) })
      .catch((err) => { if (active) setError(err.message || 'Unable to load manufacturers.') })
      .finally(() => { if (active) setLoadingBrands(false) })
    return () => { active = false }
  }, [])

  const selectedCount = slots.filter((slot) => slot.variant?.id).length
  const comparedVariants = useMemo(() => result?.variants || [], [result])
  const specKeys = useMemo(() => {
    const keys = new Set()
    comparedVariants.forEach((variant) => {
      if (variant.specs && typeof variant.specs === 'object' && !Array.isArray(variant.specs)) {
        Object.keys(variant.specs).forEach((key) => keys.add(key))
      }
    })
    return [...keys]
  }, [comparedVariants])

  const updateSlot = (index, variant) => {
    setSlots((current) => current.map((slot, slotIndex) => slotIndex === index ? { ...slot, variant } : slot))
    setResult(null)
  }

  const addSlot = () => {
    if (slots.length < 3) {
      const id = `slot-${nextSlotId.current++}`
      setSlots((current) => [...current, emptySlot(id)])
    }
  }

  const removeSlot = (index) => {
    setSlots((current) => current.filter((_, slotIndex) => slotIndex !== index))
    setResult(null)
  }

  const runComparison = async () => {
    const ids = slots.map((slot) => slot.variant?.id).filter(Boolean)
    if (ids.length < 2) { setError('Select at least two variants to compare.'); return }
    if (new Set(ids).size !== ids.length) { setError('Choose a different variant for each car.'); return }
    setComparing(true)
    setError('')
    try {
      const data = await compareCarVariants(ids)
      setResult(data)
    } catch (err) {
      setError(err.message || 'Unable to compare these variants.')
      setResult(null)
    } finally {
      setComparing(false)
    }
  }

  const priceComparison = result?.price_comparison || {}

  return (
    <main className="compare-page">
      <section className="compare-hero"><span className="compare-eyebrow">MAKE THE RIGHT CALL</span><h1>Every detail.<br /><span>Side by side.</span></h1><p>Compare new-car variants on pricing, specifications and features before you decide.</p><div className="compare-hero-mark"><Scale size={72} strokeWidth={1.1} /></div></section>
      <section className="compare-content">
        <div className="compare-heading"><div><span className="compare-eyebrow">BUILD YOUR COMPARISON</span><h2>Choose your cars.</h2><p>Select two or three variants from the AutoHub catalogue.</p></div><div className="compare-count">{selectedCount} of {slots.length} selected</div></div>
        {loadingBrands ? <div className="compare-loading"><LoaderCircle className="compare-spin" /> Loading manufacturers…</div> : <>
          <div className="compare-slots">{slots.map((slot, index) => <CompareSlot key={slot.id} index={index} brands={brands} selected={slot.variant} onSelect={(variant) => updateSlot(index, variant)} onRemove={() => removeSlot(index)} removable={slots.length > 2} />)}</div>
          <div className="compare-actions"><button type="button" className="compare-secondary" onClick={addSlot} disabled={slots.length >= 3}><Plus size={16} /> Add third car</button><button type="button" className="compare-primary" onClick={runComparison} disabled={comparing || selectedCount < 2}>{comparing ? <LoaderCircle size={17} className="compare-spin" /> : <ArrowRightLeft size={17} />} Compare selected cars</button></div>
        </>}
        {error && <div className="compare-error">{error}</div>}

        {result && <section className="compare-result"><div className="compare-result-title"><div><span className="compare-eyebrow">YOUR COMPARISON</span><h2>See how they stack up.</h2></div><span>{result.variant_count} variants</span></div>
          <div className="compare-result-cards">{comparedVariants.map((variant) => <article className="compare-result-card" key={variant.id}><span className="compare-result-brand">{variant.brand_name}</span><h3>{variant.name}</h3><strong>{variant.ex_showroom_formatted || currency(variant.ex_showroom_price)}</strong><span>Ex-showroom</span><div className="compare-result-meta"><span>{variant.fuel || 'Fuel N/A'}</span><span>{variant.transmission || 'Transmission N/A'}</span></div></article>)}</div>
          <div className="compare-price-panels">{['ex_showroom', 'on_road'].map((kind) => { const data = priceComparison[kind]; return <article className="compare-price-panel" key={kind}><span>{kind === 'ex_showroom' ? 'EX-SHOWROOM PRICE' : 'ON-ROAD PRICE'}</span>{data?.comparable ? <><strong>{currency(data.difference)} difference</strong><p>Lowest: {data.lowest.variant_name} · {currency(data.lowest.price)}</p><p>Highest: {data.highest.variant_name} · {currency(data.highest.price)}</p>{data.pricing_city && <small>Pricing city: {data.pricing_city}</small>}</> : <p>{data?.reason || 'Comparable price data is not available.'}</p>}</article> })}</div>
          {specKeys.length > 0 && <div className="compare-spec-table-wrap"><h3>Technical specifications</h3><table className="compare-spec-table"><thead><tr><th>Specification</th>{comparedVariants.map((variant) => <th key={variant.id}>{variant.short_name || variant.name}</th>)}</tr></thead><tbody>{specKeys.map((key) => <tr key={key}><th>{key.replace(/_/g, ' ')}</th>{comparedVariants.map((variant) => <td key={variant.id}>{displayValue(variant.specs?.[key])}</td>)}</tr>)}</tbody></table></div>}
          <div className="compare-features-grid">{comparedVariants.map((variant) => <article key={variant.id}><h3>{variant.short_name || variant.name}</h3><h4>Key features</h4>{Array.isArray(variant.key_features) && variant.key_features.length ? <ul>{variant.key_features.map((feature, index) => <li key={index}>{displayValue(feature)}</li>)}</ul> : <p>Feature list unavailable.</p>}</article>)}</div>
        </section>}
      </section>
    </main>
  )
}
