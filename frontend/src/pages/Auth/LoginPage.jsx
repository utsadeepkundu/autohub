import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { ArrowRight, Eye, EyeOff, KeyRound, LoaderCircle, Mail } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import './AuthPages.css'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [form, setForm] = useState({ email: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      await login(form)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err.message || 'Unable to sign in. Check your details and try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-page"><section className="auth-card"><div className="auth-card-brand">auto<span>hub</span></div><span className="auth-eyebrow">WELCOME BACK</span><h1>Good to see you again.</h1><p className="auth-intro">Sign in to continue your AutoHub journey and keep your car decisions in one place.</p>
      <form className="auth-form" onSubmit={submit}><label>Email address<div className="auth-input-wrap"><Mail size={17} /><input type="email" autoComplete="email" required value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} placeholder="you@example.com" /></div></label><label>Password<div className="auth-input-wrap"><KeyRound size={17} /><input type={showPassword ? 'text' : 'password'} autoComplete="current-password" required value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} placeholder="Enter your password" /><button type="button" aria-label={showPassword ? 'Hide password' : 'Show password'} onClick={() => setShowPassword((value) => !value)}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></div></label>
        {error && <div className="auth-error">{error}</div>}<button type="submit" className="auth-submit" disabled={loading}>{loading ? <LoaderCircle className="auth-spin" size={17} /> : <>Sign in <ArrowRight size={17} /></>}</button></form>
      <p className="auth-switch">New to AutoHub? <Link to="/register">Create an account</Link></p><p className="auth-security-note">Your session is stored in this browser session and can be ended by signing out.</p></section><aside className="auth-visual"><div className="auth-visual-orbit" /><div className="auth-visual-content"><span>YOUR NEXT JOURNEY</span><h2>Better choices.<br /><em>Better drives.</em></h2><p>Explore vehicles, compare the details, and make your next move with confidence.</p></div><div className="auth-visual-footer">AUTOHUB · FIND YOUR DRIVE</div></aside></main>
  )
}
