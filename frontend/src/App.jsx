import {
  BrowserRouter,
  Link,
  Outlet,
  Route,
  Routes,
}

from 'react-router'
import HomePage, { Navbar, Footer } from './pages/Home/HomePage'
import NewCarsPage from './pages/NewCars/NewCarsPage'
import CarModelDetailsPage from './pages/NewCars/CarModelDetailsPage'
import UsedCarsPage from './pages/UsedCars/UsedCarsPage'
import UsedCarDetailsPage from './pages/UsedCars/UsedCarDetailsPage'
import ComparePage from './pages/Compare/ComparePage'
import ValuationPage from './pages/Valuation/ValuationPage'
import LoginPage from './pages/Auth/LoginPage'
import RegisterPage from './pages/Auth/RegisterPage'
import AccountPage from './pages/Auth/AccountPage'
import DealerDashboard from './pages/Dealer/DealerDashboard'
import DealerMarketplacePage from './pages/DealerMarketplace/DealerMarketplacePage'
import DealerVehicleDetailsPage from './pages/DealerMarketplace/DealerVehicleDetailsPage'
import { AuthProvider } from './context/AuthContext.jsx'
import './App.css'

function AppLayout() {
  return <><Navbar /><Outlet /><Footer /></>
}

function NotFoundPage() {
  return <main className="placeholder-page"><div className="placeholder-card"><div className="placeholder-brand">auto<span>hub</span></div><span className="placeholder-label">AUTOHUB EXPERIENCE</span><h1>Page not found</h1><p>The page you are looking for does not exist or may have moved.</p><Link to="/" className="placeholder-home-link">Back to homepage <span aria-hidden="true">→</span></Link><div className="placeholder-decoration" /></div></main>
}

function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<HomePage />} />
          <Route path="/new-cars" element={<NewCarsPage />} />
          <Route path="/new-cars/:brandSlug/:modelSlug" element={<CarModelDetailsPage />} />
          <Route path="/used-cars" element={<UsedCarsPage />} />
          <Route path="/used-cars/:carId" element={<UsedCarDetailsPage />} />
          <Route path="/compare" element={<ComparePage />} />
          <Route path="/valuation" element={<ValuationPage />} />
          <Route path="/dealer-marketplace" element={<DealerMarketplacePage />} />
          <Route path="/dealer-marketplace/:vehicleId" element={<DealerVehicleDetailsPage />} />
          <Route path="/dealer" element={<DealerDashboard />} />
          <Route path="/account" element={<AccountPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Routes>
    </BrowserRouter>
  )
}

function App() {
  return <AuthProvider><AppRoutes /></AuthProvider>
}

export default App
