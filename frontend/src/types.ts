export type Units = "metric" | "imperial" | "standard";

export interface GeocodeItem {
  name: string;
  lat: number;
  lon: number;
  country?: string | null;
  state?: string | null;
}

export interface WeatherMain {
  temp: number;
  feels_like: number;
  humidity: number;
  pressure: number;
}

export interface WeatherCondition {
  main: string;
  description: string;
  icon: string;
}

export interface CurrentWeatherResponse {
  city: string;
  country?: string | null;
  lat: number;
  lon: number;
  main: WeatherMain;
  weather: WeatherCondition[];
  wind_speed?: number | null;
  timestamp: number;
}

export interface ForecastItem {
  timestamp: number;
  temp: number;
  feels_like: number;
  humidity: number;
  weather_main: string;
  weather_description: string;
  icon: string;
  wind_speed?: number | null;
}

export interface ForecastResponse {
  city: string;
  country?: string | null;
  lat: number;
  lon: number;
  items: ForecastItem[];
}

export interface ParsedQuery {
  location: string;
  units: Units;
  start_date: string | null;
  end_date: string | null;
  intent: "current" | "forecast" | "both";
  confidence: number;
  notes: string | null;
}

export interface WeatherSearchResponse {
  query: string;
  parsed: ParsedQuery;
  location: GeocodeItem;
  current: CurrentWeatherResponse;
  forecast: ForecastResponse;
  saved_search_id: number;
  saved_search_key: string;
}

export interface WeatherSummary {
  query: string;
  units: Units;
  resolved_city: string;
  country_code: string | null;
  lat: number;
  lon: number;
  current: {
    temp: number;
    feels_like: number;
    humidity: number;
    condition: string | null;
  };
  forecast_count: number;
}

export interface WeatherSnapshot {
  query: string;
  units: Units;
  resolved_city: string | null;
  country_code: string | null;
  lat: number;
  lon: number;
  start_date: string | null;
  end_date: string | null;
  summary: WeatherSummary;
  current: CurrentWeatherResponse;
  forecast: ForecastResponse;
}

export interface WeatherSearchRecord {
  id: number;
  search_key: string;
  location: string;
  resolved_city: string | null;
  country_code: string | null;
  latitude: number | null;
  longitude: number | null;
  start_date: string | null;
  end_date: string | null;
  units: Units;
  notes: string | null;
  weather_data: WeatherSnapshot | null;
  created_at: string;
  updated_at: string;
}

export interface WeatherInsightResponse {
  title: string;
  summary: string;
  recommendations: string[];
  packing_tips: string[];
  risk_level: "low" | "medium" | "high";
  outdoor_score: number;
}

export interface WeatherInsightFromSearchResponse {
  search_id: number;
  search_key: string;
  location: string;
  insight: WeatherInsightResponse;
}

export interface BackendHealthResponse {
  status: string;
}
