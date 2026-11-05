
import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import {
  ArrowRight,
  CarFront,
  ChevronLeft,
  ChevronRight,
  LoaderCircle,
  Search,
  Star,
  Tag,
} from 'lucide-react'

import {
  getCarBrands,
  getBrandModels,
  searchCars,
} from '../../services/cars'

import './NewCarsPage.css'

const PAGE_SIZE = 9

function NewCarsPage() {
  const [brands, setBrands] = useState([])
  const [selectedBrand, setSelectedBrand] = useState(null)

  const [models, setModels] = useState([])
  const [pagination, setPagination] = useState({
    count: 0,
    page: 1,
    page_size: PAGE_SIZE,
    total_pages: 0,
    next_page: null,
    previous_page: null,
  })

  const [brandsLoading, setBrandsLoading] = useState(true)
  const [modelsLoading, setModelsLoading] = useState(false)

  const [brandsError, setBrandsError] = useState('')
  const [modelsError, setModelsError] = useState('')

  const [searchInput, setSearchInput] = useState('')
  const [activeSearch, setActiveSearch] = useState('')
  const [page, setPage] = useState(1)

  // Fetch all active car brands.
  useEffect(() => {
    let active = true

    async function loadBrands() {
      try {
        setBrandsLoading(true)
        setBrandsError('')

        const data = await getCarBrands()

        if (!active) return

        if (!Array.isArray(data)) {
          throw new Error('Unexpected brand API response.')
        }

        setBrands(data)

        if (data.length > 0) {
          setSelectedBrand(data[0])
        }
      } catch (error) {
        if (active) {
          setBrandsError(
            error.message || 'Unable to load car manufacturers.'
          )
        }
      } finally {
        if (active) {
          setBrandsLoading(false)
        }
      }
    }

    loadBrands()

    return () => {
      active = false
    }
  }, [])

  // Fetch models when brand, search term or page changes.
  useEffect(() => {
    if (!selectedBrand) return

    let active = true

    async function loadModels() {
      try {
        setModelsLoading(true)
        setModelsError('')

        const params = {
          page,
          page_size: PAGE_SIZE,
        }

        const response = activeSearch
          ? await searchCars(activeSearch, params)
          : await getBrandModels(selectedBrand.slug, params)

        if (!active) return

        const results = Array.isArray(response?.results)
          ? response.results
          : []

        setModels(results)

        setPagination({
          count: Number(response?.count) || 0,
          page: Number(response?.page) || page,
          page_size: Number(response?.page_size) || PAGE_SIZE,
          total_pages: Number(response?.total_pages) || 0,
          next_page: response?.next_page ?? null,
          previous_page: response?.previous_page ?? null,
        })
      } catch (error) {
        if (active) {
          setModels([])
          setModelsError(
            error.message || 'Unable to load car models.'
          )
        }
      } finally {
        if (active) {
          setModelsLoading(false)
        }
      }
    }

    loadModels()

    return () => {
      active = false
    }
  }, [selectedBrand, activeSearch, page])

  function handleBrandChange(brand) {
    setSelectedBrand(brand)
    setActiveSearch('')
    setSearchInput('')
    setPage(1)
  }

  function handleSearch(event) {
    event.preventDefault()

    setActiveSearch(searchInput.trim())
    setPage(1)
  }

  function handleClearSearch() {
    setSearchInput('')
    setActiveSearch('')
    setPage(1)
  }

  function getModelBrandSlug(model) {
    const modelBrand = brands.find(
      (brand) =>
        brand.name?.toLowerCase() ===
        model.brand_name?.toLowerCase()
    )

    return modelBrand?.slug || selectedBrand?.slug || ''
  }

  return (
    <main className="new-cars-page">
      {/* Marketplace introduction */}
      <section className="new-cars-hero">
        <div className="new-cars-hero-content">
          <span className="new-cars-eyebrow">
            <CarFront size={15} />
            AUTOHUB / NEW CAR MARKETPLACE
          </span>

          <h1>
            Find the car
            <br />
            that feels <span>right.</span>
          </h1>

          <p>
            Discover manufacturers, explore models and compare
            the details that matter before your next purchase.
          </p>

          <div className="new-cars-hero-stats">
            <div>
              <strong>{brands.length || '—'}</strong>
              <span>Manufacturers</span>
            </div>

            <div>
              <strong>Live</strong>
              <span>Catalogue data</span>
            </div>

            <div>
              <strong>INR</strong>
              <span>Indian pricing</span>
            </div>
          </div>
        </div>

        <div className="new-cars-hero-decoration">
          <span className="hero-decoration-circle" />
          <span className="hero-decoration-leaf" />
          <CarFront size={105} strokeWidth={1.2} />
          <span className="hero-decoration-caption">
            YOUR NEXT JOURNEY STARTS HERE
          </span>
        </div>
      </section>

      {/* Brand selection */}
      <section className="new-cars-content">
        <div className="marketplace-section-heading">
          <div>
            <span className="new-cars-eyebrow">
              EXPLORE BY MANUFACTURER
            </span>

            <h2>Choose your brand.</h2>

            <p>
              Select a manufacturer to explore its available models.
            </p>
          </div>
        </div>

        {brandsLoading ? (
          <div className="marketplace-status">
            <LoaderCircle className="loading-icon" size={25} />
            Loading manufacturers...
          </div>
        ) : brandsError ? (
          <div className="marketplace-error" role="alert">
            <strong>Unable to load manufacturers</strong>
            <p>{brandsError}</p>
            <button
              type="button"
              onClick={() => window.location.reload()}
            >
              Retry
            </button>
          </div>
        ) : (
          <div className="brand-selector">
            {brands.map((brand) => (
              <button
                type="button"
                key={brand.id}
                className={
                  selectedBrand?.id === brand.id
                    ? 'brand-option selected'
                    : 'brand-option'
                }
                onClick={() => handleBrandChange(brand)}
                aria-pressed={selectedBrand?.id === brand.id}
              >
                {brand.logo_url ? (
                  <img
                    src={brand.logo_url}
                    alt=""
                    className="brand-option-logo"
                  />
                ) : (
                  <span className="brand-option-initial">
                    {brand.name?.charAt(0)}
                  </span>
                )}

                <span>{brand.name}</span>
              </button>
            ))}
          </div>
        )}

        {/* Search */}
        <div className="model-search-header">
          <div>
            <span className="new-cars-eyebrow">
              {activeSearch ? 'SEARCH RESULTS' : 'AVAILABLE MODELS'}
            </span>

            <h2>
              {activeSearch
                ? `Results for "${activeSearch}"`
                : `${selectedBrand?.name || 'Car'} models`}
            </h2>

            {!modelsLoading && !modelsError && (
              <p>
                {pagination.count} models available
              </p>
            )}
          </div>

          <form className="model-search-form" onSubmit={handleSearch}>
            <Search size={19} />

            <input
              type="search"
              placeholder="Search brand or model..."
              value={searchInput}
              onChange={(event) =>
                setSearchInput(event.target.value)
              }
              aria-label="Search car brands and models"
            />

            {activeSearch && (
              <button
                type="button"
                className="clear-search"
                onClick={handleClearSearch}
              >
                Clear
              </button>
            )}

            <button type="submit" aria-label="Search">
              <ArrowRight size={18} />
            </button>
          </form>
        </div>

        {/* Model cards */}
        {modelsLoading ? (
          <div className="marketplace-status">
            <LoaderCircle className="loading-icon" size={28} />
            Loading car models...
          </div>
        ) : modelsError ? (
          <div className="marketplace-error" role="alert">
            <strong>Unable to load models</strong>
            <p>{modelsError}</p>
            <button
              type="button"
              onClick={() => setPage((currentPage) => currentPage)}
            >
              Retry
            </button>
          </div>
        ) : models.length === 0 ? (
          <div className="marketplace-empty">
            <CarFront size={42} />
            <h3>No models found</h3>
            <p>
              Try another manufacturer or change your search term.
            </p>
          </div>
        ) : (
          <div className="car-model-grid">
            {models.map((model) => {
              const brandSlug = getModelBrandSlug(model)

              return (
                <article className="car-model-card" key={model.id}>
                  <div className="car-model-image">
                    <div className="car-image-fallback">
                      <CarFront size={42} />
                    </div>

                    {model.primary_image && (
                      <img
                        src={model.primary_image}
                        alt={model.name}
                        loading="lazy"
                        onError={(event) => {
                          event.currentTarget.style.display = 'none'
                        }}
                      />
                    )}

                    <span className="model-brand-badge">
                      {model.brand_name}
                    </span>
                  </div>

                  <div className="car-model-details">
                    <h3>{model.name}</h3>

                    <div className="car-model-rating">
                      {model.rating !== null &&
                        model.rating !== undefined && (
                          <>
                            <Star
                              size={15}
                              fill="currentColor"
                            />
                            <strong>{model.rating}</strong>
                            <span>
                              ({model.review_count ?? 0} reviews)
                            </span>
                          </>
                        )}
                    </div>

                    <div className="car-model-price">
                      <span>Ex-showroom price</span>
                      <strong>
                        <Tag size={15} />
                        {model.price_range || 'Price unavailable'}
                      </strong>
                    </div>

                    <Link
                      to={`/new-cars/${brandSlug}/${model.slug}`}
                      className="model-details-link"
                    >
                      View model <ArrowRight size={17} />
                    </Link>
                  </div>
                </article>
              )
            })}
          </div>
        )}

        {/* Pagination */}
        {!modelsLoading &&
          !modelsError &&
          pagination.total_pages > 1 && (
            <div className="model-pagination">
              <button
                type="button"
                disabled={!pagination.previous_page}
                onClick={() => setPage(pagination.previous_page)}
                aria-label="Previous page"
              >
                <ChevronLeft size={19} />
                Previous
              </button>

              <span>
                Page <strong>{pagination.page}</strong> of{' '}
                <strong>{pagination.total_pages}</strong>
              </span>

              <button
                type="button"
                disabled={!pagination.next_page}
                onClick={() => setPage(pagination.next_page)}
                aria-label="Next page"
              >
                Next
                <ChevronRight size={19} />
              </button>
            </div>
          )}
      </section>
    </main>
  )
}

export default NewCarsPage
