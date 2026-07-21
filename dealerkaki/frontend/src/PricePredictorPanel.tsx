import { useState } from 'react';

interface Props {
  authToken: string | null;
}

interface PredictionForm {
  brand: string;
  name: string;
  registrationDate: string;
  mileage: string;
  owners: string;
  depreciation: string;
}

function PricePredictorPanel({ authToken }: Props) {
  const [form, setForm] = useState<PredictionForm>({
    brand: '',
    name: '',
    registrationDate: '',
    mileage: '',
    owners: '',
    depreciation: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [prediction, setPrediction] = useState<number | null>(null);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    setPrediction(null);

    try {
      const response = await fetch('/api/predict-price', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        },
        body: JSON.stringify({
          brand: form.brand,
          name: form.name,
          registration_date: form.registrationDate,
          mileage: Number(form.mileage),
          owners: Number(form.owners),
          depreciation: Number(form.depreciation),
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error('detail' in data ? data.detail : 'Failed to predict price');
      }

      setPrediction(data.predicted_price);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <label>
          Brand
          <input type="text" name="brand" value={form.brand} onChange={handleChange} required />
        </label>
        <label>
          Model
          <input type="text" name="name" value={form.name} onChange={handleChange} required />
        </label>
        <label>
          Registration Date
          <input type="date" name="registrationDate" value={form.registrationDate} onChange={handleChange} required />
        </label>
        <label>
          Mileage (km)
          <input type="number" name="mileage" min="0" step="100" value={form.mileage} onChange={handleChange} required />
        </label>
        <label>
          Number of Owners
          <input type="number" name="owners" min="0" step="1" value={form.owners} onChange={handleChange} required />
        </label>
        <label>
          Depreciation
          <input type="number" name="depreciation" min="0" step="100" value={form.depreciation} onChange={handleChange} required />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? 'Predicting...' : 'Predict Price'}
        </button>
      </form>

      {error && <p className="error-message">{error}</p>}
      {prediction !== null && (
        <div className="result-card">
          <h3>Predicted Selling Price</h3>
          <p className="result-value">S${prediction.toLocaleString(undefined, { maximumFractionDigits: 2 })}</p>
        </div>
      )}
    </div>
  );
}

export default PricePredictorPanel;
