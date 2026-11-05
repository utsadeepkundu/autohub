import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { ArrowRight, Eye, EyeOff, LoaderCircle, LockKeyhole, Mail, UserRound } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import './AuthPages.css'

export default function RegisterPage() {
  const navigate = useNavigate()
  const { register } = useAuth()
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', password: '', password_confirm: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const update = (event) => setForm((current) => ({ ...current, [event.target.name]: event.target.value }))

  const submit = async (event) => {
    event.preventDefault()
    setError('')
    if (form.password !== form.password_confirm) { setError('Passwords do not match.'); return }
    if (form.password.length < 8) { setError('Use a password with at least 8 characters.'); return }
    setLoading(true)
    try {
      await register(form)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err.message || 'Unable to create your account.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-page"><section className="auth-card auth-register-card"><div className="auth-card-brand">auto<span>hub</span></div><span className="auth-eyebrow">JOIN THE COMMUNITY</span><h1>Your next drive starts here.</h1><p className="auth-intro">Create your account to save vehicle valuations and enjoy a more connected AutoHub experience.</p>
      <form className="auth-form" onSubmit={submit}><div className="auth-two-fields"><label>First name<div className="auth-input-wrap"><UserRound size={17} /><input name="first_name" autoComplete="given-name" required value={form.first_name} onChange={update} placeholder="First name" /></div></label><label>Last name<div className="auth-input-wrap"><UserRound size={17} /><input name="last_name" autoComplete="family-name" required value={form.last_name} onChange={update} placeholder="Last name" /></div></label></div><label>Email address<div className="auth-input-wrap"><Mail size={17} /><input type="email" name="email" autoComplete="email" required value={form.email} onChange={update} placeholder="you@example.com" /></div></label><label>Password<div className="auth-input-wrap"><LockKeyhole size={17} /><input type={showPassword ? 'text' : 'password'} name="password" autoComplete="new-password" required minLength={8} value={form.password} onChange={update} placeholder="At least 8 characters" /><button type="button" aria-label="Toggle password visibility" onClick={() => setShowPassword((value) => !value)}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></div></label><label>Confirm password<div className="auth-input-wrap"><LockKeyhole size={17} /><input type={showPassword ? 'text' : 'password'} name="password_confirm" autoComplete="new-password" required minLength={8} value={form.password_confirm} onChange={update} placeholder="Enter password again" /></div></label>
        {error && <div className="auth-error">{error}</div>}<button type="submit" className="auth-submit" disabled={loading}>{loading ? <LoaderCircle className="auth-spin" size={17} /> : <>Create account <ArrowRight size={17} /></>}</button></form>
      <p className="auth-switch">Already have an account? <Link to="/login">Sign in</Link></p><p className="auth-security-note">By creating an account, you agree to use the platform responsibly.</p></section><aside className="auth-visual"><div className="auth-visual-orbit" /><div className="auth-visual-content"><span>DRIVE INTO WHAT'S NEXT</span><h2>Find your fit.<br /><em>Own your road.</em></h2><p>From the first shortlist to the final decision, make every car choice count.</p></div><div className="auth-visual-footer">AUTOHUB · FIND YOUR DRIVE</div></aside></main>
  )
}
