
import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router';
import {
  Search,
  SlidersHorizontal,
  RotateCcw,
  MapPin,
  CalendarDays,
  Gauge,
  Fuel,
  Settings2,
  CarFront,
  ChevronLeft,
  ChevronRight,
  LoaderCircle,
  X,
} from 'lucide-react';

import {
  getUsedCars,
  getUsedCarFilters,
} from '../../services/usedCars';

import './UsedCarsPage.css';

const PAGE_SIZE = 9;

const INITIAL_FILTERS = {
  search: '',
  make: '',
  model: '',
  city: '',
  locality: '',
  fuel: '',
  transmission: '',
  body_type: '',
  seller_type: '',
  owner_count: '',
  min_price: '',
  max_price: '',
  min_year: '',
  max_year: '',
  min_km: '',
  max_km: '',
  ordering: '-last_seen_at',
};

const formatPrice = (price) => {
  const amount = Number(price);

  if (!Number.isFinite(amount) || amount <= 0) {
    return 'Price on request';
  }

  if (amount >= 10000000) {
    return `₹${(amount / 10000000).toFixed(2)} Cr`;
  }

  return `₹${(amount / 100000).toFixed(2)} Lakh`;
};

const formatKm = (value) => {
  const amount = Number(value);

  if (!Number.isFinite(amount)) {
    return 'N/A';
  }

  return `${amount.toLocaleString('en-IN')} km`;
};

const getOwnerLabel = (count) => {
  const labels = {
    1: '1st Owner',
    2: '2nd Owner',
    3: '3rd Owner',
  };

  return labels[count] || `${count || 'N/A'} Owner`;
};

function FilterField({ label, children }) {
  return (
    <div className="used-filter-field">
      <label>{label}</label>
      {children}
    </div>
  );
}

function UsedCarCard({ car }) {
  const imageUrl =
    car.primary_image ||
    car.images?.primary ||
    car.images?.placeholder ||
    '';

  const title =
    car.title ||
    `${car.year || ''} ${car.make || ''} ${car.model || ''} ${car.variant || ''}`.trim();

  return (
    <article className="used-car-card">
      <Link
        to={`/used-cars/${car.id}`}
        className="used-car-image-link"
        aria-label={`View ${title}`}
      >
        <div className="used-car-image">
          <div className="used-car-image-fallback">
            <CarFront size={42} strokeWidth={1.4} />
            <span>Image unavailable</span>
          </div>

          {imageUrl && (
            <img
              src={imageUrl}
              alt={title}
              loading="lazy"
              onError={(event) => {
                event.currentTarget.style.display = 'none';
              }}
            />
          )}

          {car.ai_price_badge && (
            <span className="used-price-badge">
              {car.ai_price_badge}
            </span>
          )}
        </div>
      </Link>

      <div className="used-car-content">
        <div className="used-car-title-row">
          <Link to={`/used-cars/${car.id}`} className="used-car-title">
            {title}
          </Link>
        </div>

        <div className="used-car-location">
          <MapPin size={14} />
          <span>
            {[car.locality, car.city].filter(Boolean).join(', ') ||
              'Location not available'}
          </span>
        </div>

        <div className="used-car-specs">
          <div>
            <CalendarDays size={15} />
            <span>{car.year || 'N/A'}</span>
          </div>

          <div>
            <Gauge size={15} />
            <span>{formatKm(car.km_driven)}</span>
          </div>

          <div>
            <Fuel size={15} />
            <span>{car.fuel || 'N/A'}</span>
          </div>

          <div>
            <Settings2 size={15} />
            <span>{car.transmission || 'N/A'}</span>
          </div>
        </div>

        <div className="used-car-details">
          <span>{getOwnerLabel(car.owner_count)}</span>
          <span>{car.body_type || 'Vehicle'}</span>
          <span>{car.seller_type || 'Seller'}</span>
        </div>

        <div className="used-car-card-footer">
          <div>
            <span className="used-car-price">
              {formatPrice(car.price)}
            </span>
            <span className="used-car-price-caption">
              Asking price
            </span>
          </div>

          <Link
            to={`/used-cars/${car.id}`}
            className="used-car-view-button"
          >
            View Details
            <ChevronRight size={16} />
          </Link>
        </div>
      </div>
    </article>
  );
}

export default function UsedCarsPage() {
  const [searchParams] = useSearchParams();
  const initialFilters = {
    ...INITIAL_FILTERS,
    search: searchParams.get('search') || '',
    city: searchParams.get('city') === 'kolkata' ? 'Kolkata' : (searchParams.get('city') || ''),
    min_price: searchParams.get('min_price') || '',
    max_price: searchParams.get('max_price') || '',
  };
  const [cars, setCars] = useState([]);
  const [filterOptions, setFilterOptions] = useState({});
  const [filters, setFilters] = useState(initialFilters);
  const [appliedFilters, setAppliedFilters] = useState(initialFilters);

  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filterLoading, setFilterLoading] = useState(true);
  const [error, setError] = useState('');
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);

  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE));

  // Load available filter options.
  useEffect(() => {
    let cancelled = false;

    const loadFilters = async () => {
      try {
        const data = await getUsedCarFilters();

        if (!cancelled) {
          setFilterOptions(data || {});
        }
      } catch (err) {
        if (!cancelled) {
          console.error('Failed to load used car filters:', err);
        }
      } finally {
        if (!cancelled) {
          setFilterLoading(false);
        }
      }
    };

    loadFilters();

    return () => {
      cancelled = true;
    };
  }, []);

  // Load used car listings whenever the page or applied filters change.
  useEffect(() => {
    let cancelled = false;

    const loadCars = async () => {
      setLoading(true);
      setError('');

      try {
        const data = await getUsedCars({
          ...appliedFilters,
          page,
          page_size: PAGE_SIZE,
        });

        if (!cancelled) {
          setCars(Array.isArray(data.results) ? data.results : []);
          setTotalCount(Number(data.count) || 0);
        }
      } catch (err) {
        if (!cancelled) {
          setCars([]);
          setTotalCount(0);
          setError(
            err.message || 'Unable to load used cars. Please try again.'
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadCars();

    return () => {
      cancelled = true;
    };
  }, [appliedFilters, page]);

  const updateFilter = (event) => {
    const { name, value } = event.target;

    setFilters((current) => ({
      ...current,
      [name]: value,
    }));
  };

  const applyFilters = (event) => {
    event?.preventDefault();

    setAppliedFilters({ ...filters });
    setPage(1);
    setMobileFiltersOpen(false);
  };

  const resetFilters = () => {
    setFilters({ ...INITIAL_FILTERS });
    setAppliedFilters({ ...INITIAL_FILTERS });
    setPage(1);
    setMobileFiltersOpen(false);
  };

  const handleSort = (event) => {
    const { value } = event.target;

    setFilters((current) => ({
      ...current,
      ordering: value,
    }));

    setAppliedFilters((current) => ({
      ...current,
      ordering: value,
    }));

    setPage(1);
  };

  const renderOptions = (items = []) =>
    items.map((item) => (
      <option key={String(item)} value={item}>
        {item}
      </option>
    ));

  const renderFilterPanel = () => (
    <form className="used-filters-form" onSubmit={applyFilters}>
      <div className="used-filter-heading">
        <div>
          <span className="used-section-eyebrow">CUSTOMIZE</span>
          <h3>Filter Cars</h3>
        </div>

        <button
          type="button"
          className="used-reset-button"
          onClick={resetFilters}
        >
          <RotateCcw size={14} />
          Reset
        </button>
      </div>

      <FilterField label="Manufacturer">
        <select
          name="make"
          value={filters.make}
          onChange={updateFilter}
        >
          <option value="">All Manufacturers</option>
          {renderOptions(filterOptions.makes)}
        </select>
      </FilterField>

      <FilterField label="Model">
        <select
          name="model"
          value={filters.model}
          onChange={updateFilter}
        >
          <option value="">All Models</option>
          {renderOptions(filterOptions.models)}
        </select>
      </FilterField>

      <FilterField label="City">
        <select
          name="city"
          value={filters.city}
          onChange={updateFilter}
        >
          <option value="">All Cities</option>
          {renderOptions(filterOptions.cities)}
        </select>
      </FilterField>

      <FilterField label="Locality">
        <select
          name="locality"
          value={filters.locality}
          onChange={updateFilter}
        >
          <option value="">All Localities</option>
          {renderOptions(filterOptions.localities)}
        </select>
      </FilterField>

      <FilterField label="Fuel Type">
        <select
          name="fuel"
          value={filters.fuel}
          onChange={updateFilter}
        >
          <option value="">All Fuel Types</option>
          {renderOptions(filterOptions.fuels)}
        </select>
      </FilterField>

      <FilterField label="Transmission">
        <select
          name="transmission"
          value={filters.transmission}
          onChange={updateFilter}
        >
          <option value="">All Transmissions</option>
          {renderOptions(filterOptions.transmissions)}
        </select>
      </FilterField>

      <FilterField label="Body Type">
        <select
          name="body_type"
          value={filters.body_type}
          onChange={updateFilter}
        >
          <option value="">All Body Types</option>
          {renderOptions(filterOptions.body_types)}
        </select>
      </FilterField>

      <FilterField label="Seller Type">
        <select
          name="seller_type"
          value={filters.seller_type}
          onChange={updateFilter}
        >
          <option value="">All Sellers</option>
          {renderOptions(filterOptions.seller_types)}
        </select>
      </FilterField>

      <FilterField label="Number of Owners">
        <select
          name="owner_count"
          value={filters.owner_count}
          onChange={updateFilter}
        >
          <option value="">Any Owner Count</option>
          {renderOptions(filterOptions.owner_options)}
        </select>
      </FilterField>

      <div className="used-filter-range">
        <span className="used-filter-range-label">Price Range (₹)</span>

        <div className="used-range-inputs">
          <input
            type="number"
            name="min_price"
            placeholder="Min price"
            min="0"
            value={filters.min_price}
            onChange={updateFilter}
          />

          <input
            type="number"
            name="max_price"
            placeholder="Max price"
            min="0"
            value={filters.max_price}
            onChange={updateFilter}
          />
        </div>
      </div>

      <div className="used-filter-range">
        <span className="used-filter-range-label">Manufacturing Year</span>

        <div className="used-range-inputs">
          <input
            type="number"
            name="min_year"
            placeholder="From"
            min="1900"
            value={filters.min_year}
            onChange={updateFilter}
          />

          <input
            type="number"
            name="max_year"
            placeholder="To"
            min="1900"
            value={filters.max_year}
            onChange={updateFilter}
          />
        </div>
      </div>

      <div className="used-filter-range">
        <span className="used-filter-range-label">Kilometres Driven</span>

        <div className="used-range-inputs">
          <input
            type="number"
            name="min_km"
            placeholder="Min km"
            min="0"
            value={filters.min_km}
            onChange={updateFilter}
          />

          <input
            type="number"
            name="max_km"
            placeholder="Max km"
            min="0"
            value={filters.max_km}
            onChange={updateFilter}
          />
        </div>
      </div>

      <button type="submit" className="used-apply-filter-button">
        <SlidersHorizontal size={16} />
        Apply Filters
      </button>

      {filterLoading && (
        <p className="used-filter-loading">
          Loading filter options...
        </p>
      )}
    </form>
  );

  return (
    <main className="used-marketplace">
      <section className="used-marketplace-hero">
        <div className="used-marketplace-hero-inner">
          <div className="used-hero-copy">
            <span className="used-section-eyebrow">
              THE PRE-OWNED COLLECTION
            </span>

            <h1>
              Find a car that feels
              <span> right at home.</span>
            </h1>

            <p>
              Explore quality pre-owned cars, compare your options,
              and find the right drive for your next journey.
            </p>
          </div>

          <div className="used-hero-stat">
            <span className="used-hero-stat-number">
              {totalCount.toLocaleString('en-IN')}
            </span>
            <span>Available listings</span>
          </div>

          <form
            className="used-search-bar"
            onSubmit={(event) => {
              event.preventDefault();
              applyFilters();
            }}
          >
            <Search size={20} />

            <input
              type="search"
              name="search"
              placeholder="Search by brand, model, city..."
              value={filters.search}
              onChange={updateFilter}
            />

            {filters.search && (
              <button
                type="button"
                className="used-clear-search"
                aria-label="Clear search"
                onClick={() =>
                  setFilters((current) => ({
                    ...current,
                    search: '',
                  }))
                }
              >
                <X size={16} />
              </button>
            )}

            <button type="submit">
              Search Cars
            </button>
          </form>
        </div>
      </section>

      <section className="used-marketplace-main">
        <div className="used-marketplace-toolbar">
          <div>
            <span className="used-section-eyebrow">
              EXPLORE PRE-OWNED CARS
            </span>
            <h2>Used Cars in India</h2>
            <p>
              Discover available listings and find your next car.
            </p>
          </div>

          <button
            type="button"
            className="used-mobile-filter-button"
            onClick={() => setMobileFiltersOpen(true)}
          >
            <SlidersHorizontal size={17} />
            Filters
          </button>
        </div>

        <div className="used-marketplace-layout">
          <aside className="used-filter-sidebar">
            {renderFilterPanel()}
          </aside>

          {mobileFiltersOpen && (
            <div
              className="used-mobile-filter-overlay"
              onClick={() => setMobileFiltersOpen(false)}
            >
              <div
                className="used-mobile-filter-panel"
                onClick={(event) => event.stopPropagation()}
              >
                <div className="used-mobile-filter-top">
                  <h3>Filter Cars</h3>

                  <button
                    type="button"
                    aria-label="Close filters"
                    onClick={() => setMobileFiltersOpen(false)}
                  >
                    <X size={21} />
                  </button>
                </div>

                {renderFilterPanel()}
              </div>
            </div>
          )}

          <div className="used-results-area">
            <div className="used-results-toolbar">
              <div className="used-results-count">
                <strong>
                  {totalCount.toLocaleString('en-IN')}
                </strong>
                <span>cars found</span>
              </div>

              <div className="used-sort-control">
                <label htmlFor="used-sort">Sort by</label>

                <select
                  id="used-sort"
                  value={appliedFilters.ordering}
                  onChange={handleSort}
                >
                  <option value="-last_seen_at">Recently Updated</option>
                  <option value="price">Price: Low to High</option>
                  <option value="-price">Price: High to Low</option>
                  <option value="-year">Newest First</option>
                  <option value="year">Oldest First</option>
                  <option value="km_driven">Lowest Kilometres</option>
                  <option value="-km_driven">Highest Kilometres</option>
                </select>
              </div>
            </div>

            {loading && (
              <div className="used-loading-state">
                <LoaderCircle size={34} className="used-spinner" />
                <h3>Finding your next car...</h3>
                <p>Loading available vehicles.</p>
              </div>
            )}

            {!loading && error && (
              <div className="used-error-state">
                <CarFront size={38} />
                <h3>Unable to load cars</h3>
                <p>{error}</p>
                <button
                  type="button"
                  onClick={() => {
                    setAppliedFilters((current) => ({ ...current }));
                  }}
                >
                  Try Again
                </button>
              </div>
            )}

            {!loading && !error && cars.length === 0 && (
              <div className="used-empty-state">
                <CarFront size={42} />
                <h3>No cars found</h3>
                <p>
                  Try changing your search or removing some filters.
                </p>
                <button type="button" onClick={resetFilters}>
                  Clear All Filters
                </button>
              </div>
            )}

            {!loading && !error && cars.length > 0 && (
              <>
                <div className="used-cars-grid">
                  {cars.map((car) => (
                    <UsedCarCard key={car.id} car={car} />
                  ))}
                </div>

                <div className="used-pagination">
                  <button
                    type="button"
                    disabled={page <= 1}
                    onClick={() => {
                      setPage((current) => Math.max(1, current - 1));
                    }}
                  >
                    <ChevronLeft size={17} />
                    Previous
                  </button>

                  <span>
                    Page <strong>{page}</strong> of{' '}
                    <strong>{totalPages}</strong>
                  </span>

                  <button
                    type="button"
                    disabled={page >= totalPages}
                    onClick={() => {
                      setPage((current) =>
                        Math.min(totalPages, current + 1)
                      );
                    }}
                  >
                    Next
                    <ChevronRight size={17} />
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}
