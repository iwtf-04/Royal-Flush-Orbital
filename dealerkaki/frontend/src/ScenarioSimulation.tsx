import React, { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface Vehicle {
  id: number;
  make: string;
  model: string;
  year: number;
  purchase_price: number;
  current_market_value: number;
  current_coe: number;
  days_in_inventory: number;
  profit_margin: number;
  vehicle_type: string;
  license_plate: string;
}

interface Props {
  authToken: string | null;
}

function ScenarioSimulation({ authToken }: Props) {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [selectedVehicle, setSelectedVehicle] = useState<Vehicle | null>(null);
  const [coePercent, setCoePercent] = useState<number>(0);
  const [parfPercent, setParfPercent] = useState<number>(0);
  const [depreciationRate, setDepreciationRate] = useState<number>(0.05);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [trendData, setTrendData] = useState<any>(null);

  const generateTrendData = () => {
    if (!selectedVehicle) return;

    const current_value = selectedVehicle.current_market_value;
    const purchase_price = selectedVehicle.purchase_price;

    const coeRange = Array.from({ length: 9 }, (_, i) => i * 5 - 20); // -20, -15, -10, ..., 20
    const prices: number[] = [];

    coeRange.forEach((coePercent) => {
      const coe_multiplier = 1.0 + coePercent / 100.0;
      const parf_multiplier = 1.0 + parfPercent / 100.0;
      const depreciation_loss = current_value * depreciationRate;

      const simulated_value =
        Math.max(0, current_value * coe_multiplier * parf_multiplier - depreciation_loss);
      prices.push(simulated_value);
    });

    setTrendData({
      labels: coeRange.map((p) => `${p}%`),
      datasets: [
        {
          label: 'Simulated Selling Price (S$)',
          data: prices,
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.1)',
          tension: 0.4,
          fill: true,
        },
      ],
    });
  };

  useEffect(() => {
    generateTrendData();
  }, [coePercent, parfPercent, depreciationRate, selectedVehicle]);

  useEffect(() => {
    fetch('/api/inventory')
      .then((res) => res.json())
      .then((data) => {
        setVehicles(data.vehicles || []);
        setLoading(false);
      })
      .catch((err) => {
        setError('Failed to fetch inventory');
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (selectedId !== null) {
      const v = vehicles.find((x) => x.id === selectedId) || null;
      setSelectedVehicle(v);
      setResult(null);
    }
  }, [selectedId, vehicles]);

  const handleSimulate = async () => {
    setError('');
    if (!selectedId) {
      setError('Select a vehicle first');
      return;
    }

    try {
      const response = await fetch(`/api/inventory/${selectedId}/simulate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        },
        body: JSON.stringify({
          coePercent: coePercent,
          parfPercent: parfPercent,
          depreciationRate: depreciationRate,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error('detail' in data ? data.detail : 'Simulation failed');
      }
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Simulation error');
    }
  };

  if (loading) return <div>Loading vehicles...</div>;

  return (
    <div className="simulation-panel">
      <h2>Scenario Simulation Tool</h2>
      {error && <p className="error-message">{error}</p>}

      <label>
        Select Vehicle
        <select value={selectedId ?? ''} onChange={(e) => setSelectedId(e.target.value ? Number(e.target.value) : null)}>
          <option value="">-- Select --</option>
          {vehicles.map((v) => (
            <option key={v.id} value={v.id}>{v.make} {v.model} ({v.license_plate})</option>
          ))}
        </select>
      </label>

      {selectedVehicle && (
        <div className="vehicle-summary">
          <h3>Current Vehicle Information</h3>
          <div className="summary-grid">
            <div><strong>Name</strong><div>{selectedVehicle.make} {selectedVehicle.model}</div></div>
            <div><strong>Year</strong><div>{selectedVehicle.year}</div></div>
            <div><strong>Purchase Price</strong><div>S${selectedVehicle.purchase_price.toLocaleString()}</div></div>
            <div><strong>Current Selling Price</strong><div>S${selectedVehicle.current_market_value.toLocaleString()}</div></div>
            <div><strong>Current COE</strong><div>S${selectedVehicle.current_coe.toLocaleString()}</div></div>
            <div><strong>Days in Inventory</strong><div>{selectedVehicle.days_in_inventory} days</div></div>
            <div><strong>Current Profit Margin</strong><div>{(selectedVehicle.profit_margin * 100).toFixed(1)}%</div></div>
          </div>
        </div>
      )}

      {selectedVehicle && (
        <div className="simulation-inputs">
          <h3>Simulation Inputs</h3>
          <label>
            COE Change (%)
            <input type="range" min={-20} max={20} value={coePercent} onChange={(e) => setCoePercent(Number(e.target.value))} />
            <div>{coePercent}%</div>
          </label>

          <label>
            PARF Rebate Adjustment (%)
            <input type="range" min={-30} max={30} value={parfPercent} onChange={(e) => setParfPercent(Number(e.target.value))} />
            <div>{parfPercent}%</div>
          </label>

          <label>
            Expected Depreciation Rate (%)
            <input type="range" min={0} max={20} value={depreciationRate * 100} onChange={(e) => setDepreciationRate(Number(e.target.value) / 100)} />
            <div>{(depreciationRate * 100).toFixed(1)}%</div>
          </label>

          <button type="button" className="primary-button" onClick={handleSimulate}>Run Simulation</button>
        </div>
      )}

      {result && (
        <div className="simulation-results">
          <h3>Results</h3>
          <div className="results-grid">
            <div>
              <h4>Current</h4>
              <div>Selling price: S${Number(result.current.selling_price).toLocaleString()}</div>
              <div>Profit: S${Number(result.current.profit).toLocaleString()}</div>
              <div>Margin: {result.current.margin}%</div>
            </div>
            <div>
              <h4>Simulated</h4>
              <div>Selling price: S${Number(result.simulated.selling_price).toLocaleString()}</div>
              <div>Profit: S${Number(result.simulated.profit).toLocaleString()}</div>
              <div>Margin: {result.simulated.margin_percent}%</div>
              <div>Risk: {result.simulated.risk_level} (score {result.simulated.risk_score})</div>
              <div>Recommendation: {result.simulated.recommendation}</div>
              <div className="recommendation-reason">{result.simulated.recommendation_reason}</div>
            </div>
          </div>

          {trendData && (
            <div className="simulation-chart">
              <h4>Price Trend: How COE % Changes Affect Selling Price</h4>
              <Line data={trendData} options={{
                responsive: true,
                plugins: {
                  title: { display: false },
                  legend: { display: true },
                },
                scales: {
                  y: {
                    title: { display: true, text: 'Selling Price (S$)' },
                  },
                  x: {
                    title: { display: true, text: 'COE % Change' },
                  },
                },
              }} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ScenarioSimulation;
