import { useState } from 'react';
import Login from './Login';
import InventoryDashboard from './InventoryDashboard';
import ScenarioSimulation from './ScenarioSimulation';
import MembersEditor from './MembersEditor';

interface FormData {
  make: string;
  model: string;
  licensePlate: string;
  year: string;
  mileage: string;
  vehicleType: string;
  seatCount: string;
  ageYears: string;
  arf: string;
  coe: string;
  registrationDate: string;
  agreedPurchaseCost: string;
}

interface ValuationResult {
  ageYears: number;
  arf: number;
  coe: number;
  registrationDate: string;
  parfScheme: string;
  parfCap: number;
  estimatedParfRebate: number;
  depreciationValue: number;
  estimatedMarketPrice: number;
  recommendedIntakePrice: number;
}

interface UserProfile {
  username: string;
  role: string;
}

type FeatureId = 'dashboard' | 'valuation' | 'simulation' | 'inventory' | 'members';

const initialForm: FormData = {
  make: '',
  model: '',
  licensePlate: '',
  year: '',
  mileage: '0',
  vehicleType: 'Sedan',
  seatCount: '5',
  ageYears: '',
  arf: '',
  coe: '',
  registrationDate: '',
  agreedPurchaseCost: '',
};

function App() {
  const [form, setForm] = useState<FormData>(initialForm);
  const [result, setResult] = useState<ValuationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [addInventoryLoading, setAddInventoryLoading] = useState(false);
  const [inventorySaveMessage, setInventorySaveMessage] = useState('');
  const [error, setError] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [activeFeature, setActiveFeature] = useState<FeatureId>('dashboard');

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.currentTarget;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      };

      if (authToken) {
        headers.Authorization = `Bearer ${authToken}`;
      }

      const response = await fetch('/api/vehicle-valuation', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          ageYears: Number(form.ageYears),
          arf: Number(form.arf),
          coe: Number(form.coe),
          registrationDate: form.registrationDate
        })
      });

      const data: ValuationResult = await response.json();
      if (!response.ok) {
        throw new Error('detail' in data ? (data as any).detail : 'Failed to calculate valuation');
      }
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleAddToInventory = async () => {
    if (!result || !authToken) return;
    setAddInventoryLoading(true);
    setError('');
    setInventorySaveMessage('');

    try {
      const response = await fetch('/api/inventory/add', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          vin: '',
          licensePlate: form.licensePlate,
          make: form.make,
          model: form.model,
          year: Number(form.year),
          mileage: Number(form.mileage),
          arf: Number(form.arf),
          coe: Number(form.coe),
          currentCoe: Number(form.coe),
          registrationDate: form.registrationDate,
          agreedPurchaseCost: Number(form.agreedPurchaseCost),
          estimatedMarketValue: result.estimatedMarketPrice,
          recommendedIntakePrice: result.recommendedIntakePrice,
          targetSellingPrice: result.recommendedIntakePrice,
          depreciationRate: result.depreciationValue / (Number(form.arf || 0) + Number(form.coe || 1)),
          dateAcquired: new Date().toISOString().split('T')[0],
          vehicleType: form.vehicleType,
          seatCount: Number(form.seatCount),
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error('detail' in data ? (data as any).detail : 'Failed to add vehicle to inventory');
      }

      setInventorySaveMessage('Vehicle added to inventory successfully.');
      setForm((prev) => ({ ...prev, agreedPurchaseCost: '' }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setAddInventoryLoading(false);
    }
  };

  const handleLogin = (token: string, username: string, role: string) => {
    setAuthToken(token);
    setProfile({ username, role });
    setIsAuthenticated(true);
    setError('');
  };

  const handleLogout = () => {
    setAuthToken(null);
    setProfile(null);
    setIsAuthenticated(false);
    setResult(null);
    setForm(initialForm);
    setError('');
    setIsProfileOpen(false);
    setActiveFeature('dashboard');
  };

  const features = [
    {
      id: 'valuation' as const,
      title: '1) VEHICLE VALUATION CALCULATOR',
      description: 'Use the existing valuation tool for ARF, COE, depreciation, and PARF estimates.',
      roles: ['admin', 'dealer', 'frontline staff'],
    },
    {
      id: 'inventory' as const,
      title: '2) INVENTORY DASHBOARD',
      description: 'View stock levels, inventory status, and vehicle pipeline summaries.',
      roles: ['admin', 'dealer', 'inventory manager', 'frontline staff'],
    },
    {
      id: 'simulation' as const,
      title: '3) SCENARIO SIMULATION TOOL',
      description: 'Build and compare vehicle trade-in scenarios for margin planning.',
      roles: ['admin', 'dealer'],
    },
    {
      id: 'members' as const,
      title: '4) EDIT MEMBERS',
      description: 'Manage salesperson and dealer access for the application.',
      roles: ['admin', 'dealer'],
    },
  ];

  const canAccessFeature = (featureId: FeatureId) => {
    if (!profile) return false;
    const feature = features.find((item) => item.id === featureId);
    return feature ? feature.roles.includes(profile.role) : false;
  };

  const openFeature = (featureId: FeatureId) => {
    if (canAccessFeature(featureId)) {
      setActiveFeature(featureId);
      setError('');
      setResult(null);
    }
  };

  const getProfileDescription = (role: string) => {
    const mapping: Record<string, string> = {
      'frontline staff': 'Supports customer-facing operations.',
      'inventory manager': 'Manages stock and inventory planning.',
      'dealer': 'Dealer.',
      'admin': 'Admin.',
    };
    return mapping[role] ?? 'View and manage your account details.';
  };

  return (
    <div className="app-shell">
      {!isAuthenticated ? (
        <main>
          <Login onLogin={handleLogin} />
        </main>
      ) : (
        <>
          <header>
            <div className="header-row">
              <div>
                <h1>DealerKaki</h1>
              </div>
              <div className="header-actions">
                <button
                  type="button"
                  className="profile-button"
                  onClick={() => setIsProfileOpen((open) => !open)}
                >
                  {profile?.username.charAt(0).toUpperCase() || 'U'}
                </button>
                <button type="button" className="logout-button" onClick={handleLogout}>
                  Logout
                </button>
              </div>
            </div>
          </header>

          {profile && (
            <aside className={`profile-panel ${isProfileOpen ? 'open' : ''}`}>
              <div className="profile-panel-header">
                <h3>Profile</h3>
                <button type="button" className="close-profile-button" onClick={() => setIsProfileOpen(false)}>
                  ×
                </button>
              </div>
              <div className="profile-summary">
                <div className="profile-icon-large">{profile.username.charAt(0).toUpperCase()}</div>
                <div>
                  <p className="profile-name">{profile.username}</p>
                  <p className="profile-role">{profile.role}</p>
                </div>
              </div>
              <p className="profile-description">{getProfileDescription(profile.role)}</p>
            </aside>
          )}

          <main>
            {activeFeature === 'dashboard' ? (
              <section className="dashboard-card">
                <div className="dashboard-header">
                  <div>
                    <h2>Welcome, {profile?.username}</h2>
                  </div>
                </div>
                <div className="dashboard-grid">
                  {features.map((feature) => {
                    const allowed = canAccessFeature(feature.id);
                    return (
                      <button
                        key={feature.id}
                        type="button"
                        className={`feature-card ${allowed ? '' : 'disabled'}`}
                        disabled={!allowed}
                        onClick={() => openFeature(feature.id)}
                      >
                        <div className="feature-card-title">{feature.title}</div>
                        {!allowed && <span className="feature-card-badge">No access</span>}
                      </button>
                    );
                  })}
                </div>
              </section>
            ) : (
              <section className="feature-page">
                <button type="button" className="secondary-button" onClick={() => setActiveFeature('dashboard')}>
                  ← Back to dashboard
                </button>
                {activeFeature === 'valuation' && (
                  <>
                    <section className="form-card">
                      <h2>Vehicle Details</h2>
                      <form onSubmit={handleSubmit}>
                        <label>
                          Vehicle Age (years)
                          <input
                            type="number"
                            name="ageYears"
                            min="0"
                            step="0.1"
                            placeholder="Enter vehicle age"
                            value={form.ageYears}
                            onChange={handleChange}
                          />
                        </label>

                        <label>
                          Make
                          <input
                            type="text"
                            name="make"
                            placeholder="Vehicle make"
                            value={form.make}
                            onChange={handleChange}
                          />
                        </label>

                        <label>
                          Model
                          <input
                            type="text"
                            name="model"
                            placeholder="Vehicle model"
                            value={form.model}
                            onChange={handleChange}
                          />
                        </label>

                        <label>
                          License Plate
                          <input
                            type="text"
                            name="licensePlate"
                            placeholder="License plate"
                            value={form.licensePlate}
                            onChange={handleChange}
                          />
                        </label>

                        <label>
                          Mileage (km)
                          <input
                            type="number"
                            name="mileage"
                            min="0"
                            step="100"
                            placeholder="Enter mileage"
                            value={form.mileage}
                            onChange={handleChange}
                          />
                        </label>

                        <label>
                          Year
                          <input
                            type="number"
                            name="year"
                            min="1900"
                            max="2099"
                            step="1"
                            placeholder="Year of vehicle"
                            value={form.year}
                            onChange={handleChange}
                          />
                        </label>

                        <label>
                          Vehicle Type
                          <input
                            type="text"
                            name="vehicleType"
                            placeholder="Sedan, SUV, MPV"
                            value={form.vehicleType}
                            onChange={handleChange}
                          />
                        </label>

                        <label>
                          Seats
                          <input
                            type="number"
                            name="seatCount"
                            min="1"
                            step="1"
                            placeholder="Number of seats"
                            value={form.seatCount}
                            onChange={handleChange}
                          />
                        </label>

                        <label>
                          ARF ($)
                          <input
                            type="number"
                            name="arf"
                            min="0"
                            step="100"
                            placeholder="Enter ARF amount"
                            value={form.arf}
                            onChange={handleChange}
                          />
                        </label>

                        <label>
                          COE ($)
                          <input
                            type="number"
                            name="coe"
                            min="0"
                            step="100"
                            placeholder="Enter COE amount"
                            value={form.coe}
                            onChange={handleChange}
                          />
                        </label>
                        <label>
                          Registration Date
                          <input
                            type="date"
                            name="registrationDate"
                            value={form.registrationDate}
                            onChange={handleChange}
                            required
                          />
                        </label>
                        <button type="submit" disabled={loading}>
                          {loading ? 'Calculating...' : 'Calculate Valuation'}
                        </button>
                      </form>
                    </section>

                    {error && (
                      <section className="error-card">
                        <h3>Error</h3>
                        <p>{error}</p>
                      </section>
                    )}

                    {result && (
                      <>
                        <section className="result-card">
                          <h2>Valuation Results</h2>
                          <div className="result-info">
                            <p><strong>PARF Scheme:</strong> {result.parfScheme}</p>
                            <p><strong>PARF Cap:</strong> S${result.parfCap.toLocaleString()}</p>
                          </div>
                          <div className="result-grid">
                          <div className="result-item">
                            <label>Estimated PARF Rebate</label>
                            <p className="result-value">S${result.estimatedParfRebate.toLocaleString()}</p>
                          </div>

                          <div className="result-item">
                            <label>Depreciation Value</label>
                            <p className="result-value">S${result.depreciationValue.toLocaleString()}</p>
                          </div>

                          <div className="result-item">
                            <label>Estimated Market Price</label>
                            <p className="result-value">S${result.estimatedMarketPrice.toLocaleString()}</p>
                          </div>

                          <div className="result-item">
                            <label>Recommended Intake Price</label>
                            <p className="result-value">S${result.recommendedIntakePrice.toLocaleString()}</p>
                          </div>
                        </div>
                      </section>

                      <section className="result-card">
                        <h2>Add to Inventory</h2>
                        <div className="result-info">
                          <p><strong>Estimated Market Value:</strong> S${result.estimatedMarketPrice.toLocaleString()}</p>
                          <p><strong>Recommended Selling Price:</strong> S${result.recommendedIntakePrice.toLocaleString()}</p>
                        </div>
                        <div className="inventory-entry-form">
                          <label>
                            Agreed Purchase / Trade-in Cost
                            <input
                              type="number"
                              name="agreedPurchaseCost"
                              min="0"
                              step="100"
                              placeholder="Enter agreed cost"
                              value={form.agreedPurchaseCost}
                              onChange={handleChange}
                            />
                          </label>
                          <button
                            type="button"
                            className="primary-button"
                            onClick={handleAddToInventory}
                            disabled={addInventoryLoading || !form.agreedPurchaseCost}
                          >
                            {addInventoryLoading ? 'Adding...' : 'Add To Inventory'}
                          </button>
                        </div>
                        {inventorySaveMessage && <p className="success-message">{inventorySaveMessage}</p>}
                      </section>
                    </>
                    )}
                  </>
                )}

                {activeFeature === 'simulation' && (
                  <ScenarioSimulation authToken={authToken} />
                )}

                {activeFeature === 'inventory' && (
                  <InventoryDashboard />
                )}

                {activeFeature === 'members' && (
                  <MembersEditor authToken={authToken} />
                )}
              </section>
            )}
          </main>
        </>
      )}
    </div>
  );
}

export default App;
