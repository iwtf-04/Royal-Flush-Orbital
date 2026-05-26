import { useState } from 'react';
import Login from './Login';

interface FormData {
  ageYears: string;
  arf: string;
  coe: string;
  registrationDate: string;
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

const initialForm: FormData = {
  ageYears: '',
  arf: '',
  coe: '',
  registrationDate: ''
};

function App() {
  const [form, setForm] = useState<FormData>(initialForm);
  const [result, setResult] = useState<ValuationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authToken, setAuthToken] = useState<string | null>(null);

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

  const handleLogin = (token: string) => {
    setAuthToken(token);
    setIsAuthenticated(true);
    setError('');
  };

  const handleLogout = () => {
    setAuthToken(null);
    setIsAuthenticated(false);
    setResult(null);
    setForm(initialForm);
    setError('');
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
                <h1>DealerKaki Valuation Tool</h1>
                <p>Enter trade-in details to compute PARF rebate, depreciation, market price, and intake recommendation.</p>
              </div>
              <button type="button" className="logout-button" onClick={handleLogout}>
                Logout
              </button>
            </div>
          </header>

          <main>
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
            )}
          </main>
        </>
      )}
    </div>
  );
}

export default App;
