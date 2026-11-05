import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { ArrowRight, BadgeIndianRupee, CheckCircle2, Clock3, LoaderCircle, Save, UserRound } from 'lucide-react'
import { apiRequest } from '../../services/api'
import { useAuth } from '../../context/AuthContext'
import './AccountPage.css'

const money = (value) => value === null || value === undefined
  ? 'Not available'
  : `₹${Number(value).toLocaleString('en-IN')}`

export default function AccountPage() {
  const { user, isAuthenticated, loading: authLoading, refreshUser } = useAuth()
  const [form, setForm] = useState({ first_name: '', last_name: '' })
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [historyError, setHistoryError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    if (!isAuthenticated) return undefined

    let active = true
    Promise.allSettled([
      apiRequest('/accounts/me/'),
      apiRequest('/pricing/history/?page=1&page_size=6'),
    ]).then(([profileResult, valuationResult]) => {
      if (!active) return
      if (profileResult.status === 'fulfilled') {
        const profile = profileResult.value
        setForm({ first_name: profile.first_name || '', last_name: profile.last_name || '' })
        setError('')
      } else {
        setError(profileResult.reason?.message || 'Unable to load your account details.')
      }
      if (valuationResult.status === 'fulfilled') {
        setHistory(Array.isArray(valuationResult.value.results) ? valuationResult.value.results : [])
        setHistoryError('')
      } else {
        setHistoryError(valuationResult.reason?.message || 'Valuation history could not be loaded.')
      }
    }).finally(() => {
      if (active) setLoading(false)
    })

    return () => { active = false }
  }, [isAuthenticated])

  const update = (event) => {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }))
  }

  const saveProfile = async (event) => {
    event.preventDefault()
    setSaving(true)
    setError('')
    setNotice('')
    try {
      await apiRequest('/accounts/me/', {
        method: 'PATCH',
        body: JSON.stringify(form),
      })
      await refreshUser()
      setNotice('Your account details have been updated.')
    } catch (requestError) {
      setError(requestError.message || 'Unable to update your account.')
    } finally {
      setSaving(false)
    }
  }

  if (authLoading || (isAuthenticated && loading)) {
    return <main className="account-state"><LoaderCircle className="account-spin" size={30} /> Loading your account…</main>
  }

  if (!isAuthenticated) {
    return <main className="account-gate"><div><UserRound size={36} /><span>YOUR AUTOHUB ACCOUNT</span><h1>Sign in to see your account.</h1><p>Manage your profile and revisit saved vehicle valuations.</p><Link to="/login">Sign in <ArrowRight size={16} /></Link></div></main>
  }

  return (
    <main className="account-page">
      <div className="account-container">
        <header className="account-heading">
          <span>YOUR AUTOHUB ACCOUNT</span>
          <h1>Welcome back{user?.first_name ? `, ${user.first_name}` : ''}.</h1>
          <p>Keep your details current and revisit your recent price estimates.</p>
        </header>

        {notice && <div className="account-notice"><CheckCircle2 size={16} /> {notice}</div>}
        {error && <div className="account-error">{error}</div>}

        <div className="account-grid">
          <section className="account-card">
            <div className="account-card-heading"><div><span>PROFILE</span><h2>Personal details</h2></div><UserRound size={20} /></div>
            <form className="account-form" onSubmit={saveProfile}>
              <label>First name<input name="first_name" required minLength={1} maxLength={150} value={form.first_name} onChange={update} /></label>
              <label>Last name<input name="last_name" maxLength={150} value={form.last_name} onChange={update} /></label>
              <label>Email address<input value={user?.email || ''} readOnly /></label>
              <button type="submit" disabled={saving}>{saving ? <LoaderCircle className="account-spin" size={16} /> : <Save size={16} />} Save changes</button>
            </form>
            <p className="account-note">Your email address is used to sign in and cannot be changed from this form.</p>
          </section>

          <section className="account-card account-history-card">
            <div className="account-card-heading"><div><span>PRICE INTELLIGENCE</span><h2>Recent valuations</h2></div><Clock3 size={20} /></div>
            {historyError ? <p className="account-empty">{historyError}</p> : history.length ? <div className="account-history-list">{history.map((item) => <article key={item.id} className="account-history-item"><div><strong>{item.year} {item.make} {item.model}</strong><span>{item.city || 'All catalogue cities'} · {new Date(item.created_at).toLocaleDateString('en-IN')}</span><small>{item.comparable_count || 0} comparable listings · {item.confidence || 'insufficient'} confidence</small></div><strong>{money(item.estimated_price)}</strong></article>)}</div> : <div className="account-empty"><BadgeIndianRupee size={30} /><p>No valuations saved yet. Request an estimate to start your history.</p><Link to="/valuation">Estimate a car's value <ArrowRight size={15} /></Link></div>}
            {history.length > 0 && <Link className="account-history-link" to="/valuation">Open price valuation <ArrowRight size={15} /></Link>}
          </section>
        </div>
      </div>
    </main>
  )
}
