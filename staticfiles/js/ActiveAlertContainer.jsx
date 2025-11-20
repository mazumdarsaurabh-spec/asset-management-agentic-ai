import React, { useState, useContext, createContext, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { AlertTriangle, TrendingUp, Calendar, Zap, X } from 'lucide-react';

// --- Data Structure and Context ---

// Define the structure for a Forecast/Planning alert item
// The type determines the icon and styling (e.g., 'forecast', 'critical', 'schedule')
const AlertContext = createContext();

export const useAlert = () => {
  return useContext(AlertContext);
};

const AlertProvider = ({ children }) => {
  const [alerts, setAlerts] = useState([
    { id: 'initial-1', title: 'Forecast & Planning', detail: 'No forecasts yet', type: 'forecast', time: 'N/A' }
  ]);
  
  const generateId = () => Date.now().toString();

  const addAlert = useCallback((title, detail, type) => {
    const id = generateId();
    const time = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    const newAlert = { id, title, detail, type, time };

    setAlerts((prevAlerts) => {
      // If the default "No forecasts yet" is present, remove it when the first real alert comes in
      if (prevAlerts.length === 1 && prevAlerts[0].id === 'initial-1') {
        return [newAlert];
      }
      return [newAlert, ...prevAlerts];
    });

  }, []);

  const dismissAlert = useCallback((id) => {
    setAlerts((prevAlerts) => prevAlerts.filter(alert => alert.id !== id));
    // If the list becomes empty, restore the default 'No forecasts yet' item
    if (alerts.length === 1 && id !== 'initial-1') {
      setAlerts([{ id: 'initial-1', title: 'Forecast & Planning', detail: 'No forecasts yet', type: 'forecast', time: 'N/A' }]);
    }
  }, [alerts.length]);

  return (
    <AlertContext.Provider value={{ alerts, addAlert, dismissAlert }}>
      {children}
      <AlertPanel alerts={alerts} dismissAlert={dismissAlert} />
    </AlertContext.Provider>
  );
};

// --- Alert Item Renderer ---

const ForecastItem = ({ alert, dismissAlert }) => {
  const { id, title, detail, type, time } = alert;

  const typeConfig = {
    forecast: {
      Icon: TrendingUp,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
    critical: {
      Icon: Zap,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
    },
    schedule: {
      Icon: Calendar,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
  };

  const { Icon, color, bgColor } = typeConfig[type] || typeConfig.forecast;

  const isPlaceholder = id === 'initial-1';

  return (
    <div className={`p-4 border-b border-gray-100 last:border-b-0 transition-all ${isPlaceholder ? 'opacity-70' : 'hover:bg-gray-50'}`}>
      <div className="flex items-start space-x-3">
        <div className={`p-2 rounded-full ${bgColor} ${color} flex-shrink-0`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-grow min-w-0">
          <h3 className="font-semibold text-gray-800 flex justify-between items-center">
            <span className="truncate">{title}</span>
            {!isPlaceholder && (
              <span className="text-xs font-normal text-gray-400 ml-2">{time}</span>
            )}
          </h3>
          <p className={`text-sm mt-0.5 ${isPlaceholder ? 'text-gray-500 italic' : 'text-gray-600'}`}>
            {detail}
          </p>
        </div>
        {!isPlaceholder && (
          <button
            onClick={() => dismissAlert(id)}
            className="text-gray-400 hover:text-red-500 transition-colors p-1 rounded-full flex-shrink-0"
            aria-label={`Dismiss alert: ${title}`}
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

// --- Main Alert Panel Component ---

const AlertPanel = ({ alerts, dismissAlert }) => {
  if (typeof document === 'undefined') return null;

  const activeAlertCount = alerts.filter(a => a.id !== 'initial-1').length;
  
  return createPortal(
    <div
      className="
        fixed bottom-4 right-4 md:bottom-8 md:right-8 w-full max-w-sm
        shadow-2xl rounded-2xl overflow-hidden pointer-events-none
        transform transition-transform duration-300
        z-[1000]
      "
    >
      <div className="bg-white rounded-2xl pointer-events-auto">
        
        {/* Header matching the user's image with gradient and count */}
        <div 
          className="p-4 flex items-center justify-between text-white rounded-t-2xl"
          style={{ background: 'linear-gradient(90deg, #ff4e50 0%, #fc913a 100%)' }}
        >
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5" />
            <h2 className="text-lg font-bold">Active Alerts</h2>
          </div>
          <span className="px-3 py-1 bg-white/30 rounded-full text-sm font-semibold">
            {activeAlertCount}
          </span>
        </div>

        {/* Alerts List Body */}
        <div className="max-h-80 overflow-y-auto bg-white">
          {alerts.map(alert => (
            <ForecastItem key={alert.id} alert={alert} dismissAlert={dismissAlert} />
          ))}
        </div>
        
        {/* Footer for mobile visibility */}
        <div className="p-2 text-center text-xs text-gray-400 border-t border-gray-100">
          Showing {activeAlertCount} active alerts.
        </div>
      </div>
    </div>,
    document.body
  );
};

// --- Demo UI Component ---

const AlertTriggerUI = () => {
  const { addAlert } = useAlert();
  const [title, setTitle] = useState('Critical System Alert');
  const [detail, setDetail] = useState('High latency detected in Database replica.');
  const [type, setType] = useState('critical');

  const handleAddAlert = () => {
    addAlert(title, detail, type);
    // Optionally reset fields or provide feedback
  };

  return (
    <div className="p-8 space-y-6 max-w-xl mx-auto bg-white rounded-2xl shadow-xl border border-gray-200">
      <h1 className="text-3xl font-extrabold text-gray-800">
        Forecast & Planning Panel Simulator
      </h1>
      <p className="text-gray-600">
        Use this form to push new "live" alerts into the custom panel on the bottom-right.
        The initial "No forecasts yet" item will disappear when you add the first one.
      </p>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Alert Type</label>
          <select 
            value={type} 
            onChange={(e) => setType(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="forecast">Forecast & Planning</option>
            <option value="critical">Critical</option>
            <option value="schedule">Schedule Update</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
          <input 
            type="text"
            value={title} 
            onChange={(e) => setTitle(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., Q3 Revenue Projection"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Detail / Message</label>
          <textarea 
            value={detail} 
            onChange={(e) => setDetail(e.target.value)}
            rows="2"
            className="w-full p-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., Expect 5% variance due to market changes."
          />
        </div>

        <button
          onClick={handleAddAlert}
          disabled={!title || !detail}
          className="w-full py-3 bg-indigo-600 text-white font-semibold rounded-lg shadow-md hover:bg-indigo-700 transition duration-150 transform disabled:opacity-50"
        >
          Push New Live Alert
        </button>
      </div>
    </div>
  );
};

// --- Root Component ---
const App = () => (
  <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4 font-sans">
    <AlertProvider>
      <AlertTriggerUI />
    </AlertProvider>
  </div>
);

export default App;