import { useState, useEffect } from 'react';

interface Vehicle {
  id: number;
  vehicle_id: string;
  vin: string;
  license_plate: string;
  make: string;
  model: string;
  year: number;
  age: number;
  mileage: number;
  purchase_price: number;
  current_market_value: number;
  recommended_intake_price: number;
  target_selling_price: number;
  date_acquired: string;
  coe_at_purchase: number;
  current_coe: number;
  depreciation_rate: number;
  profit_margin: number;
  profit_amount: number;
  risk_level: string;
  risk_score: number;
  recommendation: string;
  recommendation_reason: string;
  sold_price: number;
  sold_date: string;
  vehicle_type: string;
  seat_count: number;
  days_in_inventory: number;
  status: string;
}

interface InventorySummary {
  total_vehicles: number;
  high_risk_count: number;
  total_inventory_value: number;
  average_days_in_inventory: number;
}

interface InventoryData {
  vehicles: Vehicle[];
  summary: InventorySummary;
}

const ageBuckets = [
  { label: '0-30 days', min: 0, max: 30 },
  { label: '30-60 days', min: 31, max: 60 },
  { label: '60-90 days', min: 61, max: 90 },
  { label: '90+ days', min: 91, max: Infinity },
];

function InventoryDashboard() {
  const [inventory, setInventory] = useState<InventoryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<'all' | 'high-risk'>('all');
  const [brandFilter, setBrandFilter] = useState('all');
  const [ageFilter, setAgeFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [seatFilter, setSeatFilter] = useState('all');
  const [selectedVehicle, setSelectedVehicle] = useState<Vehicle | null>(null);
  const [sellPrice, setSellPrice] = useState('');
  const [sellError, setSellError] = useState('');
  const [sellSuccess, setSellSuccess] = useState('');

  useEffect(() => {
    fetchInventory();
  }, []);

  const fetchInventory = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/inventory');
      if (!response.ok) {
        throw new Error('Failed to fetch inventory');
      }
      const data: InventoryData = await response.json();
      setInventory(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getRiskBadgeClass = (riskLevel: string) => {
    return `risk-badge ${riskLevel.toLowerCase()}`;
  };

  const getStatusLabel = (status: string) => {
    switch (status.toUpperCase()) {
      case 'SOLD':
        return 'SOLD';
      case 'RESERVED':
        return 'RESERVED';
      default:
        return 'AVAILABLE';
    }
  };

  const getVehicleAgeLabel = (age: number) => {
    if (age <= 3) return '0-3 yrs';
    if (age <= 7) return '4-7 yrs';
    return '8+ yrs';
  };

  const getUniqueValues = (key: keyof Vehicle) => {
    if (!inventory) return [] as string[];
    return Array.from(new Set(inventory.vehicles.map((vehicle) => String(vehicle[key] || ''))))
      .filter((value) => value && value !== '0')
      .sort();
  };

  const getRecommendationLabel = (rec: string) => rec || 'MONITOR';

  const buildAgeDistribution = () => {
    if (!inventory) return ageBuckets.map((bucket) => ({ ...bucket, count: 0 }));
    return ageBuckets.map((bucket) => ({
      ...bucket,
      count: inventory.vehicles.filter(
        (vehicle) => vehicle.days_in_inventory >= bucket.min && vehicle.days_in_inventory <= bucket.max
      ).length,
    }));
  };

  const getDepreciationTrend = (vehicle: Vehicle) => {
    const purchase = vehicle.purchase_price;
    const current = vehicle.current_market_value;
    const delta = current - purchase;
    if (delta < -10000) return 'Steep decline';
    if (delta < 0) return 'Moderate decline';
    return 'Stable';
  };

  const filterAge = (vehicle: Vehicle) => {
    if (ageFilter === 'all') return true;
    return getVehicleAgeLabel(vehicle.age) === ageFilter;
  };

  const filterSeat = (vehicle: Vehicle) => seatFilter === 'all' || String(vehicle.seat_count) === seatFilter;

  const filteredVehicles = inventory?.vehicles.filter((vehicle) => {
    const brandMatch = brandFilter === 'all' || vehicle.make === brandFilter;
    const typeMatch = typeFilter === 'all' || vehicle.vehicle_type === typeFilter;
    const ageMatch = filterAge(vehicle);
    const seatMatch = filterSeat(vehicle);
    const riskMatch = filter === 'high-risk' ? vehicle.risk_level === 'HIGH' : true;
    return brandMatch && typeMatch && ageMatch && seatMatch && riskMatch;
  }) ?? [];

  const sortedVehicles = [...filteredVehicles].sort((a, b) => {
    const recommendationOrder: Record<string, number> = {
      'SELL SOON': 0,
      'HOLD INVENTORY': 1,
      'MONITOR': 2,
    };
    const riskOrder: Record<string, number> = {
      HIGH: 0,
      MEDIUM: 1,
      LOW: 2,
    };
    const aRec = recommendationOrder[a.recommendation] ?? 3;
    const bRec = recommendationOrder[b.recommendation] ?? 3;
    if (aRec !== bRec) return aRec - bRec;
    const aRisk = riskOrder[a.risk_level] ?? 3;
    const bRisk = riskOrder[b.risk_level] ?? 3;
    return aRisk - bRisk;
  });

  const openVehicle = (vehicle: Vehicle) => {
    setSelectedVehicle(vehicle);
    setSellPrice(vehicle.target_selling_price.toString());
    setSellError('');
    setSellSuccess('');
  };

  const closeModal = () => {
    setSelectedVehicle(null);
    setSellPrice('');
    setSellError('');
    setSellSuccess('');
  };

  const handleSellVehicle = async () => {
    if (!selectedVehicle) return;
    setSellError('');
    setSellSuccess('');

    try {
      const response = await fetch(`/api/inventory/${selectedVehicle.id}/sell`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          soldPrice: Number(sellPrice),
          soldDate: new Date().toISOString().split('T')[0],
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error('detail' in data ? (data as any).detail : 'Failed to confirm sale');
      }
      if (data.vehicle) {
        setSelectedVehicle(data.vehicle);
        if (inventory) {
          setInventory({
            ...inventory,
            vehicles: inventory.vehicles.map((vehicle) => (vehicle.id === data.vehicle.id ? data.vehicle : vehicle)),
          });
        }
        setSellSuccess('Sale confirmed. Vehicle status updated to SOLD.');
      }
    } catch (err) {
      setSellError(err instanceof Error ? err.message : 'An unexpected error occurred');
    }
  };

  const handleRemoveVehicle = async (vehicle: Vehicle) => {
    const confirmed = window.confirm(`Remove ${vehicle.make} ${vehicle.model} from inventory? This cannot be undone.`);
    if (!confirmed) return;

    try {
      const response = await fetch(`/api/inventory/${vehicle.id}`, {
        method: 'DELETE',
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error('detail' in data ? (data as any).detail : 'Failed to remove vehicle');
      }
      if (inventory) {
        setInventory({
          ...inventory,
          vehicles: inventory.vehicles.filter((item) => item.id !== vehicle.id),
          summary: {
            ...inventory.summary,
            total_vehicles: inventory.summary.total_vehicles - 1,
            high_risk_count: inventory.summary.high_risk_count - (vehicle.risk_level === 'HIGH' ? 1 : 0),
            total_inventory_value: inventory.summary.total_inventory_value - vehicle.current_market_value,
          },
        });
      }
      if (selectedVehicle?.id === vehicle.id) {
        closeModal();
      }
    } catch (err) {
      window.alert(err instanceof Error ? err.message : 'Could not remove vehicle');
    }
  };

  if (loading) {
    return <div className="inventory-loading">Loading inventory...</div>;
  }

  if (error) {
    return <div className="inventory-error">Error: {error}</div>;
  }

  if (!inventory) {
    return <div className="inventory-error">No inventory data available</div>;
  }

  const ageDistribution = buildAgeDistribution();

  return (
    <div className="inventory-dashboard">
      <div className="inventory-header-row">
        <div>
          <h2>Inventory Dashboard</h2>
          <p className="inventory-note">Track risk, value exposure, and selling recommendations across your stock.</p>
        </div>
        <div>
          <button type="button" className="secondary-button" onClick={fetchInventory}>Refresh</button>
        </div>
      </div>

      <section className="inventory-summary-section">
        <div className="summary-card">
          <div className="summary-label">Total Vehicles</div>
          <div className="summary-value">{inventory.summary.total_vehicles}</div>
        </div>
        <div className="summary-card high-risk">
          <div className="summary-label">High Risk Vehicles</div>
          <div className="summary-value">{inventory.summary.high_risk_count}</div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Average Days in Inventory</div>
          <div className="summary-value">{Math.round(inventory.summary.average_days_in_inventory)}</div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Inventory Value Exposure</div>
          <div className="summary-value">S${(inventory.summary.total_inventory_value / 1000).toFixed(0)}k</div>
        </div>
      </section>

      <section className="inventory-chart-grid">
        <div className="inventory-chart-card">
          <h3>Inventory Age Distribution</h3>
          <div className="age-distribution">
            {ageDistribution.map((bucket) => (
              <div key={bucket.label} className="age-bar-row">
                <span>{bucket.label}</span>
                <div className="age-bar">
                  <div
                    className="age-bar-fill"
                    style={{ width: `${Math.min(100, (bucket.count / Math.max(inventory.vehicles.length, 1)) * 100)}%` }}
                  />
                </div>
                <strong>{bucket.count}</strong>
              </div>
            ))}
          </div>
        </div>

        <div className="inventory-chart-card">
          <h3>Depreciation Trend Snapshot</h3>
          <div className="trend-list">
            {inventory.vehicles.slice(0, 4).map((vehicle) => (
              <div key={vehicle.id} className="trend-item">
                <div>
                  <strong>{vehicle.make} {vehicle.model}</strong>
                  <span>{vehicle.license_plate}</span>
                </div>
                <div>{getDepreciationTrend(vehicle)}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="inventory-filters">
        <div className="inventory-controls">
          <button
            type="button"
            className={`filter-button ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All Vehicles ({inventory.vehicles.length})
          </button>
          <button
            type="button"
            className={`filter-button ${filter === 'high-risk' ? 'active' : ''}`}
            onClick={() => setFilter('high-risk')}
          >
            High Risk ({inventory.summary.high_risk_count})
          </button>
        </div>
        <div className="inventory-filter-row">
          <label>
            Brand
            <select value={brandFilter} onChange={(event) => setBrandFilter(event.target.value)}>
              <option value="all">All</option>
              {getUniqueValues('make').map((make) => (
                <option key={make} value={make}>{make}</option>
              ))}
            </select>
          </label>
          <label>
            Age
            <select value={ageFilter} onChange={(event) => setAgeFilter(event.target.value)}>
              <option value="all">All</option>
              <option value="0-3 yrs">0-3 yrs</option>
              <option value="4-7 yrs">4-7 yrs</option>
              <option value="8+ yrs">8+ yrs</option>
            </select>
          </label>
          <label>
            Type
            <select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}>
              <option value="all">All</option>
              {getUniqueValues('vehicle_type').map((value) => (
                <option key={value} value={value}>{value}</option>
              ))}
            </select>
          </label>
          <label>
            Seats
            <select value={seatFilter} onChange={(event) => setSeatFilter(event.target.value)}>
              <option value="all">All</option>
              {getUniqueValues('seat_count').map((value) => (
                <option key={value} value={value}>{value}</option>
              ))}
            </select>
          </label>
        </div>
      </section>

      <section className="inventory-table-section">
        <table className="inventory-table">
          <thead>
            <tr>
              <th>Vehicle</th>
              <th>Age</th>
              <th>Days</th>
              <th>Current Value</th>
              <th>Profit Margin</th>
              <th>Risk</th>
              <th>Recommendation</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {sortedVehicles.map((vehicle) => (
              <tr key={vehicle.id} className={vehicle.risk_level === 'HIGH' ? 'high-risk-row' : ''}>
                <td>
                  <div className="vehicle-name">
                    <strong>{vehicle.make} {vehicle.model}</strong>
                  </div>
                  <div className="vehicle-meta">
                    <span>{vehicle.license_plate}</span>
                    <span>{vehicle.status}</span>
                  </div>
                </td>
                <td>{vehicle.age} yrs</td>
                <td>
                  <span className={vehicle.days_in_inventory > 90 ? 'days-warning' : ''}>
                    {vehicle.days_in_inventory} days
                  </span>
                </td>
                <td>S${vehicle.current_market_value.toLocaleString()}</td>
                <td>{(vehicle.profit_margin * 100).toFixed(1)}%</td>
                <td>
                  <span className={getRiskBadgeClass(vehicle.risk_level)}>{vehicle.risk_level}</span>
                </td>
                <td>{getRecommendationLabel(vehicle.recommendation)}</td>
                <td>
                  <button type="button" className="table-action-button" onClick={() => openVehicle(vehicle)}>
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {selectedVehicle && (
        <div className="modal-backdrop" onClick={closeModal}>
          <div className="vehicle-modal" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3>{selectedVehicle.make} {selectedVehicle.model}</h3>
                <p>{selectedVehicle.license_plate} • {selectedVehicle.status}</p>
              </div>
              <button type="button" className="close-profile-button" onClick={closeModal}>×</button>
            </div>
            <div className="modal-body">
              <div className="detail-grid">
                <div className="detail-card">
                  <label>Purchase Price</label>
                  <div>S${selectedVehicle.purchase_price.toLocaleString()}</div>
                </div>
                <div className="detail-card">
                  <label>Current Market Value</label>
                  <div>S${selectedVehicle.current_market_value.toLocaleString()}</div>
                </div>
                <div className="detail-card">
                  <label>Estimated Profit / Loss</label>
                  <div>S${(selectedVehicle.current_market_value - selectedVehicle.purchase_price).toLocaleString()}</div>
                </div>
                <div className="detail-card">
                  <label>COE Impact</label>
                  <div>S${(selectedVehicle.current_coe - selectedVehicle.coe_at_purchase).toLocaleString()}</div>
                </div>
              </div>

              <div className="detail-section">
                <h4>Vehicle Details</h4>
                <div className="detail-row"><span>Year</span><span>{selectedVehicle.year}</span></div>
                <div className="detail-row"><span>Mileage</span><span>{selectedVehicle.mileage.toLocaleString()} km</span></div>
                <div className="detail-row"><span>Date Acquired</span><span>{selectedVehicle.date_acquired}</span></div>
                <div className="detail-row"><span>Depreciation Rate</span><span>{(selectedVehicle.depreciation_rate * 100).toFixed(1)}%</span></div>
                <div className="detail-row"><span>Target Selling Price</span><span>S${selectedVehicle.target_selling_price.toLocaleString()}</span></div>
                <div className="detail-row"><span>Recommended Intake</span><span>S${selectedVehicle.recommended_intake_price.toLocaleString()}</span></div>
              </div>

              <div className="detail-section">
                <h4>Recommendation</h4>
                <p className="recommendation-text">{selectedVehicle.recommendation}</p>
                <p className="recommendation-reason">{selectedVehicle.recommendation_reason}</p>
              </div>

              <div className="detail-section">
                <h4>Depreciation Trend</h4>
                <div className="trend-chart">
                  <div className="trend-point">
                    <span>Purchase</span>
                    <strong>S${selectedVehicle.purchase_price.toLocaleString()}</strong>
                  </div>
                  <div className="trend-point">
                    <span>Current</span>
                    <strong>S${selectedVehicle.current_market_value.toLocaleString()}</strong>
                  </div>
                </div>
              </div>

              <div className="detail-section">
                <h4>Sale & Profit</h4>
                <div className="detail-row"><span>Profit</span><span>S${selectedVehicle.profit_amount.toLocaleString()}</span></div>
                {selectedVehicle.sold_price > 0 && (
                  <>
                    <div className="detail-row"><span>Sold Price</span><span>S${selectedVehicle.sold_price.toLocaleString()}</span></div>
                    <div className="detail-row"><span>Sold Date</span><span>{selectedVehicle.sold_date}</span></div>
                  </>
                )}
              </div>

              {selectedVehicle.status !== 'SOLD' && (
                <div className="detail-section sale-form-section">
                  <h4>Sell Vehicle</h4>
                  <label>
                    Final Selling Price
                    <input
                      type="number"
                      value={sellPrice}
                      onChange={(event) => setSellPrice(event.target.value)}
                      min="0"
                      step="100"
                    />
                  </label>
                  <div className="sale-actions">
                    <button type="button" className="primary-button" onClick={handleSellVehicle}>
                      Confirm Sale
                    </button>
                  </div>
                  {sellError && <p className="error-message">{sellError}</p>}
                  {sellSuccess && <p className="success-message">{sellSuccess}</p>}
                </div>
              )}

              <div className="detail-section remove-action-section">
                <h4>Inventory Actions</h4>
                <button type="button" className="table-action-button remove-button" onClick={() => handleRemoveVehicle(selectedVehicle)}>
                  Remove Vehicle
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default InventoryDashboard;
