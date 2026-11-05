
import { useEffect, useState } from 'react'
import {
  BadgeIndianRupee,
  CarFront,
  CheckCircle2,
  Clock3,
  LoaderCircle,
  ShieldCheck,
  TrendingUp,
} from 'lucide-react'

import { apiRequest } from '../../services/api'
import { getUsedCarFilters } from '../../services/usedCars'
import { useAuth } from '../../context/AuthContext'
import './ValuationPage.css'

const initialForm = {
  make: '',
  model: '',
  year: '',
  fuel: '',
  transmission: '',
  km_driven: '',
  city: 'Kolkata',
}

const money = (value) =>
  value === null || value === undefined
    ? 'Not available'
    : `₹${Number(value).toLocaleString('en-IN')}`

export default function ValuationPage() {
  const { isAuthenticated, user } = useAuth()

  const [form, setForm] = useState(initialForm)
  const [options, setOptions] = useState({})
  const [models, setModels] = useState([])

  const [loadingOptions, setLoadingOptions] = useState(true)
  const [loadingModels, setLoadingModels] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const [history, setHistory] = useState([])
  const [historyError, setHistoryError] = useState('')

  // Load general valuation filter options.
  useEffect(() => {
    let active = true

    getUsedCarFilters()
      .then((data) => {
        if (active) {
          setOptions(data || {})
        }
      })
      .catch((err) => {
        if (active) {
          setError(
            err.message || 'Could not load valuation options.'
          )
        }
      })
      .finally(() => {
        if (active) {
          setLoadingOptions(false)
        }
      })

    return () => {
      active = false
    }
  }, [])

  // Load models belonging only to the selected manufacturer.
  useEffect(() => {
    let active = true

    if (!form.make) {
      return () => {
        active = false
      }
    }

    getUsedCarFilters({ make: form.make })
      .then((data) => {
        if (active) {
          setModels(data.models || [])
        }
      })
      .catch((err) => {
        if (active) {
          setModels([])
          setError(
            err.message ||
              'Could not load models for selected manufacturer.'
          )
        }
      })
      .finally(() => {
        if (active) {
          setLoadingModels(false)
        }
      })

    return () => {
      active = false
    }
  }, [form.make])

  // Load recent valuation history for authenticated users.
  useEffect(() => {
    let active = true

    if (!isAuthenticated) {
      return undefined
    }

    apiRequest('/pricing/history/?page=1&page_size=5')
      .then((data) => {
        if (active) {
          setHistory(data.results || [])
          setHistoryError('')
        }
      })
      .catch((err) => {
        if (active) {
          setHistoryError(
            err.message || 'History could not be loaded.'
          )
        }
      })

    return () => {
      active = false
    }
  }, [isAuthenticated, result])

  // Handle form changes.
  const update = (event) => {
    const { name, value } = event.target

    setForm((current) => ({
      ...current,
      [name]: value,
      ...(name === 'make' ? { model: '' } : {}),
    }))

    if (name === 'make') {
      setModels([])
      setLoadingModels(Boolean(value))
      setError('')
    }
  }

  // Submit vehicle details for valuation.
  const submit = async (event) => {
    event.preventDefault()

    setSubmitting(true)
    setError('')
    setResult(null)

    try {
      const payload = {
        ...form,
        year: Number(form.year),
        km_driven: Number(form.km_driven),
      }

      const data = await apiRequest('/pricing/estimate/', {
        method: 'POST',
        body: JSON.stringify(payload),
      })

      setResult(data)
    } catch (err) {
      setError(
        err.message || 'Unable to estimate this vehicle.'
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="valuation-page">
      <section className="valuation-hero">
        <div>
          <span className="valuation-eyebrow">
            AUTOHUB PRICE INTELLIGENCE
          </span>

          <h1>
            Know what your car
            <br />
            <span>is really worth.</span>
          </h1>

          <p>
            Get an indicative market estimate from comparable
            active used-car listings in the AutoHub catalogue.
          </p>

          <div className="valuation-trust">
            <span>
              <ShieldCheck size={15} />
              Transparent estimate
            </span>

            <span>
              <TrendingUp size={15} />
              Comparable listings
            </span>
          </div>
        </div>

        <div className="valuation-hero-icon">
          <BadgeIndianRupee size={82} strokeWidth={1.1} />
        </div>
      </section>

      <section className="valuation-layout">
        <div className="valuation-form-card">
          <div className="valuation-section-heading">
            <span className="valuation-eyebrow">
              VEHICLE INFORMATION
            </span>

            <h2>Tell us about your car.</h2>

            <p>
              Choose details that match your vehicle as closely
              as possible.
            </p>
          </div>

          <form className="valuation-form" onSubmit={submit}>
            <label>
              Manufacturer

              <select
                required
                name="make"
                value={form.make}
                onChange={update}
                disabled={loadingOptions}
              >
                <option value="">Select manufacturer</option>

                {(options.makes || []).map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Model

              <select
                required
                name="model"
                value={form.model}
                onChange={update}
                disabled={
                  loadingOptions ||
                  !form.make ||
                  loadingModels
                }
              >
                <option value="">
                  {!form.make
                    ? 'Select manufacturer first'
                    : loadingModels
                      ? 'Loading models...'
                      : 'Select model'}
                </option>

                {models.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Manufacturing year

              <select
                required
                name="year"
                value={form.year}
                onChange={update}
              >
                <option value="">Select year</option>

                {(options.years || []).map((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Fuel type

              <select
                required
                name="fuel"
                value={form.fuel}
                onChange={update}
              >
                <option value="">Select fuel</option>

                {(options.fuels || []).map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Transmission

              <select
                required
                name="transmission"
                value={form.transmission}
                onChange={update}
              >
                <option value="">Select transmission</option>

                {(options.transmissions || []).map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Kilometres driven

              <input
                required
                type="number"
                min="0"
                name="km_driven"
                value={form.km_driven}
                onChange={update}
                placeholder="e.g. 45000"
              />
            </label>

            <label className="valuation-full-width">
              City

              <select
                name="city"
                value={form.city}
                onChange={update}
              >
                <option value="">All catalogue cities</option>

                {(options.cities || []).map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>

            <button
              className="valuation-submit"
              type="submit"
              disabled={submitting || loadingOptions}
            >
              {submitting ? (
                <LoaderCircle
                  className="valuation-spin"
                  size={17}
                />
              ) : (
                <BadgeIndianRupee size={17} />
              )}

              Estimate my car value
            </button>

            {error && (
              <p className="valuation-error">{error}</p>
            )}
          </form>

          <p className="valuation-form-note">
            This is an indicative estimate based on listed asking
            prices. It is not a formal appraisal, offer, or
            guarantee of sale price.
          </p>
        </div>

        <aside className="valuation-result-column">
          {!result ? (
            <div className="valuation-result-placeholder">
              <div>
                <CarFront size={45} />
              </div>

              <h3>Your valuation appears here.</h3>

              <p>
                Complete the vehicle details and request an estimate
                to see the latest comparison result.
              </p>

              <div className="valuation-result-steps">
                <span>
                  <CheckCircle2 size={15} />
                  Vehicle details
                </span>

                <span>
                  <CheckCircle2 size={15} />
                  Comparable listings
                </span>

                <span>
                  <CheckCircle2 size={15} />
                  Indicative value
                </span>
              </div>
            </div>
          ) : (
            <div className="valuation-result-card">
              <span className="valuation-eyebrow">
                YOUR ESTIMATE
              </span>

              {result.status === 'estimated' ? (
                <>
                  <h3>Indicative market value</h3>

                  <strong className="valuation-estimated-price">
                    {money(result.estimated_price)}
                  </strong>

                  <div className="valuation-range">
                    <div>
                      <span>Lower range</span>
                      <strong>
                        {money(result.price_range?.lower)}
                      </strong>
                    </div>

                    <div>
                      <span>Upper range</span>
                      <strong>
                        {money(result.price_range?.upper)}
                      </strong>
                    </div>
                  </div>

                  <div
                    className={`valuation-confidence confidence-${result.confidence}`}
                  >
                    <span>Confidence</span>
                    <strong>{result.confidence}</strong>
                  </div>
                </>
              ) : (
                <>
                  <h3>Not enough market data</h3>

                  <p>
                    {result.message ||
                      'We could not find enough comparable vehicles for a reliable estimate.'}
                  </p>

                  <div className="valuation-insufficient-count">
                    {result.comparable_count || 0}{' '}
                    comparable listings ·{' '}
                    {result.minimum_required || 5} required
                  </div>
                </>
              )}

              <div className="valuation-result-meta">
                <span>
                  {result.comparable_count || 0} comparable listings
                </span>

                {result.comparison_scope && (
                  <span>
                    {result.comparison_scope.replace(/_/g, ' ')}
                  </span>
                )}
              </div>

              {result.method && (
                <p className="valuation-method">
                  {result.method}
                </p>
              )}

              {result.data_note && (
                <p className="valuation-method">
                  {result.data_note}
                </p>
              )}

              {result.valuation_id && (
                <p className="valuation-saved">
                  <CheckCircle2 size={15} />
                  Saved to your valuation history
                </p>
              )}

              {!isAuthenticated && (
                <p className="valuation-login-note">
                  Sign in to save future estimates to your account.
                </p>
              )}
            </div>
          )}

          {isAuthenticated && (
            <div className="valuation-history-card">
              <div className="valuation-history-heading">
                <div>
                  <span className="valuation-eyebrow">
                    YOUR ACCOUNT
                  </span>

                  <h3>Recent valuations</h3>
                </div>

                <Clock3 size={19} />
              </div>

              {historyError && (
                <p className="valuation-history-empty">
                  {historyError}
                </p>
              )}

              {history.length ? (
                history.map((item) => (
                  <div
                    className="valuation-history-item"
                    key={item.id}
                  >
                    <div>
                      <strong>
                        {item.year} {item.make} {item.model}
                      </strong>

                      <span>
                        {item.city || 'All cities'} ·{' '}
                        {new Date(
                          item.created_at
                        ).toLocaleDateString('en-IN')}
                      </span>
                    </div>

                    <strong>
                      {money(item.estimated_price)}
                    </strong>
                  </div>
                ))
              ) : (
                !historyError && (
                  <p className="valuation-history-empty">
                    No saved estimates yet.
                  </p>
                )
              )}

              <small>Signed in as {user?.email}</small>
            </div>
          )}
        </aside>
      </section>
    </main>
  )
}
