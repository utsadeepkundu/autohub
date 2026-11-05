
import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { useAuth } from '../../context/AuthContext'
import {
  ArrowRight,
  BadgeCheck,
  CarFront,
  ChevronDown,
  CircleDollarSign,
  Fuel,
  Gauge,
  MapPin,
  Menu,
  Search,
  ShieldCheck,
  Sparkles,
  X,
} from 'lucide-react'

import './HomePage.css'

/* =================================
   BRAND LOGO
================================= */

function BrandLogo() {
  return (
    <Link className="brand" to="/" aria-label="AutoHub home">
      <span className="brand-symbol" aria-hidden="true">
        <span />
        <span />
        <span />
      </span>

      <span className="brand-name">
        auto<span>hub</span>
      </span>
    </Link>
  )
}

/* =================================
   SHARED NAVIGATION
================================= */

export function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)
  const { user, isAuthenticated, logout } = useAuth()

  const closeMenu = () => setMenuOpen(false)
  const handleLogout = async () => {
    closeMenu()
    try { await logout() } catch { /* Tokens are cleared by the auth context. */ }
  }

  return (
    <header className="site-header">
      <div className="header-inner">
        <BrandLogo />

        <nav
          className={`site-nav ${menuOpen ? 'is-open' : ''}`}
          aria-label="Main navigation"
        >
          <Link to="/new-cars" onClick={closeMenu}>
            New cars
          </Link>

          <Link to="/used-cars" onClick={closeMenu}>
            Used cars
          </Link>

          <Link to="/dealer-marketplace" onClick={closeMenu}>
            Dealer cars
          </Link>

          <Link to="/compare" onClick={closeMenu}>
            Compare
          </Link>

          <Link to="/valuation" onClick={closeMenu}>
            Valuation
          </Link>

          <Link to="/dealer" onClick={closeMenu}>
            Dealer portal
          </Link>
        </nav>

        <div className="header-actions">
          {isAuthenticated ? (
            <>
              <Link className="login-link" to="/account" onClick={closeMenu}>
                {user?.first_name ? `Hi, ${user.first_name}` : 'My account'}
              </Link>
              <button type="button" className="header-signout" onClick={handleLogout}>Sign out</button>
            </>
          ) : (
            <>
              <Link className="login-link" to="/login" onClick={closeMenu}>Sign in</Link>
              <Link className="header-cta" to="/register" onClick={closeMenu}>Join AutoHub <ArrowRight size={16} /></Link>
            </>
          )}
        </div>

        <button
          type="button"
          className="mobile-menu-button"
          aria-label={menuOpen ? 'Close navigation' : 'Open navigation'}
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((open) => !open)}
        >
          {menuOpen ? <X size={23} /> : <Menu size={23} />}
        </button>
      </div>
    </header>
  )
}

/* =================================
   SEARCH PANEL
================================= */

function SearchPanel() {
  const navigate = useNavigate()
  const [category, setCategory] = useState('New cars')
  const [city, setCity] = useState('Kolkata')
  const [budget, setBudget] = useState('Any budget')
  const [searchMessage, setSearchMessage] = useState('')

  const handleSearch = (event) => {
    event.preventDefault()
    if (category === 'New cars') {
      navigate('/new-cars')
      return
    }
    const query = new URLSearchParams()
    if (city === 'Kolkata') query.set('city', 'Kolkata')
    const budgetRanges = {
      'Under ₹5 lakh': { max_price: 500000 },
      '₹5–10 lakh': { min_price: 500000, max_price: 1000000 },
      '₹10–20 lakh': { min_price: 1000000, max_price: 2000000 },
      '₹20–40 lakh': { min_price: 2000000, max_price: 4000000 },
      'Above ₹40 lakh': { min_price: 4000000 },
    }
    Object.entries(budgetRanges[budget] || {}).forEach(([key, value]) => query.set(key, String(value)))
    const searchQuery = query.toString()
    navigate(`/used-cars${searchQuery ? `?${searchQuery}` : ''}`)
  }

  return (
    <section className="search-section" aria-label="Find your car">
      <div className="search-panel">
        <div className="search-heading">
          <div>
            <span className="eyebrow">START YOUR JOURNEY</span>
            <h2>Find your perfect match.</h2>
          </div>

          <div className="search-heading-icon">
            <Search size={21} />
          </div>
        </div>

        <div
          className="search-tabs"
          role="group"
          aria-label="Vehicle category"
        >
          {['New cars', 'Used cars'].map((item) => (
            <button
              className={
                category === item
                  ? 'search-tab active'
                  : 'search-tab'
              }
              key={item}
              type="button"
              aria-pressed={category === item}
              onClick={() => {
                setCategory(item)
                setSearchMessage('')
              }}
            >
              {item}
            </button>
          ))}
        </div>

        <form className="search-form" onSubmit={handleSearch}>
          <label className="search-field">
            <span className="field-icon">
              <MapPin size={19} />
            </span>

            <span className="field-content">
              <span className="field-label">Your city</span>

              <select
                value={city}
                onChange={(event) => setCity(event.target.value)}
              >
                <option>Kolkata</option>
                <option>Delhi</option>
                <option>Mumbai</option>
                <option>Bengaluru</option>
                <option>Hyderabad</option>
                <option>Pune</option>
                <option>Chennai</option>
              </select>
            </span>

            <ChevronDown size={16} className="field-chevron" />
          </label>

          <span className="field-divider" />

          <label className="search-field">
            <span className="field-icon">
              <CircleDollarSign size={19} />
            </span>

            <span className="field-content">
              <span className="field-label">Your budget</span>

              <select
                value={budget}
                onChange={(event) => setBudget(event.target.value)}
              >
                <option>Any budget</option>
                <option>Under ₹5 lakh</option>
                <option>₹5–10 lakh</option>
                <option>₹10–20 lakh</option>
                <option>₹20–40 lakh</option>
                <option>Above ₹40 lakh</option>
              </select>
            </span>

            <ChevronDown size={16} className="field-chevron" />
          </label>

          <button className="search-submit" type="submit">
            <Search size={18} />
            Search cars
          </button>
        </form>

        {searchMessage && (
          <p className="search-feedback" role="status">
            {searchMessage}
          </p>
        )}
      </div>
    </section>
  )
}

/* =================================
   HERO SECTION
================================= */

function Hero() {
  return (
    <section className="hero-section" id="top">
      <div className="hero-background-shape" />

      <div className="hero-inner">
        <div className="hero-copy">
          <div className="hero-badge">
            <Sparkles size={14} />
            A BETTER WAY TO FIND YOUR NEXT CAR
          </div>

          <h1>
            Your next car.
            <br />
            Your kind of <span>journey.</span>
          </h1>

          <p className="hero-description">
            Discover new and pre-owned cars, compare what matters
            and make your next move with confidence.
          </p>

          <div className="hero-actions">
            <Link to="/new-cars" className="primary-button">
              Explore cars <ArrowRight size={18} />
            </Link>

            <Link to="/valuation" className="secondary-button">
              Estimate my car <CircleDollarSign size={18} />
            </Link>
          </div>

          <div className="hero-assurance">
            <span>
              <ShieldCheck size={16} />
              Smarter comparisons
            </span>

            <span>
              <BadgeCheck size={16} />
              Informed decisions
            </span>
          </div>
        </div>

        <div className="hero-visual">
          <div className="hero-image-frame">
            <img
              src="https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1500&q=85"
              alt="Sports car photographed on a scenic road"
            />
          </div>

          <div className="hero-floating-card">
            <div className="floating-card-icon">
              <CarFront size={22} />
            </div>

            <div>
              <strong>Every journey starts somewhere.</strong>
              <span>Find the one that feels right.</span>
            </div>

            <ArrowRight size={19} />
          </div>

          <div className="hero-decoration hero-decoration-one" />
          <div className="hero-decoration hero-decoration-two" />
        </div>
      </div>

      <SearchPanel />
    </section>
  )
}

/* =================================
   FEATURE CARDS
================================= */

const features = [
  {
    id: 'new-cars',
    icon: <CarFront size={25} />,
    label: '01 / NEW CARS',
    title: 'Discover something new.',
    description:
      'Explore models, variants, specifications and pricing.',
    link: 'Explore new cars',
    href: '/new-cars',
    className: 'feature-coral',
  },
  {
    id: 'used-cars',
    icon: <Gauge size={25} />,
    label: '02 / PRE-OWNED',
    title: 'Find more for less.',
    description:
      'Browse pre-owned cars using practical search filters.',
    link: 'Browse used cars',
    href: '/used-cars',
    className: 'feature-green',
  },
  {
    id: 'compare',
    icon: <Fuel size={25} />,
    label: '03 / COMPARISON',
    title: 'Compare before you decide.',
    description:
      'Put vehicle specifications and prices side by side.',
    link: 'Compare cars',
    href: '/compare',
    className: 'feature-pink',
  },
  {
    id: 'valuation',
    icon: <CircleDollarSign size={25} />,
    label: '04 / CAR VALUATION',
    title: 'Know what your car is worth.',
    description:
      'Get an indicative market valuation using comparable listings.',
    link: 'Estimate car value',
    href: '/valuation',
    className: 'feature-dark',
  },
]

function DiscoverSection() {
  return (
    <section className="discover-section">
      <div className="section-heading">
        <div>
          <span className="eyebrow">MADE FOR CAR PEOPLE</span>

          <h2>
            Everything you need. <span>All in one place.</span>
          </h2>
        </div>

        <p>
          From the first shortlist to the final decision,
          make every step a little easier.
        </p>
      </div>

      <div className="feature-grid">
        {features.map((feature) => (
          <article
            className={`feature-card ${feature.className}`}
            id={feature.id}
            key={feature.id}
          >
            <div className="feature-card-top">
              <span className="feature-icon">
                {feature.icon}
              </span>

              <span className="feature-label">
                {feature.label}
              </span>
            </div>

            <div className="feature-card-content">
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </div>

            <Link to={feature.href} className="feature-link">
              {feature.link} <ArrowRight size={17} />
            </Link>
          </article>
        ))}
      </div>
    </section>
  )
}

/* =================================
   TRUST SECTION
================================= */

function TrustSection() {
  return (
    <section className="trust-section" id="account">
      <div className="trust-copy">
        <span className="eyebrow">THE AUTOHUB DIFFERENCE</span>

        <h2>
          Less guesswork.
          <br />
          <span>More confidence.</span>
        </h2>

        <p>
          Explore the information that matters, understand your
          options and make decisions at your own pace.
        </p>
      </div>

      <div className="trust-points">
        <div className="trust-point">
          <span className="trust-point-icon">
            <Search size={21} />
          </span>

          <div>
            <strong>Explore with clarity</strong>
            <p>
              Useful details and filters help narrow your choices.
            </p>
          </div>
        </div>

        <div className="trust-point">
          <span className="trust-point-icon">
            <ShieldCheck size={21} />
          </span>

          <div>
            <strong>Compare what matters</strong>
            <p>
              Understand the differences before making a decision.
            </p>
          </div>
        </div>

        <div className="trust-point">
          <span className="trust-point-icon">
            <CircleDollarSign size={21} />
          </span>

          <div>
            <strong>Understand market value</strong>
            <p>
              Use comparable listings for an indicative valuation.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}

/* =================================
   SHARED FOOTER
================================= */

export function Footer() {
  return (
    <footer className="site-footer">
      <div className="footer-top">
        <BrandLogo />
        <p>Find your drive. Find your AutoHub.</p>
      </div>

      <div className="footer-bottom">
        <span>© {new Date().getFullYear()} AutoHub</span>
        <span>Developer - Utsadeep</span>
      </div>
    </footer>
  )
}
/* =================================
   HOME PAGE
================================= */

function HomePage() {
  return (
    <main>
      <Hero />
      <DiscoverSection />
      <TrustSection />
    </main>
  )
}

export default HomePage
