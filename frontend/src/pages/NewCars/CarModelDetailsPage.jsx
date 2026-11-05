
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'
import {
  ArrowLeft,
  ArrowRight,
  BadgeCheck,
  CarFront,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Fuel,
  Gauge,
  LoaderCircle,
  MapPin,
  Settings2,
  ShieldCheck,
  Star,
  Users,
  Zap,
} from 'lucide-react'

import {
  getCarModelDetails,
  getCarVariants,
} from '../../services/cars'

import './CarModelDetailsPage.css'

function formatSpecLabel(value) {
  return String(value || '')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/\s+/g, ' ')
    .trim()
}

function CarModelDetailsPage() {
  const { brandSlug, modelSlug } = useParams()

  const [model, setModel] = useState(null)
  const [variants, setVariants] = useState([])

  const [loading, setLoading] = useState(true)
  const [variantsLoading, setVariantsLoading] = useState(true)

  const [error, setError] = useState('')
  const [variantsError, setVariantsError] = useState('')

  const [galleryCategory, setGalleryCategory] = useState('exterior')
  const [selectedImageIndex, setSelectedImageIndex] = useState(0)
  const [imageFailed, setImageFailed] = useState(false)

  const [selectedVariantId, setSelectedVariantId] = useState(null)

  // Fetch the model details.
  useEffect(() => {
    let active = true

    async function loadModel() {
      try {
        setLoading(true)
        setError('')
        setModel(null)

        const data = await getCarModelDetails(
          brandSlug,
          modelSlug
        )

        if (!active) return

        if (!data || typeof data !== 'object') {
          throw new Error('Unexpected vehicle details response.')
        }

        setModel(data)

        const exterior = data.images?.exteriorimages
        const interior = data.images?.interiorimages

        if (!Array.isArray(exterior) || exterior.length === 0) {
          if (Array.isArray(interior) && interior.length > 0) {
            setGalleryCategory('interior')
          }
        }

        setSelectedImageIndex(0)
      } catch (requestError) {
        if (active) {
          setError(
            requestError.message || 'Unable to load vehicle details.'
          )
        }
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    loadModel()

    return () => {
      active = false
    }
  }, [brandSlug, modelSlug])

  // Fetch available variants independently of model details.
  useEffect(() => {
    let active = true

    async function loadVariants() {
      try {
        setVariantsLoading(true)
        setVariantsError('')
        setVariants([])
        setSelectedVariantId(null)

        const response = await getCarVariants(
          brandSlug,
          modelSlug,
          {
            page: 1,
            page_size: 100,
          }
        )

        if (!active) return

        const results = Array.isArray(response?.results)
          ? response.results
          : []

        setVariants(results)

        if (results.length > 0) {
          setSelectedVariantId(results[0].id)
        }
      } catch (requestError) {
        if (active) {
          setVariantsError(
            requestError.message || 'Unable to load variants.'
          )
        }
      } finally {
        if (active) {
          setVariantsLoading(false)
        }
      }
    }

    loadVariants()

    return () => {
      active = false
    }
  }, [brandSlug, modelSlug])

  // Prepare the exterior and interior image collections.
  const exteriorImages = Array.isArray(model?.images?.exteriorimages)
    ? model.images.exteriorimages.map((image) => ({
        url: image.imageUrl || image.webpImage || image.image,
        title: image.title || model.name,
      }))
    : []

  const interiorImages = Array.isArray(model?.images?.interiorimages)
    ? model.images.interiorimages.map((image) => ({
        url: image.imageUrl || image.webpImage || image.image,
        title: image.title || model.name,
      }))
    : []

  let visibleImages =
    galleryCategory === 'interior'
      ? interiorImages
      : exteriorImages

  if (visibleImages.length === 0 && model?.primary_image) {
    visibleImages = [
      {
        url: model.primary_image,
        title: model.name,
      },
    ]
  }

  const currentImage =
    visibleImages[selectedImageIndex] || visibleImages[0] || null

  const selectedVariant =
    variants.find(
      (variant) => variant.id === selectedVariantId
    ) || variants[0] || null

  const specifications = Array.isArray(model?.key_specs)
    ? model.key_specs.flatMap((section) =>
        Array.isArray(section.items) ? section.items : []
      )
    : []

  const cityPrices = Array.isArray(model?.city_prices)
    ? model.city_prices.flatMap((section) =>
        Array.isArray(section.childs) ? section.childs : []
      )
    : []

  const features = Array.isArray(selectedVariant?.key_features)
    ? selectedVariant.key_features
    : []

  const handleGalleryChange = (category) => {
    setGalleryCategory(category)
    setSelectedImageIndex(0)
    setImageFailed(false)
  }

  const handleImageChange = (index) => {
    setSelectedImageIndex(index)
    setImageFailed(false)
  }

  if (loading) {
    return (
      <main className="model-details-state">
        <LoaderCircle size={34} className="loading-icon" />
        <p>Loading vehicle information...</p>
      </main>
    )
  }

  if (error || !model) {
    return (
      <main className="model-details-state">
        <CarFront size={45} />
        <h2>Vehicle information unavailable</h2>
        <p>{error || 'This vehicle could not be found.'}</p>

        <Link to="/new-cars" className="model-back-button">
          <ArrowLeft size={17} />
          Back to new cars
        </Link>
      </main>
    )
  }

  return (
    <main className="model-details-page">
      {/* Breadcrumb */}
      <div className="model-breadcrumb">
        <Link to="/">Home</Link>
        <ChevronRight size={14} />
        <Link to="/new-cars">New cars</Link>
        <ChevronRight size={14} />
        <span>{model.brand_name}</span>
        <ChevronRight size={14} />
        <strong>{model.name}</strong>
      </div>

      {/* Model introduction */}
      <section className="model-intro">
        <div>
          <span className="model-details-eyebrow">
            {model.brand_name?.toUpperCase()} / MODEL OVERVIEW
          </span>

          <h1>{model.name}</h1>

          <div className="model-intro-rating">
            <Star size={17} fill="currentColor" />
            <strong>{model.rating || 'N/A'}</strong>
            <span>
              {model.review_count ?? 0} reviews
            </span>
            <BadgeCheck size={16} />
          </div>

          <p>
            Explore images, specifications, available variants
            and pricing information for the {model.name}.
          </p>
        </div>

        <Link to="/new-cars" className="model-back-link">
          <ArrowLeft size={16} />
          All new cars
        </Link>
      </section>

      {/* Gallery and price */}
      <section className="model-main-grid">
        <div className="model-gallery">
          <div className="gallery-heading">
            <div>
              <span className="model-details-eyebrow">
                VEHICLE GALLERY
              </span>
              <h2>Take a closer look.</h2>
            </div>

            <div className="gallery-tabs">
              <button
                type="button"
                className={
                  galleryCategory === 'exterior'
                    ? 'gallery-tab active'
                    : 'gallery-tab'
                }
                onClick={() => handleGalleryChange('exterior')}
                disabled={exteriorImages.length === 0}
              >
                Exterior
                <span>{exteriorImages.length}</span>
              </button>

              <button
                type="button"
                className={
                  galleryCategory === 'interior'
                    ? 'gallery-tab active'
                    : 'gallery-tab'
                }
                onClick={() => handleGalleryChange('interior')}
                disabled={interiorImages.length === 0}
              >
                Interior
                <span>{interiorImages.length}</span>
              </button>
            </div>
          </div>

          <div className="model-main-image">
            <div className="model-image-fallback">
              <CarFront size={65} />
              <span>Vehicle image unavailable</span>
            </div>

            {currentImage?.url && !imageFailed && (
              <img
                src={currentImage.url}
                alt={currentImage.title || model.name}
                onError={() => setImageFailed(true)}
              />
            )}

            {visibleImages.length > 1 && (
              <>
                <button
                  type="button"
                  className="gallery-arrow previous"
                  aria-label="Previous image"
                  onClick={() =>
                    handleImageChange(
                      (selectedImageIndex - 1 + visibleImages.length) %
                        visibleImages.length
                    )
                  }
                >
                  <ChevronLeft size={22} />
                </button>

                <button
                  type="button"
                  className="gallery-arrow next"
                  aria-label="Next image"
                  onClick={() =>
                    handleImageChange(
                      (selectedImageIndex + 1) %
                        visibleImages.length
                    )
                  }
                >
                  <ChevronRight size={22} />
                </button>
              </>
            )}

            <span className="gallery-image-count">
              {visibleImages.length > 0
                ? `${selectedImageIndex + 1} / ${visibleImages.length}`
                : 'Image unavailable'}
            </span>
          </div>

          {visibleImages.length > 1 && (
            <div className="model-gallery-thumbnails">
              {visibleImages.slice(0, 7).map((image, index) => (
                <button
                  type="button"
                  key={`${galleryCategory}-${image.url}-${index}`}
                  className={
                    selectedImageIndex === index
                      ? 'gallery-thumbnail active'
                      : 'gallery-thumbnail'
                  }
                  onClick={() => handleImageChange(index)}
                  aria-label={`View image ${index + 1}`}
                >
                  <img src={image.url} alt="" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Pricing summary */}
        <aside className="model-price-panel">
          <span className="model-details-eyebrow">
            STARTING PRICE
          </span>

          <h2>₹{model.price_range || 'Price unavailable'}</h2>

          <p className="model-price-caption">
            Indicative ex-showroom price from catalogue data.
          </p>

          <div className="model-price-divider" />

          <div className="model-price-info">
            <span>Manufacturer</span>
            <strong>{model.brand_name}</strong>
          </div>

          <div className="model-price-info">
            <span>Variants available</span>
            <strong>
              {variantsLoading ? 'Loading...' : variants.length}
            </strong>
          </div>

          <div className="model-price-info">
            <span>Customer rating</span>
            <strong>
              <Star size={15} fill="currentColor" />
              {model.rating || 'N/A'}
            </strong>
          </div>

          {selectedVariant && (
            <>
              <div className="model-price-divider" />

              <span className="model-details-eyebrow">
                SELECTED VARIANT
              </span>

              <strong className="selected-variant-name">
                {selectedVariant.short_name || selectedVariant.name}
              </strong>

              <div className="selected-variant-price">
                <span>On-road price</span>
                <strong>
                  {selectedVariant.on_road_formatted
                    ? `₹${selectedVariant.on_road_formatted}`
                    : 'Not available'}
                </strong>
              </div>

              <p className="model-price-caption">
                {selectedVariant.pricing_city
                  ? `Pricing city: ${selectedVariant.pricing_city}`
                  : 'Pricing city unavailable'}
              </p>
            </>
          )}

          <a href="#model-variants" className="model-price-action">
            Explore variants <ArrowRight size={17} />
          </a>
        </aside>
      </section>

      {/* Key specifications */}
      <section className="model-spec-section">
        <div className="model-section-heading">
          <div>
            <span className="model-details-eyebrow">
              AT A GLANCE
            </span>
            <h2>Key specifications.</h2>
            <p>The important details of the {model.name}.</p>
          </div>
        </div>

        <div className="model-spec-grid">
          {specifications.map((specification, index) => {
            const label = formatSpecLabel(specification.text)

            return (
              <div
                className="model-spec-card"
                key={`${specification.text}-${index}`}
              >
                <span className="model-spec-icon">
                  {label.toLowerCase().includes('fuel') ? (
                    <Fuel size={21} />
                  ) : label.toLowerCase().includes('transmission') ? (
                    <Settings2 size={21} />
                  ) : label.toLowerCase().includes('mileage') ? (
                    <Gauge size={21} />
                  ) : label.toLowerCase().includes('seating') ? (
                    <Users size={21} />
                  ) : label.toLowerCase().includes('power') ? (
                    <Zap size={21} />
                  ) : (
                    <CarFront size={21} />
                  )}
                </span>

                <span className="model-spec-label">
                  {label}
                </span>

                <strong>{specification.value || 'Not available'}</strong>
              </div>
            )
          })}
        </div>

        {model.mileage_data?.description && (
          <div className="model-mileage-note">
            <Gauge size={19} />
            <p>{model.mileage_data.description}</p>
          </div>
        )}
      </section>

      {/* Variant selection */}
      <section className="model-variants-section" id="model-variants">
        <div className="model-section-heading">
          <div>
            <span className="model-details-eyebrow">
              FIND YOUR VERSION
            </span>
            <h2>Choose your variant.</h2>
            <p>
              Select a variant to view its pricing, specifications
              and features.
            </p>
          </div>

          <span className="variant-total">
            {variants.length} variants
          </span>
        </div>

        {variantsLoading ? (
          <div className="model-details-state compact">
            <LoaderCircle size={25} className="loading-icon" />
            Loading variants...
          </div>
        ) : variantsError ? (
          <div className="model-details-error" role="alert">
            Unable to load variants: {variantsError}
          </div>
        ) : variants.length === 0 ? (
          <div className="model-details-empty">
            No variants are currently available.
          </div>
        ) : (
          <div className="model-variant-grid">
            {variants.map((variant) => {
              const isSelected =
                selectedVariant?.id === variant.id

              return (
                <button
                  type="button"
                  key={variant.id}
                  className={
                    isSelected
                      ? 'model-variant-card selected'
                      : 'model-variant-card'
                  }
                  onClick={() => setSelectedVariantId(variant.id)}
                  aria-pressed={isSelected}
                >
                  <div className="variant-card-top">
                    <span className="variant-tag">
                      {variant.tag || 'Available variant'}
                    </span>

                    {isSelected && (
                      <CheckCircle2 size={20} />
                    )}
                  </div>

                  <h3>{variant.short_name || variant.name}</h3>

                  <p>{variant.summary || 'Specifications unavailable'}</p>

                  <div className="variant-card-price">
                    <span>Ex-showroom price</span>
                    <strong>
                      {variant.ex_showroom_formatted
                        ? `₹${variant.ex_showroom_formatted}`
                        : 'Not available'}
                    </strong>
                  </div>

                  <div className="variant-card-price">
                    <span>On-road price</span>
                    <strong>
                      {variant.on_road_formatted
                        ? `₹${variant.on_road_formatted}`
                        : 'Not available'}
                    </strong>
                  </div>

                  <div className="variant-card-city">
                    <MapPin size={14} />
                    {variant.pricing_city || 'City unavailable'}
                  </div>

                  {variant.waiting_period && (
                    <p className="variant-waiting">
                      Waiting period: {variant.waiting_period}
                    </p>
                  )}

                  <span className="variant-select-label">
                    {isSelected ? 'Selected variant' : 'Select this variant'}
                  </span>
                </button>
              )
            })}
          </div>
        )}

        {/* Selected variant features */}
        {selectedVariant && (
          <div className="selected-variant-features">
            <div className="model-section-heading">
              <div>
                <span className="model-details-eyebrow">
                  SELECTED VARIANT
                </span>
                <h2>{selectedVariant.name}</h2>
                <p>
                  Features and equipment available in this variant.
                </p>
              </div>
            </div>

            {features.length > 0 ? (
              <div className="variant-features-grid">
                {features.map((feature, index) => (
                  <div
                    className="variant-feature"
                    key={`${feature}-${index}`}
                  >
                    <CheckCircle2 size={17} />
                    <span>{feature}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="model-details-empty">
                Feature information is not available for this variant.
              </p>
            )}

            {selectedVariant.missing_features?.length > 0 && (
              <div className="variant-missing-features">
                <strong>Unavailable features</strong>
                {selectedVariant.missing_features.join(', ')}
              </div>
            )}
          </div>
        )}
      </section>

      {/* City-wise prices */}
      <section className="model-city-section">
        <div className="model-section-heading">
          <div>
            <span className="model-details-eyebrow">
              LOCATION-BASED PRICING
            </span>
            <h2>On-road prices by city.</h2>
            <p>
              Available catalogue pricing for selected cities.
            </p>
          </div>
        </div>

        {cityPrices.length > 0 ? (
          <div className="model-city-grid">
            {cityPrices.map((city, index) => (
              <div
                className="model-city-card"
                key={`${city.text}-${index}`}
              >
                <div className="city-card-icon">
                  <MapPin size={19} />
                </div>

                <div>
                  <span>{city.text}</span>
                  <strong>
                    {city.price ? `₹${city.price}` : 'Not available'}
                  </strong>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="model-details-empty">
            City-wise pricing is not available.
          </div>
        )}

        <p className="city-pricing-disclaimer">
          <ShieldCheck size={15} />
          Prices are shown as supplied by the catalogue and can vary
          by location, taxes and other charges. Check availability
          for your city before making a purchase decision.
        </p>
      </section>

      {/* Footer call to action */}
      <section className="model-details-bottom">
        <div>
          <span className="model-details-eyebrow">
            STILL EXPLORING?
          </span>
          <h2>Find the car that fits your journey.</h2>
          <p>Explore more manufacturers and models on AutoHub.</p>
        </div>

        <Link to="/new-cars" className="model-price-action">
          Browse all new cars <ArrowRight size={17} />
        </Link>
      </section>
    </main>
  )
}

export default CarModelDetailsPage
