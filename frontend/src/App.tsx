import { type FormEvent, useEffect, useMemo, useState } from "react";

import {
  ApiError,
  deleteSearch,
  generateInsightFromSearch,
  getBackendHealth,
  listSearches,
  searchWeather,
  updateSearchNotes,
} from "./api";
import type {
  ForecastItem,
  ParsedQuery,
  WeatherInsightFromSearchResponse,
  WeatherSearchRecord,
  WeatherSnapshot,
  Units,
} from "./types";

const QUICK_QUERIES = [
  "weather in New York",
  "weather in London next weekend",
  "weather in Mumbai today",
  "weather in Tokyo this weekend",
];

function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "—";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function formatDayLabel(timestamp: number): string {
  return new Intl.DateTimeFormat("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  }).format(new Date(timestamp * 1000));
}

function formatTemperature(value: number | null | undefined, units: Units): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }

  const suffix = units === "imperial" ? "°F" : "°C";
  return `${Math.round(value)}${suffix}`;
}

function formatWindSpeed(value: number | null | undefined, units: Units): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }

  const suffix = units === "imperial" ? "mph" : "m/s";
  return `${value.toFixed(1)} ${suffix}`;
}

function weatherIconUrl(icon: string | undefined | null): string | null {
  if (!icon) {
    return null;
  }

  return `https://openweathermap.org/img/wn/${icon}@2x.png`;
}

function summarizeForecast(items: ForecastItem[] | undefined): Array<{
  dayLabel: string;
  icon: string | null;
  condition: string;
  description: string;
  high: number;
  low: number;
  humidity: number;
  windSpeed: number | null;
}> {
  if (!items?.length) {
    return [];
  }

  const grouped = new Map<string, ForecastItem[]>();
  for (const item of items) {
    const dayKey = new Intl.DateTimeFormat("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
    }).format(new Date(item.timestamp * 1000));

    const bucket = grouped.get(dayKey) ?? [];
    bucket.push(item);
    grouped.set(dayKey, bucket);
  }

  return Array.from(grouped.entries())
    .slice(0, 5)
    .map(([dayLabel, bucket]) => {
      const sorted = [...bucket].sort((left, right) => left.timestamp - right.timestamp);
      const representative = sorted[Math.floor(sorted.length / 2)] ?? sorted[0];
      const highs = bucket.map((item) => item.temp);
      const lows = bucket.map((item) => item.temp);
      const humidities = bucket.map((item) => item.humidity);
      const winds = bucket
        .map((item) => item.wind_speed)
        .filter((value): value is number => typeof value === "number");

      return {
        dayLabel,
        icon: representative ? representative.icon : null,
        condition: representative?.weather_main ?? "Unknown",
        description: representative?.weather_description ?? "No description",
        high: highs.length ? Math.max(...highs) : 0,
        low: lows.length ? Math.min(...lows) : 0,
        humidity: humidities.length ? Math.round(humidities.reduce((sum, value) => sum + value, 0) / humidities.length) : 0,
        windSpeed: winds.length ? winds[Math.floor(winds.length / 2)] ?? null : null,
      };
    });
}

function buildMapUrl(record: WeatherSearchRecord | null): string | null {
  if (!record) {
    return null;
  }

  if (typeof record.latitude === "number" && typeof record.longitude === "number") {
    return `https://www.google.com/maps?q=${record.latitude},${record.longitude}&z=10&output=embed`;
  }

  const query = record.resolved_city || record.location;
  if (!query) {
    return null;
  }

  return `https://www.google.com/maps?q=${encodeURIComponent(query)}&z=10&output=embed`;
}

function extractSnapshot(record: WeatherSearchRecord | null): WeatherSnapshot | null {
  if (!record?.weather_data) {
    return null;
  }

  return record.weather_data;
}

function getLocationLabel(record: WeatherSearchRecord | null): string {
  if (!record) {
    return "No search selected";
  }

  return [record.resolved_city ?? record.location, record.country_code].filter(Boolean).join(", ");
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return fallback;
}

function downloadTextFile(fileName: string, content: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  anchor.click();
  URL.revokeObjectURL(url);
}

function buildExportPayload(record: WeatherSearchRecord, insight: WeatherInsightFromSearchResponse | null) {
  return {
    selected_search: record,
    insight,
  };
}

function buildMarkdownExport(record: WeatherSearchRecord, insight: WeatherInsightFromSearchResponse | null): string {
  const snapshot = extractSnapshot(record);
  const lines: string[] = [];

  lines.push(`# Weather Search — ${record.resolved_city ?? record.location}`);
  lines.push("");
  lines.push(`- Search ID: ${record.id}`);
  lines.push(`- Search Key: \`${record.search_key}\``);
  lines.push(`- Query: ${snapshot?.query ?? record.location}`);
  lines.push(`- Units: ${record.units}`);
  lines.push(`- Saved: ${formatDateTime(record.created_at)}`);
  lines.push("");

  if (snapshot?.summary) {
    lines.push("## Summary");
    lines.push("");
    lines.push(`- Current Temp: ${snapshot.summary.current.temp}`);
    lines.push(`- Feels Like: ${snapshot.summary.current.feels_like}`);
    lines.push(`- Humidity: ${snapshot.summary.current.humidity}%`);
    lines.push(`- Condition: ${snapshot.summary.current.condition ?? "Unknown"}`);
    lines.push(`- Forecast Items: ${snapshot.summary.forecast_count}`);
    lines.push("");
  }

  if (insight) {
    lines.push("## AI Insight");
    lines.push("");
    lines.push(`### ${insight.insight.title}`);
    lines.push("");
    lines.push(insight.insight.summary);
    lines.push("");
    lines.push("#### Recommendations");
    for (const item of insight.insight.recommendations) {
      lines.push(`- ${item}`);
    }
    lines.push("");
  }

  if (snapshot?.forecast.items?.length) {
    lines.push("## Forecast Preview");
    lines.push("");
    lines.push("| Day | Temp | Feels Like | Humidity | Condition |");
    lines.push("| --- | --- | --- | --- | --- |");
    for (const item of summarizeForecast(snapshot.forecast.items)) {
      lines.push(
        `| ${item.dayLabel} | ${formatTemperature(item.high, record.units)} | ${formatTemperature(item.low, record.units)} | ${item.humidity}% | ${item.condition} |`,
      );
    }
  }

  return lines.join("\n");
}

function buildCsvExport(record: WeatherSearchRecord): string {
  const snapshot = extractSnapshot(record);
  const rows = [
    ["field", "value"],
    ["search_id", String(record.id)],
    ["search_key", record.search_key],
    ["query", snapshot?.query ?? record.location],
    ["resolved_city", record.resolved_city ?? ""],
    ["country_code", record.country_code ?? ""],
    ["latitude", record.latitude?.toString() ?? ""],
    ["longitude", record.longitude?.toString() ?? ""],
    ["units", record.units],
    ["saved_at", record.created_at],
    ["current_temp", snapshot?.summary.current.temp?.toString() ?? ""],
    ["current_feels_like", snapshot?.summary.current.feels_like?.toString() ?? ""],
    ["humidity", snapshot?.summary.current.humidity?.toString() ?? ""],
    ["condition", snapshot?.summary.current.condition ?? ""],
    ["forecast_count", snapshot?.summary.forecast_count?.toString() ?? ""],
  ];

  return rows
    .map(([field, value]) =>
      [field, value]
        .map((cell) => `"${String(cell).replaceAll('"', '""')}"`)
        .join(","),
    )
    .join("\n");
}

function buildJsonExport(record: WeatherSearchRecord, insight: WeatherInsightFromSearchResponse | null): string {
  return JSON.stringify(buildExportPayload(record, insight), null, 2);
}

function LocationBadge({ children }: { children: string }) {
  return <span className="chip chip-location">{children}</span>;
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span className="metric-label">{label}</span>
      <span className="metric-value">{value}</span>
    </div>
  );
}

function App() {
  const [query, setQuery] = useState("");
  const [latestParse, setLatestParse] = useState<ParsedQuery | null>(null);
  const [history, setHistory] = useState<WeatherSearchRecord[]>([]);
  const [selectedSearch, setSelectedSearch] = useState<WeatherSearchRecord | null>(null);
  const [insight, setInsight] = useState<WeatherInsightFromSearchResponse | null>(null);
  const [notesDraft, setNotesDraft] = useState("");
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [searching, setSearching] = useState(false);
  const [insightLoading, setInsightLoading] = useState(false);
  const [savingNotes, setSavingNotes] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [statusMessage, setStatusMessage] = useState(
    "Search a city or natural-language weather query to populate the terminal.",
  );
  const [error, setError] = useState<string | null>(null);

  const snapshot = extractSnapshot(selectedSearch);
  const forecastCards = useMemo(() => summarizeForecast(snapshot?.forecast.items), [snapshot]);
  const mapUrl = useMemo(() => buildMapUrl(selectedSearch), [selectedSearch]);

  useEffect(() => {
    document.title = "WITHER";
    void bootstrap();
  }, []);

  useEffect(() => {
    setNotesDraft(selectedSearch?.notes ?? "");
  }, [selectedSearch?.id, selectedSearch?.notes]);

  async function bootstrap(): Promise<void> {
    setLoadingHistory(true);
    try {
      const [healthResult, historyResult] = await Promise.allSettled([getBackendHealth(), listSearches()]);

      if (healthResult.status === "fulfilled") {
        setBackendHealthy(healthResult.value.status === "ok");
      } else {
        setBackendHealthy(false);
      }

      if (historyResult.status === "fulfilled") {
        const records = historyResult.value;
        setHistory(records);
        const initialSelection = records[0] ?? null;
        setSelectedSearch(initialSelection);
        setInsight(null);
        setNotesDraft(initialSelection?.notes ?? "");
        if (initialSelection) {
          setStatusMessage(`Loaded ${records.length} saved weather searches.`);
        } else {
          setStatusMessage("No saved searches yet. Run your first weather query.");
        }
      } else {
        setHistory([]);
        setSelectedSearch(null);
        setInsight(null);
        setStatusMessage("Backend connected, but no search history could be loaded.");
        setError(getErrorMessage(historyResult.reason, "Unable to load search history."));
      }
    } finally {
      setLoadingHistory(false);
    }
  }

  async function reloadHistory(preferredId?: number | null): Promise<WeatherSearchRecord | null> {
    const records = await listSearches();
    setHistory(records);
    const preferredRecord = preferredId == null ? null : records.find((item) => item.id === preferredId) ?? null;
    const nextSelection = preferredRecord ?? records[0] ?? null;
    setSelectedSearch(nextSelection);
    setInsight(null);
    setNotesDraft(nextSelection?.notes ?? "");
    return nextSelection;
  }

  async function runSearch(nextQuery: string): Promise<void> {
    const trimmedQuery = nextQuery.trim();
    if (!trimmedQuery) {
      setError("Type a city or weather query first.");
      return;
    }

    setSearching(true);
    setError(null);
    setInsight(null);
    setStatusMessage(`Searching ${trimmedQuery} and saving the result...`);

    try {
      const result = await searchWeather(trimmedQuery);
      setLatestParse(result.parsed);
      await reloadHistory(result.saved_search_id);
      setStatusMessage(
        `Saved #${result.saved_search_id} for ${result.parsed.location} with ${result.parsed.intent} mode.`,
      );
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Could not load weather for that location."));
      setStatusMessage("Weather request failed.");
    } finally {
      setSearching(false);
    }
  }

  async function onSearchSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    await runSearch(query);
  }

  async function onQuickSearch(text: string): Promise<void> {
    setQuery(text);
    await runSearch(text);
  }

  async function onCurrentLocation(): Promise<void> {
    setError(null);

    if (!navigator.geolocation) {
      setError("Geolocation is not available in this browser.");
      return;
    }

    setSearching(true);
    setStatusMessage("Resolving your current location...");

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const label = await reverseGeocode(position.coords.latitude, position.coords.longitude);
          setQuery(label);
          await runSearch(label);
        } catch (currentLocationError) {
          setError(getErrorMessage(currentLocationError, "Could not resolve your current location."));
          setStatusMessage("Current location lookup failed.");
          setSearching(false);
        }
      },
      (geoError) => {
        setError(geoError.message || "Unable to access your location.");
        setStatusMessage("Current location lookup failed.");
        setSearching(false);
      },
      {
        enableHighAccuracy: false,
        timeout: 10000,
        maximumAge: 30000,
      },
    );
  }

  async function reverseGeocode(latitude: number, longitude: number): Promise<string> {
    const url = new URL("https://api.bigdatacloud.net/data/reverse-geocode-client");
    url.searchParams.set("latitude", String(latitude));
    url.searchParams.set("longitude", String(longitude));
    url.searchParams.set("localityLanguage", "en");

    const response = await fetch(url.toString());
    if (!response.ok) {
      throw new Error("Reverse geocoding failed.");
    }

    const data = (await response.json()) as {
      city?: string | null;
      locality?: string | null;
      principalSubdivision?: string | null;
      countryName?: string | null;
    };

    const label = [data.city, data.locality, data.principalSubdivision, data.countryName]
      .filter((value): value is string => Boolean(value && value.trim()))
      .join(", ");

    if (!label) {
      throw new Error("Could not resolve a city name from your location.");
    }

    return label;
  }

  async function onGenerateInsight(record: WeatherSearchRecord | null = selectedSearch): Promise<void> {
    if (!record) {
      setError("Run a search first or pick a saved search from history.");
      return;
    }

    setInsightLoading(true);
    setError(null);
    setStatusMessage(`Generating insight for ${record.resolved_city ?? record.location}...`);

    try {
      const response = await generateInsightFromSearch(record.id);
      setInsight(response);
      setStatusMessage(`Insight ready for ${response.location}.`);
    } catch (insightError) {
      setError(getErrorMessage(insightError, "Could not generate insight for that search."));
      setStatusMessage("AI insight failed.");
    } finally {
      setInsightLoading(false);
    }
  }

  async function onSaveNotes(): Promise<void> {
    if (!selectedSearch) {
      setError("Pick a saved search before saving notes.");
      return;
    }

    setSavingNotes(true);
    setError(null);

    try {
      const updated = await updateSearchNotes(
        selectedSearch.id,
        notesDraft.trim().length > 0 ? notesDraft.trim() : null,
      );
      setSelectedSearch(updated);
      setHistory((items) => items.map((item) => (item.id === updated.id ? updated : item)));
      setStatusMessage(`Notes updated for ${updated.resolved_city ?? updated.location}.`);
    } catch (notesError) {
      setError(getErrorMessage(notesError, "Could not save notes."));
      setStatusMessage("Saving notes failed.");
    } finally {
      setSavingNotes(false);
    }
  }

  async function onDeleteSearch(searchId: number): Promise<void> {
    const isConfirmed = window.confirm("Delete this saved search?");
    if (!isConfirmed) {
      return;
    }

    setDeletingId(searchId);
    setError(null);

    const previousSelectedId = selectedSearch?.id ?? null;

    try {
      await deleteSearch(searchId);
      await reloadHistory(previousSelectedId === searchId ? null : previousSelectedId);
      setStatusMessage(`Deleted search #${searchId}.`);
    } catch (deleteError) {
      setError(getErrorMessage(deleteError, "Could not delete the selected search."));
      setStatusMessage("Delete failed.");
    } finally {
      setDeletingId(null);
    }
  }

  function onSelectSearch(record: WeatherSearchRecord): void {
    setSelectedSearch(record);
    setInsight(null);
    setError(null);
    setStatusMessage(`Viewing ${record.resolved_city ?? record.location}.`);
  }

  function downloadJson(): void {
    if (!selectedSearch) {
      setError("Pick a search before exporting.");
      return;
    }

    downloadTextFile(
      `${slugify(selectedSearch.resolved_city ?? selectedSearch.location)}.json`,
      buildJsonExport(selectedSearch, insight),
      "application/json",
    );
  }

  function downloadCsv(): void {
    if (!selectedSearch) {
      setError("Pick a search before exporting.");
      return;
    }

    downloadTextFile(
      `${slugify(selectedSearch.resolved_city ?? selectedSearch.location)}.csv`,
      buildCsvExport(selectedSearch),
      "text/csv",
    );
  }

  function downloadMarkdown(): void {
    if (!selectedSearch) {
      setError("Pick a search before exporting.");
      return;
    }

    downloadTextFile(
      `${slugify(selectedSearch.resolved_city ?? selectedSearch.location)}.md`,
      buildMarkdownExport(selectedSearch, insight),
      "text/markdown",
    );
  }

  const currentWeather = snapshot?.current ?? null;
  const currentCondition = currentWeather?.weather?.[0] ?? null;
  const summary = snapshot?.summary ?? null;
  const selectedForecast = forecastCards;

  return (
    <div className="app-shell">
      <header className="hero panel">
        <div className="hero-copy">
          <div className="eyebrow-row">
            <span className="eyebrow">WITHER</span>
            <span className={`status-pill ${backendHealthy ? "status-ok" : backendHealthy === false ? "status-bad" : "status-warn"}`}>
              {backendHealthy === null ? "Checking backend" : backendHealthy ? "Backend online" : "Backend offline"}
            </span>
            <span className="status-pill status-live">LIVE</span>
          </div>
          <h1>Bloomberg-style weather intelligence for city-first searches.</h1>
          <p className="hero-subtitle">
            Search a city, persist the result, and generate AI insight on demand. The terminal keeps the weather signal
            clean, fast, and easy to scan.
          </p>
        </div>

        <div className="hero-stats">
          <div className="metric-card">
            <span className="metric-label">Saved searches</span>
            <strong className="metric-large">{history.length}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Selected city</span>
            <strong className="metric-large">{selectedSearch ? (selectedSearch.resolved_city ?? selectedSearch.location) : "None"}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Status</span>
            <strong className="metric-large">{statusMessage}</strong>
          </div>
        </div>
      </header>

      <section className="panel search-panel">
        <form className="search-form" onSubmit={onSearchSubmit}>
          <div className="search-input-wrap">
            <label className="section-label" htmlFor="weather-query">
              Search
            </label>
            <input
              id="weather-query"
              className="search-input"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder='Try "weather in Paris next weekend" or "Mumbai this weekend"'
              maxLength={120}
              autoComplete="off"
              spellCheck={false}
            />
          </div>

          <div className="search-actions">
            <button className="btn btn-primary" type="submit" disabled={searching}>
              {searching ? "Searching..." : "Search weather"}
            </button>
            <button className="btn btn-secondary" type="button" onClick={() => void onCurrentLocation()} disabled={searching}>
              Use my location
            </button>
          </div>
        </form>

        <div className="quick-queries">
          {QUICK_QUERIES.map((item) => (
            <button key={item} type="button" className="chip" onClick={() => void onQuickSearch(item)}>
              {item}
            </button>
          ))}
        </div>

        <div className="search-meta">
          <div className="meta-group">
            <span className="section-label">Backend base</span>
            <span className="mono">{import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1"}</span>
          </div>
          <div className="meta-group">
            <span className="section-label">Parsed query</span>
            <span className="mono">
              {latestParse ? `${latestParse.location} · ${latestParse.intent} · ${(latestParse.confidence * 100).toFixed(0)}%` : "Waiting for a search"}
            </span>
          </div>
        </div>
      </section>

      {error ? (
        <section className="panel error-panel">
          <span className="error-title">Request failed</span>
          <p>{error}</p>
        </section>
      ) : null}

      <main className="dashboard">
        <section className="main-column">
          <section className="panel weather-panel">
            <div className="panel-heading">
              <div>
                <span className="section-label">Current weather</span>
                <h2>{selectedSearch ? getLocationLabel(selectedSearch) : "No location selected"}</h2>
              </div>
              <div className="panel-actions">
                <button className="btn btn-secondary" type="button" onClick={() => void onGenerateInsight()} disabled={!selectedSearch || insightLoading}>
                  {insightLoading ? "Generating..." : "Generate insight"}
                </button>
              </div>
            </div>

            {selectedSearch && currentWeather ? (
              <>
                <div className="weather-hero">
                  <div className="weather-temp">
                    <img
                      src={weatherIconUrl(currentCondition?.icon) ?? ""}
                      alt={currentCondition?.description ?? "Weather icon"}
                      className="weather-icon"
                    />
                    <div>
                      <div className="temp-value">{formatTemperature(currentWeather.main.temp, selectedSearch.units)}</div>
                      <div className="temp-feels">
                        Feels like {formatTemperature(currentWeather.main.feels_like, selectedSearch.units)} ·{" "}
                        {currentCondition?.description ?? "No description"}
                      </div>
                    </div>
                  </div>

                  <div className="weather-hero-metrics">
                    <Metric label="Humidity" value={`${currentWeather.main.humidity}%`} />
                    <Metric label="Wind" value={formatWindSpeed(currentWeather.wind_speed, selectedSearch.units)} />
                    <Metric label="Pressure" value={`${currentWeather.main.pressure} hPa`} />
                    <Metric label="Updated" value={formatDateTime(selectedSearch.updated_at)} />
                  </div>
                </div>

                <div className="summary-grid">
                  <div className="summary-card">
                    <span className="summary-label">Resolved city</span>
                    <strong>{selectedSearch.resolved_city ?? selectedSearch.location}</strong>
                  </div>
                  <div className="summary-card">
                    <span className="summary-label">Units</span>
                    <strong>{selectedSearch.units}</strong>
                  </div>
                  <div className="summary-card">
                    <span className="summary-label">Forecast count</span>
                    <strong>{summary?.forecast_count ?? selectedSearch.weather_data?.forecast.items.length ?? 0}</strong>
                  </div>
                  <div className="summary-card">
                    <span className="summary-label">Search key</span>
                    <strong className="truncate">{selectedSearch.search_key}</strong>
                  </div>
                </div>
              </>
            ) : (
              <div className="empty-state">
                <p>Run a search to load current weather, forecast, and persistence metadata.</p>
              </div>
            )}
          </section>

          <section className="panel forecast-panel">
            <div className="panel-heading">
              <div>
                <span className="section-label">Five-day forecast</span>
                <h2>Daily forecast overview</h2>
              </div>
              <span className="mono">{selectedForecast.length ? `${selectedForecast.length} day view` : "No forecast"}</span>
            </div>

            {selectedForecast.length ? (
              <div className="forecast-grid">
                {selectedForecast.map((day) => (
                  <article className="forecast-card" key={day.dayLabel}>
                    <div className="forecast-topline">
                      <span className="forecast-day">{day.dayLabel}</span>
                      <img
                        src={weatherIconUrl(day.icon) ?? ""}
                        alt={day.description}
                        className="forecast-icon"
                      />
                    </div>
                    <strong className="forecast-condition">{day.condition}</strong>
                    <p className="forecast-description">{day.description}</p>
                    <div className="forecast-temps">
                      <span className="forecast-high">{formatTemperature(day.high, selectedSearch?.units ?? "metric")}</span>
                      <span className="forecast-low">{formatTemperature(day.low, selectedSearch?.units ?? "metric")}</span>
                    </div>
                    <div className="forecast-metrics">
                      <span>Humidity {day.humidity}%</span>
                      <span>Wind {day.windSpeed !== null ? formatWindSpeed(day.windSpeed, selectedSearch?.units ?? "metric") : "—"}</span>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <p>The forecast strip will populate after your first weather search.</p>
              </div>
            )}
          </section>

          <section className="panel insight-panel">
            <div className="panel-heading">
              <div>
                <span className="section-label">AI insight</span>
                <h2>On-demand recommendation from persisted weather data</h2>
              </div>
              <button className="btn btn-secondary" type="button" onClick={() => void onGenerateInsight()} disabled={!selectedSearch || insightLoading}>
                {insightLoading ? "Working..." : "Generate insight"}
              </button>
            </div>

            {insight ? (
              <div className="insight-card">
                <div className="insight-topline">
                  <div>
                    <span className={`risk-pill risk-${insight.insight.risk_level}`}>{insight.insight.risk_level} risk</span>
                    <h3>{insight.insight.title}</h3>
                  </div>
                  <div className="score-box">
                    <span className="section-label">Outdoor score</span>
                    <strong>{insight.insight.outdoor_score}/100</strong>
                  </div>
                </div>

                <p className="insight-summary">{insight.insight.summary}</p>

                <div className="insight-lists">
                  <div>
                    <span className="section-label">Recommendations</span>
                    <ul className="bullet-list">
                      {insight.insight.recommendations.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <span className="section-label">Packing tips</span>
                    <ul className="bullet-list">
                      {insight.insight.packing_tips.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <p>Choose a saved search and click Generate insight to let the AI summarize conditions for you.</p>
              </div>
            )}
          </section>
        </section>

        <aside className="sidebar">
          <section className="panel map-panel">
            <div className="panel-heading">
              <div>
                <span className="section-label">Map</span>
                <h2>Selected location</h2>
              </div>
            </div>

            {mapUrl ? (
              <iframe
                title="Selected location map"
                src={mapUrl}
                className="map-iframe"
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
              />
            ) : (
              <div className="empty-state">
                <p>Pick a saved search to render the location map.</p>
              </div>
            )}
          </section>

          <section className="panel notes-panel">
            <div className="panel-heading">
              <div>
                <span className="section-label">Notes</span>
                <h2>Update persisted search</h2>
              </div>
            </div>

            <textarea
              className="notes-textarea"
              value={notesDraft}
              onChange={(event) => setNotesDraft(event.target.value)}
              placeholder="Add a note to this saved search..."
              rows={6}
              maxLength={1000}
              disabled={!selectedSearch}
            />
            <div className="notes-actions">
              <button className="btn btn-primary" type="button" onClick={() => void onSaveNotes()} disabled={!selectedSearch || savingNotes}>
                {savingNotes ? "Saving..." : "Save notes"}
              </button>
              <span className="mono">{notesDraft.length}/1000</span>
            </div>
          </section>

          <section className="panel export-panel">
            <div className="panel-heading">
              <div>
                <span className="section-label">Export</span>
                <h2>Download the selected record</h2>
              </div>
            </div>

            <div className="export-actions">
              <button className="btn btn-secondary" type="button" onClick={downloadJson} disabled={!selectedSearch}>
                JSON
              </button>
              <button className="btn btn-secondary" type="button" onClick={downloadCsv} disabled={!selectedSearch}>
                CSV
              </button>
              <button className="btn btn-secondary" type="button" onClick={downloadMarkdown} disabled={!selectedSearch}>
                Markdown
              </button>
            </div>
          </section>

          <section className="panel history-panel">
            <div className="panel-heading">
              <div>
                <span className="section-label">Search history</span>
                <h2>Persisted weather queries</h2>
              </div>
              <span className="mono">{history.length} rows</span>
            </div>

            {loadingHistory ? (
              <div className="empty-state">
                <p>Loading history...</p>
              </div>
            ) : history.length ? (
              <div className="history-table-wrap">
                <table className="history-table">
                  <thead>
                    <tr>
                      <th>City</th>
                      <th>Units</th>
                      <th>Saved</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((record) => {
                      const isSelected = selectedSearch?.id === record.id;
                      return (
                        <tr key={record.id} className={isSelected ? "selected-row" : undefined}>
                          <td>
                            <button type="button" className="table-link" onClick={() => onSelectSearch(record)}>
                              {record.resolved_city ?? record.location}
                            </button>
                            <div className="table-subtext">{record.country_code ?? "—"}</div>
                          </td>
                          <td>{record.units}</td>
                          <td>{formatDateTime(record.created_at)}</td>
                          <td>
                            <div className="row-actions">
                              <button type="button" className="mini-btn" onClick={() => onSelectSearch(record)}>
                                View
                              </button>
                              <button type="button" className="mini-btn" onClick={() => void onGenerateInsight(record)}>
                                AI
                              </button>
                              <button
                                type="button"
                                className="mini-btn danger"
                                onClick={() => void onDeleteSearch(record.id)}
                                disabled={deletingId === record.id}
                              >
                                {deletingId === record.id ? "Deleting..." : "Delete"}
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-state">
                <p>No saved searches yet. Search for a city to populate this table.</p>
              </div>
            )}
          </section>
        </aside>
      </main>

      <footer className="footer panel">
        <div>
          <strong>Built for the PM Accelerator assessment by Rahul.</strong>
          <p>
            Bloomberg-inspired weather terminal, full-stack backend wiring, saved search persistence, and on-demand AI
            insight.
          </p>
        </div>
        <div className="footer-meta">
          <span className="mono">Weather search + persistence + AI insight</span>
          <span className="mono">Desktop-first, responsive layout</span>
        </div>
      </footer>
    </div>
  );
}

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 64);
}

export default App;
